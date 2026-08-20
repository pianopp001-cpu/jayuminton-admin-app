#!/usr/bin/env python3
"""Final post-contract hardening for admin Cloudflare HTML.

Also enforces the final alert-role split:
- member devices own wait1/court popup+vibration
- admin does not replay transition popup/vibration
- admin only speaks the court call, with softer Korean TTS phrasing
"""
from pathlib import Path
import sys

path = Path(sys.argv[1])
html = path.read_text(encoding='utf-8')
marker = '</body>'
if marker not in html:
    raise SystemExit('body end marker missing')

old_finish = "function finishText(courtNo,members){var calls=(members||[]).map(cleanName).filter(Boolean).map(function(n){return n+'님';});var base=Number(courtNo)+'번 코트 경기가 종료되었습니다.';return calls.length?base+'\\n대기 1번 '+calls.join(', ')+'\\n'+Number(courtNo)+'번 코트로 들어가 주세요.':base+'\\n대기 1번에 입장할 인원이 없습니다.';}"
new_finish = "function finishText(courtNo,members){var calls=(members||[]).map(cleanName).filter(Boolean).map(function(n){return n+' 님';});var base=Number(courtNo)+'번 코트 나왔습니다.';return calls.length?base+'\\n'+calls.join(', '):base+'\\n입장할 대기 1번 인원이 없습니다.';}"
if old_finish not in html:
    raise SystemExit('admin finishText anchor missing')
html = html.replace(old_finish, new_finish, 1)
html = html.replace("window.NativeVoice.speak('court_finish_'+Date.now(),text,.88,1,'')", "window.NativeVoice.speak('court_finish_'+Date.now(),text,.82,1,'')", 1)
html = html.replace('heldUtterance.rate=.88', 'heldUtterance.rate=.82', 1)

addon = r'''
<style id="jayuminton-admin-post-contract-v20">
#pairStatisticsModal .pair-statistics-modal{overflow-y:auto!important;padding-bottom:max(32px,env(safe-area-inset-bottom))!important}
#pairStatisticsModal .pair-statistics-list{max-height:none!important;height:auto!important;overflow:visible!important;padding-bottom:max(56px,calc(env(safe-area-inset-bottom) + 40px))!important}
#pairStatisticsModal .pair-statistics-row{height:auto!important;max-height:none!important;overflow:visible!important}
#pairStatisticsModal .pair-statistics-row:last-child{margin-bottom:32px!important;padding-bottom:16px!important}
#pairStatisticsModal .pair-statistics-partners{height:auto!important;max-height:none!important;overflow:visible!important;white-space:normal!important}
</style>
<script id="jayuminton-admin-alert-role-v20">
(function(){
  window.__JAYUMINTON_ADMIN_POST_CONTRACT_V19__=true;
  window.__JAYUMINTON_ADMIN_STATISTICS_NO_CLIP_FINAL__=true;
  window.__JAYUMINTON_ADMIN_ALERT_ROLE_V20__={
    memberWaitAlert:'member-device-only',
    memberCourtAlert:'member-device-only',
    adminWaitVoice:false,
    adminTransitionVibration:false,
    adminCourtVoice:true,
    voiceRepeatCount:3,
    voiceRate:.82
  };
  // Persistent transition events still exist for member push delivery, but the
  // administrator phone must not mirror those user notifications.
  window.__JAYUMINTON_TRANSITION_ALERT__=function(){ return; };
})();
</script>
'''
html = html.replace(marker, addon + '\n' + marker, 1)
for required in (
    'jayuminton-admin-post-contract-v20',
    '__JAYUMINTON_ADMIN_STATISTICS_NO_CLIP_FINAL__',
    '__JAYUMINTON_ADMIN_ALERT_ROLE_V20__',
    "memberWaitAlert:'member-device-only'",
    "memberCourtAlert:'member-device-only'",
    'adminWaitVoice:false',
    'adminTransitionVibration:false',
    'adminCourtVoice:true',
    "번 코트 나왔습니다.",
    "return n+' 님'",
    'text,.82,1',
    'heldUtterance.rate=.82',
    'max-height:none!important',
    'overflow:visible!important'
):
    if required not in html:
        raise SystemExit('post-contract marker missing: '+required)
path.write_text(html, encoding='utf-8')
print('ADMIN_POST_CONTRACT_V20_OK')
