#!/usr/bin/env python3
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text(encoding='utf-8')
marker='</body>'
if marker not in s: raise SystemExit('body marker missing')
patch=r'''<style id="jayuminton-admin-voice-test-style">
#adminVoiceTestButton{position:fixed;right:12px;bottom:72px;z-index:9999;padding:10px 14px;border:2px solid #111;border-radius:10px;background:#fff;color:#111;font-weight:900;font-size:14px}
</style>
<button id="adminVoiceTestButton" type="button">음성 테스트</button>
<script id="jayuminton-admin-finish-alert-v15">
(function(){
  var heldUtterance=null;
  function waitingOneMembers(){var ids=(STATE&&STATE.waitGroups&&STATE.waitGroups[0]||[]).slice();return ids.map(function(id){return memberById(id);}).filter(Boolean);}
  function cleanName(m){return String(m&&m.name||m&&m.fullName||'').trim().replace(/[()（）]/g,' ').replace(/\s+/g,' ');}
  function finishText(courtNo,members){var calls=(members||[]).map(cleanName).filter(Boolean).map(function(n){return n+'님';});var base=Number(courtNo)+'번 코트 경기가 종료되었습니다.';return calls.length?base+' 대기 1번, '+calls.join(', ')+', '+Number(courtNo)+'번 코트로 들어가 주세요.':base+' 대기 1번에 입장할 인원이 없습니다.';}
  function directSpeak(text){
    var result={ok:false,reason:'',engine:''}; text=String(text||'').trim();
    try{
      if(window.NativeVoice && typeof window.NativeVoice.speak==='function'){
        window.NativeVoice.speak(text); result.ok=true; result.engine='NativeVoice'; result.reason='Android NativeVoice 호출 완료'; return result;
      }
      if(window.speechSynthesis && typeof window.SpeechSynthesisUtterance==='function'){
        window.speechSynthesis.cancel(); heldUtterance=new window.SpeechSynthesisUtterance(text);
        heldUtterance.lang='ko-KR';heldUtterance.rate=.88;heldUtterance.pitch=1;heldUtterance.volume=1;
        heldUtterance.onerror=function(e){console.error('JAYUMINTON_TTS_ERROR',e&&e.error,e);};
        heldUtterance.onend=function(){heldUtterance=null;}; window.speechSynthesis.resume();window.speechSynthesis.speak(heldUtterance);
        result.ok=true;result.engine='speechSynthesis';result.reason='브라우저 TTS 호출 완료';return result;
      }
      result.reason='NativeVoice 및 speechSynthesis 없음'; return result;
    }catch(e){result.reason=String(e&&e.message||e);return result;}
  }
  window.adminVoiceDiagnostic=function(){var r=directSpeak('음성 안내 테스트입니다. 소리가 들리면 정상입니다.');setTimeout(function(){if(!r.ok)alert('음성 테스트 실패: '+r.reason);},50);return r;};
  var btn=document.getElementById('adminVoiceTestButton');if(btn)btn.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();window.adminVoiceDiagnostic();});
  window.finishCourt=async function(courtNo){
    var previousState=JSON.parse(JSON.stringify(STATE));var finishingIds=(STATE.courts[courtNo]||[]).slice();var waitingMembers=waitingOneMembers();
    if(!finishingIds.length){alert('종료할 경기 인원이 없습니다.');return;}
    var text=finishText(courtNo,waitingMembers);var voice=directSpeak(text);if(!voice.ok)alert('경기종료 음성 실행 실패: '+voice.reason);
    try{if(window.NativeVoice&&typeof window.NativeVoice.vibrate==='function')window.NativeVoice.vibrate();else if(navigator.vibrate)navigator.vibrate([320,180,320,180,500]);}catch(e){}
    try{var state=await server('finishCourt',[ADMIN_PIN_VALUE,courtNo]);SELECTED.clear();renderState(state);setUndoState(previousState);rememberVoiceAnnouncement(Number(courtNo),waitingMembers);}catch(error){alert(error&&error.message||error);}
  };
  window.__JAYUMINTON_V15_VOICE_TEST__=function(){return {nativeVoice:!!(window.NativeVoice&&typeof window.NativeVoice.speak==='function'),speech:!!window.speechSynthesis,waiting:waitingOneMembers().map(cleanName)};};
})();
</script>'''
s=s.replace(marker,patch+'\n'+marker,1)
for x in ['jayuminton-admin-finish-alert-v15','NativeVoice.speak','adminVoiceTestButton','__JAYUMINTON_V15_VOICE_TEST__']:
    if x not in s: raise SystemExit('missing '+x)
p.write_text(s,encoding='utf-8')
