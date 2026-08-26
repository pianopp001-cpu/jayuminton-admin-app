#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_user_route_guard.py <apps-script-root>')

root = Path(sys.argv[1])
code_path = root / 'Code.js'
if not code_path.exists():
    raise SystemExit('Code.js missing')

src = code_path.read_text(encoding='utf-8')

def replace_function(text: str, name: str, replacement: str) -> str:
    token = f'function {name}('
    start = text.find(token)
    if start < 0:
        raise SystemExit(f'{name} missing')
    brace = text.find('{', start)
    if brace < 0:
        raise SystemExit(f'{name} opening brace missing')
    depth = 0
    quote = None
    escape = False
    i = brace
    while i < len(text):
        ch = text[i]
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
                return text[:start] + replacement + text[i + 1:]
        i += 1
    raise SystemExit(f'{name} unbalanced')

replacement = r'''function doGet(e) {
  ensureSetup_();

  const requestedMode = String(
    e && e.parameter && e.parameter.mode || ''
  ).trim().toLowerCase();

  // Safety rule: ONLY an explicit ?mode=admin may open the admin page.
  // User web, user APK, missing mode, apkUser=1 and mode=user always use Index.
  const isAdmin = requestedMode === 'admin';

  const template = HtmlService.createTemplateFromFile(
    isAdmin ? 'Admin' : 'Index'
  );

  if (!isAdmin) {
    template.memberPageUrl = ScriptApp.getService().getUrl() || '';
    template.pushReturn = JSON.stringify({
      connected: Boolean(e && e.parameter && e.parameter.push === 'on'),
      memberId: String(e && e.parameter && e.parameter.pushMemberId || ''),
      memberName: String(e && e.parameter && e.parameter.pushMemberName || '')
    });
  }

  return template
    .evaluate()
    .setTitle(
      isAdmin
        ? '자유민턴 코트배정 관리자'
        : '자유민턴 코트배정 현황'
    )
    .addMetaTag(
      'viewport',
      'width=device-width,initial-scale=1'
    )
    .setXFrameOptionsMode(
      HtmlService.XFrameOptionsMode.ALLOWALL
    );
}'''

src = replace_function(src, 'doGet', replacement)

required = [
    "const isAdmin = requestedMode === 'admin';",
    "isAdmin ? 'Admin' : 'Index'",
    "template.memberPageUrl = ScriptApp.getService().getUrl() || '';",
]
for marker in required:
    if marker not in src:
        raise SystemExit('user route marker missing: ' + marker)

code_path.write_text(src, encoding='utf-8')
print('USER_ROUTE_GUARD_OK')
