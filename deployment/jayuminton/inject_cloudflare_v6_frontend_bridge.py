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
<style id="jayuminton-announcement-controls-v2021">
.court-voice-controls{display:flex!important;flex-wrap:wrap!important;gap:6px!important}
.court-voice-controls button{white-space:nowrap!important}
#announcementMuteButton.is-muted,#emergencyAnnouncementMuteButton.is-muted{background:#9f1239!important;border-color:#9f1239!important;color:#fff!important}
.admin-save-notice{z-index:2147483600!important;background:rgba(15,23,42,.66)!important;backdrop-filter:none!important;-webkit-backdrop-filter:none!important;cursor:wait!important;contain:strict!important}
.admin-save-notice::before{content:'';position:fixed;top:0;left:0;width:38%;height:5px;background:linear-gradient(90deg,#60a5fa,#fff,#2563eb);box-shadow:0 0 12px rgba(96,165,250,.8);transform:translate3d(-110%,0,0);animation:jm-save-progress 1.05s ease-in-out infinite;will-change:transform}
@keyframes jm-save-progress{0%{transform:translate3d(-110%,0,0)}100%{transform:translate3d(365%,0,0)}}
@media(prefers-reduced-motion:reduce){.admin-save-notice::before{animation-duration:2.4s}}
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
    controls.classList.toggle('is-visible',isSaveOverlayVisible()&&isAnnouncementActive());
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
    "controls.classList.toggle('is-visible',isSaveOverlayVisible()&&isAnnouncementActive())",
    'backdrop-filter:none!important',
    'animation:jm-save-progress 1.05s ease-in-out infinite',
    "if(locked)app.setAttribute('inert','')",
    'filter:none!important;backdrop-filter:none!important',
]:
    if required_voice_marker not in html:
        raise SystemExit('announcement voice control missing: ' + required_voice_marker)
path.write_text(html, encoding='utf-8')
print('CLOUDFLARE_V6_FRONTEND_BRIDGE_OK')
