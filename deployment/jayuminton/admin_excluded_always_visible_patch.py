#!/usr/bin/env python3
"""Move court-excluded members out of the collapsible admin settings area."""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
path = root / 'Admin.html'
html = path.read_text(encoding='utf-8')

MARKER = '__JAYUMINTON_ADMIN_EXCLUDED_ALWAYS_VISIBLE_V1__'
if MARKER in html:
    print('ADMIN_EXCLUDED_ALWAYS_VISIBLE_ALREADY_OK')
    raise SystemExit(0)

def balanced_element(source, start, name):
    tag = re.compile(r'</?' + re.escape(name) + r'\b[^>]*>', re.I)
    depth = 0
    for match in tag.finditer(source, start):
        depth += -1 if match.group(0).startswith('</') else 1
        if depth == 0:
            return source[start:match.end()], match.end()
    raise SystemExit('excluded panel closing tag missing')

match = re.search(r'<(?P<tag>section|div)\b[^>]*class=["\'][^"\']*\bexcluded-panel\b[^"\']*["\'][^>]*>', html, re.I)
if not match:
    raise SystemExit('excluded-panel section missing')
excluded, excluded_end = balanced_element(html, match.start(), match.group('tag'))

handlers = ('decreaseSelectedGames()', 'increaseSelectedGames()', 'resetSelectedGames()', 'selectAllMembers()')
game_buttons = []
for handler in handlers:
    button_match = re.search(r'<button\b[^>]*onclick=["\']' + re.escape(handler) + r'["\'][^>]*>.*?</button>', excluded, re.S | re.I)
    if not button_match:
        raise SystemExit('game-count control missing: ' + handler)
    game_buttons.append(button_match.group(0))
    excluded = excluded.replace(button_match.group(0), '', 1)

if 'onclick="setSelectedStatus(\'active\')"' not in excluded and "onclick='setSelectedStatus(\"active\")'" not in excluded:
    raise SystemExit('return-to-active control missing from excluded panel')

excluded, class_updates = re.subn(
    r'class=(["\'])([^"\']*\bexcluded-panel\b[^"\']*)\1',
    lambda m: 'class=' + m.group(1) + m.group(2).strip() + ' admin-excluded-always-visible' + m.group(1),
    excluded, count=1, flags=re.I,
)
if class_updates != 1:
    raise SystemExit('excluded panel class update failed')
game_panel = '''<div class="card admin-game-count-panel" style="box-shadow:none;margin-top:12px">
  <h2>게임횟수 카운트 조정</h2>
  <div class="toolbar section">\n%s\n  </div>
</div>''' % '\n'.join(game_buttons)

html = html[:match.start()] + game_panel + html[excluded_end:]
anchor = re.search(r'<section\b[^>]*class=["\'][^"\']*\bv4-wait-summary\b[^"\']*["\'][^>]*>', html, re.I)
if not anchor:
    raise SystemExit('quick-assignment right rail anchor missing')
html = html[:anchor.start()] + excluded + '\n\n      ' + html[anchor.start():]
html = html.replace('멤버 등록·비밀번호·제외 인원 관리', '멤버 등록·비밀번호·게임횟수 관리', 1)

style = '''
<style id="adminExcludedAlwaysVisibleStyle">
#adminApp .admin-excluded-always-visible{display:block!important;visibility:visible!important}
#adminApp .admin-excluded-always-visible .roster{max-height:none!important;overflow:visible!important}
</style>
<!-- %s -->
''' % MARKER
if '</head>' not in html:
    raise SystemExit('head closing tag missing')
html = html.replace('</head>', style + '</head>', 1)

details_start = html.find('<details class="admin-setup-details"')
details_end = html.find('</details>', details_start)
visible_pos = html.find('admin-excluded-always-visible')
if details_start < 0 or details_end < 0 or details_start < visible_pos < details_end:
    raise SystemExit('excluded panel is still inside collapsible settings')
if html.count('id="excludedMembers"') != 1:
    raise SystemExit('excluded roster must exist exactly once')

path.write_text(html, encoding='utf-8')
print('ADMIN_EXCLUDED_ALWAYS_VISIBLE_OK')
