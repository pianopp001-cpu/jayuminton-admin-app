#!/usr/bin/env python3
"""Rename the "제외인원관리" label inside the "멤버등록·비밀번호·게임횟수·제외인원 관리"
collapsible menu to "콕제출체크", and add a per-member 콕(셔틀콕) submission checklist
inside that same panel: 남자 2개 · 여자 1개 기준으로 제출 인원수/콕 개수를 집계한다.
전체/남자/여자 탭으로 필터링할 수 있고, 각 탭 안에서 가나다순 정렬된다. 이름이 잘리지
않도록 전용 세로 목록 레이아웃을 쓴다 (기존 .roster 그리드는 좁은 칸에 이름이 잘림).

V4: per user feedback, this dropped the V3 "click name to pick, then bulk-apply" flow
entirely (no selection checkbox, no bulk toolbar) -- it added a second, confusing
"box around a box" visual with no real benefit. Left exactly one control per row: a
single 완료/복귀 button that is completely independent of member.status (court
assignment / 코트배정 제외 등과 절대 얽히지 않는 새 kokInactive 플래그).

V5: V4 still reused the site-wide "member" CSS class and a "data-member-id" attribute
on each row for convenience. That was the actual bug behind the user's real-device
report ("완료 누르면 테두리 씌워지고 콕제출 카운트도 안세어지고 비활성화도 안되고
아래로 가지지도 않아") -- a completely unrelated, pre-existing feature
(jmUnifiedSwapMoveFixV1's "멤버선택 · 상태변경 · 회원삭제" bulk toolbar, and several
sibling IIFEs like it) attaches a CAPTURING click listener directly on #adminApp whose
CARD_SELECTOR/ID_SELECTOR match any ".member" element or any element carrying
"data-member-id" anywhere inside #adminApp. Because our kok-check rows matched that
selector, that listener's `ev.stopImmediatePropagation()` fired in the capture phase --
before our own button's onclick ever ran -- toggled that OTHER feature's own selection
Set, and painted its own green checkmark/selection state (what looked like "a border")
on the row. completeKokMember() never executed at all: hence no line-through, no count,
no reordering. Since a capturing listener on an ancestor (#adminApp) always runs before
any listener on a descendant regardless of registration order, this cannot be fixed by
capturing "harder" on our own button -- the only real fix is to stop matching that
selector. V5 renames the row's class from "member" to "jm-kok-row" and its identifying
attribute from "data-member-id" to "data-jm-kok-member-id", neither of which appears in
any of the CARD_SELECTOR/ID_SELECTOR lists used across the codebase, so the legacy
click-capture features now ignore these rows entirely and our own button's onclick is
the only thing that runs.

Operates on the fully-built admin index.html (same file build-admin-native-session-fix.yml
extracts from the latest release APK)."""
from pathlib import Path
import re
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
html = path.read_text(encoding='utf-8')

MARKER = 'jmKokSubmitCheckV5'
if MARKER in html:
    print('ADMIN_KOK_SUBMIT_CHECK_ALREADY_OK')
    raise SystemExit(0)

for old in ('jmKokSubmitCheckV1', 'jmKokSubmitCheckV2', 'jmKokSubmitCheckV3', 'jmKokSubmitCheckV4'):
    if old in html:
        raise SystemExit(f'old {old} marker present -- base HTML already has an older panel, refusing to double-patch')

# 1) Collapsible summary label: "...게임횟수·제외인원 관리" -> "...게임횟수·콕제출체크"
OLD_SUMMARY = '멤버등록·비밀번호·게임횟수·제외인원 관리'
NEW_SUMMARY = '멤버등록·비밀번호·게임횟수·콕제출체크'
if html.count(OLD_SUMMARY) != 1:
    raise SystemExit(f'expected exactly one admin-setup-details summary match, found {html.count(OLD_SUMMARY)}')
html = html.replace(OLD_SUMMARY, NEW_SUMMARY, 1)

# 2) New panel, inserted right after the existing 게임횟수 카운트 조정 panel (same
# collapsible <details class="admin-setup-details">), listing every registered member
# with 전체/남자/여자 filter tabs and a single per-row 완료/복귀 button.
GAME_COUNT_PANEL = (
    '<div class="card admin-game-count-panel" style="box-shadow:none;margin-top:12px">\n'
    '      <h2>게임횟수 카운트 조정</h2>\n'
    '      <div class="toolbar section md-game-actions">\n'
    '        <button type="button" onclick="selectAllMembers()">멤버 모두선택</button>\n'
    '        <span class="meta">카드를 눌러 여러 명 선택</span>\n'
    '        <button type="button" onclick="resetSelectedGames()">게임횟수 모두 0</button>\n'
    '        <button type="button" onclick="increaseSelectedGames()">게임횟수 +1</button>\n'
    '        <button type="button" onclick="decreaseSelectedGames()">게임횟수 -1</button>\n'
    '      </div>\n'
    '    </div>'
)
if html.count(GAME_COUNT_PANEL) != 1:
    raise SystemExit('game-count panel anchor not found or not unique -- HTML has drifted')

KOK_PANEL = (
    '\n    <div class="card admin-kok-submit-panel" style="box-shadow:none;margin-top:12px">\n'
    '      <h2>콕 제출 체크</h2>\n'
    '      <div class="sub">완료를 누르면 그 회원의 콕 제출이 완료 처리되어 남자 2개 · 여자 1개씩 '
    '집계에 반영되고, 목록 맨 아래로 내려갑니다. 다시 누르면 복귀됩니다.</div>\n'
    '      <div class="toolbar section" style="margin-top:8px">\n'
    '        <span id="kokSubmitTotal" class="meta admin-member-counts">완료 0명 · 콕 0개</span>\n'
    '      </div>\n'
    '      <div class="toolbar section jm-kok-tabs" style="margin-top:6px;gap:6px">\n'
    '        <button type="button" class="jm-kok-tab active" data-jm-kok-tab="all" onclick="setKokSubmitTab(\'all\')">전체</button>\n'
    '        <button type="button" class="jm-kok-tab" data-jm-kok-tab="male" onclick="setKokSubmitTab(\'male\')">남자</button>\n'
    '        <button type="button" class="jm-kok-tab" data-jm-kok-tab="female" onclick="setKokSubmitTab(\'female\')">여자</button>\n'
    '      </div>\n'
    '      <div id="kokSubmitRoster" class="jm-kok-roster-list"></div>\n'
    '    </div>'
)
html = html.replace(GAME_COUNT_PANEL, GAME_COUNT_PANEL + KOK_PANEL, 1)

# 3) Hook the panel into the existing render pipeline, right next to renderExcluded().
RENDER_ANCHOR = 'renderExcluded();'
if html.count(RENDER_ANCHOR) != 1:
    raise SystemExit('renderState() renderExcluded() anchor not found or not unique')
html = html.replace(RENDER_ANCHOR, RENDER_ANCHOR + '\n  renderKokSubmitPanel();', 1)

# 4) CSS: give the kok list its own full-width vertical layout instead of the .roster
# multi-column grid (which squeezed name+quantity into a narrow cell and clipped names
# via the site-wide bare ".name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}"
# rule), style the filter tabs, and style the 완료-처리 state (struck-through, dimmed name).
# Rows use a dedicated ".jm-kok-row" class (NOT the site-wide ".member" class) -- see the
# V5 note above for why that matters.
KOK_STYLE = (
    '\n<style id="jmKokSubmitCheckStyle">\n'
    '/* ' + MARKER + ' */\n'
    '#kokSubmitRoster.jm-kok-roster-list{display:flex;flex-direction:column;gap:6px;'
    'margin-top:8px;max-height:none}\n'
    '#kokSubmitRoster.jm-kok-roster-list .jm-kok-row{display:flex!important;align-items:center;'
    'gap:8px;width:100%!important;max-width:none!important;box-sizing:border-box;'
    'border:1px solid transparent;border-radius:8px;padding:4px 6px}\n'
    '#kokSubmitRoster.jm-kok-roster-list .jm-kok-row .name{white-space:normal!important;'
    'overflow:visible!important;text-overflow:clip!important;flex:1 1 auto;min-width:0;'
    'word-break:keep-all}\n'
    '.jm-kok-tabs .jm-kok-tab{opacity:.55}\n'
    '.jm-kok-tabs .jm-kok-tab.active{opacity:1;font-weight:900;text-decoration:underline;'
    'text-underline-offset:3px}\n'
    '#kokSubmitRoster.jm-kok-roster-list .jm-kok-row.jm-kok-inactive{opacity:.55}\n'
    '#kokSubmitRoster.jm-kok-roster-list .jm-kok-row.jm-kok-inactive .name{'
    'text-decoration:line-through}\n'
    '.jm-kok-complete-btn{margin-left:auto;flex:0 0 auto}\n'
    '</style>\n'
)
if html.count('</head>') != 1:
    raise SystemExit('</head> anchor not found or not unique')
html = html.replace('</head>', KOK_STYLE + '</head>', 1)

# 5) The panel's own render/toggle/tab functions, injected before </body>.
KOK_SCRIPT = '''
<script>
/* %s */
var KOK_SUBMIT_TAB = 'all';

function setKokSubmitTab(tab) {
  KOK_SUBMIT_TAB = (tab === 'male' || tab === 'female') ? tab : 'all';
  document.querySelectorAll('.jm-kok-tab').forEach(function(button) {
    button.classList.toggle('active', button.getAttribute('data-jm-kok-tab') === KOK_SUBMIT_TAB);
  });
  renderKokSubmitPanel();
}

function renderKokSubmitPanel() {
  var container = document.getElementById('kokSubmitRoster');
  var totalEl = document.getElementById('kokSubmitTotal');
  if (!container && !totalEl) return;
  var all = sortMembersByKoreanName((STATE.members || []).slice());
  var doneCount = 0;
  var kokTotal = 0;
  all.forEach(function(member) {
    if (member.kokInactive) {
      doneCount += 1;
      kokTotal += member.gender === 'female' ? 1 : 2;
    }
  });
  if (totalEl) {
    totalEl.textContent = '완료 ' + doneCount + '명 · 콕 ' + kokTotal + '개';
  }
  if (container) {
    var list = KOK_SUBMIT_TAB === 'all'
      ? all
      : all.filter(function(member) { return genderClass(member) === KOK_SUBMIT_TAB; });
    // Array.prototype.sort is stable, and `list` is already 가나다순 -- sorting only on
    // the inactive flag keeps each group's existing alphabetical order while sinking
    // 완료 처리된 (kokInactive) members to the bottom.
    list = list.slice().sort(function(a, b) {
      return (a.kokInactive ? 1 : 0) - (b.kokInactive ? 1 : 0);
    });
    container.innerHTML = list.length
      ? list.map(function(member) {
          var qtyLabel = member.gender === 'female' ? '여자 · 1개' : '남자 · 2개';
          var inactive = !!member.kokInactive;
          /* jm-kok-row: a dedicated class + data attribute, deliberately NOT reusing the
             site-wide "member" class or "data-member-id" attribute -- see the V5 note at
             the top of this file for why that combination gets hijacked by unrelated
             legacy click-capture features elsewhere in the app. */
          var rowClass = 'jm-kok-row ' + genderClass(member) + (inactive ? ' jm-kok-inactive' : '');
          return '<div class="' + rowClass + '" data-jm-kok-member-id="' + member.id + '">' +
            '<span class="name">' + member.name + '</span>' +
            '<span class="meta">' + qtyLabel + (inactive ? ' · 완료' : '') + '</span>' +
            '<button type="button" class="ghost-button jm-kok-complete-btn" onclick="completeKokMember(\\'' + member.id + '\\')">' +
            (inactive ? '복귀' : '완료') +
            '</button>' +
            '</div>';
        }).join('')
      : '<div class="sub">' + (KOK_SUBMIT_TAB === 'all' ? '등록된 멤버가 없습니다.' : '해당하는 멤버가 없습니다.') + '</div>';
  }
}

/* 개별 완료/복귀 토글: member.status(코트배정/제외)는 절대 건드리지 않는, 콕제출체크
   화면 전용의 새 kokInactive 플래그만 바꾼다. 이 플래그 하나로 "완료 처리 + 콕 집계 +
   목록 맨 아래로 이동"을 전부 겸한다 (별도의 선택/체크박스 없음). */
function completeKokMember(memberId) {
  var member = (STATE.members || []).find(function(item) { return String(item.id) === String(memberId); });
  if (!member) return;
  var previous = !!member.kokInactive;
  var next = !previous;
  member.kokInactive = next;
  renderKokSubmitPanel();
  server('setMemberKokInactive', [ADMIN_PIN_VALUE, memberId, next])
    .then(function(state) { renderState(state); })
    .catch(function(error) {
      member.kokInactive = previous;
      renderKokSubmitPanel();
      alert(error.message || error);
    });
}
</script>
''' % MARKER

if html.count('</body>') != 1:
    raise SystemExit('</body> anchor not found or not unique')
html = html.replace('</body>', KOK_SCRIPT + '</body>', 1)

# 6) Route the new RPC through the same save-lock overlay as every other member mutation.
mutations_match = re.search(r"var MUTATIONS=new Set\(\[(?P<items>.*?)\]\);", html)
if not mutations_match:
    raise SystemExit('MUTATIONS set anchor not found')
extra = []
if "'setMemberKokInactive'" not in mutations_match.group('items'):
    extra.append("'setMemberKokInactive'")
if extra:
    insertion = mutations_match.group(0).replace(']);', ',' + ','.join(extra) + ']);', 1)
    html = html[:mutations_match.start()] + insertion + html[mutations_match.end():]

if MARKER not in html:
    raise SystemExit('marker missing after patch (should be unreachable)')
if html.count('id="kokSubmitRoster"') != 1:
    raise SystemExit('kok submit roster must exist exactly once')
if html.count('function setKokSubmitTab(') != 1:
    raise SystemExit('setKokSubmitTab must exist exactly once')
if html.count('jm-kok-tab') < 3:
    raise SystemExit('expected 3 filter tab buttons (all/male/female)')
if html.count('function completeKokMember(') != 1:
    raise SystemExit('completeKokMember must exist exactly once')
if html.count("server('setMemberKokInactive'") != 1:
    raise SystemExit('setMemberKokInactive must be called exactly once, from completeKokMember')
if html.count('text-decoration:line-through') != 1:
    raise SystemExit('completed member name must get a line-through style')
if html.count("'jm-kok-row '") != 1:
    raise SystemExit('row must be built with the dedicated jm-kok-row class exactly once')
if html.count('data-jm-kok-member-id="') != 1:
    raise SystemExit('row must carry the dedicated data-jm-kok-member-id attribute exactly once')
if "data-member-id=\\'\" + member.id" in html or 'data-member-id=" + member.id' in html:
    raise SystemExit('V5 regression: kok row must not use the shared data-member-id attribute')
if 'jm-kok-bulk' in html or 'kokBulkDeactivate' in html or 'kokBulkReactivate' in html or 'KOK_PICKED' in html:
    raise SystemExit('V5 must not contain any leftover bulk-select code from V3')

path.write_text(html, encoding='utf-8')
print('ADMIN_KOK_SUBMIT_CHECK_OK')
