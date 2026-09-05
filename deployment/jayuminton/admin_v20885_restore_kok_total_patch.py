#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
html = path.read_text(encoding='utf-8')
MARKER = 'jmAdminRestoreKokTotalV20885'

if MARKER in html:
    print('ADMIN_RESTORE_KOK_TOTAL_V20885_ALREADY_OK')
    raise SystemExit(0)

for required in (
    'jmAdminUniversalUndoV20884',
    'jmAdminKokCompactV20882',
    '완료 총 0명 · 남자 0명 · 여자 0명',
    "var maleDoneCount = 0;",
    "var femaleDoneCount = 0;",
):
    if required not in html:
        raise SystemExit('v208.85 prerequisite missing: ' + required)

OLD_INITIAL = '완료 총 0명 · 남자 0명 · 여자 0명'
NEW_INITIAL = '총 콕개수 0개  완료: 총 0명 (남자: 0명 여자: 0명)'
if html.count(OLD_INITIAL) != 1:
    raise SystemExit(f'kok initial summary mismatch: {html.count(OLD_INITIAL)}')
html = html.replace(OLD_INITIAL, NEW_INITIAL, 1)

OLD_BLOCK = """var doneCount = 0;
  var maleDoneCount = 0;
  var femaleDoneCount = 0;
  all.forEach(function(member) {
    if (member.kokInactive) {
      doneCount += 1;
      if (member.gender === 'female') femaleDoneCount += 1;
      else maleDoneCount += 1;
    }
  });
  if (totalEl) {
    totalEl.textContent = '완료 총 ' + doneCount + '명 · 남자 ' + maleDoneCount + '명 · 여자 ' + femaleDoneCount + '명';
  }"""
NEW_BLOCK = """var doneCount = 0;
  var maleDoneCount = 0;
  var femaleDoneCount = 0;
  var kokTotal = 0;
  all.forEach(function(member) {
    if (member.kokInactive) {
      doneCount += 1;
      if (member.gender === 'female') {
        femaleDoneCount += 1;
        kokTotal += 1;
      } else {
        maleDoneCount += 1;
        kokTotal += 2;
      }
    }
  });
  if (totalEl) {
    totalEl.textContent = '총 콕개수 ' + kokTotal + '개  완료: 총 ' + doneCount + '명 (남자: ' + maleDoneCount + '명 여자: ' + femaleDoneCount + '명)';
  }"""
if html.count(OLD_BLOCK) != 1:
    raise SystemExit(f'kok summary block mismatch: {html.count(OLD_BLOCK)}')
html = html.replace(OLD_BLOCK, NEW_BLOCK, 1)

marker = '<style id="jmAdminRestoreKokTotalV20885Style">/* jmAdminRestoreKokTotalV20885; counter text only, no font-size change */</style>'
if html.count('</head>') != 1:
    raise SystemExit('</head> anchor not unique')
html = html.replace('</head>', marker + '</head>', 1)

for required in (
    MARKER,
    NEW_INITIAL,
    'var kokTotal = 0;',
    'kokTotal += 1;',
    'kokTotal += 2;',
    "totalEl.textContent = '총 콕개수 ' + kokTotal + '개  완료: 총 ' + doneCount + '명 (남자: ' + maleDoneCount + '명 여자: ' + femaleDoneCount + '명)';",
    'jmAdminUniversalUndoV20884',
    'grid-template-columns:repeat(2,minmax(0,1fr))!important',
    'min-height:26px!important;height:26px!important',
):
    if required not in html:
        raise SystemExit('v208.85 requirement missing: ' + required)

path.write_text(html, encoding='utf-8')
print('ADMIN_RESTORE_KOK_TOTAL_V20885_OK')
