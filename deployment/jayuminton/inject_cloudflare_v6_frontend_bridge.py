#!/usr/bin/env python3
"""Replace legacy JSONP/GAS bridges in an already-rendered admin or member HTML file."""
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: inject_cloudflare_v6_frontend_bridge.py HTML_FILE')
path = Path(sys.argv[1]); html = path.read_text(encoding='utf-8')
bridge = (Path(__file__).with_name('cloudflare_v6_frontend_bridge.js')).read_text(encoding='utf-8')

# The v200.8 UI has observers that unconditionally rewrite nodes inside their
# own observation roots. Android WebView can then remain in a self-sustaining
# microtask/render loop before onPageFinished. Guard every self-write so the
# latest UI remains intact without starving the native page lifecycle.
replacements = {
    "  el.textContent = '전체 ' + total + ' · 남 ' + male + ' · 여 ' + female;":
        "  const nextText = '전체 ' + total + ' · 남 ' + male + ' · 여 ' + female;\n"
        "  if (el.textContent !== nextText) el.textContent = nextText;",
    "    label.textContent = member && isAdminNewMember(member) ? String(member.name || '') : '';":
        "    var nextLabel = member && isAdminNewMember(member) ? String(member.name || '') : '';\n"
        "    if (label.textContent !== nextLabel) label.textContent = nextLabel;",
    "      more.textContent = expanded ? '접기' : '+' + hiddenCount + '명';":
        "      var nextMoreText = expanded ? '접기' : '+' + hiddenCount + '명';\n"
        "      if (more.textContent !== nextMoreText) more.textContent = nextMoreText;",
    "      buttons[0].textContent='실행취소';":
        "      if(buttons[0].textContent!=='실행취소')buttons[0].textContent='실행취소';",
    "      if(!buttons[1].disabled)buttons[1].textContent='새로고침';":
        "      if(!buttons[1].disabled&&buttons[1].textContent!=='새로고침')buttons[1].textContent='새로고침';",
    "      buttons[2].textContent='자동배정';":
        "      if(buttons[2].textContent!=='자동배정')buttons[2].textContent='자동배정';",
}
for old, new in replacements.items():
    count = html.count(old)
    if count != 1:
        raise SystemExit(f'WebView observer guard target mismatch ({count}): {old[:72]}')
    html = html.replace(old, new, 1)

# Consolidate the latest administrator member-management UI. v200.8 carried
# both the original fields and a later MD-specific copy, which displayed the
# new/sponsor controls twice and could save different values on add vs edit.
duplicate_fields = '''      <textarea id="mdPublicMemo" maxlength="120" rows="2" placeholder="메모(생일·특이사항·부상 등, 선택)"></textarea>
      <label class="md-member-check"><input id="mdIsNew" type="checkbox"> new 신규</label>
      <label class="md-member-check"><input id="mdIsSponsor" type="checkbox"> 🎁 찬조</label>

      <input id="newPublicMemo" maxlength="40" placeholder="메모(선택, 생일·특이사항 등)">
      <label class="member-flag-check"><input id="newIsNew" type="checkbox"> 신규</label>
      <label class="member-flag-check"><input id="newIsSponsor" type="checkbox"> 🎁 찬조</label>'''
canonical_fields = '''      <textarea id="newPublicMemo" maxlength="120" rows="2" placeholder="메모 · 생일 · 특이사항 · 부상 등 (선택)"></textarea>
      <label class="md-member-check"><input id="newIsNew" type="checkbox"> new 아이콘 · 신규</label>
      <label class="md-member-check"><input id="newIsSponsor" type="checkbox"> 🎁 아이콘 · 찬조</label>'''
if html.count(duplicate_fields) != 1:
    raise SystemExit('duplicate member fields block mismatch')
html = html.replace(duplicate_fields, canonical_fields, 1)
html = html.replace("document.getElementById('mdPublicMemo')", "document.getElementById('newPublicMemo')")
html = html.replace("document.getElementById('mdIsNew')", "document.getElementById('newIsNew')")
html = html.replace("document.getElementById('mdIsSponsor')", "document.getElementById('newIsSponsor')")
html = html.replace('#mdPublicMemo', '#newPublicMemo')

old_summary = '<summary>멤버 등록·비밀번호·게임횟수 관리</summary>'
new_summary = '<summary>멤버등록·비밀번호·게임횟수·제외인원 관리</summary>'
if html.count(old_summary) != 1:
    raise SystemExit('member management summary mismatch')
html = html.replace(old_summary, new_summary, 1)

old_game_panel = '''    <div class="card admin-game-count-panel" style="box-shadow:none;margin-top:12px">
  <h2>게임횟수 카운트 조정</h2>
  <div class="toolbar section">
<button onclick="decreaseSelectedGames()">
          게임횟수 -1
        </button>
<button onclick="increaseSelectedGames()">게임횟수 +1</button>
<button onclick="resetSelectedGames()">
          게임횟수 모두 0
        </button>
<button type="button" onclick="selectAllMembers()">멤버 모두 선택</button>
  </div>
</div>'''
new_game_panel = '''    <div class="card admin-game-count-panel" style="box-shadow:none;margin-top:12px">
      <h2>게임횟수 카운트 조정</h2>
      <div class="toolbar section md-game-actions">
        <button type="button" onclick="selectAllMembers()">멤버 모두선택</button>
        <span class="meta">카드를 눌러 여러 명 선택</span>
        <button type="button" onclick="resetSelectedGames()">게임횟수 모두 0</button>
        <button type="button" onclick="increaseSelectedGames()">게임횟수 +1</button>
        <button type="button" onclick="decreaseSelectedGames()">게임횟수 -1</button>
      </div>
    </div>
    <div class="card admin-member-bulk-panel" style="box-shadow:none;margin-top:12px">
      <h2>멤버 선택·상태 변경·회원 삭제</h2>
      <div class="md-bulk-member-actions" id="mdBulkDeleteRow">
        <button type="button" onclick="selectAllMembers()">모두선택</button>
        <button type="button" onclick="applyMdSelectedStatus('active')">코트배정</button>
        <button type="button" onclick="applyMdSelectedStatus('before')">도착전</button>
        <button type="button" onclick="applyMdSelectedStatus('rest')">휴식</button>
        <button type="button" onclick="applyMdSelectedStatus('away')">귀가</button>
        <button id="mdBulkDeleteButton" class="danger" type="button" onclick="deleteMdSelectedMembers()" disabled>삭제</button>
      </div>
      <span id="mdBulkDeleteCount" class="meta">0명 선택</span>
    </div>'''
if html.count(old_game_panel) != 1:
    raise SystemExit('game count panel mismatch')
html = html.replace(old_game_panel, new_game_panel, 1)

old_quick_bulk = '''        <div class="md-bulk-delete-row" id="mdBulkDeleteRow">
          <button id="mdBulkDeleteButton" class="danger" type="button" onclick="deleteMdSelectedMembers()" disabled>선택 멤버 삭제</button>
          <span id="mdBulkDeleteCount" class="meta">0명 선택</span>
        </div>
'''
if html.count(old_quick_bulk) != 1:
    raise SystemExit('old quick bulk row mismatch')
html = html.replace(old_quick_bulk, '', 1)

# Keep the combined grade/experience and radio controls synchronized when an
# existing member is opened for editing.
edit_gender = "  gender.value = member.gender === 'female' ? 'female' : 'male';"
edit_gender_next = edit_gender + "\n  document.querySelectorAll('input[name=\"newGenderChoice\"]').forEach(function(input) { input.checked = input.value === gender.value; });"
if html.count(edit_gender) != 1:
    raise SystemExit('edit gender synchronization point mismatch')
html = html.replace(edit_gender, edit_gender_next, 1)
edit_exp = "  experience.value = String(member.experience || '');"
edit_exp_next = edit_exp + "\n  const combinedGradeExperience = document.getElementById('newGradeExperience');\n  if (combinedGradeExperience) combinedGradeExperience.value = [grade.value, experience.value].filter(Boolean).join(' / ');"
if html.count(edit_exp) != 1:
    raise SystemExit('edit grade/experience synchronization point mismatch')
html = html.replace(edit_exp, edit_exp_next, 1)

management_patch = r'''
<style id="jayuminton-admin-member-management-v202">
.admin-setup-details>summary{display:inline-flex!important;align-items:center!important;user-select:none!important}
.admin-setup-details[open]>summary{background:#eaf1ff!important;border-color:#315efb!important;color:#1746b0!important}
#newPublicMemo{min-width:220px;min-height:52px;resize:vertical}
.md-game-actions{align-items:center!important}
.md-bulk-member-actions{display:flex!important;flex-flow:row nowrap!important;gap:5px!important;overflow-x:auto!important;padding:4px 0 6px!important;scrollbar-width:thin}
.md-bulk-member-actions button{flex:1 0 auto!important;min-width:72px!important;min-height:38px!important;padding:6px 8px!important;white-space:nowrap!important;font-size:11px!important;font-weight:900!important}
.md-bulk-member-actions .danger{background:#c62828!important;color:#fff!important;border-color:#c62828!important}
#adminApp .member.male,#adminApp .person.male,#adminApp .quick-member.male{background:#e4f1ff!important;color:#0756b6!important;font-weight:900!important}
#adminApp .member.female,#adminApp .person.female,#adminApp .quick-member.female{background:#ffe7f0!important;color:#c51b4f!important;font-weight:900!important}
#adminApp .member .name,#adminApp .person .name,#adminApp .quick-member-name{font-weight:950!important}
@media(max-width:620px){.admin-setup-details>summary{width:100%!important;box-sizing:border-box!important;justify-content:center!important}.admin-panel{padding:10px!important}.admin-panel h2{font-size:15px!important}.md-game-actions{gap:5px!important}.md-game-actions button{font-size:10px!important;padding:5px 7px!important}.md-bulk-member-actions button{min-width:64px!important;font-size:10px!important;padding:5px!important}}
</style>
<script id="jayuminton-admin-member-management-v202-script">
(function(){
  'use strict';
  window.applyMdSelectedStatus=function(status){
    var ids=[];try{ids=Array.from(SELECTED||[]);}catch(e){}
    if(!ids.length){alert('먼저 멤버 카드를 선택해 주세요.');return;}
    return runAction('setMemberStatus',[ADMIN_PIN_VALUE,ids,status]);
  };
  // Administrator cards always show the game count. Optional profile rows are
  // still rendered only when a value exists.
  if(typeof memberCard==='function'&&!window.__JM_ADMIN_GAMES_REQUIRED_V202__){
    var originalMemberCard=memberCard;
    memberCard=function(member,showGames,clickable){return originalMemberCard(member,IS_ADMIN?true:showGames,clickable);};
    window.__JM_ADMIN_GAMES_REQUIRED_V202__=true;
  }
})();
</script>
'''
if '</body>' not in html:
    raise SystemExit('body closing tag missing')
html = html.replace('</body>', management_patch + '\n</body>', 1)

html = re.sub(r'<script\b[^>]*id=["\']jayuminton-admin-cloudflare-rpc["\'][^>]*>.*?</script>\s*', '', html, flags=re.S | re.I)
html = re.sub(r'<script\b[^>]*id=["\']jayumintonCloudflareRpcV6["\'][^>]*>.*?</script>\s*', '', html, flags=re.S | re.I)
comment = '/* jayuminton-v3-cloudflare-member-preview */'
if comment in html:
    pos = html.index(comment); start = html.rfind('<script', 0, pos); end = html.find('</script>', pos)
    if start < 0 or end < 0: raise SystemExit('member legacy bridge boundary missing')
    html = html[:start] + html[end + len('</script>'):]

marker = re.search(r'<script>\s*const IS_ADMIN\s*=\s*(?:true|false);\s*</script>', html)
if not marker: raise SystemExit('IS_ADMIN marker missing')
injected = marker.group(0) + '\n<script id="jayumintonCloudflareRpcV6">\n' + bridge + '\n</script>'
html = html[:marker.start()] + injected + html[marker.end():]

if html.count('__JAYUMINTON_CLOUDFLARE_RPC_V6__') != 1: raise SystemExit('v6 bridge count mismatch')
if 'script.google.com/macros/s/' in html: raise SystemExit('direct GAS URL remains')
if "if (el.textContent !== nextText) el.textContent = nextText;" not in html:
    raise SystemExit('member count observer guard missing')
if html.count('id="newIsNew"') != 1 or html.count('id="newIsSponsor"') != 1:
    raise SystemExit('member flag controls are not singular')
if 'id="mdIsNew"' in html or 'id="mdIsSponsor"' in html:
    raise SystemExit('duplicate MD member flag controls remain')
path.write_text(html, encoding='utf-8')
print('CLOUDFLARE_V6_FRONTEND_BRIDGE_OK')
