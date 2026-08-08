#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = "JAYUMINTON_PUSH_SERVER_VERIFY_V1"


def replace_js_function(source: str, name: str, replacement: str) -> str:
    token = f"function {name}("
    start = source.find(token)
    if start < 0:
        raise RuntimeError(f"{name} missing")
    brace = source.find("{", start)
    if brace < 0:
        raise RuntimeError(f"{name} opening brace missing")

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
                return source[:start] + replacement + source[i + 1 :]
        i += 1

    raise RuntimeError(f"{name} braces are unbalanced")


def main(js_path: Path) -> None:
    source = js_path.read_text(encoding="utf-8")

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

    js_path.write_text(source, encoding="utf-8")

    final = js_path.read_text(encoding="utf-8")
    required = [
        MARKER,
        "async function verifyRelayToken(memberId, token)",
        "action:'token_status'",
        "PUSH 서버 연결 확인에 실패했습니다.",
        "else if (!(await verifyRelayToken(member.id, currentToken)))",
        "pushConnected:Boolean(isConnected && localStorage.getItem(STORAGE.token)",
    ]
    missing = [item for item in required if item not in final]
    if missing:
        raise RuntimeError("push verification checks missing: " + repr(missing))

    print("Push token server-verification patch validated")


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise RuntimeError("usage: patch_push_setup_verification.py <setup-v205.js>")
        main(Path(sys.argv[1]).resolve())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
