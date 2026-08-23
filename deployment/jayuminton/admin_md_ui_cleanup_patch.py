#!/usr/bin/env python3
"""Strict final UI cleanup: rebuild admin menus from the operations MD only."""
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
    pat = re.compile(r'<(?P<tag>section|div)\b[^>]*class=["\'][^"\']*\b' + re.escape(class_name) + r'\b[^"\']*["\'][^>]*>.*?</(?P=tag)>\s*', re.S | re.I)
    return pat.sub('', source, count=1)

# 관리·설정: MD에 적힌 정확히 네 기능만.
top_actions = '''<div class="top-actions md-only-top-actions">
        <button class="ghost-button" type="button" onclick="openPairStatistics()">함께 경기통계</button>
        <button class="ghost-button" type="button" onclick="createBackup()">백업 저장</button>
        <button class="ghost-button" type="button" onclick="restoreBackup()">백업 복원</button>
        <button class="danger" type="button" onclick="resetAllData()">전체 초기화</button>
      </div>'''
html, n = re.subn(r'<div\s+class=["\']top-actions["\'][^>]*>.*?</div>', top_actions, html, count=1, flags=re.S | re.I)
if n != 1:
    raise SystemExit('top admin actions container missing')

for handler in ('toggleVoiceGuide()', 'testVoiceGuide()', 'setSelectedBundle()', 'clearSelectedBundle()', 'unlockVoiceSound()'):
    html = remove_button_by_onclick(html, handler)

# 실행취소는 하단 고정바에만.
html = re.sub(r'<button\b[^>]*\bid=["\']undoButton["\'][^>]*>.*?</button>\s*', '', html, count=1, flags=re.S | re.I)

# MD에 없는 대시보드/중복 상태관리 패널 제거.
html = remove_block_by_class(html, 'dashboard-shell')
html = remove_block_by_class(html, 'compact-admin-tools')

# 빠른 코트배정: MD 필수 필터는 정확히 전체/남자/여자 3개만.
html = remove_block_by_class(html, 'quick-status-actions')
html = remove_block_by_class(html, 'quick-search-box')
filter_block = '''<div class="quick-filter-row md-only-quick-filter-row">
          <button id="filterAllBtn" class="filter-chip active" onclick="setQuickFilter('all')">전체</button>
          <button id="filterMaleBtn" class="filter-chip" onclick="setQuickFilter('male')">남자</button>
          <button id="filterFemaleBtn" class="filter-chip" onclick="setQuickFilter('female')">여자</button>
        </div>'''
html, n = re.subn(r'<div\s+class=["\']quick-filter-row["\'][^>]*>.*?</div>', filter_block, html, count=1, flags=re.S | re.I)
if n != 1:
    raise SystemExit('quick filter row missing')
# 하단 고정 자동배정과 중복되는 내부 실행 버튼은 제거.
html = remove_block_by_class(html, 'v4-court-action-grid')
html = re.sub(r'<button\b(?![^>]*mobile-assign-button)[^>]*onclick=["\']smartAssignSelected\(\)["\'][^>]*>.*?</button>\s*', '', html, flags=re.S | re.I)

# 접는 설정 제목 정리. 제외명단은 밖으로 이동되어 항상 보인다.
html = html.replace('멤버 등록·비밀번호·제외 인원 관리', '멤버 등록·비밀번호·게임횟수 관리')
html = html.replace('멤버 등록·비밀번호·게임횟수·제외 인원 관리', '멤버 등록·비밀번호·게임횟수 관리')

required = (
    'class="top-actions md-only-top-actions"',
    '>함께 경기통계</button>', '>백업 저장</button>', '>백업 복원</button>', '>전체 초기화</button>',
    'onclick="openPairStatistics()"', 'onclick="createBackup()"', 'onclick="restoreBackup()"', 'onclick="resetAllData()"',
    'onclick="selectAllMembers()"', 'onclick="increaseSelectedGames()"', 'onclick="decreaseSelectedGames()"', 'onclick="resetSelectedGames()"',
    'class="quick-filter-row md-only-quick-filter-row"', "setQuickFilter('all')", "setQuickFilter('male')", "setQuickFilter('female')",
    '>전체</button>', '>남자</button>', '>여자</button>',
    'id="replayVoiceButton"', 'id="repeatVoiceButton"', 'onclick="stopVoiceAnnouncement()"',
    'admin-vnext-bottom-bar', 'mobile-undo-button', 'mobile-refresh-button', 'mobile-assign-button',
    'id="quickActiveRoster"', 'id="adminCourts"', 'id="adminWaitGroups"', 'id="excludedMembers"',
)
for marker in required:
    if marker not in html:
        raise SystemExit('required MD control missing: ' + marker)

top = re.search(r'<div\s+class=["\']top-actions md-only-top-actions["\'][^>]*>(.*?)</div>', html, re.S | re.I)
if not top or len(re.findall(r'<button\b', top.group(1), re.I)) != 4:
    raise SystemExit('management settings must contain exactly four buttons')
flt = re.search(r'<div\s+class=["\']quick-filter-row md-only-quick-filter-row["\'][^>]*>(.*?)</div>', html, re.S | re.I)
if not flt or len(re.findall(r'<button\b', flt.group(1), re.I)) != 3:
    raise SystemExit('quick filters must contain exactly three buttons')

for forbidden in (
    'onclick="toggleVoiceGuide()"', 'onclick="testVoiceGuide()"', 'onclick="setSelectedBundle()"', 'onclick="clearSelectedBundle()"',
    'onclick="unlockVoiceSound()"', 'id="undoButton"', 'compact-admin-tools', 'dashboard-shell', 'quick-status-actions',
    'quick-search-box', 'v4-court-action-grid', '음성 테스트', '음성 안내 켜짐', '묶음 지정', '묶음 해제',
    '오늘의 운영 현황', '선택 위치 자동배정', '위치 자동배정', '선택 해제',
):
    if forbidden in html:
        raise SystemExit('unnecessary control survived: ' + forbidden)

if '__JAYUMINTON_ADMIN_MD_UI_CLEANUP_V4__' not in html:
    html = html.replace('</body>', '<!-- __JAYUMINTON_ADMIN_MD_UI_CLEANUP_V4__ -->\n</body>', 1)
path.write_text(html, encoding='utf-8')
print('ADMIN_MD_UI_CLEANUP_V4_OK')
