#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = "JAYUMINTON_PUSH_SERVER_VERIFY_V1"
INSTALL_MARKER = "JAYUMINTON_NATIVE_PWA_ONLY_V1"


def function_bounds(source: str, name: str):
    token = f"function {name}("
    function_start = source.find(token)
    if function_start < 0:
        return None
    start = function_start
    # Include an existing `async ` prefix so replacing an async function cannot
    # accidentally leave `async async function ...` behind.
    if function_start >= 6 and source[function_start - 6:function_start] == "async ":
        start = function_start - 6
    brace = source.find("{", function_start)
    if brace < 0:
        return None

    depth = 0
    quote = None
    escaped = False
    i = brace
    while i < len(source):
        ch = source[i]
        if quote is not None:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"', "`"):
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
        i += 1
    return None


def replace_js_function(source: str, name: str, replacement: str) -> str:
    bounds = function_bounds(source, name)
    if not bounds:
        raise RuntimeError(f"{name} missing or unbalanced")
    start, end = bounds
    return source[:start] + replacement + source[end:]


def replace_exact_once(source: str, old: str, new: str, label: str) -> str:
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise RuntimeError(f"{label} changed unexpectedly")


def assert_no_legacy_handoffs(source: str) -> None:
    forbidden = {
        "intent://": "Android intent handoff",
        "S.browser_fallback_url": "Android browser fallback resolver",
        "drive.google": "Google Drive handoff",
        "docs.google.com": "Google Docs/Drive handoff",
        "appInstallChromeLink.href = links.intentUrl": "transparent intent link",
        "window.location.href = links.intentUrl": "JavaScript intent navigation",
    }
    found = [label for token, label in forbidden.items() if token in source]
    if found:
        raise RuntimeError("legacy external handoff remains: " + ", ".join(found))


def patch_native_pwa_only(source: str) -> str:
    required_native_markers = (
        "window.addEventListener('beforeinstallprompt', captureAndroidInstallPrompt);",
        "promptResult = promptEvent.prompt();",
    )
    missing_native = [marker for marker in required_native_markers if marker not in source]
    if missing_native:
        raise RuntimeError("native PWA prompt baseline missing: " + repr(missing_native))

    source = replace_js_function(
        source,
        "buildAndroidChromeIntent",
        f"""/* {INSTALL_MARKER} */
function buildAndroidChromeIntent() {{
  const target = buildChromeUserTarget();
  const targetUrl = target.toString();
  // Compatibility-shaped object only. No Android intent/external resolver is used.
  return {{ targetUrl, intentUrl: targetUrl }};
}}""",
    )

    source = replace_js_function(
        source,
        "launchChromeFromFirebaseTop",
        """function launchChromeFromFirebaseTop() {
  const targetUrl = buildChromeUserTarget().toString();
  const detail = 'Chrome 앱에서 아래 주소를 열어 주세요: ' + targetUrl;
  setInstallMessage(detail, 'success');
  sendAppInstallStatus(detail);
  showToast('Chrome에서 링크를 열어 주세요.');
  return targetUrl;
}""",
    )

    source = replace_js_function(
        source,
        "handleEmbeddedChromeLinkClick",
        """function handleEmbeddedChromeLinkClick(event) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  const targetUrl = buildChromeUserTarget().toString();
  const detail = 'Chrome 앱에서 아래 주소를 열어 주세요: ' + targetUrl;
  setInstallMessage(detail, 'success');
  sendAppInstallStatus(detail);
  showToast('Chrome에서 링크를 열어 주세요.');
}""",
    )

    old_overlay = """if (androidDevice && embeddedBrowser) {
      const links = buildAndroidChromeIntent();
      appInstallChromeLink.href = links.intentUrl;
      appInstallChromeLink.style.left = left;
      appInstallChromeLink.style.top = top;
      appInstallChromeLink.style.width = width;
      appInstallChromeLink.style.height = height;
      appInstallChromeLink.hidden = false;
      appInstallClickProxy.hidden = true;
      if (nativeInstallControl) nativeInstallControl.hidden = true;
      return;
    }"""
    new_overlay = """if (androidDevice && embeddedBrowser) {
      appInstallChromeLink.removeAttribute('href');
      appInstallChromeLink.hidden = true;
      appInstallClickProxy.hidden = true;
      if (nativeInstallControl) nativeInstallControl.hidden = true;
      return;
    }"""
    source = replace_exact_once(source, old_overlay, new_overlay, "embedded install overlay")

    old_touch = """appInstallChromeLink.addEventListener('touchstart', () => {
    if (androidDevice && embeddedBrowser) appInstallChromeLink.href = buildAndroidChromeIntent().intentUrl;
  }, {passive:true});"""
    new_touch = """appInstallChromeLink.addEventListener('touchstart', () => {
    if (androidDevice && embeddedBrowser) appInstallChromeLink.removeAttribute('href');
  }, {passive:true});"""
    source = replace_exact_once(source, old_touch, new_touch, "embedded install touch handler")

    bounds = function_bounds(source, "handleAppInstallButton")
    if not bounds:
        raise RuntimeError("handleAppInstallButton missing")
    start, end = bounds
    block = source[start:end]
    old_branch = """if (androidDevice && embeddedBrowser) {
      const detail = 'Chrome에서 설치 화면을 준비합니다.';
      setInstallMessage(detail, 'success');
      sendAppInstallStatus(detail);
      showToast('Chrome으로 이동합니다.');
      openInAndroidChrome();
      return;
    }"""
    new_branch = """if (androidDevice && embeddedBrowser) {
      const targetUrl = buildChromeUserTarget().toString();
      const detail = 'Chrome 앱에서 아래 주소를 열어 주세요: ' + targetUrl;
      setInstallMessage(detail, 'success');
      sendAppInstallStatus(detail);
      showToast('Chrome에서 링크를 열어 주세요.');
      return;
    }"""
    if old_branch in block:
        block = block.replace(old_branch, new_branch, 1)
    elif new_branch not in block:
        raise RuntimeError("embedded Android install button branch changed unexpectedly")
    source = source[:start] + block + source[end:]

    source = source.replace(
        "// v1.6.37: embedded browsers use a real top-level intent link; Chrome uses the native beforeinstallprompt event without reload loops.",
        "// Embedded browsers never invoke external resolvers; real Chrome uses the native beforeinstallprompt event without reload loops.",
    )
    source = source.replace(
        "// Kakao/Daangn WebView must receive a real top-level <a href=\"intent://...\">\n    // generated from the user's direct tap. JavaScript location changes can be blocked\n    // or converted into a refresh by the host app.",
        "// Embedded Android browsers do not receive a transparent external-app handoff overlay.",
    )

    assert_no_legacy_handoffs(source)
    for marker in required_native_markers:
        if marker not in source:
            raise RuntimeError("native PWA prompt was lost after patch: " + marker)
    if INSTALL_MARKER not in source:
        raise RuntimeError("native-PWA-only install marker missing")
    return source


def main(js_path: Path) -> None:
    source = js_path.read_text(encoding="utf-8")
    source = patch_native_pwa_only(source)

    submit_replacement = f"""/* {MARKER} */
async function jayumintonPushTokenHash(value) {{
  const bytes = new TextEncoder().encode(String(value || ''));
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('');
}}

function jayumintonPushJsonp(baseUrl, params, callbackName) {{
  return new Promise((resolve, reject) => {{
    const script = document.createElement('script');
    const timeout = setTimeout(() => finish(new Error('PUSH 서버 확인 시간이 초과되었습니다.')), 8000);

    function finish(error, value) {{
      clearTimeout(timeout);
      try {{ delete window[callbackName]; }} catch (_) {{ window[callbackName] = undefined; }}
      if (script.parentNode) script.parentNode.removeChild(script);
      if (error) reject(error); else resolve(value);
    }}

    window[callbackName] = (value) => finish(null, value);
    const target = new URL(baseUrl);
    Object.keys(params || {{}}).forEach((key) => target.searchParams.set(key, String(params[key])));
    script.src = target.toString();
    script.async = true;
    script.onerror = () => finish(new Error('PUSH 서버 연결 확인에 실패했습니다.'));
    document.head.appendChild(script);
  }});
}}

async function verifyRelayToken(memberId, token) {{
  const tokenHash = await jayumintonPushTokenHash(token);
  const callbackName = '__jayumintonRelayStatus205_' + Date.now() + '_' + Math.floor(Math.random() * 1000000);
  const response = await jayumintonPushJsonp(cfg.relayUrl, {{
    action:'token_status',
    memberId:String(memberId || ''),
    tokenHash,
    callback:callbackName
  }}, callbackName);
  return Boolean(response && response.ok && response.registered);
}}

async function submitRelay(action, token) {{
  const targetMember = member && member.id
    ? {{id:String(member.id), name:String(member.name || '')}}
    : null;
  if (!targetMember || !token) throw new Error('알림 받을 회원 또는 토큰 정보가 없습니다.');

  const body = new URLSearchParams();
  body.set('payload', JSON.stringify({{
    action,
    memberId:targetMember.id,
    memberName:targetMember.name,
    token,
    userAgent:navigator.userAgent
  }}));
  await fetch(cfg.relayUrl, {{
    method:'POST',
    mode:'no-cors',
    headers:{{'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8'}},
    body:body.toString(),
    keepalive:true
  }});

  const expectedRegistered = action === 'register_web_token'
    ? true
    : action === 'unregister_web_token'
      ? false
      : null;
  if (expectedRegistered === null) return true;

  for (let attempt = 0; attempt < 4; attempt += 1) {{
    const registered = await verifyRelayToken(targetMember.id, token);
    if (registered === expectedRegistered) return true;
    await new Promise((resolve) => setTimeout(resolve, 350 * (attempt + 1)));
  }}

  throw new Error(expectedRegistered
    ? 'PUSH 서버 연결 확인에 실패했습니다. 잠시 후 다시 눌러 주세요.'
    : 'PUSH 서버 해지 확인에 실패했습니다. 잠시 후 다시 눌러 주세요.');
}}"""

    source = replace_js_function(source, "submitRelay", submit_replacement)

    refresh_replacement = """async function refreshConnectionState() {
  const token = localStorage.getItem(STORAGE.token);
  if (!(member && token && 'Notification' in window && Notification.permission === 'granted')) {
    setOff(member ? '알림 연결이 꺼져 있습니다.' : '직접 입력하거나 명단에서 이름을 누르세요.');
    return;
  }

  try {
    const instance = await initializeMessaging();
    const currentToken = await instance.getToken({
      vapidKey:cfg.vapidKey,
      serviceWorkerRegistration:registration
    });
    if (!currentToken) throw new Error('알림 연결이 끊어졌습니다.');

    if (currentToken !== token) {
      await submitRelay('register_web_token', currentToken);
      localStorage.setItem(STORAGE.token, currentToken);
    } else if (!(await verifyRelayToken(member.id, currentToken))) {
      throw new Error('PUSH 서버에 연결 정보가 없습니다.');
    }

    setConnected();
  } catch (error) {
    setOff('알림 연결이 끊어졌습니다. 완료를 눌러 다시 연결해 주세요.');
    sendCourtMessage('JAYUMINTON_UNIFIED_PUSH_STATUS', {
      connected:false,
      member,
      message:'알림 연결이 끊어졌습니다.'
    });
  }
}"""
    source = replace_js_function(source, "refreshConnectionState", refresh_replacement)

    old_bootstrap = "pushConnected:Boolean(localStorage.getItem(STORAGE.token) && member && 'Notification' in window && Notification.permission === 'granted'),"
    new_bootstrap = "pushConnected:Boolean(isConnected && localStorage.getItem(STORAGE.token) && member && 'Notification' in window && Notification.permission === 'granted'),"
    if old_bootstrap in source:
        source = source.replace(old_bootstrap, new_bootstrap, 1)
    elif new_bootstrap not in source:
        raise RuntimeError("pushConnected bootstrap expression changed unexpectedly")

    assert_no_legacy_handoffs(source)
    if "promptResult = promptEvent.prompt();" not in source:
        raise RuntimeError("native Chrome PWA prompt missing after push patch")
    if "async async function" in source:
        raise RuntimeError("duplicate async prefix remains after patch")
    js_path.write_text(source, encoding="utf-8")

    final = js_path.read_text(encoding="utf-8")
    required = [
        INSTALL_MARKER,
        "promptResult = promptEvent.prompt();",
        MARKER,
        "async function verifyRelayToken(memberId, token)",
        "action:'token_status'",
        "PUSH 서버 연결 확인에 실패했습니다.",
        "else if (!(await verifyRelayToken(member.id, currentToken)))",
        "pushConnected:Boolean(isConnected && localStorage.getItem(STORAGE.token)",
    ]
    missing = [item for item in required if item not in final]
    if missing:
        raise RuntimeError("final checks missing: " + repr(missing))

    print("Native-PWA-only install and push server-verification patch validated")


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise RuntimeError("usage: patch_push_setup_verification.py <setup-v205.js>")
        main(Path(sys.argv[1]).resolve())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
