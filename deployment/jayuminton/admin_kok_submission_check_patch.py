#!/usr/bin/env python3
"""Rename the "제외인원관리" label inside the "멤버등록·비밀번호·게임횟수·제외인원 관리"
collapsible menu to "콕제출체크", and add a per-member 콕(셔틀콕) submission checklist
inside that same panel: 남자 2개 · 여자 1개 기준으로 제출 인원수/콕 개수를 집계한다.

Operates on the fully-built admin index.html (same file build-admin-native-session-fix.yml
extracts from the latest release APK)."""
from pathlib import Path
import re
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
html = path.read_text(encoding='utf-8')

MARKER = 'jmKokSubmitCheckV1'
if MARKER in html:
    print('ADMIN_KOK_SUBMIT_CHECK_ALREADY_OK')
    raise SystemExit(0)

# 1) Collapsible summary label: "...게임횟수·제외인원 관리" -> "...게임횟수·콕제출체크"
OLD_SUMMARY = '멤버등록·비밀번호·게임횟수·제외인원 관리'
NEW_SUMMARY = '멤버등록·비밀번호·게임횟수·콕제출체크'
if html.count(OLD_SUMMARY) != 1:
    raise SystemExit(f'expected exactly one admin-setup-details summary match, found {html.count(OLD_SUMMARY)}')
html = html.replace(OLD_SUMMARY, NEW_SUMMARY, 1)

# 2) New panel, inserted right after the existing 게임횟수 카운트 조정 panel (same
# collapsible <details class="admin-setup-details">), listing every registered member
# with a checkbox for 콕 제출 여부.
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
    '      <div class="sub">전체 명단에서 콕(셔틀콕)을 제출한 인원을 체크하세요. 남자 2개 · 여자 1개 기준으로 자동 집계합니다.</div>\n'
    '      <div class="toolbar section" style="margin-top:8px">\n'
    '        <span id="kokSubmitTotal" class="meta admin-member-counts">제출 0명 · 콕 0개</span>\n'
    '      </div>\n'
    '      <div id="kokSubmitRoster" class="roster"></div>\n'
    '    </div>'
)
html = html.replace(GAME_COUNT_PANEL, GAME_COUNT_PANEL + KOK_PANEL, 1)

# 3) Hook the panel into the existing render pipeline, right next to renderExcluded().
RENDER_ANCHOR = 'renderExcluded();'
if html.count(RENDER_ANCHOR) != 1:
    raise SystemExit('renderState() renderExcluded() anchor not found or not unique')
html = html.replace(RENDER_ANCHOR, RENDER_ANCHOR + '\n  renderKokSubmitPanel();', 1)

# 4) The panel's own render/toggle functions + a small style tweak, injected before </body>.
KOK_SCRIPT = '''
<script>
/* %s */
function renderKokSubmitPanel() {
  var container = document.getElementById('kokSubmitRoster');
  var totalEl = document.getElementById('kokSubmitTotal');
  if (!container && !totalEl) return;
  var list = sortMembersByKoreanName((STATE.members || []).slice());
  var submittedCount = 0;
  var kokTotal = 0;
  list.forEach(function(member) {
    if (member.kokSubmitted) {
      submittedCount += 1;
      kokTotal += member.gender === 'female' ? 1 : 2;
    }
  });
  if (totalEl) {
    totalEl.textContent = '제출 ' + submittedCount + '명 · 콕 ' + kokTotal + '개';
  }
  if (container) {
    container.innerHTML = list.length
      ? list.map(function(member) {
          var checked = member.kokSubmitted ? ' checked' : '';
          var qtyLabel = member.gender === 'female' ? '여자 · 1개' : '남자 · 2개';
          return '<label class="member ' + genderClass(member) + (member.kokSubmitted ? ' selected' : '') +
            '" style="display:flex;align-items:center;gap:8px;cursor:pointer">' +
            '<input type="checkbox" class="jm-kok-check" data-member-id="' + member.id + '"' + checked +
            ' onchange="toggleKokSubmitted(\\'' + member.id + '\\', this.checked)">' +
            '<span class="name">' + member.name + '</span>' +
            '<span class="meta">' + qtyLabel + '</span>' +
            '</label>';
        }).join('')
      : '<div class="sub">등록된 멤버가 없습니다.</div>';
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
</script>
''' % MARKER

if html.count('</body>') != 1:
    raise SystemExit('</body> anchor not found or not unique')
html = html.replace('</body>', KOK_SCRIPT + '</body>', 1)

# 5) Route the new RPC through the same save-lock overlay as every other member mutation.
mutations_match = re.search(r"var MUTATIONS=new Set\(\[(?P<items>.*?)\]\);", html)
if not mutations_match:
    raise SystemExit('MUTATIONS set anchor not found')
if "'setMemberKokSubmitted'" not in mutations_match.group('items'):
    insertion = mutations_match.group(0).replace(']);', ",'setMemberKokSubmitted']);", 1)
    html = html[:mutations_match.start()] + insertion + html[mutations_match.end():]

if MARKER not in html:
    raise SystemExit('marker missing after patch (should be unreachable)')
if html.count('id="kokSubmitRoster"') != 1:
    raise SystemExit('kok submit roster must exist exactly once')

path.write_text(html, encoding='utf-8')
print('ADMIN_KOK_SUBMIT_CHECK_OK')
