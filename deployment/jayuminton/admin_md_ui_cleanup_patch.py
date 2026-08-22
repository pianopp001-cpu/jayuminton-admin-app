#!/usr/bin/env python3
"""Keep only the administrator controls explicitly required by the operations MD."""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
path = root / 'Admin.html'
html = path.read_text(encoding='utf-8')

def remove_button_by_onclick(source, handler):
    pattern = re.compile(r'<button\b[^>]*\bonclick=["\']' + re.escape(handler) + r'["\'][^>]*>.*?</button>\s*', re.S)
    return pattern.sub('', source)

# Management/settings contains exactly the four MD operations. Voice always
# follows the finish-court contract and therefore needs no toggle/test UI.
for handler in ('toggleVoiceGuide()', 'testVoiceGuide()', 'setSelectedBundle()', 'clearSelectedBundle()', 'unlockVoiceSound()'):
    html = remove_button_by_onclick(html, handler)

# Undo is intentionally available only in the fixed bottom action bar.
html = re.sub(r'<button\b[^>]*\bid=["\']undoButton["\'][^>]*>.*?</button>\s*', '', html, count=1, flags=re.S)

# Quick assignment and long-press actions replace this duplicate bulk-status
# panel. Keeping two copies caused avoidable buttons and extra render work.
html, removed = re.subn(
    r'<section\b[^>]*class=["\'][^"\']*compact-admin-tools[^"\']*["\'][^>]*>.*?</section>\s*',
    '', html, count=1, flags=re.S,
)
if removed != 1:
    raise SystemExit('duplicate selected-member management panel missing')

required = (
    'onclick="openPairStatistics()"', 'onclick="createBackup()"',
    'onclick="restoreBackup()"', 'onclick="resetAllData()"',
    'onclick="increaseSelectedGames()"', 'onclick="decreaseSelectedGames()"',
    'onclick="resetSelectedGames()"', 'onclick="selectAllMembers()"',
    'id="replayVoiceButton"', 'id="repeatVoiceButton"',
    'onclick="stopVoiceAnnouncement()"', 'admin-vnext-bottom-bar',
    'mobile-undo-button', 'mobile-refresh-button', 'mobile-assign-button',
)
for marker in required:
    if marker not in html:
        raise SystemExit('required MD control missing: ' + marker)

for forbidden in (
    'onclick="toggleVoiceGuide()"', 'onclick="testVoiceGuide()"',
    'onclick="setSelectedBundle()"', 'onclick="clearSelectedBundle()"',
    'onclick="unlockVoiceSound()"', 'id="undoButton"',
    'compact-admin-tools', '음성 테스트', '묶음 지정', '묶음 해제',
):
    if forbidden in html:
        raise SystemExit('unnecessary control survived: ' + forbidden)

html = html.replace('</body>', '<!-- __JAYUMINTON_ADMIN_MD_UI_CLEANUP_V1__ -->\n</body>', 1)
path.write_text(html, encoding='utf-8')
print('ADMIN_MD_UI_CLEANUP_OK')
