#!/usr/bin/env python3
"""Patch the live Cloudflare member page without rebuilding its protected UI."""

from pathlib import Path
import sys


MARKER = "JAYUMINTON_MEMBER_USER_REQUIREMENTS_V1"
NATIVE_SYNC_MARKER = "JAYUMINTON_MEMBER_NATIVE_IDENTITY_SYNC_V2"
AUTO_SYNC_MARKER = "JAYUMINTON_MEMBER_REVISION_AUTOSYNC_V1"
TEAM_STATUS_MARKER = "JAYUMINTON_MEMBER_TEAM_STATUS_BADGES_V1"
MEMBER_MESSAGE_MARKER = "JAYUMINTON_MEMBER_DIRECT_MESSAGE_ALERT_V1"
SELF_PROFILE_MARKER = "JAYUMINTON_MEMBER_SELF_PROFILE_EDIT_V1"
TEAM_ONLY_V2_MARKER = "JAYUMINTON_MEMBER_TEAM_ONLY_BADGES_V2"
SELF_MEMO_ONLY_V2_MARKER = "JAYUMINTON_MEMBER_SELF_MEMO_ONLY_V2"
TEAM_CARD_LAYOUT_V3_MARKER = "JAYUMINTON_MEMBER_TEAM_CARD_LAYOUT_V5"
IDENTITY_BIND_MARKER = "JAYUMINTON_MEMBER_IDENTITY_BIND_V2"
REFRESH_STATUS_MARKER = "JAYUMINTON_MEMBER_REFRESH_STATUS_V1"
SELF_INFO_MENU_MARKER = "JAYUMINTON_MEMBER_SELF_INFO_MENU_V1"
MEMBER_FLAGS_MARKER = "JAYUMINTON_MEMBER_FLAGS_V1"
MEMO_DEDUPE_MARKER = "JAYUMINTON_MEMBER_MEMO_DEDUPE_V1"
COMPLETION_MARKER = "JAYUMINTON_MEMBER_REQUIREMENTS_COMPLETION_V1"

ADDON = r'''
<script>
/* JAYUMINTON_MEMBER_USER_REQUIREMENTS_V1
   - eight rounds of three strong vibration pulses
   - stop vibration immediately when the foreground alert is confirmed
   - announce all four promoted wait-1 members on court assignment
   - expire an unanswered outgoing swap request after five minutes
*/
(function installMemberUserRequirementsV1(){
  if (window.__JAYUMINTON_MEMBER_USER_REQUIREMENTS_V1__) return;
  window.__JAYUMINTON_MEMBER_USER_REQUIREMENTS_V1__ = true;

  var SWAP_TIMEOUT_MS = 5 * 60 * 1000;
  var swapExpiryTimer = null;
  var alertAudioTimers = [];

  function stopAlertFeedback(){
    alertAudioTimers.forEach(function(timer){ clearTimeout(timer); });
    alertAudioTimers = [];
    try { if (navigator.vibrate) navigator.vibrate(0); } catch (error) {}
    try {
      if (window.JayumintonNative && typeof window.JayumintonNative.stopVibration === 'function') {
        window.JayumintonNative.stopVibration();
      }
    } catch (error) {}
    try { postUnifiedMemberMessage('JAYUMINTON_STOP_MEMBER_ALERT', {}); } catch (error) {}
  }

  function strongThreeByEightPattern(){
    var pattern = [];
    for (var round = 0; round < 8; round += 1) {
      for (var pulse = 0; pulse < 3; pulse += 1) {
        pattern.push(360);
        if (!(round === 7 && pulse === 2)) pattern.push(pulse === 2 ? 520 : 150);
      }
    }
    return pattern;
  }

  window.memberVibrationPattern = function(){ return strongThreeByEightPattern(); };
  window.memberAlertRepeatCount = function(){ return 1; };

  window.playMemberAlertCue = function(type, title, body, eventId){
    stopAlertFeedback();
    try {
      if (memberVibrationEnabled() && navigator.vibrate) {
        navigator.vibrate(strongThreeByEightPattern());
      }
    } catch (error) {}
    if (!memberAlertEnabled()) return;
    for (var round = 0; round < 8; round += 1) {
      (function(index){
        alertAudioTimers.push(setTimeout(function(){
          try { playSingleMemberAlertCue(type); } catch (error) {}
        }, index * 1600));
      })(round);
    }
  };

  var originalCloseAlert = window.closeMemberForegroundAlert;
  window.closeMemberForegroundAlert = function(){
    stopAlertFeedback();
    if (typeof originalCloseAlert === 'function') return originalCloseAlert.apply(this, arguments);
  };

  function waitOneNames(state){
    var ids = state && Array.isArray(state.waitGroups) && Array.isArray(state.waitGroups[0])
      ? state.waitGroups[0].slice(0, 4) : [];
    return ids.map(function(id){
      var member = (state.members || []).find(function(item){ return item && String(item.id) === String(id); });
      return member ? String(member.name || '') : '';
    }).filter(Boolean);
  }

  window.detectMemberForegroundTransition = function(previousState, nextState){
    if (IS_ADMIN || !previousState || !nextState) return;
    normalizeStateMemberProfiles(previousState);
    normalizeStateMemberProfiles(nextState);
    var member = selectedWebPushMember();
    if (!member) return;
    var before = memberLocation(previousState, member.id);
    var after = memberLocation(nextState, member.id);
    var updatedAt = String(nextState.updatedAt || Date.now());

    if (before.type === 'wait' && before.index === 1 && after.type === 'wait' && after.index === 0) {
      showMemberForegroundAlert(
        '대기 1순위 안내',
        '대기1순위 입니다. 라켓 들고 준비해주세요.',
        'wait1_' + member.id + '_' + updatedAt,
        'wait1_ready'
      );
    }

    if (before.type === 'wait' && before.index === 0 && after.type === 'court') {
      var courtNo = Number(after.index);
      var names = waitOneNames(previousState);
      var callout = names.length ? ' 대기1: ' + names.join(', ') + '님' : '';
      showMemberForegroundAlert(
        '코트 배정 안내',
        courtNo + '번 코트 나왔습니다.' + callout + ' ' + courtNo + '번 코트로 들어가주세요.',
        'court_' + courtNo + '_' + member.id + '_' + updatedAt,
        'court_assignment'
      );
    }
  };

  function clearSwapExpiry(){
    if (swapExpiryTimer) clearTimeout(swapExpiryTimer);
    swapExpiryTimer = null;
  }

  var originalStopOutgoing = window.memberAnywhereStopOutgoingSync_;
  window.memberAnywhereStopOutgoingSync_ = function(){
    clearSwapExpiry();
    if (typeof originalStopOutgoing === 'function') return originalStopOutgoing.apply(this, arguments);
  };

  var originalStartOutgoing = window.memberAnywhereStartOutgoingSync_;
  window.memberAnywhereStartOutgoingSync_ = function(baseline, startedAt, targetLocationKey, targetMemberId){
    clearSwapExpiry();
    var result = typeof originalStartOutgoing === 'function'
      ? originalStartOutgoing.apply(this, arguments) : undefined;
    var createdAt = Number(startedAt || 0) || Date.now();
    var remaining = Math.max(0, SWAP_TIMEOUT_MS - (Date.now() - createdAt));
    swapExpiryTimer = setTimeout(function(){
      Promise.resolve(memberAnywhereCancelOutgoingServer_()).finally(function(){
        clearSwapExpiry();
        if (typeof originalStopOutgoing === 'function') originalStopOutgoing();
        if (window.memberAnywhereSelection) window.memberAnywhereSelection.clear();
        if (window.memberAnywhereModal) {
          window.memberAnywhereModal.show('교환 요청 실패','5분 동안 응답이 없어 자리교환 요청이 종료됐어요.');
        }
        if (typeof refreshMemberState === 'function') refreshMemberState();
      });
    }, remaining);
    return result;
  };

  window.addEventListener('pagehide', stopAlertFeedback);
})();
</script>
'''

NATIVE_SYNC_ADDON = r'''
<script>
/* JAYUMINTON_MEMBER_NATIVE_IDENTITY_SYNC_V2
   Keep the native APK FCM token bound to the currently selected self member.
   This is intentionally independent of visual rendering and repeats safely.
*/
(function installMemberNativeIdentitySyncV2(){
  if (window.__JAYUMINTON_MEMBER_NATIVE_IDENTITY_SYNC_V2__) return;
  window.__JAYUMINTON_MEMBER_NATIVE_IDENTITY_SYNC_V2__ = true;
  var lastIdentityKey = null;

  function currentSelfForNative(){
    try {
      if (typeof selectedWebPushMember === 'function') {
        var selected = selectedWebPushMember();
        if (selected && selected.id) return selected;
      }
    } catch (error) {}
    try {
      if (typeof currentStoredWebPushMember === 'function') {
        var stored = currentStoredWebPushMember();
        if (stored && stored.id) return stored;
      }
    } catch (error) {}
    return null;
  }

  window.syncNativeUserPushBridge = function(){
    if (typeof IS_ADMIN !== 'undefined' && IS_ADMIN) return;
    if (!window.NativeUserApp) return;
    var member = currentSelfForNative();
    try {
      if (typeof window.NativeUserApp.setPushEnabled === 'function' && typeof memberAlertEnabled === 'function') {
        window.NativeUserApp.setPushEnabled(!!memberAlertEnabled());
      }
    } catch (error) {}
    try {
      if (typeof window.NativeUserApp.setVibrationEnabled === 'function' && typeof memberVibrationEnabled === 'function') {
        window.NativeUserApp.setVibrationEnabled(!!memberVibrationEnabled());
      }
    } catch (error) {}

    if (member && member.id) {
      var memberId = String(member.id);
      var memberName = String(member.name || '');
      var nextKey = memberId + '\n' + memberName;
      try {
        if (lastIdentityKey !== nextKey && typeof window.NativeUserApp.setMember === 'function') {
          window.NativeUserApp.setMember(memberId, memberName);
          lastIdentityKey = nextKey;
        }
      } catch (error) {
        lastIdentityKey = null;
      }
    } else {
      try {
        if (lastIdentityKey !== '' && typeof window.NativeUserApp.clearMember === 'function') {
          window.NativeUserApp.clearMember();
          lastIdentityKey = '';
        }
      } catch (error) {}
    }
  };

  function syncSoon(delay){ setTimeout(function(){ try { window.syncNativeUserPushBridge(); } catch (error) {} }, delay); }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function(){ syncSoon(0); syncSoon(300); syncSoon(1500); }, {once:true});
  } else {
    syncSoon(0); syncSoon(300); syncSoon(1500);
  }
  window.addEventListener('load', function(){ syncSoon(100); syncSoon(1000); });
  document.addEventListener('visibilitychange', function(){ if (!document.hidden) syncSoon(50); });
  document.addEventListener('click', function(){ syncSoon(80); }, true);
  document.addEventListener('change', function(){ syncSoon(80); }, true);
  setInterval(function(){ try { window.syncNativeUserPushBridge(); } catch (error) {} }, 15000);
})();
</script>
'''

AUTO_SYNC_ADDON = r'''
<script>
/* JAYUMINTON_MEMBER_REVISION_AUTOSYNC_V1
   Poll only for a newer revision and render through the page's normal refresh path.
*/
(function installMemberRevisionAutosyncV1(){
  if (window.__JAYUMINTON_MEMBER_REVISION_AUTOSYNC_V1__) return;
  window.__JAYUMINTON_MEMBER_REVISION_AUTOSYNC_V1__ = true;
  var busy = false;
  var lastSeenRevision = null;

  function currentRevision(){
    try {
      if (window.STATE && Number.isFinite(Number(window.STATE.revision))) return Number(window.STATE.revision);
      if (typeof STATE !== 'undefined' && STATE && Number.isFinite(Number(STATE.revision))) return Number(STATE.revision);
    } catch (error) {}
    return null;
  }

  function rememberRevision(){
    var rev = currentRevision();
    if (rev !== null) lastSeenRevision = rev;
  }

  function pollRevision(){
    if (busy || document.hidden) return;
    if (typeof server !== 'function' || typeof refreshMemberState !== 'function') return;
    busy = true;
    Promise.resolve(server('getPublicState', []))
      .then(function(next){
        var rev = next && Number(next.revision);
        if (!Number.isFinite(rev)) return;
        var local = currentRevision();
        var baseline = local !== null ? local : lastSeenRevision;
        if (baseline === null) { lastSeenRevision = rev; return; }
        if (rev !== baseline) {
          return Promise.resolve(refreshMemberState()).then(function(){ lastSeenRevision = rev; });
        }
        lastSeenRevision = rev;
      })
      .catch(function(){})
      .finally(function(){ busy = false; });
  }

  rememberRevision();
  setInterval(pollRevision, 1800);
  window.addEventListener('focus', pollRevision);
  document.addEventListener('visibilitychange', function(){ if (!document.hidden) pollRevision(); });
})();
</script>
'''

TEAM_STATUS_ADDON = r'''
<style id="jayuminton-member-team-status-badges-v1">
.jm-member-badges{display:inline-flex;flex-wrap:wrap;gap:3px;margin-left:5px;vertical-align:middle}
.jm-member-badge{display:inline-flex;align-items:center;padding:2px 6px;border-radius:999px;background:#fff;font-size:10px;font-weight:900;line-height:1.3;white-space:nowrap}
.jm-team-badge{border:1px solid var(--jm-team-color);color:var(--jm-team-color)}
</style>
<script>
/* JAYUMINTON_MEMBER_TEAM_STATUS_BADGES_V1 */
(function installMemberTeamStatusBadgesV1(){
  if(window.__JAYUMINTON_MEMBER_TEAM_STATUS_BADGES_V1__)return;
  window.__JAYUMINTON_MEMBER_TEAM_STATUS_BADGES_V1__=true;
  var scheduled=false;
  function state(){try{return window.STATE||(typeof STATE!=='undefined'?STATE:null);}catch(e){return null;}}
  function color(value){var p=['#5b21b6','#0f766e','#b45309','#0369a1','#be123c','#4338ca','#15803d','#a21caf'],h=0;String(value||'').split('').forEach(function(c){h=((h*31)+c.charCodeAt(0))>>>0;});return p[h%p.length];}
  function decorate(){
    scheduled=false;var s=state();if(!s||!Array.isArray(s.members))return;
    var map={};s.members.forEach(function(m){map[String(m.id)]=m;});
    document.querySelectorAll('[data-member-id]').forEach(function(card){
      var member=map[String(card.getAttribute('data-member-id')||'')];if(!member)return;
      var host=card.querySelector('.name,.member-name,.quick-member-name')||card;
      var wrap=card.querySelector('.jm-member-badges');if(!wrap){wrap=document.createElement('span');wrap.className='jm-member-badges';host.insertAdjacentElement('afterend',wrap);}
      var team=String(member.teamLabel||'').trim();
      var next=team?'<span class="jm-member-badge jm-team-badge" style="--jm-team-color:'+color(team)+'">'+team.replace(/[&<>]/g,function(x){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[x];})+'</span>':'';
      if(wrap.innerHTML!==next)wrap.innerHTML=next;
      wrap.hidden=!wrap.innerHTML;
    });
  }
  function schedule(){if(scheduled)return;scheduled=true;requestAnimationFrame(decorate);}
  new MutationObserver(schedule).observe(document.documentElement,{childList:true,subtree:true});
  document.addEventListener('DOMContentLoaded',schedule,{once:true});
  document.addEventListener('click',function(){setTimeout(schedule,80);},true);
  setInterval(schedule,1800);schedule();
})();
</script>
'''

SELF_PROFILE_ADDON = r'''
<style id="jayuminton-member-self-profile-edit-v1">
.jm-self-edit{display:inline-flex;margin-left:5px;padding:3px 7px;border-radius:8px;background:#315efb;color:#fff;font-size:10px;font-weight:900;cursor:pointer;vertical-align:middle}.jm-public-memo{display:block;margin-top:4px;font-size:11px;font-weight:750;color:#475569;white-space:normal;word-break:break-word}
#jmSelfProfileModal{position:fixed;z-index:2147483646;inset:0;display:flex;align-items:center;justify-content:center;padding:14px;background:rgba(15,23,42,.58)}#jmSelfProfileModal.hidden{display:none!important}.jm-self-profile-card{width:min(92vw,440px);padding:17px;border-radius:16px;background:#fff;box-shadow:0 20px 60px rgba(0,0,0,.4)}.jm-self-profile-card h2{margin:0 0 10px}.jm-self-profile-card input,.jm-self-profile-card textarea{width:100%;box-sizing:border-box;margin-top:8px}.jm-self-profile-card textarea{min-height:92px;resize:vertical}.jm-self-profile-help{margin:7px 0;font-size:11px;color:#64748b}.jm-self-profile-actions{display:flex;justify-content:flex-end;gap:7px;margin-top:10px}.jm-self-profile-actions button{min-height:40px;padding:8px 14px;font-weight:900}.jm-self-profile-save{background:#315efb!important;color:#fff!important;border-color:#315efb!important}
</style>
<div id="jmSelfProfileModal" class="hidden" role="dialog" aria-modal="true" aria-labelledby="jmSelfProfileTitle"><div class="jm-self-profile-card"><h2 id="jmSelfProfileTitle">내 카드 메모 수정</h2><textarea id="jmSelfProfileMemo" maxlength="120" placeholder="카드에 표시할 메모 (선택)"></textarea><p class="jm-self-profile-help">이름·닉네임·구력·급수·성별·신규·팀 설정은 관리자만 수정할 수 있습니다.</p><div class="jm-self-profile-actions"><button type="button" onclick="closeJmSelfProfile()">취소</button><button class="jm-self-profile-save" type="button" onclick="saveJmSelfProfile()">저장</button></div></div></div>
<script>
/* JAYUMINTON_MEMBER_SELF_PROFILE_EDIT_V1 */
(function installMemberSelfProfileEditV1(){
  if(window.__JAYUMINTON_MEMBER_SELF_PROFILE_EDIT_V1__)return;window.__JAYUMINTON_MEMBER_SELF_PROFILE_EDIT_V1__=true;var scheduled=false;
  function me(){try{return typeof selectedWebPushMember==='function'?selectedWebPushMember():null;}catch(e){return null;}}
  function state(){try{return window.STATE||(typeof STATE!=='undefined'?STATE:null);}catch(e){return null;}}
  function current(){var selected=me(),s=state();if(!selected||!s||!Array.isArray(s.members))return null;return s.members.find(function(m){return String(m.id)===String(selected.id);})||selected;}
  window.openJmSelfProfile=function(event){if(event){event.preventDefault();event.stopPropagation();}var member=current();if(!member)return;var memo=document.getElementById('jmSelfProfileMemo'),modal=document.getElementById('jmSelfProfileModal');if(memo)memo.value=String(member.publicMemo||'');if(modal)modal.classList.remove('hidden');setTimeout(function(){if(memo)memo.focus();},50);};
  window.closeJmSelfProfile=function(){var modal=document.getElementById('jmSelfProfileModal');if(modal)modal.classList.add('hidden');};
  window.saveJmSelfProfile=async function(){var member=current(),memo=String(document.getElementById('jmSelfProfileMemo')&&document.getElementById('jmSelfProfileMemo').value||'').trim();if(!member)return;try{await server('updateMyProfile',[String(member.id),memo]);closeJmSelfProfile();if(typeof refreshMemberState==='function')await refreshMemberState();}catch(error){alert(error&&error.message?error.message:error);}};
  function decorate(){scheduled=false;var member=current();if(!member)return;document.querySelectorAll('[data-member-id="'+String(member.id).replace(/"/g,'')+'"]').forEach(function(card){var host=card.querySelector('.name,.member-name,.quick-member-name')||card;if(!card.querySelector('.jm-self-edit')){var edit=document.createElement('span');edit.className='jm-self-edit';edit.textContent='카드 메모 수정';edit.setAttribute('role','button');edit.onclick=openJmSelfProfile;host.insertAdjacentElement('afterend',edit);}var old=card.querySelector('.jm-public-memo'),memo=String(member.publicMemo||'').trim();if(memo&&!old){old=document.createElement('span');old.className='jm-public-memo';card.appendChild(old);}if(old){if(old.textContent!==memo)old.textContent=memo;old.hidden=!memo;}});}
  function schedule(){if(scheduled)return;scheduled=true;requestAnimationFrame(decorate);}new MutationObserver(schedule).observe(document.documentElement,{childList:true,subtree:true});setInterval(schedule,1800);document.addEventListener('DOMContentLoaded',schedule,{once:true});schedule();
})();
</script>
'''

TEAM_ONLY_V2_ADDON = r'''
<style id="jayuminton-member-team-only-badges-v2">
/* JAYUMINTON_MEMBER_TEAM_ONLY_BADGES_V2 */
.jm-status-badge{display:none!important}
</style>
'''

TEAM_CARD_LAYOUT_V3_ADDON = r'''
<style id="jayuminton-member-team-card-layout-v5">
/* JAYUMINTON_MEMBER_TEAM_CARD_LAYOUT_V5 */
#memberApp [data-member-id]{position:relative!important;inset:auto!important;transform:none!important;display:flex!important;flex-direction:column!important;align-items:stretch!important;justify-content:center!important;width:100%!important;min-width:0!important;max-width:100%!important;height:auto!important;min-height:52px!important;max-height:none!important;box-sizing:border-box!important;overflow:hidden!important;contain:paint!important}
#memberApp [data-member-id].jm-has-team{border-color:transparent!important;outline:1px solid var(--jm-team-color,#6d28d9)!important;outline-offset:2px!important;box-shadow:0 0 0 4px rgba(255,255,255,.98),0 0 0 5px var(--jm-team-color,#6d28d9)!important;overflow:visible!important;contain:none!important;background-clip:padding-box!important}
#memberApp [data-member-id].jm-temp-pair{outline:0!important;box-shadow:0 0 0 4px #facc15!important;border:2px solid #facc15!important}
#memberApp [data-member-id].jm-has-team.jm-temp-pair{outline:1px solid var(--jm-team-color,#6d28d9)!important;outline-offset:3px!important;box-shadow:0 0 0 6px #facc15!important;border:2px solid #facc15!important}
#memberApp [data-member-id]>.name,#memberApp [data-member-id]>.member-name,#memberApp [data-member-id]>.quick-member-name,#memberApp [data-member-id]>.member-info-detail,#memberApp [data-member-id]>.member-public-memo,#memberApp [data-member-id]>.jm-public-memo,#memberApp [data-member-id]>.member-status-list{position:static!important;inset:auto!important;transform:none!important;display:block!important;flex:0 0 auto!important;width:100%!important;min-width:0!important;max-width:100%!important;height:auto!important;max-height:none!important;box-sizing:border-box!important;margin-left:0!important;margin-right:0!important;text-align:center!important;white-space:normal!important;overflow:hidden!important;text-overflow:clip!important;overflow-wrap:anywhere!important;word-break:keep-all!important}
#memberApp [data-member-id]>.member-self-star{top:2px!important;right:2px!important}
#memberApp [data-member-id]>.jm-member-badges{position:static!important;inset:auto!important;transform:none!important;display:flex!important;align-items:center!important;justify-content:center!important;flex:0 0 auto!important;width:100%!important;min-width:0!important;max-width:100%!important;height:auto!important;box-sizing:border-box!important;margin:2px 0 0!important;padding:0!important;overflow:hidden!important}
#memberApp [data-member-id]>.jm-member-badges .jm-team-badge{position:static!important;inset:auto!important;transform:none!important;display:inline-flex!important;width:auto!important;max-width:100%!important;height:auto!important;min-height:0!important;box-sizing:border-box!important;margin:0!important;padding:1px 3px!important;border-radius:4px!important;font-size:6px!important;line-height:1.1!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important}
.jm-self-edit{display:none!important}
#jmSelfCardAction{position:fixed;z-index:2147483647;left:50%;bottom:calc(env(safe-area-inset-bottom,0px) + 18px);transform:translateX(-50%);width:min(90vw,360px);padding:10px;border-radius:14px;background:#fff;box-shadow:0 18px 55px rgba(15,23,42,.35)}
#jmSelfCardAction.hidden{display:none!important}#jmSelfCardAction button{width:100%;min-height:44px;border:0;border-radius:10px;background:#315efb;color:#fff;font-weight:900}#jmSelfCardAction .jm-close{margin-top:6px;background:#e2e8f0;color:#334155}
</style>
<div id="jmSelfCardAction" class="hidden"><button type="button" onclick="openJmSelfProfile(event);closeJmSelfCardAction()">카드 내용 수정</button><button class="jm-close" type="button" onclick="closeJmSelfCardAction()">닫기</button></div>
<script>
(function installMemberTeamCardLayoutV5(){
  function mine(card){try{var me=typeof selectedWebPushMember==='function'?selectedWebPushMember():null;return !!(me&&card&&String(card.getAttribute('data-member-id'))===String(me.id));}catch(e){return false;}}
  function normalize(){document.querySelectorAll('.jm-self-edit').forEach(function(x){x.remove();});document.querySelectorAll('[data-member-id]').forEach(function(card){var wrap=card.querySelector('.jm-member-badges'),team=wrap&&wrap.querySelector('.jm-team-badge'),color=team&&team.style&&team.style.getPropertyValue('--jm-team-color');card.classList.toggle('jm-has-team',!!team);if(color)card.style.setProperty('--jm-team-color',color);else card.style.removeProperty('--jm-team-color');if(wrap&&wrap.parentElement!==card)card.appendChild(wrap);});}
  window.closeJmSelfCardAction=function(){var box=document.getElementById('jmSelfCardAction');if(box)box.classList.add('hidden');};
  var timer=0,startCard=null;document.addEventListener('pointerdown',function(e){var card=e.target&&e.target.closest&&e.target.closest('[data-member-id]');if(!mine(card))return;startCard=card;clearTimeout(timer);timer=setTimeout(function(){if(startCard===card){var box=document.getElementById('jmSelfCardAction');if(box)box.classList.remove('hidden');}},650);},true);['pointerup','pointercancel','pointermove'].forEach(function(type){document.addEventListener(type,function(){clearTimeout(timer);timer=0;startCard=null;},true);});
  var queued=false;function schedule(){if(queued)return;queued=true;requestAnimationFrame(function(){queued=false;normalize();});}
  new MutationObserver(schedule).observe(document.documentElement,{childList:true,subtree:true});document.addEventListener('DOMContentLoaded',schedule,{once:true});setInterval(schedule,1800);schedule();
})();
</script>
'''

SELF_MEMO_ONLY_V2_ADDON = r'''
<script>
/* JAYUMINTON_MEMBER_SELF_MEMO_ONLY_V2 */
(function installMemberSelfMemoOnlyV2(){
  function current(){try{var selected=typeof selectedWebPushMember==='function'?selectedWebPushMember():null,s=window.STATE||(typeof STATE!=='undefined'?STATE:null);return selected&&s&&Array.isArray(s.members)?s.members.find(function(m){return String(m.id)===String(selected.id);})||selected:null;}catch(e){return null;}}
  function normalize(){var modal=document.getElementById('jmSelfProfileModal');if(!modal)return;var name=document.getElementById('jmSelfProfileName');if(name)name.remove();var title=document.getElementById('jmSelfProfileTitle'),titleText='내 카드 메모 수정';if(title&&title.textContent!==titleText)title.textContent=titleText;var help=modal.querySelector('.jm-self-profile-help'),helpText='이름·닉네임·구력·급수·성별·신규·팀 설정은 관리자만 수정할 수 있습니다.';if(help&&help.textContent!==helpText)help.textContent=helpText;document.querySelectorAll('.jm-self-edit').forEach(function(x){if(x.textContent!=='카드 메모 수정')x.textContent='카드 메모 수정';});}
  window.openJmSelfProfile=function(event){if(event){event.preventDefault();event.stopPropagation();}var member=current(),memo=document.getElementById('jmSelfProfileMemo'),modal=document.getElementById('jmSelfProfileModal');if(!member||!modal)return;normalize();if(memo)memo.value=String(member.publicMemo||'');modal.classList.remove('hidden');setTimeout(function(){if(memo)memo.focus();},30);};
  window.saveJmSelfProfile=async function(){var member=current(),memo=String(document.getElementById('jmSelfProfileMemo')&&document.getElementById('jmSelfProfileMemo').value||'').trim();if(!member)return;try{await server('updateMyProfile',[String(member.id),memo]);closeJmSelfProfile();if(typeof refreshMemberState==='function')await refreshMemberState();}catch(error){alert(error&&error.message?error.message:error);}};
  new MutationObserver(normalize).observe(document.documentElement,{childList:true,subtree:true});document.addEventListener('DOMContentLoaded',normalize,{once:true});normalize();
})();
</script>
'''

MEMBER_MESSAGE_ADDON = r'''
<style id="jayuminton-member-direct-message-alert-v1">
#jmDirectMessageAlert{position:fixed;z-index:2147483647;inset:0;display:flex;align-items:flex-start;justify-content:center;padding:calc(env(safe-area-inset-top,0px) + 16px) 14px 14px;background:rgba(15,23,42,.58)}
#jmDirectMessageAlert.hidden{display:none!important}.jm-direct-message-card{width:min(94vw,480px);padding:18px;border-radius:17px;background:#fff;box-shadow:0 20px 65px rgba(0,0,0,.4);text-align:center}
.jm-direct-message-card h2{margin:0 0 10px;font-size:20px}.jm-direct-message-card p{margin:0 0 16px;font-size:16px;font-weight:800;line-height:1.55;white-space:pre-wrap;word-break:break-word}.jm-direct-message-card button{width:100%;min-height:48px;border:0;border-radius:12px;background:#315efb;color:#fff;font-size:16px;font-weight:950}
</style>
<div id="jmDirectMessageAlert" class="hidden" role="alertdialog" aria-modal="true" aria-labelledby="jmDirectMessageTitle">
  <div class="jm-direct-message-card"><h2 id="jmDirectMessageTitle">관리자 메시지</h2><p id="jmDirectMessageBody"></p><button type="button" onclick="confirmJmDirectMessage()">확인</button></div>
</div>
<script>
/* JAYUMINTON_MEMBER_DIRECT_MESSAGE_ALERT_V1 */
(function installMemberDirectMessageAlertV1(){
  if(window.__JAYUMINTON_MEMBER_DIRECT_MESSAGE_ALERT_V1__)return;
  window.__JAYUMINTON_MEMBER_DIRECT_MESSAGE_ALERT_V1__=true;
  var activeId='',vibrationTimer=0,seenKey='jayuminton_seen_direct_messages_v1';
  function selected(){try{return typeof selectedWebPushMember==='function'?selectedWebPushMember():null;}catch(e){return null;}}
  function state(){try{return window.STATE||(typeof STATE!=='undefined'?STATE:null);}catch(e){return null;}}
  function seen(){try{return JSON.parse(localStorage.getItem(seenKey)||'[]');}catch(e){return [];}}
  function remember(id){var list=seen().filter(function(x){return x!==id;});list.push(id);try{localStorage.setItem(seenKey,JSON.stringify(list.slice(-100)));}catch(e){}}
  function pattern(){if(typeof strongThreeByEightPattern==='function')return strongThreeByEightPattern();var p=[];for(var r=0;r<8;r++)for(var n=0;n<3;n++){p.push(360);if(!(r===7&&n===2))p.push(n===2?520:150);}return p;}
  function stop(){if(vibrationTimer)clearInterval(vibrationTimer);vibrationTimer=0;try{if(navigator.vibrate)navigator.vibrate(0);}catch(e){}try{if(window.JayumintonNative&&typeof window.JayumintonNative.stopVibration==='function')window.JayumintonNative.stopVibration();}catch(e){}try{postUnifiedMemberMessage('JAYUMINTON_STOP_MEMBER_ALERT',{});}catch(e){}}
  function vibrate(){try{if(navigator.vibrate)navigator.vibrate(pattern());}catch(e){}try{postUnifiedMemberMessage('JAYUMINTON_MEMBER_MESSAGE_ALERT',{messageId:activeId});}catch(e){}}
  function show(item){activeId=String(item.id||'');var box=document.getElementById('jmDirectMessageAlert'),body=document.getElementById('jmDirectMessageBody');if(body)body.textContent=String(item.text||'');if(box)box.classList.remove('hidden');stop();vibrate();vibrationTimer=setInterval(vibrate,14500);}
  window.confirmJmDirectMessage=function(){if(activeId)remember(activeId);activeId='';stop();var box=document.getElementById('jmDirectMessageAlert');if(box)box.classList.add('hidden');};
  function check(){var me=selected(),s=state();if(!me||!s||!Array.isArray(s.memberMessages)||activeId)return;var done=seen();var next=s.memberMessages.filter(function(item){return item&&done.indexOf(String(item.id||''))<0;}).slice(-1)[0];if(next)show(next);}
  setInterval(check,1200);document.addEventListener('visibilitychange',function(){if(document.hidden)stop();else check();});window.addEventListener('pagehide',stop);setTimeout(check,300);
})();
</script>
'''

IDENTITY_BIND_ADDON = r'''
<style id="jayuminton-member-identity-confirm-v2-style">
#jmMemberIdentityConfirm{position:fixed;z-index:2147483647;inset:0;display:flex;align-items:center;justify-content:center;padding:16px;background:rgba(15,23,42,.58)}
#jmMemberIdentityConfirm.hidden{display:none!important}.jm-identity-confirm-card{width:min(92vw,420px);padding:18px;border-radius:16px;background:#fff;box-shadow:0 20px 60px rgba(0,0,0,.38);text-align:center}.jm-identity-confirm-card p{margin:0 0 16px;font-size:17px;font-weight:900}.jm-identity-confirm-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px}.jm-identity-confirm-actions button{min-height:46px;border:0;border-radius:11px;font-size:15px;font-weight:900}.jm-identity-confirm-cancel{background:#e2e8f0;color:#334155}.jm-identity-confirm-ok{background:#315efb;color:#fff}
</style>
<div id="jmMemberIdentityConfirm" class="hidden" role="dialog" aria-modal="true"><div class="jm-identity-confirm-card"><p id="jmMemberIdentityConfirmText"></p><div class="jm-identity-confirm-actions"><button type="button" class="jm-identity-confirm-cancel">취소</button><button type="button" class="jm-identity-confirm-ok">네, 저예요</button></div></div></div>
<script>
/* JAYUMINTON_MEMBER_IDENTITY_BIND_V2 */
(function installMemberIdentityBindV2(){
  if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;
  if(window.__JAYUMINTON_MEMBER_IDENTITY_BIND_V2__)return;
  window.__JAYUMINTON_MEMBER_IDENTITY_BIND_V2__=true;
  var originalSelect=window.selectMemberSelf,binding=false,boundKey='jayuminton_member_bound_session_v2';
  function find(id){try{return (STATE.members||[]).find(function(m){return m&&String(m.id)===String(id);})||null;}catch(_){return null;}}
  function ask(member){return new Promise(function(resolve){
    var box=document.getElementById('jmMemberIdentityConfirm'),label=document.getElementById('jmMemberIdentityConfirmText');
    if(!box||!label){resolve(confirm(String(member.name||'선택한 회원')+'님이 본인인가요?'));return;}
    label.textContent=String(member.name||'선택한 회원')+'님이 본인인가요?';box.classList.remove('hidden');
    var cancel=box.querySelector('.jm-identity-confirm-cancel'),ok=box.querySelector('.jm-identity-confirm-ok');
    function done(value){box.classList.add('hidden');cancel.onclick=null;ok.onclick=null;resolve(value);}
    cancel.onclick=function(){done(false);};ok.onclick=function(){done(true);};
  });}
  async function bind(member,quiet){
    if(binding||!member||!member.id)return false;
    var token=typeof currentMemberSessionToken==='function'?String(currentMemberSessionToken()||''):'';
    if(!token)return false;
    var signature=String(member.id)+'|'+token;
    try{if(quiet&&localStorage.getItem(boundKey)===signature)return true;}catch(_){}
    binding=true;
    try{
      var result=await server('bindMemberIdentity',[token,String(member.id)]),nextToken=String(result&&result.sessionToken||'');
      if(!nextToken)throw new Error('본인 인증 세션을 만들지 못했습니다.');
      if(typeof storeMemberSessionToken==='function')storeMemberSessionToken(nextToken);
      try{localStorage.setItem(boundKey,String(member.id)+'|'+nextToken);}catch(_){}
      return true;
    }catch(error){if(!quiet)alert(String(error&&error.message||error||'본인 확인에 실패했습니다.'));return false;}
    finally{binding=false;}
  }
  window.selectMemberSelf=async function(memberId,options){
    var member=find(memberId);if(!member)return false;
    if(!(options&&options.skipConfirm===true)&&!(await ask(member)))return false;
    if(!(await bind(member,false)))return false;
    if(typeof originalSelect==='function')originalSelect.call(window,String(member.id));
    if(typeof refreshMemberState==='function')await refreshMemberState();
    return true;
  };
  async function migrate(){var stored=typeof currentStoredWebPushMember==='function'?currentStoredWebPushMember():null,member=stored&&find(stored.id);if(member&&await bind(member,true)&&typeof refreshMemberState==='function')refreshMemberState();}
  setTimeout(migrate,600);setTimeout(migrate,2200);
})();
</script>
'''

REFRESH_STATUS_ADDON = r'''
<script>
/* JAYUMINTON_MEMBER_REFRESH_STATUS_V1 */
(function installMemberRefreshStatusV1(){
  if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;
  if(window.__JAYUMINTON_MEMBER_REFRESH_STATUS_V1__)return;
  window.__JAYUMINTON_MEMBER_REFRESH_STATUS_V1__=true;
  var original=window.refreshMemberState,busy=false;if(typeof original!=='function')return;
  window.refreshMemberState=async function(){
    if(busy)return;busy=true;var button=document.getElementById('memberRefreshButton');
    if(button){button.disabled=true;button.textContent='↻ 동기화 중...';}
    try{var result=await original.apply(this,arguments);if(button)button.textContent='✓ 동기화 완료';setTimeout(function(){if(button)button.textContent='↻ 현황 갱신';},1200);return result;}
    catch(error){if(button)button.textContent='! 동기화 실패';setTimeout(function(){if(button)button.textContent='↻ 현황 갱신';},1800);throw error;}
    finally{if(button)button.disabled=false;busy=false;}
  };
})();
</script>
'''

SELF_INFO_MENU_ADDON = r'''
<script>
/* JAYUMINTON_MEMBER_SELF_INFO_MENU_V1 */
(function installMemberSelfInfoMenuV1(){
  if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;
  if(window.__JAYUMINTON_MEMBER_SELF_INFO_MENU_V1__)return;
  window.__JAYUMINTON_MEMBER_SELF_INFO_MENU_V1__=true;
  function ensure(){
    var menu=document.getElementById('jmMemberSelfStatusMenu');if(!menu||menu.querySelector('[data-action="내 정보 입력"]'))return;
    var cancel=menu.querySelector('[data-action="선택취소"]'),button=document.createElement('button');
    button.type='button';button.setAttribute('data-action','내 정보 입력');button.textContent='내 정보 입력';
    button.style.cssText='width:100%;min-height:52px;border:0;border-top:1px solid #e5e7eb;background:#fff;font-size:16px;font-weight:800;color:#315efb';
    if(cancel&&cancel.parentNode)cancel.parentNode.insertBefore(button,cancel);else{var card=menu.firstElementChild||menu;card.appendChild(button);}
  }
  document.addEventListener('click',function(event){
    var button=event.target.closest&&event.target.closest('[data-action="내 정보 입력"]');if(!button)return;
    event.preventDefault();event.stopImmediatePropagation();
    var menu=document.getElementById('jmMemberSelfStatusMenu');if(menu)menu.remove();
    if(typeof openMemberSelfSettings==='function')openMemberSelfSettings();
    setTimeout(function(){var input=document.getElementById('jmMemberSelfMemoInput');if(input){input.scrollIntoView({block:'center'});input.focus();}},80);
  },true);
  new MutationObserver(ensure).observe(document.documentElement,{childList:true,subtree:true});ensure();
})();
</script>
'''

MEMBER_FLAGS_ADDON = r'''
<style>
/* JAYUMINTON_MEMBER_FLAGS_V1 */
#memberApp [data-member-id] .jm-member-flags{display:flex!important;justify-content:center!important;align-items:center!important;gap:3px!important;flex-wrap:wrap!important;width:100%!important;margin:2px 0 0!important;pointer-events:none!important}
#memberApp [data-member-id] .jm-member-flag{display:inline-flex!important;align-items:center!important;justify-content:center!important;min-height:15px!important;padding:1px 5px!important;border-radius:999px!important;font-size:8px!important;font-weight:950!important;line-height:1.15!important;white-space:nowrap!important;box-sizing:border-box!important}
#memberApp [data-member-id] .jm-member-flag-new{background:#fff1f2!important;color:#be123c!important;border:1px solid #fda4af!important}
#memberApp [data-member-id] .jm-member-flag-sponsor{background:#fff7ed!important;color:#c2410c!important;border:1px solid #fdba74!important}
</style>
<script>
(function installMemberFlagsV1(){
  if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;if(window.__JAYUMINTON_MEMBER_FLAGS_V1__)return;window.__JAYUMINTON_MEMBER_FLAGS_V1__=true;
  var queued=false;
  function sync(){
    queued=false;var state=null;try{state=window.STATE||(typeof STATE!=='undefined'?STATE:null);}catch(error){}if(!state||!Array.isArray(state.members))return;
    var members={};state.members.forEach(function(member){if(member&&member.id!=null)members[String(member.id)]=member;});
    document.querySelectorAll('#memberApp [data-member-id]').forEach(function(card){
      var member=members[String(card.getAttribute('data-member-id')||'')];if(!member)return;
      var name=card.querySelector('.name');if(name&&member.isNew===true)name.textContent=String(member.name||'');
      var html='';if(member.isNew===true)html+='<span class="jm-member-flag jm-member-flag-new">NEW 신규</span>';if(member.isSponsor===true)html+='<span class="jm-member-flag jm-member-flag-sponsor">🎁 찬조</span>';
      var flags=card.querySelector(':scope > .jm-member-flags');if(!html){if(flags)flags.remove();return;}if(!flags){flags=document.createElement('span');flags.className='jm-member-flags';card.appendChild(flags);}if(flags.innerHTML!==html)flags.innerHTML=html;
    });
  }
  function schedule(){if(queued)return;queued=true;requestAnimationFrame(sync);}
  new MutationObserver(schedule).observe(document.getElementById('memberApp')||document.documentElement,{childList:true,subtree:true});
  document.addEventListener('DOMContentLoaded',schedule,{once:true});setInterval(schedule,1200);schedule();
})();
</script>
'''

MEMO_DEDUPE_ADDON = r'''
<style>
/* JAYUMINTON_MEMBER_MEMO_DEDUPE_V1
   The canonical card renderer already outputs .member-public-memo.
   Suppress and remove the legacy self-profile decorator's duplicate copy. */
#memberApp [data-member-id]>.jm-public-memo{display:none!important}
</style>
<script>
(function installMemberMemoDedupeV1(){
  if(window.__JAYUMINTON_MEMBER_MEMO_DEDUPE_V1__)return;window.__JAYUMINTON_MEMBER_MEMO_DEDUPE_V1__=true;
  var queued=false;
  function clean(){queued=false;document.querySelectorAll('#memberApp [data-member-id]>.jm-public-memo').forEach(function(node){node.remove();});}
  function schedule(){if(queued)return;queued=true;requestAnimationFrame(clean);}
  new MutationObserver(schedule).observe(document.getElementById('memberApp')||document.documentElement,{childList:true,subtree:true});
  document.addEventListener('DOMContentLoaded',schedule,{once:true});schedule();
})();
</script>
'''

COMPLETION_ADDON = r'''
<style>
/* JAYUMINTON_MEMBER_REQUIREMENTS_COMPLETION_V1 */
#memberApp [data-member-id].is-self-member{border:2px solid #facc15!important;outline:2px solid #facc15!important;outline-offset:2px!important;box-shadow:0 0 0 4px rgba(255,255,255,.98),0 0 0 6px #facc15!important;overflow:visible!important}
#memberApp [data-member-id].is-self-member>.member-self-star{position:absolute!important;top:2px!important;right:2px!important;left:auto!important;width:auto!important;min-width:22px!important;height:15px!important;min-height:15px!important;padding:0 3px!important;border:1px solid #fff!important;border-radius:999px!important;background:#111827!important;color:#fff!important;font-size:7px!important;font-weight:950!important;line-height:13px!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;white-space:nowrap!important;z-index:30!important;box-shadow:0 1px 3px rgba(15,23,42,.35)!important}
#memberApp [data-member-id]>.member-public-memo{color:#d946ef!important;font-size:10px!important;font-weight:900!important;text-shadow:0 0 8px rgba(217,70,239,.18)!important}
#jmMemberSelfMemoInput{font-size:11px!important;line-height:1.35!important;color:#d946ef!important;font-weight:850!important}
</style>
<script>
(function installMemberRequirementsCompletionV1(){
  if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;if(window.__JAYUMINTON_MEMBER_REQUIREMENTS_COMPLETION_V1__)return;window.__JAYUMINTON_MEMBER_REQUIREMENTS_COMPLETION_V1__=true;
  var queued=false;
  function current(){try{var selected=typeof currentStoredWebPushMember==='function'?currentStoredWebPushMember():null,state=window.STATE||(typeof STATE!=='undefined'?STATE:null);return selected&&state&&Array.isArray(state.members)?state.members.find(function(member){return member&&String(member.id)===String(selected.id);})||null:null;}catch(error){return null;}}
  function sync(){
    queued=false;var member=current(),hasMemo=!!String(member&&member.publicMemo||'').trim();
    document.querySelectorAll('#jmMemberSelfStatusMenu [data-action="내 정보 입력"]').forEach(function(button){button.textContent=hasMemo?'내 정보 수정':'내 정보 입력';});
    var save=document.getElementById('jmMemberSelfMemoSaveBtn');if(save&&!save.disabled)save.textContent=hasMemo?'메모 수정':'메모 저장';
    var input=document.getElementById('jmMemberSelfMemoInput');if(input)input.placeholder='간단한 내 메모 (예: C조, 구력4년, 생일)';
  }
  function schedule(){if(queued)return;queued=true;requestAnimationFrame(sync);}
  new MutationObserver(schedule).observe(document.documentElement,{childList:true,subtree:true});document.addEventListener('DOMContentLoaded',schedule,{once:true});setInterval(schedule,1200);schedule();

  window.detectMemberForegroundTransition=function(previousState,nextState){
    if(IS_ADMIN||!previousState||!nextState)return;normalizeStateMemberProfiles(previousState);normalizeStateMemberProfiles(nextState);
    var member=selectedWebPushMember();if(!member)return;var before=memberLocation(previousState,member.id),after=memberLocation(nextState,member.id),updatedAt=String(nextState.updatedAt||Date.now());
    function names(state){var ids=state&&Array.isArray(state.waitGroups)&&Array.isArray(state.waitGroups[0])?state.waitGroups[0].slice(0,4):[];return ids.map(function(id){var item=(state.members||[]).find(function(candidate){return candidate&&String(candidate.id)===String(id);});return item?String(item.name||''):'';}).filter(Boolean);}
    if(before.type==='wait'&&before.index===1&&after.type==='wait'&&after.index===0){var ready=names(nextState);showMemberForegroundAlert('대기 1순위 안내','대기1순위 입니다. 라켓 들고 준비해주세요.'+(ready.length?' 대기1: '+ready.join(', ')+'님':''),'wait1_'+member.id+'_'+updatedAt,'wait1_ready');}
    if(before.type==='wait'&&before.index===0&&after.type==='court'){var courtNo=Number(after.index),roster=names(previousState);showMemberForegroundAlert('코트 배정 안내',courtNo+'번 코트 나왔습니다.'+(roster.length?' 대기1: '+roster.join(', ')+'님':'')+' '+courtNo+'번 코트로 들어가주세요.','court_'+courtNo+'_'+member.id+'_'+updatedAt,'court_assignment');}
  };
})();
</script>
'''


def assert_alert_contract(text: str) -> None:
    required = [
        MARKER,
        "function strongThreeByEightPattern()",
        "for (var round = 0; round < 8; round += 1)",
        "for (var pulse = 0; pulse < 3; pulse += 1)",
        "'wait1_ready'",
        "'court_assignment'",
        "window.memberAlertRepeatCount = function(){ return 1; };",
    ]
    for needle in required:
        if needle not in text:
            raise SystemExit(f"member alert 3x8 contract missing: {needle}")


def assert_native_sync_contract(text: str) -> None:
    required = [
        NATIVE_SYNC_MARKER,
        "window.syncNativeUserPushBridge = function()",
        "window.NativeUserApp.setMember(memberId, memberName)",
        "window.NativeUserApp.clearMember()",
        "window.NativeUserApp.setPushEnabled",
        "window.NativeUserApp.setVibrationEnabled",
        "typeof selectedWebPushMember === 'function'",
    ]
    for needle in required:
        if needle not in text:
            raise SystemExit(f"native identity sync contract missing: {needle}")


def assert_auto_sync_contract(text: str) -> None:
    required = [
        AUTO_SYNC_MARKER,
        "setInterval(pollRevision, 1800)",
        "server('getPublicState', [])",
        "refreshMemberState()",
        "Number(next.revision)",
    ]
    for needle in required:
        if needle not in text:
            raise SystemExit(f"member revision autosync contract missing: {needle}")


def assert_team_status_contract(text: str) -> None:
    for needle in [TEAM_STATUS_MARKER, TEAM_CARD_LAYOUT_V3_MARKER, "member.teamLabel", "jm-team-badge", "jm-has-team", "outline-offset:2px", "0 0 0 5px var(--jm-team-color"]:
        if needle not in text:
            raise SystemExit(f"member team/status contract missing: {needle}")
    if "box-shadow:inset 4px 0 0 var(--jm-team-color)" in text:
        raise SystemExit("member team/status left stripe survived")


def assert_member_message_contract(text: str) -> None:
    for needle in [MEMBER_MESSAGE_MARKER, "window.confirmJmDirectMessage=function()", "vibrationTimer=setInterval(vibrate,14500)", "JAYUMINTON_MEMBER_MESSAGE_ALERT", "navigator.vibrate(0)"]:
        if needle not in text:
            raise SystemExit(f"member direct-message contract missing: {needle}")


def assert_self_profile_contract(text: str) -> None:
    for needle in [SELF_PROFILE_MARKER, SELF_MEMO_ONLY_V2_MARKER, "server('updateMyProfile'", "카드에 표시할 메모", "이름·닉네임·구력·급수·성별·신규·팀 설정은 관리자만 수정"]:
        if needle not in text:
            raise SystemExit(f"member self-profile contract missing: {needle}")


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "releases/jayuminton-courtstatus-v1.3.4-cloudflare-complete.apk",
        "releases/jayuminton-courtstatus-v1.6.42-md-final.apk",
    )
    text = text.replace(
        "#memberApp [data-member-id].jm-has-team{box-shadow:inset 4px 0 0 var(--jm-team-color)!important}",
        "#memberApp [data-member-id].jm-has-team{border-color:transparent!important;outline:1px solid var(--jm-team-color,#6d28d9)!important;outline-offset:2px!important;box-shadow:0 0 0 4px rgba(255,255,255,.98),0 0 0 5px var(--jm-team-color,#6d28d9)!important;overflow:visible!important;contain:none!important;background-clip:padding-box!important}",
    )
    permanent_team_css = "#memberApp [data-member-id].jm-has-team{border-color:transparent!important;outline:1px solid var(--jm-team-color,#6d28d9)!important;outline-offset:2px!important;box-shadow:0 0 0 4px rgba(255,255,255,.98),0 0 0 5px var(--jm-team-color,#6d28d9)!important;overflow:visible!important;contain:none!important;background-clip:padding-box!important}"
    temporary_team_css = "\n#memberApp [data-member-id].jm-temp-pair{outline:0!important;box-shadow:0 0 0 4px #facc15!important;border:2px solid #facc15!important}\n#memberApp [data-member-id].jm-has-team.jm-temp-pair{outline:1px solid var(--jm-team-color,#6d28d9)!important;outline-offset:3px!important;box-shadow:0 0 0 6px #facc15!important;border:2px solid #facc15!important}"
    if "#memberApp [data-member-id].jm-temp-pair{outline:0!important" not in text and permanent_team_css in text:
        text = text.replace(permanent_team_css, permanent_team_css + temporary_team_css, 1)
    apk_url = (
        "https://github.com/pianopp001-cpu/jayuminton-admin-app/raw/refs/heads/main/"
        "releases/jayuminton-courtstatus-v1.6.42-md-final.apk"
    )
    text = text.replace(
        "https://github.com/pianopp001-cpu/jayuminton-admin-app/raw/refs/heads/main/"
        "releases/jayuminton-user-v1.0.0.apk",
        apk_url,
    )
    marker = "</body>"
    if marker not in text:
        raise SystemExit("member page closing body tag missing")

    if MARKER not in text:
        required = [
            "function initialize()",
            "function refreshMemberState()",
            "function memberAnywhereStartOutgoingSync_",
            "function detectMemberForegroundTransition",
            "memberAnywhereCancelOutgoingServer_",
            "↻ 현황 갱신",
            "네, 저예요",
        ]
        for needle in required:
            if needle not in text:
                raise SystemExit(f"protected live member feature missing: {needle}")
        text = text.replace(marker, ADDON + "\n" + marker, 1)

    if NATIVE_SYNC_MARKER not in text:
        text = text.replace(marker, NATIVE_SYNC_ADDON + "\n" + marker, 1)
    if AUTO_SYNC_MARKER not in text:
        text = text.replace(marker, AUTO_SYNC_ADDON + "\n" + marker, 1)
    if TEAM_STATUS_MARKER not in text:
        text = text.replace(marker, TEAM_STATUS_ADDON + "\n" + marker, 1)
    if MEMBER_MESSAGE_MARKER not in text:
        text = text.replace(marker, MEMBER_MESSAGE_ADDON + "\n" + marker, 1)
    if SELF_PROFILE_MARKER not in text:
        text = text.replace(marker, SELF_PROFILE_ADDON + "\n" + marker, 1)
    if TEAM_ONLY_V2_MARKER not in text:
        text = text.replace(marker, TEAM_ONLY_V2_ADDON + "\n" + marker, 1)
    if SELF_MEMO_ONLY_V2_MARKER not in text:
        text = text.replace(marker, SELF_MEMO_ONLY_V2_ADDON + "\n" + marker, 1)
    if TEAM_CARD_LAYOUT_V3_MARKER not in text:
        text = text.replace(marker, TEAM_CARD_LAYOUT_V3_ADDON + "\n" + marker, 1)
    if IDENTITY_BIND_MARKER not in text:
        text = text.replace(marker, IDENTITY_BIND_ADDON + "\n" + marker, 1)
    if REFRESH_STATUS_MARKER not in text:
        text = text.replace(marker, REFRESH_STATUS_ADDON + "\n" + marker, 1)
    if SELF_INFO_MENU_MARKER not in text:
        text = text.replace(marker, SELF_INFO_MENU_ADDON + "\n" + marker, 1)
    if MEMBER_FLAGS_MARKER not in text:
        text = text.replace(marker, MEMBER_FLAGS_ADDON + "\n" + marker, 1)
    if MEMO_DEDUPE_MARKER not in text:
        text = text.replace(marker, MEMO_DEDUPE_ADDON + "\n" + marker, 1)
    if COMPLETION_MARKER not in text:
        text = text.replace(marker, COMPLETION_ADDON + "\n" + marker, 1)

    assert_alert_contract(text)
    assert_native_sync_contract(text)
    assert_auto_sync_contract(text)
    assert_team_status_contract(text)
    assert_member_message_contract(text)
    assert_self_profile_contract(text)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_member_user_requirements_v1.py INDEX_HTML")
    patch(Path(sys.argv[1]))
