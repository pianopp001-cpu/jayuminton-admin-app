#!/usr/bin/env python3
"""Patch the live Cloudflare member page without rebuilding its protected UI."""

from pathlib import Path
import sys


MARKER = "JAYUMINTON_MEMBER_USER_REQUIREMENTS_V1"

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
        courtNo + '번 코트 나왔습니다.' + callout + ' 라켓 들고 이동해주세요.',
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
    if MARKER in text:
        path.write_text(text, encoding="utf-8")
        return
    marker = "</body>"
    if marker not in text:
        raise SystemExit("member page closing body tag missing")
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
    path.write_text(text.replace(marker, ADDON + "\n" + marker, 1), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_member_user_requirements_v1.py INDEX_HTML")
    patch(Path(sys.argv[1]))
