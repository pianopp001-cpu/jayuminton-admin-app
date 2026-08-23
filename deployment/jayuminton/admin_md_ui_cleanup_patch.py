#!/usr/bin/env python3
"""Strict final UI cleanup: keep only controls required by the operations MD."""
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: admin_md_ui_cleanup_patch.py INDEX_HTML_OR_ROOT')
arg = Path(sys.argv[1])
path = arg if arg.is_file() else arg / 'Admin.html'
html = path.read_text(encoding='utf-8')


def remove_button_by_onclick(source, handler):
    pattern = re.compile(r'<button\b[^>]*\bonclick=["\']' + re.escape(handler) + r'["\'][^>]*>.*?</button>\s*', re.S | re.I)
    return pattern.sub('', source)


def remove_block_by_class(source, class_name):
    # Sections/divs used here are non-nested at their own tag level in the admin template.
    pat = re.compile(r'<(?P<tag>section|div)\b[^>]*class=["\'][^"\']*\b' + re.escape(class_name) + r'\b[^"\']*["\'][^>]*>.*?</(?P=tag)>\s*', re.S | re.I)
    return pat.sub('', source, count=1)

# 관리·설정: MD의 4개 기능만. 음성 토글/테스트/소리켜기 및 묶음 메뉴 제거.
for handler in ('toggleVoiceGuide()', 'testVoiceGuide()', 'setSelectedBundle()', 'clearSelectedBundle()', 'unlockVoiceSound()'):
    html = remove_button_by_onclick(html, handler)

# 실행취소는 하단 고정바에만 둔다.
html = re.sub(r'<button\b[^>]*\bid=["\']undoButton["\'][^>]*>.*?</button>\s*', '', html, count=1, flags=re.S | re.I)

# MD에 없는 큰 대시보드 및 중복 선택상태 관리 패널 제거.
html = remove_block_by_class(html, 'dashboard-shell')
html = remove_block_by_class(html, 'compact-admin-tools')

# 빠른 코트배정은 명단/빈자리 선택에 집중. 상태변경은 길게누르기, 자동배정은 하단 고정바만 사용.
html = remove_block_by_class(html, 'quick-status-actions')
html = remove_block_by_class(html, 'quick-search-box')
html = remove_block_by_class(html, 'quick-filter-row')
html = remove_block_by_class(html, 'v4-court-action-grid')

# 헤더/설정에 중복된 자동배정·상태관리 버튼이 있으면 제거하되 하단 고정바는 보존.
html = re.sub(r'<button\b(?![^>]*mobile-assign-button)[^>]*onclick=["\']smartAssignSelected\(\)["\'][^>]*>.*?</button>\s*', '', html, flags=re.S | re.I)

required = (
    'onclick="openPairStatistics()"', 'onclick="createBackup()"',
    'onclick="restoreBackup()"', 'onclick="resetAllData()"',
    'onclick="increaseSelectedGames()"', 'onclick="decreaseSelectedGames()"',
    'onclick="resetSelectedGames()"',
    'id="replayVoiceButton"', 'id="repeatVoiceButton"',
    'onclick="stopVoiceAnnouncement()"',
    'admin-vnext-bottom-bar', 'mobile-undo-button', 'mobile-refresh-button', 'mobile-assign-button',
    'id="quickActiveRoster"', 'id="adminCourts"', 'id="adminWaitGroups"',
    'id="excludedMembers"',
)
for marker in required:
    if marker not in html:
        raise SystemExit('required MD control missing: ' + marker)

for forbidden in (
    'onclick="toggleVoiceGuide()"', 'onclick="testVoiceGuide()"',
    'onclick="setSelectedBundle()"', 'onclick="clearSelectedBundle()"',
    'onclick="unlockVoiceSound()"', 'id="undoButton"',
    'compact-admin-tools', 'dashboard-shell', 'quick-status-actions',
    'quick-search-box', 'quick-filter-row', 'v4-court-action-grid',
    '음성 테스트', '묶음 지정', '묶음 해제', '오늘의 운영 현황',
    '선택 위치 자동배정',
):
    if forbidden in html:
        raise SystemExit('unnecessary control survived: ' + forbidden)

if '__JAYUMINTON_ADMIN_MD_UI_CLEANUP_V2__' not in html:
    html = html.replace('</body>', '<!-- __JAYUMINTON_ADMIN_MD_UI_CLEANUP_V2__ -->\n</body>', 1)
path.write_text(html, encoding='utf-8')
print('ADMIN_MD_UI_CLEANUP_V2_OK')
