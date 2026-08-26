(function installJayumintonAdminMultiActionV2054Hotfix(){
  'use strict';
  if(window.__JAYUMINTON_ADMIN_MULTI_ACTION_V2054_HOTFIX__) return;
  window.__JAYUMINTON_ADMIN_MULTI_ACTION_V2054_HOTFIX__=true;
  window.__JAYUMINTON_ADMIN_MESSAGE_ANYWHERE_V2056__=true;

  // Keep container cards out: only an actual member node may receive selection/team styling.
  var CARD_SELECTOR='.member,.person,.quick-member,.member-card,.member-item,.player-card,.court-player,[data-member-id],[data-memberid],[data-player-id]';
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
  function longPressIds(){
    try{return (typeof MEMBER_ACTION_IDS!=='undefined'&&Array.isArray(MEMBER_ACTION_IDS)?MEMBER_ACTION_IDS:[]).map(String).filter(Boolean);}catch(_){return [];}
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
    s.textContent='#jm-admin-multi-action{pointer-events:none!important}#jm-admin-multi-action button{pointer-events:auto!important}#jm-admin-multi-action .jm-do-move,#jm-admin-multi-action .jm-do-move span{white-space:nowrap!important;word-break:keep-all!important;overflow-wrap:normal!important}#jm-admin-multi-action .jm-do-move{min-width:118px!important}#quickMoveBar .jm-message-anywhere-v2056{white-space:nowrap!important;word-break:keep-all!important}';
    (document.head||document.documentElement).appendChild(s);
  }
  function closeMessageComposer(){var old=document.getElementById('jm-message-anywhere-modal');if(old)old.remove();}
  function openMessageComposer(){
    var ids=longPressIds();if(!ids.length){toast('메시지를 보낼 사용자를 길게 눌러 주세요.',true);return;}
    closeMessageComposer();
    var overlay=document.createElement('div');overlay.id='jm-message-anywhere-modal';
    overlay.style.cssText='position:fixed;inset:0;z-index:2147483647;background:rgba(15,23,42,.46);display:flex;align-items:center;justify-content:center;padding:16px';
    var box=document.createElement('div');box.style.cssText='width:min(430px,100%);background:#fff;border-radius:18px;padding:16px;box-shadow:0 20px 60px rgba(0,0,0,.3);font-family:inherit';
    box.innerHTML='<div style="font-size:16px;font-weight:900;margin-bottom:8px">개인 메시지 보내기</div><div style="font-size:12px;color:#64748b;margin-bottom:10px">선택한 '+ids.length+'명에게 전송합니다.</div><textarea maxlength="300" rows="4" placeholder="메시지를 입력하세요" style="box-sizing:border-box;width:100%;resize:vertical;border:1px solid #cbd5e1;border-radius:12px;padding:11px;font:inherit"></textarea><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px"><button type="button" class="jm-msg-cancel" style="min-height:44px;border:0;border-radius:12px;font-weight:850">취소</button><button type="button" class="jm-msg-send" style="min-height:44px;border:0;border-radius:12px;background:#2563eb;color:#fff;font-weight:850">보내기</button></div>';
    overlay.appendChild(box);document.body.appendChild(overlay);
    var ta=box.querySelector('textarea');setTimeout(function(){ta.focus();},0);
    box.querySelector('.jm-msg-cancel').onclick=function(){closeMessageComposer();};
    overlay.onclick=function(e){if(e.target===overlay)closeMessageComposer();};
    box.querySelector('.jm-msg-send').onclick=async function(){
      var text=String(ta.value||'').trim();if(!text){toast('메시지를 입력하세요.',true);return;}
      var b=this;b.disabled=true;b.textContent='전송 중…';
      try{await rpc('sendMemberMessage',[null,ids,text]);closeMessageComposer();toast('메시지를 보냈습니다.',false);if(typeof closeMemberActionBar==='function')closeMemberActionBar();}
      catch(e){b.disabled=false;b.textContent='보내기';toast(String(e&&e.message||e||'메시지 전송 실패'),true);}
    };
  }
  function injectMessageButton(){
    var bar=document.getElementById('quickMoveBar');if(!bar||bar.querySelector('.jm-message-anywhere-v2056'))return;
    var b=document.createElement('button');b.type='button';b.className='jm-message-anywhere-v2056';b.textContent='메시지 보내기';
    b.onclick=function(e){e.preventDefault();e.stopPropagation();openMessageComposer();};
    bar.insertBefore(b,bar.firstChild||null);
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
    injectMessageButton();
    var p=document.getElementById('jm-admin-multi-action');if(!p)return;
    var ids=selectedIds();
    if(ids.length!==2){p.remove();return;}
    if(p.querySelector('.jm-send-court-wait'))return;
    var actions=p.querySelector('.jm-multi-actions');if(!actions)return;
    var b=document.createElement('button');b.type='button';b.className='jm-send-court-wait';b.textContent='코트배정대기로';
    b.style.cssText='border:0;border-radius:12px;min-height:44px;font-size:13px;font-weight:850;background:#e0f2fe;color:#075985;font-family:inherit;white-space:nowrap;word-break:keep-all';
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
    setTimeout(function(){paintTeamsFromState(detail);injectButton();},0);
  });
  installFastObserver();
})();
