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
var SELF_TIMEOUT_MS=15000;
/* Do not rely on admin_server_timeout_v1.js having already wrapped
   window.server by the time login runs -- that script wraps on its own
   200ms poll and can race with V24's own independent re-wrapping, so there
   is no guarantee the outermost window.server has a timeout applied yet at
   the exact moment openAdminApp() calls it (e.g. a fast login right after
   page load, before that poll's first tick). Without its own timeout here,
   a hang in getCurrentMemberPassword or loadState's underlying fetch would
   never reject and never resolve -- attemptLoad()'s try/catch only fires on
   rejection, so a true hang produces neither the render-resilience fallback
   nor this file's own error+retry UI: exactly a silent permanent blank
   screen with frozen buttons and no explanation, which is what was actually
   reported. Race every awaited call in this path against its own timeout so
   this file's recovery guarantee holds regardless of what window.server
   currently is. */
function withTimeout(promise,ms,label){
  return new Promise(function(resolve,reject){
    var settled=false;
    var timer=setTimeout(function(){
      if(settled)return;settled=true;
      reject(new Error(label+'이(가) 응답하지 않습니다 ('+(ms/1000)+'초 초과).'));
    },ms);
    Promise.resolve(promise).then(function(v){
      if(settled)return;settled=true;clearTimeout(timer);resolve(v);
    },function(e){
      if(settled)return;settled=true;clearTimeout(timer);reject(e);
    });
  });
}

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
    await withTimeout(originalLoad(),SELF_TIMEOUT_MS,'상태 불러오기');
    hideStatus();
    try{ if(typeof loadSystemStatus==='function') await withTimeout(loadSystemStatus(),SELF_TIMEOUT_MS,'시스템 상태'); }catch(err){
      console.error('[jm-login-load-resilience] loadSystemStatus failed',err);
      /* jmLoginLoadDiagnosticV1: this is the exact call that was observed
         hanging completely (a corrupted window.server wrap chain producing
         a microtask-starvation loop that even this file's own withTimeout
         could never recover from -- fixed by jmServerWrapChainFixV1). Keep
         the whole app usable (main render already succeeded above) but
         alert so a system-status failure is never silently invisible. */
      try{alert('[진단] openAdminApp:loadSystemStatus 실패 - '+String(err&&err.message||err));}catch(_e){}
    }
  }catch(err){
    console.error('[jm-login-load-resilience] loadState failed',err);
    if(retryCount<1){
      showStatus('상태를 불러오지 못했습니다. 다시 시도하는 중... ('+(retryCount+1)+'/2)',false);
      setTimeout(function(){ attemptLoad(retryCount+1); },1500);
    }else{
      showStatus('상태를 불러오지 못했습니다: '+String(err&&err.message||err||'알 수 없는 오류'),true);
      /* jmLoginLoadDiagnosticV1: this status banner is easy to miss/dismiss
         without reading it, and it's the ONLY place this failure was ever
         surfaced -- window.openAdminApp is fully replaced by this file, so
         v208.25's diagnostic alert()s on the original function never run
         for the real login path. Force an alert too so a final failure
         here can't go unnoticed again. */
      try{alert('[진단] openAdminApp:loadState 최종 실패 - '+String(err&&err.message||err||'알 수 없는 오류'));}catch(_e){}
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
    var pw=await withTimeout(server('getCurrentMemberPassword',[credential]),SELF_TIMEOUT_MS,'비밀번호 조회');
    var el=document.getElementById('currentMemberPassword');
    if(el)el.textContent=pw;
  }catch(err){
    console.error('[jm-login-load-resilience] getCurrentMemberPassword failed/timed out, continuing to load state anyway',err);
    /* jmLoginLoadDiagnosticV1 */
    try{alert('[진단] openAdminApp:getCurrentMemberPassword 실패(계속 진행) - '+String(err&&err.message||err));}catch(_e){}
  }

  await attemptLoad(0);
};
window.openAdminApp.__jmLoginLoadResilienceV1Original=originalOpen;
})();
