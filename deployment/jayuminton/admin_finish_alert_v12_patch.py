#!/usr/bin/env python3
from pathlib import Path
import sys

p=Path(sys.argv[1])
s=p.read_text(encoding='utf-8')
marker='</body>'
if marker not in s: raise SystemExit('body marker missing')
patch=r'''<script id="jayuminton-admin-finish-alert-v12">
(function(){
  function finishText(courtNo, members){
    var calls=(members||[]).map(function(m){
      var n=String(m&&m.name||'').trim().replace(/[()（）]/g,' ').replace(/\s+/g,' ');
      return n ? n+'님' : '';
    }).filter(Boolean);
    var base=Number(courtNo)+'번 코트 경기가 종료되었습니다.';
    if(!calls.length) return base+' 대기 1번에 입장할 인원이 없습니다.';
    var assign=calls.join(', ')+', '+Number(courtNo)+'번 코트로 들어가 주세요.';
    return base+' '+assign+' '+assign+' '+assign;
  }
  function speakNow(text){
    if(!text||!('speechSynthesis' in window)||!window.SpeechSynthesisUtterance) return false;
    try{
      VOICE_GUIDE_ENABLED=true;
      try{localStorage.setItem(VOICE_GUIDE_KEY,'true');}catch(e){}
      if(typeof updateVoiceGuideButton==='function') updateVoiceGuideButton();
      window.speechSynthesis.cancel();
      var u=new SpeechSynthesisUtterance(text);u.lang='ko-KR';u.rate=.92;u.pitch=1.03;u.volume=1;
      try{var v=typeof getKoreanVoice==='function'&&getKoreanVoice('female');if(v)u.voice=v;}catch(e){}
      window.speechSynthesis.resume();window.speechSynthesis.speak(u);window.speechSynthesis.resume();
      return true;
    }catch(e){return false;}
  }
  window.finishCourt=async function(courtNo){
    var previousState=JSON.parse(JSON.stringify(STATE));
    var finishingIds=(STATE.courts[courtNo]||[]).slice();
    var waitingMembers=(STATE.waitGroups[0]||[]).slice(0,4).map(memberById).filter(Boolean);
    if(!finishingIds.length){alert('종료할 경기 인원이 없습니다.');return;}
    var text=finishText(courtNo,waitingMembers);
    try{if(typeof unlockVoiceSound==='function')unlockVoiceSound();}catch(e){}
    speakNow(text);
    try{if(navigator.vibrate)navigator.vibrate([320,180,320,180,320]);}catch(e){}
    try{
      var state=await server('finishCourt',[ADMIN_PIN_VALUE,courtNo]);
      SELECTED.clear();renderState(state);setUndoState(previousState);
      rememberVoiceAnnouncement(Number(courtNo),waitingMembers);
    }catch(error){alert(error&&error.message||error);}
  };
  window.__JAYUMINTON_V12_FINISH_TEST__=function(){
    var old=window.speechSynthesis&&window.speechSynthesis.speak,count=0;
    if(!window.speechSynthesis)return false;
    try{window.speechSynthesis.speak=function(){count++;};speakNow('3번 코트 경기가 종료되었습니다.');return count>0;}finally{try{window.speechSynthesis.speak=old;}catch(e){}}
  };
})();
</script>'''
s=s.replace(marker,patch+'\n'+marker,1)
for x in ['jayuminton-admin-finish-alert-v12','window.finishCourt=async function','slice(0,4)','window.speechSynthesis.speak(u)','__JAYUMINTON_V12_FINISH_TEST__']:
    if x not in s: raise SystemExit('missing '+x)
p.write_text(s,encoding='utf-8')
