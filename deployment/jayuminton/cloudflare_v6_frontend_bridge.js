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
    if(name!=='createAdminSession'&&name!=='verifyMemberPassword'&&name!=='getMemberPasswordVersion') token=String(values[0]||storedToken());
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
})();
