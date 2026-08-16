#!/usr/bin/env python3
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text(encoding='utf-8')
marker='</body>'
if marker not in s: raise SystemExit('body marker missing')
patch=r'''<script id="jayuminton-admin-finish-alert-v13">
(function(){
  function waitingOneMembers(){
    var ids=(STATE&&STATE.waitGroups&&STATE.waitGroups[0]||[]).slice();
    return ids.map(function(id){return memberById(id);}).filter(Boolean);
  }
  function cleanName(m){return String(m&&m.name||m&&m.fullName||'').trim().replace(/[()（）]/g,' ').replace(/\s+/g,' ');}
  function finishText(courtNo,members){
    var calls=(members||[]).map(cleanName).filter(Boolean).map(function(n){return n+'님';});
    var base=Number(courtNo)+'번 코트 경기가 종료되었습니다.';
    if(!calls.length)return base+' 대기 1번에 입장할 인원이 없습니다.';
    return base+' 대기 1번, '+calls.join(', ')+', '+Number(courtNo)+'번 코트로 들어가 주세요.';
  }
  function speakNow(text){
    if(!text||!('speechSynthesis' in window)||!window.SpeechSynthesisUtterance)return false;
    try{
      window.speechSynthesis.cancel();
      var u=new SpeechSynthesisUtterance(text);u.lang='ko-KR';u.rate=.9;u.pitch=1.02;u.volume=1;
      try{var v=typeof getKoreanVoice==='function'&&getKoreanVoice('female');if(v)u.voice=v;}catch(e){}
      window.speechSynthesis.resume();window.speechSynthesis.speak(u);return true;
    }catch(e){return false;}
  }
  window.finishCourt=async function(courtNo){
    var previousState=JSON.parse(JSON.stringify(STATE));
    var finishingIds=(STATE.courts[courtNo]||[]).slice();
    /* 서버 종료 처리 전에 대기1 전체 명단을 반드시 보존한다. */
    var waitingMembers=waitingOneMembers();
    if(!finishingIds.length){alert('종료할 경기 인원이 없습니다.');return;}
    var text=finishText(courtNo,waitingMembers);
    try{if(typeof unlockVoiceSound==='function')unlockVoiceSound();}catch(e){}
    speakNow(text);
    try{if(navigator.vibrate)navigator.vibrate([320,180,320,180,500]);}catch(e){}
    try{
      var state=await server('finishCourt',[ADMIN_PIN_VALUE,courtNo]);
      SELECTED.clear();renderState(state);setUndoState(previousState);
      rememberVoiceAnnouncement(Number(courtNo),waitingMembers);
    }catch(error){alert(error&&error.message||error);}
  };
  window.__JAYUMINTON_V13_WAITING_ONE_TEST__=function(){
    var members=waitingOneMembers(),text=finishText(2,members);
    return {count:members.length,text:text,names:members.map(cleanName)};
  };
})();
</script>'''
s=s.replace(marker,patch+'\n'+marker,1)
for x in ['jayuminton-admin-finish-alert-v13','waitingOneMembers()','var waitingMembers=waitingOneMembers();','대기 1번,','__JAYUMINTON_V13_WAITING_ONE_TEST__']:
    if x not in s: raise SystemExit('missing '+x)
p.write_text(s,encoding='utf-8')
