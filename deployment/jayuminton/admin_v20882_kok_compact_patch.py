#!/usr/bin/env python3
from pathlib import Path
import re
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
html = path.read_text(encoding='utf-8')
MARKER = 'jmAdminKokCompactV20882'

if MARKER in html:
    print('ADMIN_KOK_COMPACT_V20882_ALREADY_OK')
    raise SystemExit(0)

for required in ('jmAdminEdgeUiV20881', 'jmAdminFixedQuickMenuV20880', 'jmKokSubmitCheckV5'):
    if required not in html:
        raise SystemExit('v208.82 prerequisite missing: ' + required)

# 1) 콕제출체크 제목 바로 아래의 장문 설명만 제거한다.
DESCRIPTION = (
    '<div class="sub">완료를 누르면 그 회원의 콕 제출이 완료 처리되어 남자 2개 · 여자 1개씩 '
    '집계에 반영되고, 목록 맨 아래로 내려갑니다. 다시 누르면 복귀됩니다.</div>'
)
if html.count(DESCRIPTION) != 1:
    raise SystemExit(f'kok description anchor mismatch: {html.count(DESCRIPTION)}')
html = html.replace(DESCRIPTION, '', 1)

# 2) 최초 표시 문구도 새 완료 집계 형식으로 맞춘다.
OLD_INITIAL = '<span id="kokSubmitTotal" class="meta admin-member-counts">완료 0명 · 콕 0개</span>'
NEW_INITIAL = '<span id="kokSubmitTotal" class="meta admin-member-counts">완료 총 0명 · 남자 0명 · 여자 0명</span>'
if html.count(OLD_INITIAL) != 1:
    raise SystemExit(f'kok initial summary anchor mismatch: {html.count(OLD_INITIAL)}')
html = html.replace(OLD_INITIAL, NEW_INITIAL, 1)

# 3) 완료 인원 집계를 총/남/여로 바꾼다. 콕 개수 집계는 이 화면에서 더 이상 표시하지 않는다.
old_summary = re.compile(
    r"var doneCount = 0;\s*"
    r"var kokTotal = 0;\s*"
    r"all\.forEach\(function\(member\) \{\s*"
    r"if \(member\.kokInactive\) \{\s*"
    r"doneCount \+= 1;\s*"
    r"kokTotal \+= member\.gender === 'female' \? 1 : 2;\s*"
    r"\}\s*"
    r"\}\);\s*"
    r"if \(totalEl\) \{\s*"
    r"totalEl\.textContent = '완료 ' \+ doneCount \+ '명 · 콕 ' \+ kokTotal \+ '개';\s*"
    r"\}"
)
new_summary = """var doneCount = 0;
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
html, count = old_summary.subn(new_summary, html, count=1)
if count != 1:
    raise SystemExit(f'kok render summary anchor mismatch: {count}')

# 4) 글자 크기는 절대 더 줄이지 않는다. 40명이 한 화면에 들어오도록 글자 대신
#    설명/메타행/세로 여백/버튼 높이만 줄이고 2열 x 최대 20행 형태로 압축한다.
COMPACT_STYLE = r'''
<style id="jmAdminKokCompactV20882Style">
/* jmAdminKokCompactV20882 : keep existing font sizes; compact spacing only */
.admin-kok-submit-panel{padding:6px!important;margin-top:4px!important;box-sizing:border-box!important}
.admin-kok-submit-panel h2{margin:0 0 2px!important;line-height:1.1!important}
.admin-kok-submit-panel>.toolbar.section{margin-top:2px!important;margin-bottom:0!important;padding:0!important;gap:3px!important;min-height:0!important}
.admin-kok-submit-panel .jm-kok-tabs{margin-top:2px!important;gap:3px!important}
.admin-kok-submit-panel .jm-kok-tabs .jm-kok-tab{height:22px!important;min-height:22px!important;padding:0 5px!important;margin:0!important;line-height:1!important}
.admin-kok-submit-panel #kokSubmitRoster.jm-kok-roster-list{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;grid-auto-flow:row!important;gap:2px!important;margin-top:3px!important;max-height:none!important;overflow:visible!important}
.admin-kok-submit-panel #kokSubmitRoster .jm-kok-row{display:grid!important;grid-template-columns:minmax(0,1fr) auto!important;grid-template-areas:'name button'!important;align-items:center!important;column-gap:2px!important;row-gap:0!important;width:100%!important;min-height:26px!important;height:26px!important;padding:1px 3px!important;margin:0!important;border-radius:5px!important;box-sizing:border-box!important}
.admin-kok-submit-panel #kokSubmitRoster .jm-kok-row .name{grid-area:name!important;min-width:0!important;white-space:nowrap!important;overflow:visible!important;text-overflow:clip!important;line-height:1.1!important;margin:0!important}
.admin-kok-submit-panel #kokSubmitRoster .jm-kok-row .meta{display:none!important}
.admin-kok-submit-panel #kokSubmitRoster .jm-kok-complete-btn{grid-area:button!important;height:22px!important;min-height:22px!important;padding:0 4px!important;margin:0!important;line-height:1!important;align-self:center!important}
</style>
'''
if 'font-size' in COMPACT_STYLE:
    raise SystemExit('v208.82 must not reduce font size')
if html.count('</head>') != 1:
    raise SystemExit('</head> anchor not unique')
html = html.replace('</head>', COMPACT_STYLE + '</head>', 1)

# Final invariants.
for required in (
    MARKER,
    '완료 총 0명 · 남자 0명 · 여자 0명',
    "totalEl.textContent = '완료 총 ' + doneCount + '명 · 남자 ' + maleDoneCount + '명 · 여자 ' + femaleDoneCount + '명';",
    'grid-template-columns:repeat(2,minmax(0,1fr))!important',
    'min-height:26px!important;height:26px!important',
    '.jm-kok-row .meta{display:none!important}',
):
    if required not in html:
        raise SystemExit('v208.82 requirement missing: ' + required)
if '완료를 누르면 그 회원의 콕 제출이 완료 처리되어' in html:
    raise SystemExit('kok description still present')

path.write_text(html, encoding='utf-8')
print('ADMIN_KOK_COMPACT_V20882_OK')
