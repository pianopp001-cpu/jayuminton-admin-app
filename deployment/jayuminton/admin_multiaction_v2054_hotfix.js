(function installJayumintonAdminMultiActionV2054Hotfix(){
  'use strict';
  if(window.__JAYUMINTON_ADMIN_MULTI_ACTION_V2054_HOTFIX__) return;
  window.__JAYUMINTON_ADMIN_MULTI_ACTION_V2054_HOTFIX__=true;

  var CARD_SELECTOR='.member,.person,.quick-member,.member-card,.member-item,.wait-card,.wait-item,.player-card,.court-player,[data-member-id],[data-memberid],[data-player-id]';
  var lastAuthoritativeState=null;
  function app(){return document.getElementById('adminApp');}
  function idOf(c){
    if(!c)return '';
    var a=['data-member-id','data-memberid','data-player-id','data-id','data-member'];
    for(var i=0;i<a.length;i++){var v=c.getAttribute&&c.getAttribute(a[i]);if(v)return String(v);}
    var n=c.querySelector&&c.querySelector('[data-member-id],[data-memberid],[data-player-id],[data-id],[data-member]');
    if(n){for(var j=0;j<a.length;j++){var x=n.getAttribute(a[j]);if(x)return String(x);}}
    var raw=String(c.getAttribute&&c.getAttribute('onclick')||''),m=raw.match(/[0-9a-f]{8}-[0-9a-f-]{27,}/i);
    return m?m[0]:'';
  }
  function selectedIds(){
    var a=app(),out=[];
    if(!a)return out;
    Array.prototype.forEach.call(a.querySelectorAll('.jm-source-selected'),function(el){
      var c=el.closest&&el.closest(CARD_SELECTOR)||el,id=idOf(c);
      if(id&&out.indexOf(id)<0)out.push(id);
    });
    return out.slice(0,4);
  }
  function rpc(name,args){
    if(typeof window.server!=='function')return Promise.reject(new Error('Cloudflare 서버 연결을 찾을 수 없습니다.'));
    return window.server(String(name||''),Array.isArray(args)?args:[]);
  }
  function toast(t,bad){
    var old=document.getElementById('jm-admin-v2054-toast');if(old)old.remove();
    var e=document.createElement('div');e.id='jm-admin-v2054-toast';e.textContent=String(t||'');
    e.style.cssText='position:fixed;left:50%;bottom:92px;transform:translateX(-50%);z-index:2147483647;padding:10px 14px;border-radius:12px;background:'+(bad?'#991b1b':'#111827')+';color:#fff;font-size:14px;font-weight:800;box-shadow:0 8px 26px rgba(0,0,0,.22)';
    document.body.appendChild(e);setTimeout(function(){e.remove();},1600);
  }
  function installPassThroughStyle(){
    if(document.getElementById('jm-admin-v2054-pass-through-style'))return;
    var s=document.createElement('style');s.id='jm-admin-v2054-pass-through-style';
    s.textContent='#jm-admin-multi-action{pointer-events:none!important}#jm-admin-multi-action button{pointer-events:auto!important}';
    (document.head||document.documentElement).appendChild(s);
  }
  function resetUi(){
    var p=document.getElementById('jm-admin-multi-action');if(p)p.remove();
    var a=app();if(a)Array.prototype.forEach.call(a.querySelectorAll('.jm-source-selected,.jm-target-selected'),function(e){e.classList.remove('jm-source-selected');e.classList.remove('jm-target-selected');});
  }
  function authoritativeState(candidate){
    if(candidate&&candidate.state&&Array.isArray(candidate.state.members))candidate=candidate.state;
    if(candidate&&Array.isArray(candidate.members))lastAuthoritativeState=candidate;
    if(lastAuthoritativeState)return lastAuthoritativeState;
    try{if(typeof window.STATE!=='undefined'&&window.STATE)return window.STATE;}catch(_){}
    return null;
  }
  async function sendToCourtWaiting(){
    var ids=selectedIds();
    if(ids.length!==2){toast('2명을 선택한 상태에서 사용하세요.',true);return;}
    try{
      var saved=await rpc('setMemberStatus',[null,ids,'active']);
      authoritativeState(saved);
      resetUi();
      paintTeamsFromState(saved);
      if(typeof window.renderState==='function')window.renderState();
      toast('2명을 코트배정 대기로 보냈습니다.',false);
    }catch(e){toast(String(e&&e.message||e||'코트배정 대기 이동 실패'),true);}
  }
  function injectButton(){
    var p=document.getElementById('jm-admin-multi-action');if(!p)return;
    var ids=selectedIds();
    if(ids.length!==2){p.remove();return;}
    if(p.querySelector('.jm-send-court-wait'))return;
    var actions=p.querySelector('.jm-multi-actions');if(!actions)return;
    var b=document.createElement('button');b.type='button';b.className='jm-send-court-wait';b.textContent='코트배정대기로';
    b.style.cssText='border:0;border-radius:12px;min-height:44px;font-size:13px;font-weight:850;background:#e0f2fe;color:#075985;font-family:inherit';
    b.onclick=function(e){e.preventDefault();e.stopPropagation();if(e.stopImmediatePropagation)e.stopImmediatePropagation();sendToCourtWaiting();};
    actions.insertBefore(b,actions.lastElementChild||null);
    actions.style.gridTemplateColumns='1fr 1fr 1fr 72px';
  }
  function tempIds(p){
    var out=[];[p&&p.members,p&&p.pairA,p&&p.pairB].forEach(function(v){(Array.isArray(v)?v:[]).forEach(function(x){x=String(x||'');if(x&&out.indexOf(x)<0)out.push(x);});});
    return out.slice(0,4);
  }
  function paintTeamsFromState(candidate){
    var a=app();if(!a)return;
    var st=authoritativeState(candidate);
    Array.prototype.forEach.call(a.querySelectorAll('.jm-temp-team-v2047,.jm-temp-pair'),function(e){e.classList.remove('jm-temp-team-v2047');e.classList.remove('jm-temp-pair');});
    var ids=[];(Array.isArray(st&&st.tempPairs)?st.tempPairs:[]).forEach(function(p){tempIds(p).forEach(function(id){if(ids.indexOf(id)<0)ids.push(id);});});
    ids.forEach(function(id){Array.prototype.forEach.call(a.querySelectorAll(CARD_SELECTOR),function(el){var c=el.closest&&el.closest(CARD_SELECTOR)||el;if(idOf(c)===String(id))c.classList.add('jm-temp-team-v2047');});});
    // Permanent team styling (.has-member-team) is intentionally untouched so its double border always follows the member.
  }
  function installFastObserver(){
    var a=app();if(!a){setTimeout(installFastObserver,80);return;}
    try{if(a.__jmV2053Observer&&a.__jmV2053Observer.disconnect)a.__jmV2053Observer.disconnect();}catch(_){}
    if(a.__jmV2054FastObserver)return;
    var queued=false;
    var obs=new MutationObserver(function(){
      if(queued)return;queued=true;
      requestAnimationFrame(function(){queued=false;injectButton();paintTeamsFromState();});
    });
    obs.observe(a,{childList:true,subtree:true});a.__jmV2054FastObserver=obs;
    injectButton();paintTeamsFromState();
  }
  installPassThroughStyle();
  window.addEventListener('click',function(event){
    var p=document.getElementById('jm-admin-multi-action');
    if(!p)return;
    var ids=selectedIds();
    if(ids.length!==2){p.remove();return;}
    var c=event.target&&event.target.closest&&event.target.closest(CARD_SELECTOR);
    if(c&&c.closest('#adminApp')){
      var id=idOf(c);
      if(id&&ids.indexOf(id)<0){
        p.style.display='none';
        setTimeout(function(){var now=selectedIds();var q=document.getElementById('jm-admin-multi-action');if(q&&now.length!==2)q.remove();else if(q)q.style.display='';},0);
      }
    }
  },true);
  document.addEventListener('click',function(){setTimeout(injectButton,0);},true);
  window.addEventListener('jayuminton:state',function(event){
    var detail=event&&event.detail;
    authoritativeState(detail);
    setTimeout(function(){paintTeamsFromState(detail);injectButton();},0);
  });
  window.addEventListener('jayuminton:court-finished',function(event){
    var detail=event&&event.detail;
    authoritativeState(detail);
    setTimeout(function(){paintTeamsFromState(detail);},0);
  });
  installFastObserver();
})();
