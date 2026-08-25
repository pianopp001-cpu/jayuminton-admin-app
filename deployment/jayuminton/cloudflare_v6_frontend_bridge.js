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
    if(name==='updateMyProfile'&&values.length===2)values=[null,values[0],values[1]];
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

  if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN){
    function installAdminTeamSafetyStyle(){
      if(document.getElementById('jayuminton-admin-team-safety-v2033'))return;
      var style=document.createElement('style');
      style.id='jayuminton-admin-team-safety-v2033';
      style.textContent='#adminApp .member-team-badge,#adminApp .jm-team-badge,#adminApp .team-badge,#adminApp .team-label,#adminApp [data-team-label]{display:none!important;visibility:hidden!important;width:0!important;height:0!important;min-width:0!important;max-width:0!important;margin:0!important;padding:0!important;border:0!important;overflow:hidden!important;pointer-events:none!important}#adminApp .has-member-team{position:relative!important;border:2px solid var(--member-team-color)!important;outline:2px solid var(--member-team-color)!important;outline-offset:-5px!important;box-shadow:none!important;overflow:visible!important;height:auto!important;min-height:0!important}#adminApp .member-card,#adminApp .member-item,#adminApp .wait-card,#adminApp .wait-item,#adminApp .player-card,#adminApp .court-player{height:auto!important;min-height:0!important;max-height:none!important;overflow:visible!important}#adminApp .member-card .member-info,#adminApp .member-card .member-meta,#adminApp .member-card .member-detail,#adminApp .member-card .member-sub,#adminApp .member-card .member-memo,#adminApp .member-item .member-info,#adminApp .member-item .member-meta,#adminApp .member-item .member-detail,#adminApp .member-item .member-sub,#adminApp .member-item .member-memo,#adminApp .wait-card .member-info,#adminApp .wait-card .member-meta,#adminApp .wait-card .member-detail,#adminApp .wait-card .member-sub,#adminApp .wait-card .member-memo,#adminApp .wait-item .member-info,#adminApp .wait-item .member-meta,#adminApp .wait-item .member-detail,#adminApp .wait-item .member-sub,#adminApp .wait-item .member-memo{height:auto!important;min-height:0!important;max-height:none!important;overflow:visible!important;white-space:normal!important;line-height:1.25!important;word-break:keep-all!important}';
      (document.head||document.documentElement).appendChild(style);
    }
    function scrubAdminTeamText(root){
      var scope=root&&root.querySelectorAll?root:document;
      var cards=scope.querySelectorAll('#adminApp .has-member-team');
      for(var i=0;i<cards.length;i++){
        var nodes=cards[i].querySelectorAll('span,div,small,b,strong,em,i,label');
        for(var j=0;j<nodes.length;j++){
          var text=String(nodes[j].textContent||'').replace(/\s+/g,'').trim();
          if(/^팀\d+$/.test(text)||/^TEAM\d+$/i.test(text)){
            nodes[j].textContent='';
            nodes[j].style.setProperty('display','none','important');
            nodes[j].setAttribute('aria-hidden','true');
          }
        }
      }
    }
    function watchAdminTeamText(){
      scrubAdminTeamText(document);
      var app=document.getElementById('adminApp');
      if(!app||app.__jmTeamTextObserver)return;
      app.__jmTeamTextObserver=new MutationObserver(function(){scrubAdminTeamText(app);});
      app.__jmTeamTextObserver.observe(app,{childList:true,subtree:true,characterData:true});
    }
    function loginBox(){return document.getElementById('adminLoginBox');}
    function adminApp(){return document.getElementById('adminApp');}
    function hideApp(){var a=adminApp(),b=loginBox();if(a){a.classList.add('hidden');a.hidden=true;a.style.setProperty('display','none','important');}if(b){b.classList.remove('hidden');b.hidden=false;b.removeAttribute('hidden');b.style.setProperty('display','block','important');}}
    function revealApp(){var a=adminApp(),b=loginBox();if(a){a.hidden=false;a.removeAttribute('hidden');a.style.removeProperty('display');a.classList.remove('hidden');watchAdminTeamText();}if(b){b.classList.add('hidden');b.hidden=true;b.style.setProperty('display','none','important');}}
    function ensureStatus(){var box=loginBox();if(!box||document.getElementById('adminCloudflareLoginStatus'))return;var el=document.createElement('div');el.id='adminCloudflareLoginStatus';el.setAttribute('role','status');el.setAttribute('aria-live','polite');el.style.cssText='margin-top:10px;font-size:13px;font-weight:700;text-align:center';box.appendChild(el);}
    function status(text,isError){var el=document.getElementById('adminCloudflareLoginStatus');if(el){el.textContent=String(text||'');el.style.color=isError?'#b42318':'#667085';}}
    function reset(){var b=document.getElementById('adminCloudflareLoginButton');if(b){b.disabled=false;b.textContent='로그인';}}
    function clearAdminSession(){try{localStorage.removeItem('jayuminton_admin_session_v1');}catch(_){}}
    function resumeSavedSession(){var token=storedToken();if(!token)return false;status('저장된 관리자 인증으로 연결하고 있습니다.',false);if(typeof window.openAdminApp!=='function'){clearAdminSession();hideApp();return false;}Promise.resolve(window.openAdminApp(token)).then(function(){installAdminTeamSafetyStyle();revealApp();status('',false);}).catch(function(){clearAdminSession();hideApp();status('관리자 PIN을 한 번 입력해 주세요.',false);});return true;}
    function submit(event){if(event){event.preventDefault();event.stopPropagation();}var input=document.getElementById('adminPinInput'),pin=String(input&&input.value||'').trim();if(!pin){status('관리자 PIN을 입력하세요.',true);return;}var b=document.getElementById('adminCloudflareLoginButton');if(b){b.disabled=true;b.textContent='확인 중…';}status('관리자 서버에 연결하고 있습니다.',false);invoke('createAdminSession',[pin],function(result){if(!result||!result.ok){status('관리자 PIN이 틀렸습니다.',true);reset();return;}var token=String(result.token||'');try{localStorage.setItem('jayuminton_admin_session_v1',token);}catch(_){}if(typeof window.openAdminApp!=='function'){status('관리자 화면 초기화 함수가 없습니다.',true);reset();return;}Promise.resolve(window.openAdminApp(token)).then(function(){installAdminTeamSafetyStyle();revealApp();status('',false);reset();}).catch(function(error){hideApp();status(String(error&&error.message||error||'관리자 화면을 불러오지 못했습니다.'),true);reset();});},function(error){hideApp();status(String(error&&error.message||error||'서버에 연결할 수 없습니다.'),true);reset();});}
    function bind(){hideApp();ensureStatus();installAdminTeamSafetyStyle();var box=loginBox(),b=document.getElementById('adminCloudflareLoginButton'),input=document.getElementById('adminPinInput');if(!b&&box)b=box.querySelector('button.primary,button[type="submit"],button');if(b){b.id='adminCloudflareLoginButton';b.type='button';b.removeAttribute('onclick');}if(box){box.style.setProperty('position','relative','important');box.style.setProperty('z-index','2147483000','important');box.style.setProperty('pointer-events','auto','important');}if(b&&!b.__jmBound){b.__jmBound=true;b.style.setProperty('pointer-events','auto','important');b.addEventListener('click',submit);}if(input&&!input.__jmBound){input.__jmBound=true;input.disabled=false;input.readOnly=false;input.setAttribute('inputmode','numeric');input.setAttribute('enterkeyhint','done');input.style.setProperty('pointer-events','auto','important');input.addEventListener('click',function(){try{input.focus();}catch(_){}});input.addEventListener('keydown',function(event){if(event.key==='Enter'){event.preventDefault();submit();}});}resumeSavedSession();}
    window.__JAYUMINTON_ADMIN_PIN_INPUT_READY__=function(){var i=document.getElementById('adminPinInput'),b=document.getElementById('adminCloudflareLoginButton');return !!(i&&b&&!i.disabled&&!i.readOnly&&i.__jmBound&&b.__jmBound);};
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bind,{once:true});else setTimeout(bind,0);
  }
})();
