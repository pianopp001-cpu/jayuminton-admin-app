from __future__ import annotations

import argparse
import os
import re
from pathlib import Path


def patch_main(path: Path) -> None:
    s = path.read_text(encoding="utf-8")
    end = s.rfind("</script>")
    if end < 0:
        raise SystemExit("Script closing tag missing")
    s = s[: end + len("</script>")] + "\n"

    a = s.find("function compactMemberSelfSettings() {")
    b = s.find("function requestMemberAppInstall() {", a)
    if a < 0 or b < 0:
        raise SystemExit("compactMemberSelfSettings block missing")

    replacement = r'''function compactMemberSelfSettings() {
  let selected = currentStoredWebPushMember();
  const input = document.getElementById('memberSelfSearchInput');
  const typed = String(input && input.value || '').trim();

  // member-complete-auto-select-v12
  // If the user typed another name, never reuse the previously stored member silently.
  if (input && input.dataset.userEditing === '1' && typed) {
    const matches = memberSelfSearchMatches();
    const typedLower = typed.toLocaleLowerCase('ko-KR');
    const exact = matches.find(function(member) {
      return member && String(member.name || '').trim().toLocaleLowerCase('ko-KR') === typedLower;
    });
    const candidate = exact || (matches.length === 1 ? matches[0] : null);
    if (candidate) {
      selectMemberSelf(candidate.id);
      selected = {id:String(candidate.id), name:String(candidate.name || '').trim()};
    } else {
      showMemberSettingMessage('검색 결과에서 본인 이름을 선택하세요.', true);
      if (input) input.focus();
      return;
    }
  }

  if (!selected) {
    if (input) input.focus();
    showMemberSettingMessage('먼저 내 이름을 선택하세요.', true);
    return;
  }
  if (memberAlertEnabled()) {
    postUnifiedMemberMessage('JAYUMINTON_PUSH_SETUP_REQUEST', {
      member: selected,
      authVersion: currentMemberAuthVersion()
    });
  } else {
    postUnifiedMemberMessage('JAYUMINTON_PUSH_DISCONNECT_REQUEST', {member:selected});
  }
  if (input) input.dataset.userEditing = '0';
  try { localStorage.setItem(MEMBER_SELF_PANEL_COMPACT_KEY, 'true'); }
  catch (error) {}
  renderMemberSelfSettings();
}

'''
    s = s[:a] + replacement + s[b:]
    path.write_text(s, encoding="utf-8")

    check = path.read_text(encoding="utf-8")
    if "member-complete-auto-select-v12" not in check:
        raise SystemExit("MAIN patch marker missing")


def patch_pwa(root: Path, main_url: str, push_url: str) -> None:
    p = root / "setup-v205.js"
    s = p.read_text(encoding="utf-8")

    # Remove the Drive-risk browser fallback from the Android Chrome intent.
    s, n = re.subn(
        r"'category=android\.intent\.category\.BROWSABLE;S\.browser_fallback_url='\s*\+\s*encodeURIComponent\(targetUrl\)\s*\+\s*';end'",
        "'category=android.intent.category.BROWSABLE;end'",
        s,
        count=1,
    )
    if n != 1:
        raise SystemExit("Android browser fallback block missing")

    # Remember the user's Chrome-side install tap instead of asking for endless repeat taps.
    old = """      setInstallIntentArmed(true);\n      ensureChromeInstallControl();\n      const detail = '설치창을 준비 중입니다. 잠시 뒤 다시 누르거나 Chrome ⋮ 메뉴의 앱 설치를 선택하세요.';\n"""
    new = """      // auto-install-prompt-v12\n      installAttemptPending = true;\n      setInstallIntentArmed(true);\n      ensureChromeInstallControl();\n      const detail = '설치창을 준비 중입니다. 준비되는 즉시 시스템 설치창을 엽니다.';\n"""
    if old not in s:
        raise SystemExit("Chrome no-prompt branch missing")
    s = s.replace(old, new, 1)

    # If beforeinstallprompt arrives after that tap, consume it automatically.
    old = """    deferredInstallPrompt = event;\n    window.__JAYUMINTON_EARLY_INSTALL_PROMPT = null;\n    installAttemptPending = false;\n"""
    new = """    const shouldAutoPrompt = Boolean(installAttemptPending || installIntentArmed);\n    deferredInstallPrompt = event;\n    window.__JAYUMINTON_EARLY_INSTALL_PROMPT = null;\n    installAttemptPending = false;\n"""
    if old not in s:
        raise SystemExit("beforeinstallprompt capture state missing")
    s = s.replace(old, new, 1)

    old = """    refreshInstallState();\n    showToast('설치 준비 완료: PWA 설치 버튼을 눌러 주세요.');\n"""
    new = """    refreshInstallState();\n    if (shouldAutoPrompt) {\n      setTimeout(function() { installAndroidUserApp(true); }, 0);\n    } else {\n      showToast('설치 준비 완료: PWA 설치 버튼을 눌러 주세요.');\n    }\n"""
    if old not in s:
        raise SystemExit("beforeinstallprompt completion block missing")
    s = s.replace(old, new, 1)

    # Always accept the member selected by MAIN before reconnecting the push token.
    marker = "} else if (data.type === 'JAYUMINTON_PUSH_SETUP_REQUEST') {"
    start = s.find(marker)
    stop = s.find("} else if (data.type === 'JAYUMINTON_PUSH_DISCONNECT_REQUEST')", start)
    if start < 0 or stop < 0:
        raise SystemExit("PUSH setup branch missing")
    replacement = r'''} else if (data.type === 'JAYUMINTON_PUSH_SETUP_REQUEST') {
      if (data.member && data.member.id && data.member.name) {
        member = {id:String(data.member.id), name:String(data.member.name)};
        saveJson(STORAGE.member, member);
        nameInput.value = shortName(member.name);
        isConnected = false;
      }
      connectAlarm();
    '''
    s = s[:start] + replacement + s[stop:]
    p.write_text(s, encoding="utf-8")

    idx = root / "index.html"
    t = idx.read_text(encoding="utf-8")
    t = t.replace("/setup-v205.js?v=1637", "/setup-v205.js?v=1637-actualfix12")
    t = t.replace("/config-v204.js?v=1637", "/config-v204.js?v=1637-actualfix12")
    idx.write_text(t, encoding="utf-8")

    template = Path("deployment/jayuminton/v1637-web/config-v204.template.js").read_text(encoding="utf-8")
    cfg = template.replace("__MEMBER_PAGE_URL__", main_url).replace("__RELAY_URL__", push_url)
    if "__MEMBER_PAGE_URL__" in cfg or "__RELAY_URL__" in cfg:
        raise SystemExit("Config URL injection failed")
    for name in ("config-v202.js", "config-v203.js", "config-v204.js"):
        (root / name).write_text(cfg, encoding="utf-8")

    sw = root / "firebase-messaging-sw.js"
    w = sw.read_text(encoding="utf-8")
    w = w.replace("const JAYUMINTON_SW_VERSION = '1.6.37';", "const JAYUMINTON_SW_VERSION = '1.6.37-actualfix12';")
    w = w.replace("const JAYUMINTON_CACHE = 'jayuminton-shell-v205';", "const JAYUMINTON_CACHE = 'jayuminton-shell-v224';")
    sw.write_text(w, encoding="utf-8")

    final = p.read_text(encoding="utf-8")
    required = ["auto-install-prompt-v12", "shouldAutoPrompt", "JAYUMINTON_PUSH_SETUP_REQUEST"]
    for marker_text in required:
        if marker_text not in final:
            raise SystemExit("PWA patch marker missing: " + marker_text)
    if "S.browser_fallback_url" in final:
        raise SystemExit("Drive-risk browser fallback remains")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    m = sub.add_parser("main")
    m.add_argument("path")
    p = sub.add_parser("pwa")
    p.add_argument("root")
    p.add_argument("--main-url", required=True)
    p.add_argument("--push-url", required=True)
    args = parser.parse_args()

    if args.mode == "main":
        patch_main(Path(args.path))
    else:
        patch_pwa(Path(args.root), args.main_url, args.push_url)


if __name__ == "__main__":
    main()
