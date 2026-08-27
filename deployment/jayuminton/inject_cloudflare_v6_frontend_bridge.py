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
      <label class="md-member-check"><input id="newIsNew" type="checkbox"> 신규</label>
      <label class="md-member-check"><input id="newIsDuplicate" type="checkbox"> 동명이인</label>
      <label class="md-member-check"><input id="newIsSponsor" type="checkbox"> 찬조</label>'''
if html.count(duplicate_fields) != 1:
    raise SystemExit('duplicate member fields block mismatch')
html = html.replace(duplicate_fields, canonical_fields, 1)
html = html.replace("document.getElementById('mdPublicMemo')", "document.getElementById('newPublicMemo')")
html = html.replace("document.getElementById('mdIsNew')", "document.getElementById('newIsNew')")
html = html.replace("document.getElementById('mdIsSponsor')", "document.getElementById('newIsSponsor')")
html = html.replace('#mdPublicMemo', '#newPublicMemo')

# Extend the existing central metadata wrapper so add and edit use exactly the
# same duplicate-name and team values. This also loads and clears those fields
# when the edit target changes.
old_meta_tail = """    var sponsor=document.getElementById('newIsSponsor');
    return {
      publicMemo:String(memo&&memo.value||'').trim(),
      isNew:!!(isNew&&isNew.checked),
      isSponsor:!!(sponsor&&sponsor.checked)
    };"""
new_meta_tail = """    var sponsor=document.getElementById('newIsSponsor');
    var duplicate=document.getElementById('newIsDuplicate');
    return {
      publicMemo:String(memo&&memo.value||'').trim(),
      isNew:!!(isNew&&isNew.checked),
      isDuplicate:!!(duplicate&&duplicate.checked),
      isSponsor:!!(sponsor&&sponsor.checked)
    };"""
if html.count(old_meta_tail) != 1:
    raise SystemExit('member metadata wrapper mismatch')
html = html.replace(old_meta_tail, new_meta_tail, 1)
old_clear_tail = """    var isNew=document.getElementById('newIsNew'); if(isNew)isNew.checked=false;
    var sponsor=document.getElementById('newIsSponsor'); if(sponsor)sponsor.checked=false;"""
new_clear_tail = old_clear_tail + """
    var duplicate=document.getElementById('newIsDuplicate'); if(duplicate)duplicate.checked=false;"""
if html.count(old_clear_tail) != 1:
    raise SystemExit('member metadata clear mismatch')
html = html.replace(old_clear_tail, new_clear_tail, 1)
old_load_tail = """    var isNew=document.getElementById('newIsNew'); if(isNew)isNew.checked=!!member.isNew;
    var sponsor=document.getElementById('newIsSponsor'); if(sponsor)sponsor.checked=!!member.isSponsor;"""
new_load_tail = old_load_tail + """
    var duplicate=document.getElementById('newIsDuplicate'); if(duplicate)duplicate.checked=!!member.isDuplicate;"""
if html.count(old_load_tail) != 1:
    raise SystemExit('member metadata load mismatch')
html = html.replace(old_load_tail, new_load_tail, 1)

# The proven registration function still invokes google.script.run directly,
# bypassing the central server() wrapper. Add both new fields to its explicit
# metadata object and to the optimistic card as well.
explicit_sponsor = "isSponsor: !!(document.getElementById('newIsSponsor') && document.getElementById('newIsSponsor').checked)"
explicit_extended = explicit_sponsor + ",\n        isDuplicate: !!(document.getElementById('newIsDuplicate') && document.getElementById('newIsDuplicate').checked)"
explicit_count = html.count(explicit_sponsor)
if explicit_count != 3:
    raise SystemExit(f'explicit member metadata object mismatch ({explicit_count})')
html = html.replace(explicit_sponsor, explicit_extended)

# New members and explicitly marked same-name members always show the complete
# stored name. Other administrator cards show only the first two base-name
# characters. The later card timer must follow the same rule.
old_new_predicate = """  function isAdminNewMember(member) {
    return !!member && (member.isNew === true || ['1','true'].indexOf(String(member.isNew || '').toLowerCase()) >= 0);
  }"""
new_new_predicate = """  function isAdminNewMember(member) {
    return !!member && (member.isNew === true || ['1','true'].indexOf(String(member.isNew || '').toLowerCase()) >= 0);
  }
  function isAdminDuplicateMember(member) {
    return !!member && (member.isDuplicate === true || ['1','true'].indexOf(String(member.isDuplicate || '').toLowerCase()) >= 0);
  }
  function usesAdminFullName(member) {
    return isAdminNewMember(member) || isAdminDuplicateMember(member);
  }
  function adminTeamColor(team) {
    var colors=['#5b21b6','#0f766e','#b45309','#0369a1','#be123c','#4338ca','#15803d','#a21caf'];
    var hash=0; String(team||'').split('').forEach(function(ch){hash=((hash*31)+ch.charCodeAt(0))>>>0;});
    return colors[hash%colors.length];
  }"""
if html.count(old_new_predicate) != 1:
    raise SystemExit('administrator full-name predicate mismatch')
html = html.replace(old_new_predicate, new_new_predicate, 1)
html = html.replace('if (isAdminNewMember(member)) {', 'if (usesAdminFullName(member)) {', 1)
html = html.replace('member && isAdminNewMember(member) ? String(member.name || \'\') : \'\'',
                    'member && usesAdminFullName(member) ? String(member.name || \'\') : \'\'', 1)
html = html.replace("if(IS_ADMIN&&!member.isNew&&typeof compactMemberName==='function')displayName=compactMemberName(displayName);",
                    "if(IS_ADMIN&&!member.isNew&&!member.isDuplicate&&typeof compactMemberName==='function')displayName=compactMemberName(displayName);", 1)

# Apply a stable team stripe and team label without changing the existing male
# blue / female pink card background. Same team name always maps to same color.
team_decorator_anchor = """      var name = card.querySelector('.quick-member-name,.name');
      if (!name) return;"""
team_decorator = team_decorator_anchor + """
      var team=String(member.teamLabel||'').trim();
      card.classList.toggle('has-member-team',!!team);
      if(team){
        card.style.setProperty('--member-team-color',adminTeamColor(team));
        var badge=card.querySelector('.member-team-badge');
        if(!badge){badge=document.createElement('span');badge.className='member-team-badge';card.appendChild(badge);}
        if(badge.textContent!==team)badge.textContent=team;
        badge.title='팀 '+team;
      }else{
        card.style.removeProperty('--member-team-color');
        var oldBadge=card.querySelector('.member-team-badge');if(oldBadge)oldBadge.remove();
      }"""
if html.count(team_decorator_anchor) != 1:
    raise SystemExit('member team decorator anchor mismatch')
html = html.replace(team_decorator_anchor, team_decorator, 1)

old_summary = '<summary>멤버 등록·비밀번호·게임횟수 관리</summary>'
new_summary = '<summary>멤버등록·비밀번호·게임횟수·제외인원 관리</summary>'
if html.count(old_summary) != 1:
    raise SystemExit('member management summary mismatch')
html = html.replace(old_summary, new_summary, 1)

# Put member messaging beside Quick Assign so selected cards can be addressed
# without leaving the court screen.
quick_count = '<span id="quickSelectedCount" class="selection-pill">0명 선택</span>'
quick_message = quick_count + '\n          <button id="quickMemberMessageButton" type="button" onclick="openQuickMemberMessage()">메시지 보내기</button>\n          <button id="quickClearSelectionButton" type="button" onclick="clearAdminMemberSelection()">선택 해제</button>'
if html.count(quick_count) != 1:
    raise SystemExit('quick member message anchor mismatch')
html = html.replace(quick_count, quick_message, 1)

# Restore the missing edit control in the existing administrator long-press
# menu. The edit implementation itself is still part of the proven shell.
quick_move_delete = '    <button type="button" class="danger" onclick="deleteLongPressedMembers()">삭제</button>'
quick_move_edit = '    <button type="button" onclick="startMemberEdit()">편집</button>\n' + quick_move_delete
if html.count(quick_move_delete) != 1:
    raise SystemExit('long-press member edit button anchor mismatch')
html = html.replace(quick_move_delete, quick_move_edit, 1)

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
        <button type="button" onclick="applyMdSelectedStatus('active')">코트배정대기</button>
        <button type="button" onclick="applyMdSelectedStatus('before')">도착전</button>
        <button type="button" onclick="applyMdSelectedStatus('rest')">휴식</button>
        <button type="button" onclick="applyMdSelectedStatus('away')">귀가</button>
        <button id="mdBulkDeleteButton" class="danger" type="button" onclick="deleteMdSelectedMembers()" disabled>삭제</button>
      </div>
      <div class="md-team-member-actions">
        <button type="button" onclick="setMdSelectedTeam()">같은 팀 설정</button>
        <button type="button" onclick="clearMdSelectedTeam()">팀 해제</button>
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

# The court voice toolbar must expose an announcement-only mute. This does not
# mute background music: cancelling NativeVoice restores the temporarily
# ducked music stream immediately.
old_voice_controls = '''        <div class="court-voice-controls" aria-label="경기 종료 음성 조작">
          <button id="replayVoiceButton" type="button" onclick="replayLastVoiceAnnouncement()" disabled>▶ 재생</button>
          <button id="repeatVoiceButton" type="button" onclick="toggleVoiceRepeat()" aria-pressed="false">🔁 반복</button>
          <button type="button" onclick="stopVoiceAnnouncement()">■ 멈춤</button>
        </div>'''
new_voice_controls = '''        <div class="court-voice-controls" aria-label="경기 종료 음성 조작">
          <button id="replayVoiceButton" type="button" onclick="replayLastVoiceAnnouncement()" disabled>▶ 1회 재생</button>
          <button id="repeatVoiceButton" type="button" onclick="toggleVoiceRepeat()" aria-pressed="false">🔁 반복재생</button>
          <button id="stopVoiceButton" type="button" onclick="stopVoiceAnnouncement()">■ 멈춤</button>
          <button id="announcementMuteButton" type="button" onclick="toggleAnnouncementMute()" aria-pressed="false">🔇 멘트 음소거</button>
        </div>'''
if html.count(old_voice_controls) != 1:
    raise SystemExit('court voice controls mismatch')
html = html.replace(old_voice_controls, new_voice_controls, 1)

# A legacy finish-court compatibility layer calls NativeVoice directly. Make
# that path honor the same persisted announcement-only mute state as the main
# voice controls, otherwise court finish bypasses the mute button.
direct_speak = "  function directSpeak(text){var result={ok:false,reason:'',engine:''};text=String(text||'').replace(/\\n/g,' ').trim();try{"
direct_speak_muted = direct_speak + "if(localStorage.getItem(VOICE_GUIDE_KEY)==='false'||VOICE_GUIDE_ENABLED===false){result.ok=true;result.reason='muted';result.engine='muted';return result;}"
if html.count(direct_speak) != 1:
    raise SystemExit('legacy directSpeak mute guard anchor mismatch')
html = html.replace(direct_speak, direct_speak_muted, 1)

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
.md-bulk-member-actions{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:5px!important;width:100%!important;overflow:visible!important;padding:4px 0 6px!important}
.md-bulk-member-actions button{width:100%!important;min-width:0!important;min-height:38px!important;padding:6px 4px!important;white-space:normal!important;line-height:1.15!important;font-size:11px!important;font-weight:900!important}
.md-team-member-actions{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:5px!important;width:100%!important;margin-top:5px!important;overflow:visible!important}
.md-team-member-actions button{width:100%!important;min-width:0!important;min-height:38px!important;padding:6px 4px!important;white-space:normal!important;font-size:11px!important;font-weight:950!important;color:#1d4ed8!important;border-color:#93b4ff!important;background:#eef4ff!important}
.md-bulk-member-actions .danger{background:#c62828!important;color:#fff!important;border-color:#c62828!important}
#quickMemberMessageButton{min-height:34px;padding:6px 10px;border-radius:10px;background:#315efb;color:#fff;border:1px solid #315efb;font-size:11px;font-weight:900;white-space:nowrap}
.quick-message-modal{position:fixed;z-index:2147483500;inset:0;display:flex;align-items:center;justify-content:center;padding:16px;background:rgba(15,23,42,.55)}
.quick-message-modal.hidden{display:none!important}.quick-message-card{width:min(92vw,480px);padding:16px;border-radius:16px;background:#fff;box-shadow:0 20px 60px rgba(0,0,0,.35)}
.quick-message-card h3{margin:0 0 8px}.quick-message-card textarea{width:100%;box-sizing:border-box;min-height:110px;resize:vertical}.quick-message-actions{display:flex;justify-content:flex-end;gap:7px;margin-top:10px}.quick-message-actions button{min-height:40px;padding:8px 14px;font-weight:900}.quick-message-send{background:#315efb!important;color:#fff!important;border-color:#315efb!important}
.pair-statistics-list{overflow-y:auto!important;overflow-x:hidden!important;max-height:calc(86vh - 90px)!important}
.pair-statistics-disclosure{display:block!important;width:100%!important;box-sizing:border-box!important;margin:0 0 7px!important;border:1px solid #dce2ee!important;border-radius:11px!important;background:#fff!important;overflow:visible!important}
.pair-statistics-disclosure>summary{display:block!important;position:relative!important;padding:9px 34px 9px 10px!important;cursor:pointer!important;list-style:none!important;overflow:visible!important}
.pair-statistics-disclosure>summary::-webkit-details-marker{display:none!important}
.pair-statistics-disclosure>summary:after{content:'펼치기';position:absolute;right:9px;top:50%;transform:translateY(-50%);font-size:10px;font-weight:900;color:#315efb}
.pair-statistics-disclosure[open]>summary:after{content:'접기'}
.pair-statistics-disclosure .pair-statistics-head,.pair-statistics-disclosure .md-pair-head{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:8px!important;min-width:0!important;font-size:12px!important;line-height:1.35!important;white-space:normal!important;overflow:visible!important}
.pair-statistics-disclosure .pair-statistics-name,.pair-statistics-disclosure .md-pair-head span:first-child{min-width:0!important;overflow-wrap:anywhere!important;word-break:keep-all!important}
.pair-statistics-disclosure .pair-statistics-partners,.pair-statistics-disclosure .md-pair-partners{display:flex!important;flex-wrap:wrap!important;gap:5px!important;max-height:none!important;height:auto!important;padding:0 10px 10px!important;margin:0!important;white-space:normal!important;overflow:visible!important;overflow-wrap:anywhere!important;word-break:keep-all!important;font-size:11px!important;line-height:1.5!important}
.pair-statistics-disclosure .pair-statistics-chip{display:inline-flex!important;max-width:100%!important;white-space:normal!important;overflow-wrap:anywhere!important}
#adminApp .member.male,#adminApp .person.male,#adminApp .quick-member.male{background:#e4f1ff!important;color:#0756b6!important;font-weight:900!important}
#adminApp .member.female,#adminApp .person.female,#adminApp .quick-member.female{background:#ffe7f0!important;color:#c51b4f!important;font-weight:900!important}
#adminApp .member .name,#adminApp .person .name,#adminApp .quick-member-name{font-weight:950!important}
#adminApp .member-team-badge{display:none!important}
@media(max-width:620px){.admin-setup-details>summary{width:100%!important;box-sizing:border-box!important;justify-content:center!important}.admin-panel{padding:10px!important}.admin-panel h2{font-size:15px!important}.md-game-actions{gap:5px!important}.md-game-actions button{font-size:10px!important;padding:5px 7px!important}.md-bulk-member-actions{grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:4px!important}.md-bulk-member-actions button{min-width:0!important;font-size:10px!important;padding:5px 2px!important}}
</style>
<style id="jayuminton-announcement-controls-v2021">
.court-voice-controls{display:flex!important;flex-wrap:wrap!important;gap:6px!important}
.court-voice-controls button{white-space:nowrap!important}
#announcementMuteButton.is-muted,#emergencyAnnouncementMuteButton.is-muted{background:#9f1239!important;border-color:#9f1239!important;color:#fff!important}
.admin-save-notice{z-index:2147483600!important;background:rgba(15,23,42,.20)!important;backdrop-filter:none!important;-webkit-backdrop-filter:none!important;cursor:wait!important;contain:strict!important}
.voice-save-emergency{position:fixed;z-index:2147483647;top:max(10px,env(safe-area-inset-top,0px));left:50%;transform:translateX(-50%);display:none;align-items:center;gap:8px;padding:8px;border-radius:12px;background:#fff;border:2px solid #1d4ed8;box-shadow:0 8px 30px rgba(0,0,0,.35);pointer-events:auto!important;filter:none!important;backdrop-filter:none!important;-webkit-backdrop-filter:none!important}
.voice-save-emergency.is-visible{display:flex!important}
.voice-save-emergency button{min-height:42px;padding:8px 12px;border-radius:9px;font-weight:900;white-space:nowrap}
.voice-save-emergency .voice-stop{background:#b91c1c;color:#fff;border-color:#b91c1c}
@media(max-width:620px){.court-voice-controls{width:100%!important;display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:4px!important}.court-voice-controls button{min-width:0!important;padding:7px 4px!important;font-size:11px!important}.voice-save-emergency{width:calc(100vw - 20px);box-sizing:border-box;justify-content:center}.voice-save-emergency button{flex:1;min-width:0;font-size:13px}}
</style>
<div id="voiceSaveEmergency" class="voice-save-emergency" role="group" aria-label="저장 중 음성 멘트 긴급 조작">
  <button class="voice-stop" type="button" onclick="stopVoiceAnnouncement()">■ 멘트 멈춤</button>
  <button id="emergencyAnnouncementMuteButton" type="button" onclick="toggleAnnouncementMute()">🔇 멘트 음소거</button>
</div>
<div id="quickMemberMessageModal" class="quick-message-modal hidden" role="dialog" aria-modal="true" aria-labelledby="quickMemberMessageTitle">
  <div class="quick-message-card" onclick="event.stopPropagation()">
    <h3 id="quickMemberMessageTitle">선택 회원에게 메시지</h3>
    <div id="quickMemberMessageRecipients" class="meta"></div>
    <textarea id="quickMemberMessageText" maxlength="300" placeholder="전송할 메시지를 입력하세요."></textarea>
    <div class="quick-message-actions"><button type="button" onclick="closeQuickMemberMessage(true)">취소·선택해제</button><button class="quick-message-send" type="button" onclick="sendQuickMemberMessage()">전송</button></div>
  </div>
</div>
<script id="jayuminton-pair-statistics-disclosure-v2028">
(function(){
  'use strict';
  function upgrade(root){
    root=root||document;var selector='.pair-statistics-row:not([data-jm-disclosure-ready])',rows=[];
    if(root.matches&&root.matches(selector))rows.push(root);
    if(root.querySelectorAll)rows=rows.concat(Array.from(root.querySelectorAll(selector)));
    rows.forEach(function(row){
      row.setAttribute('data-jm-disclosure-ready','1');
      var head=row.querySelector('.pair-statistics-head,.md-pair-head');
      var partners=row.querySelector('.pair-statistics-partners,.md-pair-partners');
      if(!head||!partners)return;
      var details=document.createElement('details');details.className='pair-statistics-disclosure';
      var summary=document.createElement('summary');summary.appendChild(head);
      details.appendChild(summary);details.appendChild(partners);row.replaceWith(details);
    });
  }
  var observer=new MutationObserver(function(records){records.forEach(function(record){record.addedNodes.forEach(function(node){if(node.nodeType===1)upgrade(node);});});});
  observer.observe(document.documentElement,{childList:true,subtree:true});
  document.addEventListener('DOMContentLoaded',function(){upgrade(document);},{once:true});upgrade(document);
})();
</script>
<script id="jayuminton-admin-member-management-v202-script">
(function(){
  'use strict';
  window.__JAYUMINTON_ADMIN_SELECTION_SCOPE_V2057__=true;
  window.clearAdminMemberSelection=function(){
    try{if(typeof SELECTED!=='undefined'&&SELECTED&&typeof SELECTED.clear==='function')SELECTED.clear();}catch(e){}
    try{if(typeof window.__JAYUMINTON_RESET_MULTI_SELECTION_V2057__==='function')window.__JAYUMINTON_RESET_MULTI_SELECTION_V2057__();}catch(e){}
    document.querySelectorAll('#adminApp .selected,#adminApp .quick-picked,#adminApp .jm-source-selected,#adminApp .jm-target-selected').forEach(function(card){card.classList.remove('selected','quick-picked','jm-source-selected','jm-target-selected');});
    var quick=document.getElementById('quickSelectedCount'),mobile=document.getElementById('mobileSelectedCount'),bulk=document.getElementById('mdBulkDeleteCount'),del=document.getElementById('mdBulkDeleteButton');
    if(quick){quick.textContent='0명 선택';quick.classList.remove('has-selection');}
    if(mobile)mobile.textContent='0명 선택';
    if(bulk)bulk.textContent='0명 선택';
    if(del)del.disabled=true;
    try{if(typeof renderQuickRoster==='function')renderQuickRoster();}catch(e){}
    try{if(typeof renderQuickMoveBar==='function')renderQuickMoveBar();}catch(e){}
  };
  window.applyMdSelectedStatus=function(status){
    var ids=[];try{ids=Array.from(SELECTED||[]);}catch(e){}
    if(!ids.length){alert('먼저 멤버 카드를 선택해 주세요.');return;}
    return runAction('setMemberStatus',[ADMIN_PIN_VALUE,ids,status]);
  };
  window.setMdSelectedTeam=function(){
    var ids=[];try{ids=Array.from(SELECTED||[]);}catch(e){}
    if(ids.length<2){alert('같은 팀으로 묶을 멤버를 2명 이상 선택해 주세요.');return;}
    var occupied={};try{Object.values(STATE.courts||{}).flat().concat((STATE.waitGroups||[]).flat()).forEach(function(id){occupied[String(id)]=true;});}catch(e){}
    var invalid=[];try{invalid=(STATE.members||[]).filter(function(m){return ids.indexOf(String(m.id))>=0&&(occupied[String(m.id)]||String(m.status||'active')!=='active');});}catch(e){}
    if(invalid.length){alert('같은 팀은 코트배정 대기에 있는 멤버만 설정할 수 있습니다.');return;}
    return runAction('setBundle',[ADMIN_PIN_VALUE,ids]);
  };
  window.clearMdSelectedTeam=function(){
    var ids=[];try{ids=Array.from(SELECTED||[]);}catch(e){}
    if(!ids.length){alert('팀을 해제할 멤버 카드를 선택해 주세요.');return;}
    return runAction('clearBundle',[ADMIN_PIN_VALUE,ids]);
  };
  window.openQuickMemberMessage=function(){
    var ids=[];try{ids=Array.from(SELECTED||[]);}catch(e){}
    if(!ids.length){alert('메시지를 받을 회원카드를 먼저 선택해 주세요.');return;}
    var names=[];try{names=(STATE.members||[]).filter(function(m){return ids.indexOf(String(m.id))>=0;}).map(function(m){return String(m.name||'');});}catch(e){}
    var modal=document.getElementById('quickMemberMessageModal'),recipients=document.getElementById('quickMemberMessageRecipients'),text=document.getElementById('quickMemberMessageText');
    if(recipients)recipients.textContent=ids.length+'명 선택 · '+names.join(', ');
    if(modal)modal.classList.remove('hidden');if(text){text.value='';setTimeout(function(){text.focus();},50);}
  };
  window.closeQuickMemberMessage=function(clearSelection){var modal=document.getElementById('quickMemberMessageModal');if(modal)modal.classList.add('hidden');if(clearSelection)clearAdminMemberSelection();};
  window.sendQuickMemberMessage=async function(){
    var ids=[];try{ids=Array.from(SELECTED||[]);}catch(e){}
    var text=document.getElementById('quickMemberMessageText'),message=String(text&&text.value||'').trim();
    if(!ids.length){alert('메시지를 받을 회원카드를 선택해 주세요.');return;}
    if(!message){alert('메시지를 입력해 주세요.');if(text)text.focus();return;}
    closeQuickMemberMessage(false);
    try{await runAction('sendMemberMessage',[ADMIN_PIN_VALUE,ids,message]);alert(ids.length+'명에게 메시지를 전송했습니다.');}
    catch(error){alert(error&&error.message?error.message:error);}
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
<script id="jayuminton-announcement-controls-v2021-script">
(function(){
  'use strict';
  function isAnnouncementActive(){
    try {
      return !!VOICE_REPEAT_ENABLED || !!VOICE_QUEUE.length ||
        !!VOICE_UTTERANCES.length ||
        !!(window.speechSynthesis && window.speechSynthesis.speaking);
    } catch(error){ return false; }
  }
  function isSaveOverlayVisible(){
    var notice=document.getElementById('adminSaveNotice');
    return !!(notice && notice.classList.contains('is-visible'));
  }
  window.updateAnnouncementMuteButtons=function(){
    var muted=!VOICE_GUIDE_ENABLED;
    ['announcementMuteButton','emergencyAnnouncementMuteButton'].forEach(function(id){
      var button=document.getElementById(id); if(!button)return;
      button.classList.toggle('is-muted',muted);
      button.setAttribute('aria-pressed',muted?'true':'false');
      button.textContent=muted?'🔊 멘트 켜기':'🔇 멘트 음소거';
    });
  };
  window.toggleAnnouncementMute=function(){
    var shouldMute=VOICE_GUIDE_ENABLED;
    VOICE_GUIDE_ENABLED=!shouldMute;
    try{localStorage.setItem(VOICE_GUIDE_KEY,VOICE_GUIDE_ENABLED?'true':'false');}catch(error){}
    if(shouldMute){
      // stopVoiceAnnouncement cancels only the spoken announcement. NativeVoice
      // then restores the music stream that was temporarily lowered for speech.
      stopVoiceAnnouncement();
    }
    if(typeof updateVoiceGuideButton==='function')updateVoiceGuideButton();
    updateAnnouncementMuteButtons();
  };
  function syncEmergencyVoiceControls(){
    var controls=document.getElementById('voiceSaveEmergency');
    if(!controls)return;
    controls.classList.toggle('is-visible',isSaveOverlayVisible());
    updateAnnouncementMuteButtons();
  }
  function syncSaveInteractionLock(){
    var locked=isSaveOverlayVisible();
    var app=document.getElementById('adminApp');
    if(app){
      if(locked)app.setAttribute('inert','');
      else app.removeAttribute('inert');
      app.setAttribute('aria-busy',locked?'true':'false');
    }
    document.documentElement.classList.toggle('jm-save-locked',locked);
  }
  function blockSaveInteraction(event){
    if(!isSaveOverlayVisible())return;
    var allowed=event.target&&event.target.closest&&event.target.closest('#voiceSaveEmergency');
    if(allowed)return;
    event.preventDefault();event.stopImmediatePropagation();event.stopPropagation();
  }
  ['pointerdown','touchstart','click','keydown'].forEach(function(type){
    document.addEventListener(type,blockSaveInteraction,true);
  });
  var originalUpdateVoiceGuideButton=window.updateVoiceGuideButton;
  window.updateVoiceGuideButton=function(){
    if(typeof originalUpdateVoiceGuideButton==='function')originalUpdateVoiceGuideButton();
    updateAnnouncementMuteButtons();
  };
  document.addEventListener('DOMContentLoaded',function(){updateAnnouncementMuteButtons();syncEmergencyVoiceControls();});
  window.setInterval(function(){syncEmergencyVoiceControls();syncSaveInteractionLock();},160);
  updateAnnouncementMuteButtons();
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
for required_voice_marker in [
    'id="announcementMuteButton"',
    'id="voiceSaveEmergency"',
    'function(){\n    var shouldMute=VOICE_GUIDE_ENABLED;',
    "controls.classList.toggle('is-visible',isSaveOverlayVisible())",
    "result.reason='muted';result.engine='muted'",
    'backdrop-filter:none!important',
    "if(locked)app.setAttribute('inert','')",
    'filter:none!important;backdrop-filter:none!important',
    'id="newIsDuplicate"',
    'function usesAdminFullName(member)',
    'window.setMdSelectedTeam=function()',
    'window.clearMdSelectedTeam=function()',
    '>같은 팀 설정</button>',
    '>팀 해제</button>',
    'id="quickMemberMessageButton"',
    'window.sendQuickMemberMessage=async function()',
    'id="jayuminton-pair-statistics-disclosure-v2028"',
    "details.className='pair-statistics-disclosure'",
    'function resumeSavedSession()',
    'resumeSavedSession();',
    "event.target.closest('#voiceSaveEmergency')",
]:
    if required_voice_marker not in html:
        raise SystemExit('announcement voice control missing: ' + required_voice_marker)
path.write_text(html, encoding='utf-8')
print('CLOUDFLARE_V6_FRONTEND_BRIDGE_OK')
