#!/usr/bin/env python3
"""Patch the live Cloudflare member page without rebuilding its protected UI."""

from pathlib import Path
import sys


MARKER = "JAYUMINTON_MEMBER_USER_REQUIREMENTS_V1"
NATIVE_SYNC_MARKER = "JAYUMINTON_MEMBER_NATIVE_IDENTITY_SYNC_V2"
AUTO_SYNC_MARKER = "JAYUMINTON_MEMBER_REVISION_AUTOSYNC_V1"
TEAM_STATUS_MARKER = "JAYUMINTON_MEMBER_TEAM_STATUS_BADGES_V1"

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
.jm-status-badge{border:1px solid #64748b;color:#334155}
</style>
<script>
/* JAYUMINTON_MEMBER_TEAM_STATUS_BADGES_V1 */
(function installMemberTeamStatusBadgesV1(){
  if(window.__JAYUMINTON_MEMBER_TEAM_STATUS_BADGES_V1__)return;
  window.__JAYUMINTON_MEMBER_TEAM_STATUS_BADGES_V1__=true;
  var scheduled=false;
  function state(){try{return window.STATE||(typeof STATE!=='undefined'?STATE:null);}catch(e){return null;}}
  function color(value){var p=['#5b21b6','#0f766e','#b45309','#0369a1','#be123c','#4338ca','#15803d','#a21caf'],h=0;String(value||'').split('').forEach(function(c){h=((h*31)+c.charCodeAt(0))>>>0;});return p[h%p.length];}
  function statusText(value){return {active:'코트배정대기',before:'도착전',rest:'휴식',away:'귀가',waiting:'대기',playing:'경기중'}[String(value||'')]||'';}
  function decorate(){
    scheduled=false;var s=state();if(!s||!Array.isArray(s.members))return;
    var map={};s.members.forEach(function(m){map[String(m.id)]=m;});
    document.querySelectorAll('[data-member-id]').forEach(function(card){
      var member=map[String(card.getAttribute('data-member-id')||'')];if(!member)return;
      var host=card.querySelector('.name,.member-name,.quick-member-name')||card;
      var wrap=card.querySelector('.jm-member-badges');if(!wrap){wrap=document.createElement('span');wrap.className='jm-member-badges';host.insertAdjacentElement('afterend',wrap);}
      var team=String(member.teamLabel||'').trim(),status=statusText(member.status);
      var next=(team?'<span class="jm-member-badge jm-team-badge" style="--jm-team-color:'+color(team)+'">'+team.replace(/[&<>]/g,function(x){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[x];})+'</span>':'')+(status?'<span class="jm-member-badge jm-status-badge">'+status+'</span>':'');
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
    for needle in [TEAM_STATUS_MARKER, "member.teamLabel", "active:'코트배정대기'", "jm-team-badge", "jm-status-badge"]:
        if needle not in text:
            raise SystemExit(f"member team/status contract missing: {needle}")


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    apk_url = (
        "https://github.com/pianopp001-cpu/jayuminton-admin-app/raw/refs/heads/main/"
        "releases/jayuminton-courtstatus-v1.3.4-cloudflare-complete.apk"
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

    assert_alert_contract(text)
    assert_native_sync_contract(text)
    assert_auto_sync_contract(text)
    assert_team_status_contract(text)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_member_user_requirements_v1.py INDEX_HTML")
    patch(Path(sys.argv[1]))
