#!/usr/bin/env python3
"""Rename the "제외인원관리" label inside the "멤버등록·비밀번호·게임횟수·제외인원 관리"
collapsible menu to "콕제출체크", and add a per-member 콕(셔틀콕) submission checklist
inside that same panel: 남자 2개 · 여자 1개 기준으로 제출 인원수/콕 개수를 집계한다.
전체/남자/여자 탭으로 필터링할 수 있고, 각 탭 안에서 가나다순 정렬된다. 이름이 잘리지
않도록 전용 세로 목록 레이아웃을 쓴다 (기존 .roster 그리드는 좁은 칸에 이름이 잘림).

Also adds a "완료" workflow that is completely independent of member.status (court
assignment / 코트배정 제외 등과 절대 얽히지 않는 새 kokInactive 플래그): each row has its
own 완료/복귀 toggle button, plus panel-wide 선택 후 일괄 처리 buttons (선택 콕제출+비활성화,
선택 재활성화) driven by a click-to-pick selection local to this panel. "완료" 처리된
멤버는 목록 맨 아래로 가라앉는다.

Operates on the fully-built admin index.html (same file build-admin-native-session-fix.yml
extracts from the latest release APK)."""
from pathlib import Path
import re
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
html = path.read_text(encoding='utf-8')

MARKER = 'jmKokSubmitCheckV3'
if MARKER in html:
    print('ADMIN_KOK_SUBMIT_CHECK_ALREADY_OK')
    raise SystemExit(0)

for old in ('jmKokSubmitCheckV1', 'jmKokSubmitCheckV2'):
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
# with a checkbox for 콕 제출 여부, 전체/남자/여자 filter tabs, a per-row 완료 button, and
# panel-wide bulk pick+apply buttons.
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
    '      <div class="sub">전체 명단에서 콕(셔틀콕)을 제출한 인원을 체크하세요. 남자 2개 · 여자 1개 기준으로 자동 집계합니다. '
    '이름을 눌러 선택한 뒤 아래 버튼으로 여러 명을 한번에 처리할 수 있고, "완료"를 누르면 그 회원만 목록 맨 아래로 내려갑니다.</div>\n'
    '      <div class="toolbar section" style="margin-top:8px">\n'
    '        <span id="kokSubmitTotal" class="meta admin-member-counts">제출 0명 · 콕 0개</span>\n'
    '      </div>\n'
    '      <div class="toolbar section jm-kok-tabs" style="margin-top:6px;gap:6px">\n'
    '        <button type="button" class="jm-kok-tab active" data-jm-kok-tab="all" onclick="setKokSubmitTab(\'all\')">전체</button>\n'
    '        <button type="button" class="jm-kok-tab" data-jm-kok-tab="male" onclick="setKokSubmitTab(\'male\')">남자</button>\n'
    '        <button type="button" class="jm-kok-tab" data-jm-kok-tab="female" onclick="setKokSubmitTab(\'female\')">여자</button>\n'
    '      </div>\n'
    '      <div class="toolbar section jm-kok-bulk" style="margin-top:6px;gap:6px">\n'
    '        <span id="kokSubmitPickedCount" class="meta">0명 선택</span>\n'
    '        <button type="button" onclick="kokBulkDeactivate()">선택 콕제출+비활성화</button>\n'
    '        <button type="button" onclick="kokBulkReactivate()">선택 재활성화</button>\n'
    '        <button type="button" class="ghost-button" onclick="kokClearPicked()">선택 해제</button>\n'
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
# multi-column grid (which squeezed checkbox+name+quantity into a narrow cell and
# clipped names via the site-wide bare ".name{overflow:hidden;text-overflow:ellipsis;
# white-space:nowrap}" rule), style the filter tabs, and style the 완료-처리/선택 states.
KOK_STYLE = (
    '\n<style id="jmKokSubmitCheckStyle">\n'
    '/* ' + MARKER + ' */\n'
    '#kokSubmitRoster.jm-kok-roster-list{display:flex;flex-direction:column;gap:6px;'
    'margin-top:8px;max-height:none}\n'
    '#kokSubmitRoster.jm-kok-roster-list .member{display:flex!important;align-items:center;'
    'gap:8px;width:100%!important;max-width:none!important;box-sizing:border-box;'
    'border:1px solid transparent;border-radius:8px;padding:4px 6px}\n'
    '#kokSubmitRoster.jm-kok-roster-list .name{white-space:normal!important;'
    'overflow:visible!important;text-overflow:clip!important;flex:1 1 auto;min-width:0;'
    'word-break:keep-all;cursor:pointer}\n'
    '.jm-kok-tabs .jm-kok-tab{opacity:.55}\n'
    '.jm-kok-tabs .jm-kok-tab.active{opacity:1;font-weight:900;text-decoration:underline;'
    'text-underline-offset:3px}\n'
    '#kokSubmitRoster.jm-kok-roster-list .member.jm-kok-inactive{opacity:.5}\n'
    '#kokSubmitRoster.jm-kok-roster-list .member.jm-kok-picked{border-color:currentColor}\n'
    '.jm-kok-complete-btn{margin-left:auto;flex:0 0 auto}\n'
    '</style>\n'
)
if html.count('</head>') != 1:
    raise SystemExit('</head> anchor not found or not unique')
html = html.replace('</head>', KOK_STYLE + '</head>', 1)

# 5) The panel's own render/toggle/tab/selection/bulk functions, injected before </body>.
KOK_SCRIPT = '''
<script>
/* %s */
var KOK_SUBMIT_TAB = 'all';
var KOK_PICKED = new Set();

function setKokSubmitTab(tab) {
  KOK_SUBMIT_TAB = (tab === 'male' || tab === 'female') ? tab : 'all';
  document.querySelectorAll('.jm-kok-tab').forEach(function(button) {
    button.classList.toggle('active', button.getAttribute('data-jm-kok-tab') === KOK_SUBMIT_TAB);
  });
  renderKokSubmitPanel();
}

function toggleKokPick(memberId) {
  var id = String(memberId);
  if (KOK_PICKED.has(id)) KOK_PICKED.delete(id);
  else KOK_PICKED.add(id);
  renderKokSubmitPanel();
}

function kokClearPicked() {
  KOK_PICKED.clear();
  renderKokSubmitPanel();
}

function renderKokSubmitPanel() {
  var container = document.getElementById('kokSubmitRoster');
  var totalEl = document.getElementById('kokSubmitTotal');
  var pickedEl = document.getElementById('kokSubmitPickedCount');
  if (!container && !totalEl && !pickedEl) return;
  var all = sortMembersByKoreanName((STATE.members || []).slice());
  var submittedCount = 0;
  var kokTotal = 0;
  all.forEach(function(member) {
    if (member.kokSubmitted) {
      submittedCount += 1;
      kokTotal += member.gender === 'female' ? 1 : 2;
    }
  });
  if (totalEl) {
    totalEl.textContent = '제출 ' + submittedCount + '명 · 콕 ' + kokTotal + '개';
  }
  if (pickedEl) {
    pickedEl.textContent = KOK_PICKED.size + '명 선택';
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
          var checked = member.kokSubmitted ? ' checked' : '';
          var qtyLabel = member.gender === 'female' ? '여자 · 1개' : '남자 · 2개';
          var inactive = !!member.kokInactive;
          var picked = KOK_PICKED.has(String(member.id));
          var rowClass = 'member ' + genderClass(member) +
            (member.kokSubmitted ? ' selected' : '') +
            (inactive ? ' jm-kok-inactive' : '') +
            (picked ? ' jm-kok-picked' : '');
          return '<div class="' + rowClass + '" data-member-id="' + member.id + '">' +
            '<input type="checkbox" class="jm-kok-check" data-member-id="' + member.id + '"' + checked +
            ' onchange="toggleKokSubmitted(\\'' + member.id + '\\', this.checked)">' +
            '<span class="name" onclick="toggleKokPick(\\'' + member.id + '\\')">' + member.name + '</span>' +
            '<span class="meta">' + qtyLabel + (inactive ? ' · 완료' : '') + '</span>' +
            '<button type="button" class="ghost-button jm-kok-complete-btn" onclick="completeKokMember(\\'' + member.id + '\\')">' +
            (inactive ? '복귀' : '완료') +
            '</button>' +
            '</div>';
        }).join('')
      : '<div class="sub">' + (KOK_SUBMIT_TAB === 'all' ? '등록된 멤버가 없습니다.' : '해당하는 멤버가 없습니다.') + '</div>';
  }
}

function toggleKokSubmitted(memberId, submitted) {
  var flag = !!submitted;
  var member = (STATE.members || []).find(function(item) { return String(item.id) === String(memberId); });
  var previous = member ? !!member.kokSubmitted : false;
  if (member) member.kokSubmitted = flag;
  renderKokSubmitPanel();
  server('setMemberKokSubmitted', [ADMIN_PIN_VALUE, memberId, flag])
    .then(function(state) { renderState(state); })
    .catch(function(error) {
      if (member) member.kokSubmitted = previous;
      renderKokSubmitPanel();
      alert(error.message || error);
    });
}

/* 개별 완료/복귀 토글: member.status(코트배정/제외)는 절대 건드리지 않는, 콕제출체크
   화면 전용의 새 kokInactive 플래그만 바꾼다. */
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

/* 여러 명 선택(이름 클릭) 후 일괄 처리: 콕 제출 상태로 만들면서 동시에 완료(비활성화)까지
   한 번에 처리한다. 개별 체크박스를 하나씩 누를 필요 없이 빠르게 여러 명을 넘길 때 쓴다. */
async function kokBulkDeactivate() {
  var ids = Array.from(KOK_PICKED);
  if (!ids.length) { alert('먼저 이름을 눌러 회원을 선택하세요.'); return; }
  var previousMembers = JSON.parse(JSON.stringify(STATE.members));
  var pickedBackup = new Set(KOK_PICKED);
  ids.forEach(function(id) {
    var member = (STATE.members || []).find(function(item) { return String(item.id) === id; });
    if (member) { member.kokSubmitted = true; member.kokInactive = true; }
  });
  KOK_PICKED.clear();
  renderKokSubmitPanel();
  try {
    var state = await server('setMemberKokInactive', [ADMIN_PIN_VALUE, ids, true]);
    for (var i = 0; i < ids.length; i++) {
      state = await server('setMemberKokSubmitted', [ADMIN_PIN_VALUE, ids[i], true]);
    }
    renderState(state);
  } catch (error) {
    STATE.members = previousMembers;
    KOK_PICKED = pickedBackup;
    renderKokSubmitPanel();
    alert(error.message || error);
  }
}

/* 여러 명 선택 후 일괄 되돌리기: 완료(비활성화) 해제 + 콕 미제출 상태로 초기화한다. */
async function kokBulkReactivate() {
  var ids = Array.from(KOK_PICKED);
  if (!ids.length) { alert('먼저 이름을 눌러 회원을 선택하세요.'); return; }
  var previousMembers = JSON.parse(JSON.stringify(STATE.members));
  var pickedBackup = new Set(KOK_PICKED);
  ids.forEach(function(id) {
    var member = (STATE.members || []).find(function(item) { return String(item.id) === id; });
    if (member) { member.kokSubmitted = false; member.kokInactive = false; }
  });
  KOK_PICKED.clear();
  renderKokSubmitPanel();
  try {
    var state = await server('setMemberKokInactive', [ADMIN_PIN_VALUE, ids, false]);
    for (var i = 0; i < ids.length; i++) {
      state = await server('setMemberKokSubmitted', [ADMIN_PIN_VALUE, ids[i], false]);
    }
    renderState(state);
  } catch (error) {
    STATE.members = previousMembers;
    KOK_PICKED = pickedBackup;
    renderKokSubmitPanel();
    alert(error.message || error);
  }
}
</script>
''' % MARKER

if html.count('</body>') != 1:
    raise SystemExit('</body> anchor not found or not unique')
html = html.replace('</body>', KOK_SCRIPT + '</body>', 1)

# 6) Route the new RPCs through the same save-lock overlay as every other member mutation.
mutations_match = re.search(r"var MUTATIONS=new Set\(\[(?P<items>.*?)\]\);", html)
if not mutations_match:
    raise SystemExit('MUTATIONS set anchor not found')
extra = []
if "'setMemberKokSubmitted'" not in mutations_match.group('items'):
    extra.append("'setMemberKokSubmitted'")
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
if html.count('function kokBulkDeactivate(') != 1:
    raise SystemExit('kokBulkDeactivate must exist exactly once')
if html.count('function kokBulkReactivate(') != 1:
    raise SystemExit('kokBulkReactivate must exist exactly once')
if html.count("server('setMemberKokInactive'") < 3:
    raise SystemExit('setMemberKokInactive must be called from completeKokMember + both bulk functions')

path.write_text(html, encoding='utf-8')
print('ADMIN_KOK_SUBMIT_CHECK_OK')
