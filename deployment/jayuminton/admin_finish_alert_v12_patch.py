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
#jayumintonAlertNotice{position:fixed!important;inset:0!important;z-index:2147483500!important;display:none;align-items:center!important;justify-content:center!important;padding:22px!important;background:rgba(15,23,42,.60)!important;box-sizing:border-box!important}
#jayumintonAlertNotice.is-visible{display:flex!important}
#jayumintonAlertNotice .jm-alert-card{width:min(420px,calc(100vw - 36px))!important;background:#fff!important;color:#111827!important;border-radius:18px!important;padding:22px 18px 16px!important;box-shadow:0 18px 60px rgba(15,23,42,.28)!important;text-align:center!important}
#jayumintonAlertNotice .jm-alert-message{font-size:18px!important;font-weight:900!important;line-height:1.5!important;white-space:pre-line!important;word-break:keep-all!important}
#jayumintonAlertNotice .jm-alert-close{margin-top:18px!important;width:100%!important;min-height:50px!important;border:0!important;border-radius:13px!important;background:#2563eb!important;color:#fff!important;font-size:17px!important;font-weight:900!important}
</style>
<!-- jayuminton-admin-finish-alert-v16 compatibility marker; behavior is v18 -->
<script id="jayuminton-admin-finish-alert-v18">
(function(){
  var heldUtterance=null;
  function waitingOneMembers(){var ids=(STATE&&STATE.waitGroups&&STATE.waitGroups[0]||[]).slice();return ids.map(function(id){return memberById(id);}).filter(Boolean);}
  function cleanName(m){return String(m&&m.name||m&&m.fullName||'').trim().replace(/[()（）]/g,' ').replace(/\s+/g,' ');}
  function finishText(courtNo,members){var calls=(members||[]).map(cleanName).filter(Boolean).map(function(n){return n+'님';});var base=Number(courtNo)+'번 코트 경기가 종료되었습니다.';return calls.length?base+'\n대기 1번 '+calls.join(', ')+'\n'+Number(courtNo)+'번 코트로 들어가 주세요.':base+'\n대기 1번에 입장할 인원이 없습니다.';}
  function stopAlertVibration(){try{if(window.NativeVoice&&typeof window.NativeVoice.cancelVibration==='function')window.NativeVoice.cancelVibration();else if(navigator.vibrate)navigator.vibrate(0);}catch(e){}}
  function startAlertVibration(){try{if(window.NativeVoice&&typeof window.NativeVoice.vibrate==='function')window.NativeVoice.vibrate();else if(navigator.vibrate){var p=[0];for(var set=0;set<8;set++){for(var i=0;i<3;i++)p.push(320,180);p.push(650);}navigator.vibrate(p);}}catch(e){}}
  function ensureAlertNotice(){var n=document.getElementById('jayumintonAlertNotice');if(n)return n;n=document.createElement('div');n.id='jayumintonAlertNotice';n.innerHTML='<div class="jm-alert-card" role="alertdialog" aria-modal="true"><div class="jm-alert-message"></div><button type="button" class="jm-alert-close">확인</button></div>';document.body.appendChild(n);var close=function(){stopAlertVibration();n.classList.remove('is-visible');};n.querySelector('.jm-alert-close').addEventListener('click',close);n.addEventListener('click',function(e){if(e.target===n)close();});return n;}
  function showAlertNotice(message){var n=ensureAlertNotice();var m=n.querySelector('.jm-alert-message');if(m)m.textContent=String(message||'');n.classList.add('is-visible');return n;}
  function updateAlertNotice(message){var n=ensureAlertNotice();var m=n.querySelector('.jm-alert-message');if(m)m.textContent=String(message||'');n.classList.add('is-visible');}
  function directSpeak(text){var result={ok:false,reason:'',engine:''};text=String(text||'').replace(/\n/g,' ').trim();try{if(window.NativeVoice&&typeof window.NativeVoice.speak==='function'){window.NativeVoice.speak('court_finish_'+Date.now(),text,.88,1,'');result.ok=true;result.engine='NativeVoice';return result;}if(window.speechSynthesis&&typeof window.SpeechSynthesisUtterance==='function'){window.speechSynthesis.cancel();heldUtterance=new window.SpeechSynthesisUtterance(text);heldUtterance.lang='ko-KR';heldUtterance.rate=.88;heldUtterance.pitch=1;heldUtterance.volume=1;heldUtterance.onend=function(){heldUtterance=null;};window.speechSynthesis.resume();window.speechSynthesis.speak(heldUtterance);result.ok=true;result.engine='speechSynthesis';return result;}result.reason='NativeVoice 및 speechSynthesis 없음';return result;}catch(e){result.reason=String(e&&e.message||e);return result;}}
  window.finishCourt=async function(courtNo){
    var previousState=JSON.parse(JSON.stringify(STATE));
    var waitingMembers=waitingOneMembers();
    var message=finishText(courtNo,waitingMembers);
    var voice=directSpeak(message);
    startAlertVibration();
    showAlertNotice(message);
    if(!voice.ok)updateAlertNotice(message+'\n\n음성 실행 실패: '+voice.reason);
    try{
      var state=await server('finishCourt',[ADMIN_PIN_VALUE,courtNo]);
      SELECTED.clear();renderState(state);setUndoState(previousState);rememberVoiceAnnouncement(Number(courtNo),waitingMembers);
    }catch(error){
      stopAlertVibration();
      updateAlertNotice('저장 실패\n'+String(error&&error.message||error||'경기종료 처리에 실패했습니다.'));
    }
  };
  window.__JAYUMINTON_ADMIN_FINISH_ALERT_V18__=function(){return {nativeVoice:!!(window.NativeVoice&&typeof window.NativeVoice.speak==='function'),nativeVibrate:!!(window.NativeVoice&&typeof window.NativeVoice.vibrate==='function'),cancelVibration:!!(window.NativeVoice&&typeof window.NativeVoice.cancelVibration==='function'),waiting:waitingOneMembers().map(cleanName),emptyCourtAllowed:true,vibrationSets:8,vibrationsPerSet:3,cancelOnAlertDismiss:true,alertBeforeServerCompletion:true,statisticsNoClip:true};};
  window.__JAYUMINTON_ADMIN_FINISH_ALERT_V17__=window.__JAYUMINTON_ADMIN_FINISH_ALERT_V18__;
  window.__JAYUMINTON_ADMIN_FINISH_ALERT_V16__=window.__JAYUMINTON_ADMIN_FINISH_ALERT_V18__;
})();
</script>'''
s=s.replace(marker,patch+'\n'+marker,1)
for x in ['jayuminton-admin-finish-alert-v16','jayuminton-admin-finish-alert-v18','__JAYUMINTON_ADMIN_FINISH_ALERT_V16__','__JAYUMINTON_ADMIN_FINISH_ALERT_V17__','__JAYUMINTON_ADMIN_FINISH_ALERT_V18__','NativeVoice.speak','NativeVoice.vibrate','cancelVibration','emptyCourtAllowed:true','vibrationSets:8','vibrationsPerSet:3','cancelOnAlertDismiss:true','alertBeforeServerCompletion:true','jayuminton-admin-statistics-no-clip-v1','statisticsNoClip:true']:
    if x not in s: raise SystemExit('missing '+x)
p.write_text(s,encoding='utf-8')