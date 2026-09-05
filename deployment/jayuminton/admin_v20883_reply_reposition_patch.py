#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
html = path.read_text(encoding='utf-8')
MARKER = 'jmAdminReplyRepositionV20883'

if MARKER in html:
    print('ADMIN_REPLY_REPOSITION_V20883_ALREADY_OK')
    raise SystemExit(0)

for required in ('jmAdminKokCompactV20882', 'jmAdminEdgeUiV20881', 'jmAdminFixedQuickMenuV20880', 'jmAdminReplyButton'):
    if required not in html:
        raise SystemExit('v208.83 prerequisite missing: ' + required)

# 콕체크 패널이 열릴 때 body에 상태 클래스를 함께 토글한다.
old_toggle = "var button=document.getElementById('jmKokSideToggle');if(button){button.innerHTML=opening?'콕<br>체<br>크<br>▶':'콕<br>체<br>크<br>◀';button.classList.toggle('jm-open',opening);button.setAttribute('aria-label',opening?'콕체크 닫기':'콕체크 열기');}"
new_toggle = "var button=document.getElementById('jmKokSideToggle');if(button){button.innerHTML=opening?'콕<br>체<br>크<br>▶':'콕<br>체<br>크<br>◀';button.classList.toggle('jm-open',opening);button.setAttribute('aria-label',opening?'콕체크 닫기':'콕체크 열기');}document.body.classList.toggle('jm-kok-panel-open-v20883',opening);"
if html.count(old_toggle) != 1:
    raise SystemExit(f'kok toggle anchor mismatch: {html.count(old_toggle)}')
html = html.replace(old_toggle, new_toggle, 1)

# 원래 회원쪽지 버튼의 크기/글자/기능은 건드리지 않는다.
# 콕체크 패널이 열려 있는 동안에만 패널 시작점(top 36px) 위의 빈 공간으로 이동한다.
STYLE = r'''
<style id="jmAdminReplyRepositionV20883Style">
/* jmAdminReplyRepositionV20883 */
body.jm-kok-panel-open-v20883 #jmAdminReplyButton{
  top:1px!important;
  right:max(8px,env(safe-area-inset-right))!important;
  left:auto!important;
  margin:0!important;
}
</style>
'''
if html.count('</head>') != 1:
    raise SystemExit('</head> anchor not unique')
html = html.replace('</head>', STYLE + '</head>', 1)

for required in (
    MARKER,
    "document.body.classList.toggle('jm-kok-panel-open-v20883',opening)",
    'body.jm-kok-panel-open-v20883 #jmAdminReplyButton',
    'top:1px!important',
):
    if required not in html:
        raise SystemExit('v208.83 requirement missing: ' + required)

# 이번 패치는 콕체크 폰트/행 높이/집계 형식을 변경하지 않는다.
for required in (
    '완료 총 0명 · 남자 0명 · 여자 0명',
    'grid-template-columns:repeat(2,minmax(0,1fr))!important',
    'min-height:26px!important;height:26px!important',
):
    if required not in html:
        raise SystemExit('v208.82 preserved requirement missing: ' + required)

path.write_text(html, encoding='utf-8')
print('ADMIN_REPLY_REPOSITION_V20883_OK')
