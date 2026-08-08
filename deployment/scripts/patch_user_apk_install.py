#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_user_apk_install.py <apps-script-root>')

root = Path(sys.argv[1])
script_path = root / 'Script.html'
index_path = root / 'Index.html'

APK_URL = 'https://github.com/pianopp001-cpu/jayuminton-admin-app/raw/refs/heads/main/releases/jayuminton-user-v1.0.0.apk'


def replace_function(src: str, name: str, replacement: str) -> str:
    patterns = [f'async function {name}(', f'function {name}(']
    start = -1
    for token in patterns:
        start = src.find(token)
        if start >= 0:
            break
    if start < 0:
        raise SystemExit(f'{name} missing')
    brace = src.find('{', start)
    if brace < 0:
        raise SystemExit(f'{name} opening brace missing')
    depth = 0
    quote = None
    escape = False
    i = brace
    while i < len(src):
        ch = src[i]
        if quote:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch in "'\"`":
            quote = ch
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return src[:start] + replacement + src[i + 1:]
        i += 1
    raise SystemExit(f'{name} unbalanced')


script = script_path.read_text(encoding='utf-8')

# Remove older versions of the native-user constants if this patch is re-run.
script = re.sub(
    r"\nconst MEMBER_USER_APK_URL\s*=\s*[^;]+;\nconst MEMBER_USER_APK_HINT\s*=.*?;\n",
    '\n',
    script,
    flags=re.S,
)

anchor = "const UNIFIED_MEMBER_APP_URL =\n  'https://jayuminton-push.web.app/';"
if anchor not in script:
    raise SystemExit('UNIFIED_MEMBER_APP_URL anchor missing')
insert = anchor + "\nconst MEMBER_USER_APK_URL =\n  '" + APK_URL + "';\nconst MEMBER_USER_APK_HINT =\n  /JayumintonUserNative\\/1\\.0\\.0/i.test(String(navigator.userAgent || '')) ||\n  window.__JAYUMINTON_USER_APK__ === true ||\n  !!window.NativeUserApp;"
script = script.replace(anchor, insert, 1)

# Make APK installation the only meaning of the install toggle state.
state_pattern = re.compile(r"let MEMBER_APP_INSTALL_STATE\s*=\s*\{.*?\};")
state_replacement = (
    "let MEMBER_APP_INSTALL_STATE = {"
    "installed:MEMBER_USER_APK_HINT,"
    "choice:MEMBER_USER_APK_HINT?'on':'',"
    "platform:/Android/i.test(String(navigator.userAgent||''))?'android':'other',"
    "browserContext:MEMBER_USER_APK_HINT?'user-apk':'other',"
    "message:'',ready:true,installing:false,armed:false,prepRemaining:0,nativeInstall:true};"
)
script, n = state_pattern.subn(state_replacement, script, count=1)
if n != 1:
    raise SystemExit('MEMBER_APP_INSTALL_STATE replacement failed')

request_install = f"""function requestMemberAppInstall() {{
  publishMemberAppInstallButtonRect();

  if (MEMBER_USER_APK_HINT) {{
    MEMBER_APP_INSTALL_STATE.installed = true;
    MEMBER_APP_INSTALL_STATE.choice = 'on';
    MEMBER_APP_INSTALL_STATE.browserContext = 'user-apk';
    MEMBER_APP_INSTALL_STATE.ready = true;
    MEMBER_APP_INSTALL_STATE.installing = false;
    MEMBER_APP_INSTALL_STATE.prepRemaining = 0;
    MEMBER_APP_INSTALL_STATE.nativeInstall = true;
    renderMemberSelfSettings();
    showMemberSettingMessage('자유민턴 사용자 앱이 설치되어 있습니다.');
    return;
  }}

  MEMBER_APP_INSTALL_STATE.installed = false;
  MEMBER_APP_INSTALL_STATE.choice = '';
  MEMBER_APP_INSTALL_STATE.ready = true;
  MEMBER_APP_INSTALL_STATE.installing = true;
  MEMBER_APP_INSTALL_STATE.prepRemaining = 0;
  MEMBER_APP_INSTALL_STATE.nativeInstall = true;
  renderMemberSelfSettings();
  showMemberSettingMessage('사용자용 APK 다운로드를 시작합니다. 다운로드 후 설치하고 앱을 열어 주세요.');

  try {{
    if (window.top && window.top.location) {{
      window.top.location.href = MEMBER_USER_APK_URL;
    }} else {{
      window.location.href = MEMBER_USER_APK_URL;
    }}
  }} catch (error) {{
    try {{ window.location.href = MEMBER_USER_APK_URL; }} catch (_) {{}}
  }}

  setTimeout(function() {{
    if (MEMBER_USER_APK_HINT) return;
    MEMBER_APP_INSTALL_STATE.installing = false;
    renderMemberSelfSettings();
  }}, 2500);
}}"""
script = replace_function(script, 'requestMemberAppInstall', request_install)

# Force the display state to reflect the real native APK signal, not the old PWA state.
render_token = 'function renderMemberSelfSettings() {'
render_pos = script.find(render_token)
if render_pos < 0:
    raise SystemExit('renderMemberSelfSettings missing')
body_pos = render_pos + len(render_token)
render_guard = """
  if (MEMBER_USER_APK_HINT) {
    MEMBER_APP_INSTALL_STATE.installed = true;
    MEMBER_APP_INSTALL_STATE.choice = 'on';
    MEMBER_APP_INSTALL_STATE.browserContext = 'user-apk';
    MEMBER_APP_INSTALL_STATE.ready = true;
    MEMBER_APP_INSTALL_STATE.installing = false;
    MEMBER_APP_INSTALL_STATE.prepRemaining = 0;
    MEMBER_APP_INSTALL_STATE.nativeInstall = true;
  } else {
    MEMBER_APP_INSTALL_STATE.installed = false;
    MEMBER_APP_INSTALL_STATE.choice = '';
    MEMBER_APP_INSTALL_STATE.ready = true;
    MEMBER_APP_INSTALL_STATE.nativeInstall = true;
    MEMBER_APP_INSTALL_STATE.prepRemaining = 0;
  }
"""
# Avoid duplicate insertion if the script is patched again.
if 'MEMBER_USER_APK_HINT) {' not in script[body_pos:body_pos + 900]:
    script = script[:body_pos] + render_guard + script[body_pos:]

label_pattern = re.compile(
    r"let installLabel = '앱 설치';.*?appInstallButton\.textContent = installLabel;",
    re.S,
)
label_replacement = """let installLabel = MEMBER_APP_INSTALL_STATE.installed
      ? '앱설치 ON'
      : (MEMBER_APP_INSTALL_STATE.installing ? '앱설치 중' : '앱설치');
    appInstallButton.textContent = installLabel;"""
script, n = label_pattern.subn(label_replacement, script, count=1)
if n != 1:
    raise SystemExit('install label block replacement failed')

# This old address-copy instruction must never remain in live user install behavior.
if '아래 주소를 길게 눌러 복사한 뒤 Chrome 앱을 열어 붙여넣어 주세요' in script:
    # It may remain in an unused helper branch in old source. Remove the user-facing phrase globally.
    script = script.replace(
        "showMemberSettingMessage('아래 주소를 길게 눌러 복사한 뒤 Chrome 앱을 열어 붙여넣어 주세요: ' + installUrl);",
        "showMemberSettingMessage('사용자용 APK를 설치해 주세요.');",
    )

script_path.write_text(script, encoding='utf-8')

index = index_path.read_text(encoding='utf-8')
index = index.replace('>앱/웹</button>', '>앱설치</button>', 1)
index_path.write_text(index, encoding='utf-8')

# Hard verification of the requested UX.
checks = [
    'JayumintonUserNative\\/1\\.0\\.0',
    '!!window.NativeUserApp',
    APK_URL,
    "? '앱설치 ON'",
    "MEMBER_APP_INSTALL_STATE.installed = true;",
    "window.top.location.href = MEMBER_USER_APK_URL;",
]
for needle in checks:
    if needle not in script:
        raise SystemExit('missing patched marker: ' + needle)
if '앱 설치완료' in script:
    raise SystemExit('legacy install-complete label still present')
if '설치 준비 ' in script:
    raise SystemExit('legacy PWA preparation label still present')
if 'Chrome 열기' in script:
    raise SystemExit('legacy Chrome install label still present')
if '>앱설치</button>' not in index:
    raise SystemExit('Index initial install label was not updated')

print('User APK install UX patch verified.')
