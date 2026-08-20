#!/usr/bin/env python3
"""Final post-contract hardening for admin Cloudflare HTML."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
html = path.read_text(encoding='utf-8')
marker = '</body>'
if marker not in html:
    raise SystemExit('body end marker missing')

legacy_finish = "function finishText(courtNo,members){var calls=(members||[]).map(cleanName).filter(Boolean).map(function(n){return n+'님';});var base=Number(courtNo)+'번 코트 경기가 종료되었습니다.';return calls.length?base+'\\n대기 1번 '+calls.join(', ')+'\\n'+Number(courtNo)+'번 코트로 들어가 주세요.':base+'\\n대기 1번에 입장할 인원이 없습니다.';}"
previous_finish = "function finishText(courtNo,members){var calls=(members||[]).map(cleanName).filter(Boolean).map(function(n){return n+' 님';});var base=Number(courtNo)+'번 코트 나왔습니다.';return calls.length?base+'\\n'+calls.join(', ')+'\\n'+Number(courtNo)+'번 코트로 들어가세요.':base+'\\n입장할 대기 1번 인원이 없습니다.';}"
full_finish = "function finishText(courtNo,members){var calls=(members||[]).map(cleanName).filter(Boolean).map(function(n){return n+' 님';});var base=Number(courtNo)+'번 코트 나왔습니다.';return calls.length?base+'\\n'+calls.join(', ')+'\\n'+Number(courtNo)+'번 코트로 입장해 주세요.':base+'\\n입장할 대기 1번 인원이 없습니다.';}"
if legacy_finish in html:
    html = html.replace(legacy_finish, full_finish, 1)
elif previous_finish in html:
    html = html.replace(previous_finish, full_finish, 1)
elif full_finish not in html:
    raise SystemExit('admin finishText anchor missing')
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
    fullCourtVoiceSet:true,
    voiceRate:.82
  };
  window.__JAYUMINTON_TRANSITION_ALERT__=function(){ return; };
})();
</script>
'''
if 'jayuminton-admin-post-contract-v20' not in html:
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
    'fullCourtVoiceSet:true',
    "번 코트 나왔습니다.",
    "return n+' 님'",
    "번 코트로 입장해 주세요.",
    'text,.82,1',
    'heldUtterance.rate=.82',
    'max-height:none!important',
    'overflow:visible!important'
):
    if required not in html:
        raise SystemExit('post-contract marker missing: '+required)
path.write_text(html, encoding='utf-8')
print('ADMIN_POST_CONTRACT_V20_OK')