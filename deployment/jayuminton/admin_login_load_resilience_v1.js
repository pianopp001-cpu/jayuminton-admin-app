(function installJayumintonAdminLoginLoadResilienceV1(){
'use strict';
if(window.__JAYUMINTON_ADMIN_LOGIN_LOAD_RESILIENCE_V1__)return;
window.__JAYUMINTON_ADMIN_LOGIN_LOAD_RESILIENCE_V1__=true;
if(typeof window.openAdminApp!=='function'||typeof window.loadState!=='function')return;
/* openAdminApp() runs getCurrentMemberPassword() then loadState() then
   loadSystemStatus() back to back with no try/catch anywhere in between,
   right after #adminApp is unhidden. If getCurrentMemberPassword throws
   (a real RPC failure, or -- now that admin_server_timeout_v1.js is
   wired up -- a timeout error surfacing after 20s instead of hanging
   forever), loadState() is never even called: the app sits on a visible
   but completely empty #adminApp shell forever, with no error shown and
   no way to recover short of force-closing and reopening (which hits the
   exact same failure again if the underlying problem persists). This is
   a DIFFERENT failure point than admin_render_resilience_v1.js protects
   -- that one only guards code that runs INSIDE renderState(), which is
   never reached if the app never gets that far. Retry the state load a
   few times with a visible status message and a manual retry option
   instead of a silent, permanent blank screen. */
var originalOpen=window.openAdminApp;
var originalLoad=window.loadState;

function statusBox(){
  var el=document.getElementById('jmAdminLoginLoadStatus');
  if(!el){
    el=document.createElement('div');
    el.id='jmAdminLoginLoadStatus';
    el.style.cssText='position:fixed;left:50%;top:max(18px,env(safe-area-inset-top));transform:translateX(-50%);z-index:2147483600;max-width:88vw;padding:12px 16px;border-radius:12px;background:#111827;color:#fff;font-size:13px;font-weight:800;text-align:center;box-shadow:0 10px 32px rgba(0,0,0,.28);display:none';
    document.body.appendChild(el);
  }
  return el;
}
function showStatus(text,withRetry){
  var el=statusBox();
  el.innerHTML='';
  var msg=document.createElement('div');
  msg.textContent=text;
  el.appendChild(msg);
  if(withRetry){
    var btn=document.createElement('button');
    btn.type='button';
    btn.textContent='다시 시도';
    btn.style.cssText='margin-top:8px;min-height:34px;padding:0 16px;border:0;border-radius:8px;background:#2563eb;color:#fff;font-weight:800;font-size:13px';
    btn.onclick=function(){ hideStatus(); attemptLoad(0); };
    el.appendChild(btn);
  }
  el.style.display='block';
}
function hideStatus(){
  var el=document.getElementById('jmAdminLoginLoadStatus');
  if(el)el.style.display='none';
}

async function attemptLoad(retryCount){
  try{
    await originalLoad();
    hideStatus();
    try{ if(typeof loadSystemStatus==='function') await loadSystemStatus(); }catch(err){ console.error('[jm-login-load-resilience] loadSystemStatus failed',err); }
  }catch(err){
    console.error('[jm-login-load-resilience] loadState failed',err);
    if(retryCount<2){
      showStatus('상태를 불러오지 못했습니다. 다시 시도하는 중... ('+(retryCount+1)+'/3)',false);
      setTimeout(function(){ attemptLoad(retryCount+1); },1500);
    }else{
      showStatus('상태를 불러오지 못했습니다: '+String(err&&err.message||err||'알 수 없는 오류'),true);
    }
  }
}

window.openAdminApp=async function(credential){
  ADMIN_PIN_VALUE=credential;
  try{ updateVoiceGuideButton(); }catch(err){}
  try{ updateReplayVoiceButton(); }catch(err){}
  try{ updateVoiceRepeatButton(); }catch(err){}
  try{ updateSoundUnlockButton(); }catch(err){}

  document.getElementById('adminLoginBox').classList.add('hidden');
  document.getElementById('adminApp').classList.remove('hidden');

  try{
    var pw=await server('getCurrentMemberPassword',[credential]);
    var el=document.getElementById('currentMemberPassword');
    if(el)el.textContent=pw;
  }catch(err){
    console.error('[jm-login-load-resilience] getCurrentMemberPassword failed, continuing to load state anyway',err);
  }

  await attemptLoad(0);
};
window.openAdminApp.__jmLoginLoadResilienceV1Original=originalOpen;
})();
