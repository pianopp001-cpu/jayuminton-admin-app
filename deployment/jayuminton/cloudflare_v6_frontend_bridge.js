(function installJayumintonCloudflareV6Bridge(){
  'use strict';
  var ENDPOINT='https://jayuminton-state.pianopp001.workers.dev/api/compat/rpc';
  function storedToken(){
    try {
      if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return String(localStorage.getItem('jayuminton_admin_session_v1')||'');
      return String(localStorage.getItem('jayuminton_member_session_token_v1')||localStorage.getItem('jayuminton_member_session_token_v164')||'');
    } catch (_) { return ''; }
  }
  function invoke(name,args,success,failure){
    var values=Array.prototype.slice.call(args||[]); var token='';
    // 기존 화면의 첫 번째 인수는 관리자 PIN 또는 회원 ID일 수 있다.
    // 인증은 반드시 로그인 때 저장한 Cloudflare 세션으로만 보낸다.
    if(name!=='createAdminSession'&&name!=='verifyMemberPassword'&&name!=='getMemberPasswordVersion') token=storedToken();
    fetch(ENDPOINT,{
      method:'POST',cache:'no-store',credentials:'omit',
      headers:Object.assign({'content-type':'application/json'},token?{'authorization':'Bearer '+token}:{}),
      body:JSON.stringify({name:String(name||''),args:values})
    }).then(function(response){return response.json();}).then(function(packet){
      if(!packet||packet.ok!==true)throw new Error(String(packet&&packet.error||'서버 요청에 실패했습니다.'));
      if(typeof success==='function')success(packet.result);
    }).catch(function(error){if(typeof failure==='function')failure(error);});
  }
  function runner(success,failure){
    return new Proxy({}, {get:function(_,prop){
      if(prop==='withSuccessHandler')return function(fn){return runner(fn,failure);};
      if(prop==='withFailureHandler')return function(fn){return runner(success,fn);};
      if(prop==='then')return undefined;
      return function(){invoke(String(prop),arguments,success,failure);};
    }});
  }
  window.google=window.google||{}; window.google.script=window.google.script||{};
  window.google.script.run=runner(null,null);
  window.__JAYUMINTON_CLOUDFLARE_RPC_V6__=true;

  // The proven v200.5 login button was bound inside the retired RPC bridge.
  // Rebind it here so replacing that bridge never leaves a visible dead button.
  if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN){
    function loginBox(){return document.getElementById('adminLoginBox');}
    function adminApp(){return document.getElementById('adminApp');}
    function hideApp(){var a=adminApp(),b=loginBox();if(a){a.classList.add('hidden');a.hidden=true;a.style.setProperty('display','none','important');}if(b){b.classList.remove('hidden');b.hidden=false;b.removeAttribute('hidden');b.style.setProperty('display','block','important');}}
    function revealApp(){var a=adminApp(),b=loginBox();if(a){a.hidden=false;a.removeAttribute('hidden');a.style.removeProperty('display');a.classList.remove('hidden');}if(b){b.classList.add('hidden');b.hidden=true;b.style.setProperty('display','none','important');}}
    function ensureStatus(){var box=loginBox();if(!box||document.getElementById('adminCloudflareLoginStatus'))return;var el=document.createElement('div');el.id='adminCloudflareLoginStatus';el.setAttribute('role','status');el.setAttribute('aria-live','polite');el.style.cssText='margin-top:10px;font-size:13px;font-weight:700;text-align:center';box.appendChild(el);}
    function status(text,isError){var el=document.getElementById('adminCloudflareLoginStatus');if(el){el.textContent=String(text||'');el.style.color=isError?'#b42318':'#667085';}}
    function reset(){var b=document.getElementById('adminCloudflareLoginButton');if(b){b.disabled=false;b.textContent='로그인';}}
    function submit(event){
      if(event){event.preventDefault();event.stopPropagation();}
      var input=document.getElementById('adminPinInput'),pin=String(input&&input.value||'').trim();
      if(!pin){status('관리자 PIN을 입력하세요.',true);return;}
      var b=document.getElementById('adminCloudflareLoginButton');if(b){b.disabled=true;b.textContent='확인 중…';}
      status('관리자 서버에 연결하고 있습니다.',false);
      invoke('createAdminSession',[pin],function(result){
        if(!result||!result.ok){status('관리자 PIN이 틀렸습니다.',true);reset();return;}
        var token=String(result.token||'');try{localStorage.setItem('jayuminton_admin_session_v1',token);}catch(_){}
        if(typeof window.openAdminApp!=='function'){status('관리자 화면 초기화 함수가 없습니다.',true);reset();return;}
        Promise.resolve(window.openAdminApp(token)).then(function(){revealApp();status('',false);reset();}).catch(function(error){hideApp();status(String(error&&error.message||error||'관리자 화면을 불러오지 못했습니다.'),true);reset();});
      },function(error){hideApp();status(String(error&&error.message||error||'서버에 연결할 수 없습니다.'),true);reset();});
    }
    function bind(){
      hideApp();ensureStatus();
      var box=loginBox(),b=document.getElementById('adminCloudflareLoginButton'),input=document.getElementById('adminPinInput');
      // The latest v200.8 markup dropped the legacy button id and only kept an
      // inline adminLogin() handler. Resolve that visible button explicitly and
      // replace the inline handler so one tap performs exactly one login request.
      if(!b&&box)b=box.querySelector('button.primary,button[type="submit"],button');
      if(b){b.id='adminCloudflareLoginButton';b.type='button';b.removeAttribute('onclick');}
      if(box){box.style.setProperty('position','relative','important');box.style.setProperty('z-index','2147483000','important');box.style.setProperty('pointer-events','auto','important');}
      if(b&&!b.__jmBound){b.__jmBound=true;b.style.setProperty('pointer-events','auto','important');b.addEventListener('click',submit);}
      if(input&&!input.__jmBound){input.__jmBound=true;input.disabled=false;input.readOnly=false;input.setAttribute('inputmode','numeric');input.setAttribute('enterkeyhint','done');input.style.setProperty('pointer-events','auto','important');input.addEventListener('click',function(){try{input.focus();}catch(_){}});input.addEventListener('keydown',function(event){if(event.key==='Enter'){event.preventDefault();submit();}});}
    }
    window.__JAYUMINTON_ADMIN_PIN_INPUT_READY__=function(){var i=document.getElementById('adminPinInput'),b=document.getElementById('adminCloudflareLoginButton');return !!(i&&b&&!i.disabled&&!i.readOnly&&i.__jmBound&&b.__jmBound);};
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bind,{once:true});else setTimeout(bind,0);
  }
})();
