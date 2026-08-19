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

# Admin-only fallback for mobile WebViews without :has(). Observe only the
# Admin document and mark cards containing the already-rendered full-name span.
admin_sizer = '''
<script id="adminVnextNewCardSizer">
(function() {
  var adminCardRenderScheduled = false;
  function adminMemberById(id) {
    try {
      if (typeof STATE === 'undefined' || !STATE || !Array.isArray(STATE.members)) return null;
      return STATE.members.find(function(member) { return String(member.id) === String(id); }) || null;
    } catch (error) { return null; }
  }
  function isAdminNewMember(member) {
    return !!member && (member.isNew === true || ['1','true'].indexOf(String(member.isNew || '').toLowerCase()) >= 0);
  }
  function escapeAdminName(value) {
    return String(value == null ? '' : value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function fullAdminNameHtml(value) {
    var stored = String(value || '').trim();
    var open = stored.indexOf('(');
    if (open < 0) return '<span class="member-vnext-full-name">' + escapeAdminName(stored) + '</span>';
    return '<span class="member-vnext-full-name"><span>' + escapeAdminName(stored.slice(0, open).trim()) +
      '</span><br><small>' + escapeAdminName(stored.slice(open).trim()) + '</small></span>';
  }
  function compactAdminPairStatistics() {
    document.querySelectorAll('#pairStatisticsList .pair-statistics-partners').forEach(function(group) {
      var chips = Array.prototype.filter.call(group.querySelectorAll('.pair-statistics-chip'), function(chip) {
        return !chip.classList.contains('pair-statistics-more');
      });
      chips.forEach(function(chip, index) { chip.hidden = index >= 3; });
      var hiddenCount = Math.max(0, chips.length - 3);
      var more = group.querySelector('.pair-statistics-more');
      if (!hiddenCount) {
        if (more) more.remove();
        return;
      }
      if (!more) {
        more = document.createElement('span');
        more.className = 'pair-statistics-chip pair-statistics-more';
        group.appendChild(more);
      }
      more.textContent = '+' + hiddenCount + '명';
    });
  }
  function markAdminNewCards() {
    document.querySelectorAll('.quick-member[data-member-id],.person[data-member-id]').forEach(function(card) {
      var member = adminMemberById(card.getAttribute('data-member-id'));
      if (!member) return;
      var name = card.querySelector('.quick-member-name,.name');
      if (!name) return;
      if (isAdminNewMember(member)) {
        card.classList.add('is-new-member');
        if (name.getAttribute('data-admin-name-mode') !== 'full') {
          name.innerHTML = fullAdminNameHtml(member.name);
          name.setAttribute('data-admin-name-mode', 'full');
        }
      } else {
        card.classList.remove('is-new-member');
        if (name.getAttribute('data-admin-name-mode') !== 'compact') {
          name.textContent = String(member.name || '').replace(/\\s*\\(.*/, '').trim().slice(0, 2);
          name.setAttribute('data-admin-name-mode', 'compact');
        }
      }
    });
    renderAdminPickedFullName();
    compactAdminPairStatistics();
  }
  function scheduleAdminNewCardRender() {
    if (adminCardRenderScheduled) return;
    adminCardRenderScheduled = true;
    window.requestAnimationFrame(function() {
      adminCardRenderScheduled = false;
      markAdminNewCards();
    });
  }
  function renderAdminPickedFullName() {
    var bar = document.getElementById('quickMoveBar');
    if (!bar) return;
    var memberId = '';
    try {
      if (typeof MEMBER_ACTION_IDS !== 'undefined' && MEMBER_ACTION_IDS.length === 1) memberId = MEMBER_ACTION_IDS[0];
      else if (typeof QUICK_PICK !== 'undefined' && QUICK_PICK) memberId = QUICK_PICK.memberId;
    } catch (error) {}
    var member = adminMemberById(memberId);
    var label = document.getElementById('quickMoveMemberFullName');
    if (!label) {
      label = document.createElement('strong');
      label.id = 'quickMoveMemberFullName';
      label.className = 'quick-move-full-name';
      bar.insertBefore(label, bar.firstChild);
    }
    label.textContent = member && isAdminNewMember(member) ? String(member.name || '') : '';
    label.classList.toggle('hidden', !label.textContent);
  }
  var bubbleTimer = 0;
  function showAdminNewNameBubble(card) {
    var name = card && card.querySelector('.member-vnext-full-name');
    if (!name) return;
    var bubble = document.getElementById('adminNewNameBubble');
    if (!bubble) {
      bubble = document.createElement('div');
      bubble.id = 'adminNewNameBubble';
      bubble.className = 'admin-new-name-bubble';
      document.body.appendChild(bubble);
    }
    bubble.textContent = String(name.textContent || '').trim();
    bubble.classList.add('is-visible');
    var rect = card.getBoundingClientRect();
    var bubbleWidth = Math.min(320, Math.max(150, window.innerWidth - 24));
    var left = Math.max(12, Math.min(window.innerWidth - bubbleWidth - 12, rect.left + rect.width / 2 - bubbleWidth / 2));
    bubble.style.width = bubbleWidth + 'px';
    bubble.style.left = left + 'px';
    bubble.style.top = Math.max(12, rect.top - 58) + 'px';
    window.clearTimeout(bubbleTimer);
    bubbleTimer = window.setTimeout(function() { bubble.classList.remove('is-visible'); }, 2500);
  }
  document.addEventListener('click', function(event) {
    var card = event.target && event.target.closest ? event.target.closest('.is-new-member') : null;
    if (card) showAdminNewNameBubble(card);
    window.setTimeout(scheduleAdminNewCardRender, 0);
  }, true);
  document.addEventListener('pointerup', function() { window.setTimeout(scheduleAdminNewCardRender, 0); }, true);
  document.addEventListener('DOMContentLoaded', scheduleAdminNewCardRender);
  new MutationObserver(scheduleAdminNewCardRender).observe(document.body, {childList:true, subtree:true});
  window.setTimeout(scheduleAdminNewCardRender, 0);
})();
</script>
'''
old_sizer_start = s.find('<script id="adminVnextNewCardSizer">')
if old_sizer_start >= 0:
    old_sizer_end = s.find('</script>', old_sizer_start)
    if old_sizer_end < 0: raise SystemExit('admin new-card sizer boundary missing')
    s = s[:old_sizer_start] + admin_sizer.strip() + s[old_sizer_end + len('</script>'):]
else:
    if '</body>' not in s: raise SystemExit('body end anchor missing')
    s = s.replace('</body>', admin_sizer + '\n</body>', 1)

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
  .pair-statistics-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;max-height:58vh;overflow:auto;overscroll-behavior:contain;padding-right:2px}
  .pair-statistics-row{min-width:0;border:1px solid #dbe3ef;border-radius:12px;padding:9px;background:#fff}
  .pair-statistics-head{display:flex;justify-content:space-between;gap:12px;align-items:center;margin-bottom:8px}
  .pair-statistics-name{font-size:17px;font-weight:900;overflow-wrap:anywhere}
  .pair-statistics-games{font-size:13px;font-weight:800;color:#475569;white-space:nowrap}
  .pair-statistics-partners{display:flex;gap:6px;flex-wrap:wrap}
  .pair-statistics-chip{max-width:100%;font-size:11px;font-weight:700;background:#eef4ff;color:#244f91;border-radius:999px;padding:4px 7px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .pair-statistics-more{background:#e2e8f0;color:#334155}
  .pair-statistics-empty{padding:24px;text-align:center;color:#64748b}
  .admin-new-name-bubble{position:fixed;z-index:99999;box-sizing:border-box;padding:10px 12px;border-radius:12px;background:#172033;color:#fff;font-size:15px;font-weight:900;line-height:1.35;text-align:center;overflow-wrap:anywhere;box-shadow:0 8px 24px rgba(15,23,42,.28);opacity:0;visibility:hidden;transform:translateY(5px);transition:opacity .12s ease,transform .12s ease;pointer-events:none}
  .admin-new-name-bubble.is-visible{opacity:1;visibility:visible;transform:translateY(0)}
  .quick-move-full-name{max-width:42vw;padding:4px 7px;border-radius:8px;background:#fff;color:#172033;font-size:12px;line-height:1.2;white-space:normal;overflow-wrap:anywhere;text-align:center}
  .member-vnext-full-name{display:block!important;width:100%!important;max-width:100%!important;height:auto!important;max-height:none!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;overflow-wrap:anywhere!important;word-break:keep-all!important;-webkit-line-clamp:unset!important;-webkit-box-orient:initial!important;line-height:1.2!important;text-align:center}
  .member-vnext-full-name small{display:block!important;width:100%!important;max-width:100%!important;height:auto!important;max-height:none!important;margin-top:7px;font-size:.8em!important;line-height:1.25!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;overflow-wrap:anywhere!important;word-break:keep-all!important;-webkit-line-clamp:unset!important;-webkit-box-orient:initial!important}
  .quick-member.is-new-member,.person.is-new-member{position:relative!important;overflow:hidden!important;aspect-ratio:auto!important}
  .member-vnext-badge.new-badge{position:absolute!important;z-index:10!important;top:3px!important;right:3px!important;display:block!important;width:auto!important;margin:0!important;padding:1px 4px!important;font-size:7px!important;line-height:9px!important;letter-spacing:.2px!important;border-radius:4px!important;pointer-events:none!important}
  .quick-member.is-new-member{grid-column:1/-1!important;width:100%!important;min-width:0!important;height:auto!important;min-height:190px!important;padding:22px 16px 16px!important}
  .person.is-new-member{height:auto!important;min-height:132px!important;padding:18px 8px 10px!important}
  .quick-member.is-new-member .quick-member-name,.person.is-new-member .name{display:block!important;width:100%!important;max-width:100%!important;height:auto!important;max-height:none!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;overflow-wrap:anywhere!important;word-break:keep-all!important;-webkit-line-clamp:unset!important;-webkit-box-orient:initial!important;line-height:1.2!important}
  @media (max-width:520px){.pair-statistics-list{grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.pair-statistics-row{padding:8px}.pair-statistics-name{font-size:14px}.pair-statistics-games{font-size:11px}.pair-statistics-chip{font-size:10px;padding:3px 6px}}
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
required += ['id="adminVnextNewCardSizer"', "card.classList.add('is-new-member')", 'showAdminNewNameBubble(card)', 'admin-new-name-bubble', 'function adminMemberById(id)', 'fullAdminNameHtml(member.name)', 'quickMoveMemberFullName', 'function compactAdminPairStatistics()', 'pair-statistics-more']
missing = [item for item in required if item not in s]
if missing:
    raise SystemExit('admin UI incomplete: ' + ' | '.join(missing))

p.write_text(s, encoding='utf-8')
print('admin vNext UI patch prepared')
