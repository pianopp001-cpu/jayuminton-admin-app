#!/usr/bin/env python3
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text(encoding='utf-8')
marker='</body>'
if marker not in s: raise SystemExit('body marker missing')
patch=r'''<style id="jayuminton-admin-statistics-no-clip-v1">
#pairStatisticsModal .pair-statistics-modal{max-height:calc(100dvh - 16px)!important;overflow-y:auto!important;overscroll-behavior:contain!important;padding-bottom:max(28px,env(safe-area-inset-bottom))!important}
#pairStatisticsModal .pair-statistics-list{max-height:none!important;height:auto!important;overflow:visible!important;padding-bottom:max(48px,calc(env(safe-area-inset-bottom) + 32px))!important;align-content:start!important}
#pairStatisticsModal .pair-statistics-row:last-child{margin-bottom:24px!important}
#pairStatisticsModal .pair-statistics-partners{height:auto!important;max-height:none!important;overflow:visible!important;white-space:normal!important}
</style>
<!-- jayuminton-admin-finish-alert-v16 compatibility marker; behavior is v17 -->
<script id="jayuminton-admin-finish-alert-v17">
(function(){
  var heldUtterance=null;
  function waitingOneMembers(){var ids=(STATE&&STATE.waitGroups&&STATE.waitGroups[0]||[]).slice();return ids.map(function(id){return memberById(id);}).filter(Boolean);}
  function cleanName(m){return String(m&&m.name||m&&m.fullName||'').trim().replace(/[()（）]/g,' ').replace(/\s+/g,' ');}
  function finishText(courtNo,members){var calls=(members||[]).map(cleanName).filter(Boolean).map(function(n){return n+'님';});var base=Number(courtNo)+'번 코트 경기가 종료되었습니다.';return calls.length?base+' 대기 1번, '+calls.join(', ')+', '+Number(courtNo)+'번 코트로 들어가 주세요.':base+' 대기 1번에 입장할 인원이 없습니다.';}
  function stopAlertVibration(){try{if(window.NativeVoice&&typeof window.NativeVoice.cancelVibration==='function')window.NativeVoice.cancelVibration();else if(navigator.vibrate)navigator.vibrate(0);}catch(e){}}
  function startAlertVibration(){try{if(window.NativeVoice&&typeof window.NativeVoice.vibrate==='function')window.NativeVoice.vibrate();else if(navigator.vibrate){var p=[0];for(var set=0;set<8;set++){for(var i=0;i<3;i++)p.push(320,180);p.push(650);}navigator.vibrate(p);}}catch(e){}}
  function alertAndStop(message){alert(message);stopAlertVibration();}
  function directSpeak(text){var result={ok:false,reason:'',engine:''};text=String(text||'').trim();try{if(window.NativeVoice&&typeof window.NativeVoice.speak==='function'){window.NativeVoice.speak('court_finish_'+Date.now(),text,.88,1,'');result.ok=true;result.engine='NativeVoice';return result;}if(window.speechSynthesis&&typeof window.SpeechSynthesisUtterance==='function'){window.speechSynthesis.cancel();heldUtterance=new window.SpeechSynthesisUtterance(text);heldUtterance.lang='ko-KR';heldUtterance.rate=.88;heldUtterance.pitch=1;heldUtterance.volume=1;heldUtterance.onend=function(){heldUtterance=null;};window.speechSynthesis.resume();window.speechSynthesis.speak(heldUtterance);result.ok=true;result.engine='speechSynthesis';return result;}result.reason='NativeVoice 및 speechSynthesis 없음';return result;}catch(e){result.reason=String(e&&e.message||e);return result;}}
  window.finishCourt=async function(courtNo){var previousState=JSON.parse(JSON.stringify(STATE));var waitingMembers=waitingOneMembers();var voice=directSpeak(finishText(courtNo,waitingMembers));startAlertVibration();if(!voice.ok)alertAndStop('경기종료 음성 실행 실패: '+voice.reason);try{var state=await server('finishCourt',[ADMIN_PIN_VALUE,courtNo]);SELECTED.clear();renderState(state);setUndoState(previousState);rememberVoiceAnnouncement(Number(courtNo),waitingMembers);if(waitingMembers.length)alertAndStop('대기 1번 '+waitingMembers.map(cleanName).filter(Boolean).join(', ')+'님, '+Number(courtNo)+'번 코트로 들어가 주세요.');else alertAndStop(Number(courtNo)+'번 코트 경기가 종료되었습니다.');}catch(error){alertAndStop(error&&error.message||error);}};
  window.__JAYUMINTON_ADMIN_FINISH_ALERT_V17__=function(){return {nativeVoice:!!(window.NativeVoice&&typeof window.NativeVoice.speak==='function'),nativeVibrate:!!(window.NativeVoice&&typeof window.NativeVoice.vibrate==='function'),cancelVibration:!!(window.NativeVoice&&typeof window.NativeVoice.cancelVibration==='function'),waiting:waitingOneMembers().map(cleanName),emptyCourtAllowed:true,vibrationSets:8,vibrationsPerSet:3,statisticsNoClip:true};};
  window.__JAYUMINTON_ADMIN_FINISH_ALERT_V16__=window.__JAYUMINTON_ADMIN_FINISH_ALERT_V17__;
})();
</script>'''
s=s.replace(marker,patch+'\n'+marker,1)
for x in ['jayuminton-admin-finish-alert-v16','jayuminton-admin-finish-alert-v17','__JAYUMINTON_ADMIN_FINISH_ALERT_V16__','__JAYUMINTON_ADMIN_FINISH_ALERT_V17__','NativeVoice.speak','NativeVoice.vibrate','cancelVibration','emptyCourtAllowed:true','vibrationSets:8','vibrationsPerSet:3','jayuminton-admin-statistics-no-clip-v1','statisticsNoClip:true']:
    if x not in s: raise SystemExit('missing '+x)
p.write_text(s,encoding='utf-8')