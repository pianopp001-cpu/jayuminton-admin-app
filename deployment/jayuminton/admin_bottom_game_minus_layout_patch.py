#!/usr/bin/env python3
"""Move auto-assign beside quick selection clear and put game -1 in bottom bar."""
from pathlib import Path
import re
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
html = path.read_text(encoding='utf-8')

MARKER = 'jmAdminAutoAssignTopGameMinusBottomV20868'
if MARKER in html:
    print('ADMIN_BOTTOM_GAME_MINUS_LAYOUT_ALREADY_OK')
    raise SystemExit(0)

if 'jmGameCountSelectionUnifiedV20867' not in html:
    raise SystemExit('v208.67 unified game-count selection prerequisite missing')

# The live bottom bar has one uniquely identified auto-assign button. Replace it
# in-place with game -1 so the fixed bar keeps the same compact button count.
bottom_auto = re.compile(
    r'<button\b(?=[^>]*(?:\bid=["\']adminBottomAutoAssign["\']|\bclass=["\'][^"\']*mobile-assign-button[^"\']*["\']))'
    r'(?=[^>]*\bonclick=["\']smartAssignSelected\(\)["\'])[^>]*>.*?</button>',
    re.S | re.I,
)
matches = list(bottom_auto.finditer(html))
if len(matches) != 1:
    raise SystemExit(f'bottom auto-assign button mismatch: {len(matches)}')
game_minus = (
    '<button id="adminBottomGameMinus" class="game-minus-button" type="button" '
    'onclick="decreaseSelectedGames()">게임 -1</button>'
)
html = bottom_auto.sub(game_minus, html, count=1)

# Add auto-assign immediately after the quick Selection Clear control.
clear_button = re.compile(
    r'(<button\b(?=[^>]*\bid=["\']quickClearSelectionButton["\'])[^>]*>.*?</button>)',
    re.S | re.I,
)
matches = list(clear_button.finditer(html))
if len(matches) != 1:
    raise SystemExit(f'quick selection-clear button mismatch: {len(matches)}')
quick_auto = (
    r'\1\n        <button id="quickAutoAssignButton" class="primary" type="button" '
    r'onclick="smartAssignSelected()">자동배정</button>'
)
html = clear_button.sub(quick_auto, html, count=1)

style = r'''
<style id="jmAdminAutoAssignTopGameMinusBottomStyle">
/* jmAdminAutoAssignTopGameMinusBottomV20868 */
#adminApp .jm-quick-member-actions{grid-template-columns:repeat(3,minmax(0,1fr))!important}
#quickAutoAssignButton{background:#166534!important;border-color:#166534!important;color:#fff!important}
#adminBottomGameMinus{background:#b45309!important;border-color:#b45309!important;color:#fff!important;font-weight:950!important}
@media(max-width:620px){
  #adminApp .jm-quick-member-actions{grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:4px!important}
  #adminApp .jm-quick-member-actions button{padding:6px 3px!important;font-size:10px!important}
}
</style>
'''
if '</head>' in html:
    html = html.replace('</head>', style + '\n</head>', 1)
else:
    html = html.replace('</body>', style + '\n</body>', 1)

for required in (
    MARKER,
    'id="quickAutoAssignButton"',
    'onclick="smartAssignSelected()">자동배정</button>',
    'id="adminBottomGameMinus"',
    'onclick="decreaseSelectedGames()">게임 -1</button>',
    'grid-template-columns:repeat(3,minmax(0,1fr))',
):
    if required not in html:
        raise SystemExit('layout requirement missing: ' + required)

remaining_bottom_auto = re.findall(
    r'<button\b(?=[^>]*mobile-assign-button)(?=[^>]*smartAssignSelected\(\))[^>]*>',
    html,
    re.I,
)
if remaining_bottom_auto:
    raise SystemExit('old bottom auto-assign button still present')

path.write_text(html, encoding='utf-8')
print('ADMIN_BOTTOM_GAME_MINUS_LAYOUT_OK')
