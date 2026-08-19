#!/usr/bin/env python3
"""Patch admin-only UI by stable element IDs; never edits user Index."""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
p = root / 'Admin.html'
s = p.read_text(encoding='utf-8')

# Add metadata controls immediately after the existing experience input,
# regardless of whitespace or placeholder wording.
if 'id="newPublicMemo"' not in s or 'id="newIsNew"' not in s or 'id="newIsSponsor"' not in s:
    pos = s.find('id="newExperience"')
    if pos < 0:
        raise SystemExit('newExperience element missing')
    end = s.find('>', pos)
    if end < 0:
        raise SystemExit('newExperience element boundary missing')
    fields = """
      <input id="newPublicMemo" maxlength="40" placeholder="메모(선택, 생일·특이사항 등)">
      <label class="member-flag-check"><input id="newIsNew" type="checkbox"> 신규</label>
      <label class="member-flag-check"><input id="newIsSponsor" type="checkbox"> 🎁 찬조</label>
"""
    s = s[:end + 1] + fields + s[end + 1:]

# Insert actions relative to their stable onclick handlers, not formatted blocks.
def insert_before_button(text, onclick, html, marker):
    if marker in text:
        return text
    hit = text.find('onclick="' + onclick + '"')
    if hit < 0:
        hit = text.find("onclick='" + onclick + "'")
    start = text.rfind('<button', 0, hit + 1)
    end = text.find('>', hit)
    if hit < 0 or start < 0 or end < 0:
        raise SystemExit(marker + ' button anchor missing')
    return text[:start] + html + '\n      ' + text[start:]

s = insert_before_button(
    s,
    'decreaseSelectedGames()',
    '<button onclick="increaseSelectedGames()">게임횟수 +1</button>',
    'increaseSelectedGames()'
)
s = insert_before_button(
    s,
    'decreaseSelectedGames()',
    '<button onclick="setSelectedBundle()">🔗 묶음 지정</button>\n'
    '      <button onclick="clearSelectedBundle()">묶음 해제</button>',
    'setSelectedBundle()'
)

s = s.replace('선택 위치 자동배정', '자동배정')
s = s.replace('>위치 자동배정</button>', '>자동배정</button>')

# Separate statistics view: never place pair counts inside member cards.
if 'onclick="openPairStatistics()"' not in s:
    menu_anchor = '<button\n        class="ghost-button"\n        onclick="createBackup()"'
    stats_button = '''<button class="ghost-button" type="button" onclick="openPairStatistics()">📊 함께 경기 통계</button>\n\n      '''
    if menu_anchor not in s: raise SystemExit('top admin menu anchor missing')
    s = s.replace(menu_anchor, stats_button + menu_anchor, 1)

if 'id="pairStatisticsModal"' not in s:
    modal = '''
  <div id="pairStatisticsModal" class="modal-backdrop hidden" onclick="closePairStatistics(event)">
    <div class="modal-card pair-statistics-modal" onclick="event.stopPropagation()">
      <div class="modal-head">
        <div><span class="eyebrow dark-eyebrow">PLAY TOGETHER</span><h2>함께 경기 통계</h2></div>
        <button class="modal-close" type="button" onclick="closePairStatistics()">×</button>
      </div>
      <p class="modal-help">각 회원의 게임횟수와 함께 경기한 상대별 누적 횟수입니다.</p>
      <input id="pairStatisticsSearch" type="search" placeholder="회원 이름 검색" oninput="renderPairStatistics()">
      <div id="pairStatisticsList" class="pair-statistics-list"><div class="pair-statistics-empty">불러오는 중…</div></div>
    </div>
  </div>
'''
    if '</body>' not in s: raise SystemExit('body end anchor missing')
    s = s.replace('</body>', modal + '\n</body>', 1)

# Preserve the current mobile bar and add only the required class/control.
# Upgrade an already-deployed legacy refresh handler as well.
s = s.replace('onclick="loadState()">↻ 새로고침', 'onclick="refreshAdminState()">↻ 새로고침')
s = s.replace("onclick='loadState()'>↻ 새로고침", "onclick='refreshAdminState()'>↻ 새로고침")
bar_start = s.find('<div class="mobile-quick-bar')
if bar_start < 0:
    bar_start = s.find("<div class='mobile-quick-bar")
if bar_start < 0:
    raise SystemExit('mobile quick bar missing')
bar_open_end = s.find('>', bar_start)
bar_end = s.find('</div>', bar_open_end)
if bar_open_end < 0 or bar_end < 0:
    raise SystemExit('mobile quick bar boundary missing')
bar = s[bar_start:bar_end]
if 'admin-vnext-bottom-bar' not in bar:
    bar = bar.replace('mobile-quick-bar', 'mobile-quick-bar admin-vnext-bottom-bar', 1)
if 'mobile-refresh-button' not in bar:
    hit = bar.find('onclick="smartAssignSelected()"')
    if hit < 0:
        hit = bar.find("onclick='smartAssignSelected()'")
    assign_start = bar.rfind('<button', 0, hit + 1)
    if hit < 0 or assign_start < 0:
        raise SystemExit('mobile assign button missing')
    refresh = '<button class="ghost-button mobile-refresh-button" type="button" onclick="refreshAdminState()">↻ 새로고침</button>\n    '
    bar = bar[:assign_start] + refresh + bar[assign_start:]

s = s[:bar_start] + bar + s[bar_end:]

style = """
<style id="adminVnextBottomBarStyle">
  .admin-vnext-bottom-bar{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;align-items:stretch}
  .admin-vnext-bottom-bar #mobileSelectedCount{grid-column:1/-1;font-size:12px;line-height:14px;min-height:14px}
  .admin-vnext-bottom-bar button{width:100%!important;min-width:0!important;min-height:46px!important;margin:0!important;padding:8px 4px!important;font-size:14px!important;font-weight:800!important;white-space:nowrap;display:flex!important;align-items:center!important;justify-content:center!important;text-align:center!important;overflow:hidden!important}
  .admin-vnext-bottom-bar .mobile-undo-button,.admin-vnext-bottom-bar .mobile-refresh-button{background:#475569!important;color:#fff!important;border-color:#475569!important}
  .admin-vnext-bottom-bar .mobile-undo-button:disabled{opacity:.78!important;color:#fff!important}
  .admin-vnext-bottom-bar .mobile-refresh-button{font-size:14px!important}
  .pair-statistics-modal{width:min(720px,calc(100vw - 24px));max-height:86vh;overflow:auto}
  .pair-statistics-modal>input{width:100%;margin:4px 0 12px;box-sizing:border-box}
  .pair-statistics-list{display:grid;gap:10px}
  .pair-statistics-row{border:1px solid #dbe3ef;border-radius:14px;padding:12px;background:#fff}
  .pair-statistics-head{display:flex;justify-content:space-between;gap:12px;align-items:center;margin-bottom:8px}
  .pair-statistics-name{font-size:17px;font-weight:900;overflow-wrap:anywhere}
  .pair-statistics-games{font-size:13px;font-weight:800;color:#475569;white-space:nowrap}
  .pair-statistics-partners{display:flex;gap:6px;flex-wrap:wrap}
  .pair-statistics-chip{font-size:12px;font-weight:700;background:#eef4ff;color:#244f91;border-radius:999px;padding:5px 8px}
  .pair-statistics-empty{padding:24px;text-align:center;color:#64748b}
  .member-vnext-full-name{display:block!important;width:100%!important;max-width:100%!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;overflow-wrap:anywhere;line-height:1.12;text-align:center}
  .member-vnext-full-name small{display:block!important;width:100%!important;max-width:100%!important;margin-top:5px;font-size:.68em;line-height:1.2;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;overflow-wrap:anywhere}
  .quick-member:has(.member-vnext-full-name),.person:has(.member-vnext-full-name){position:relative!important;overflow:visible!important}
  .member-vnext-badge.new-badge{position:absolute!important;z-index:10!important;top:3px!important;right:3px!important;display:block!important;width:auto!important;margin:0!important;padding:1px 4px!important;font-size:7px!important;line-height:9px!important;letter-spacing:.2px!important;border-radius:4px!important;pointer-events:none!important}
  .quick-member:has(.member-vnext-full-name){grid-column:span 2!important;width:100%!important;min-width:0!important;height:auto!important;min-height:160px!important;padding:12px 10px!important}
  .person:has(.member-vnext-full-name){height:auto!important;min-height:112px!important;padding-top:10px!important;padding-bottom:10px!important}
  .quick-member:has(.member-vnext-full-name) .quick-member-name,.person:has(.member-vnext-full-name) .name{display:block!important;width:100%!important;max-width:100%!important;height:auto!important;max-height:none!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;line-height:1.15!important}
  @media (max-width:380px){.admin-vnext-bottom-bar{grid-template-columns:repeat(3,minmax(0,1fr));gap:5px}.admin-vnext-bottom-bar button{font-size:12px!important;padding:7px 2px!important}}
</style>
"""
style_start = s.find('<style id="adminVnextBottomBarStyle">')
if style_start >= 0:
    style_end = s.find('</style>', style_start)
    if style_end < 0:
        raise SystemExit('existing bottom bar style boundary missing')
    s = s[:style_start] + style.strip() + s[style_end + len('</style>'):]
else:
    if '</body>' not in s:
        raise SystemExit('body end anchor not found')
    s = s.replace('</body>', style + '\n</body>', 1)

required = ['id="newPublicMemo"', 'id="newIsNew"', 'id="newIsSponsor"',
            'increaseSelectedGames()', 'setSelectedBundle()',
            'admin-vnext-bottom-bar', 'mobile-refresh-button']
required += ['openPairStatistics()', 'id="pairStatisticsModal"', 'id="pairStatisticsList"']
missing = [item for item in required if item not in s]
if missing:
    raise SystemExit('admin UI incomplete: ' + ' | '.join(missing))

p.write_text(s, encoding='utf-8')
print('admin vNext UI patch prepared')
