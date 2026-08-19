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
  @media (max-width:640px){.v4-quick-roster{grid-template-columns:repeat(3,minmax(0,1fr))!important}.v4-quick-card{min-width:0!important}.v4-quick-card .member-name{white-space:normal!important;overflow-wrap:anywhere;text-align:center}}
  .admin-vnext-bottom-bar{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;align-items:stretch}
  .admin-vnext-bottom-bar #mobileSelectedCount{grid-column:1/-1;font-size:12px;line-height:14px;min-height:14px}
  .admin-vnext-bottom-bar button{width:100%!important;min-width:0!important;min-height:46px!important;margin:0!important;padding:8px 4px!important;font-size:14px!important;font-weight:800!important;white-space:nowrap;display:flex!important;align-items:center!important;justify-content:center!important;text-align:center!important;overflow:hidden!important}
  .admin-vnext-bottom-bar .mobile-undo-button,.admin-vnext-bottom-bar .mobile-refresh-button{background:#475569!important;color:#fff!important;border-color:#475569!important}
  .admin-vnext-bottom-bar .mobile-undo-button:disabled{opacity:.78!important;color:#fff!important}
  .admin-vnext-bottom-bar .mobile-refresh-button{font-size:14px!important}
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
missing = [item for item in required if item not in s]
if missing:
    raise SystemExit('admin UI incomplete: ' + ' | '.join(missing))

p.write_text(s, encoding='utf-8')
print('admin vNext UI patch prepared')
