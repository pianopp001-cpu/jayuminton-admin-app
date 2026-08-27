(function installJayumintonAdminTeamStateV2060(){
  'use strict';
  if(window.__JAYUMINTON_ADMIN_TEAM_STATE_V2060__)return;
  window.__JAYUMINTON_ADMIN_TEAM_STATE_V2060__=true;
  window.__JAYUMINTON_ADMIN_MULTI_ACTION_V2054_HOTFIX__=true;
  window.__JAYUMINTON_ADMIN_MESSAGE_ANYWHERE_V2056__=true;

  var CARD_SELECTOR='.member,.person,.quick-member,.member-card,.member-item,.player-card,.court-player,[data-member-id],[data-memberid],[data-player-id]';
  var tempIdsCache={};

  function app(){return document.getElementById('adminApp');}
  function directId(el){
    if(!el||!el.getAttribute)return '';
    var keys=['data-member-id','data-memberid','data-player-id','data-id','data-member'];
    for(var i=0;i<keys.length;i++){var v=el.getAttribute(keys[i]);if(v)return String(v);}
    return '';
  }
  function idOf(el){
    if(!el)return '';
    var id=directId(el);if(id)return id;
    var node=el.querySelector&&el.querySelector('[data-member-id],[data-memberid],[data-player-id],[data-id],[data-member]');
    if(node){id=directId(node);if(id)return id;}
    var raw=String(el.getAttribute&&el.getAttribute('onclick')||''),m=raw.match(/[0-9a-f]{8}-[0-9a-f-]{27,}/i);
    return m?m[0]:'';
  }
  function actualCards(){
    var root=app(),out=[];if(!root)return out;
    Array.prototype.forEach.call(root.querySelectorAll(CARD_SELECTOR),function(el){
      if(el.matches&&el.matches('.wait-card,.wait-item'))return;
      var id=idOf(el);if(!id)return;
      var owner=el.closest&&el.closest('.wait-card,.wait-item');
      if(owner===el)return;
      if(out.indexOf(el)<0)out.push(el);
    });
    return out;
  }
  function tempIds(group){
    var out=[];
    [group&&group.members,group&&group.pairA,group&&group.pairB].forEach(function(arr){
      (Array.isArray(arr)?arr:[]).forEach(function(v){v=String(v||'');if(v&&out.indexOf(v)<0)out.push(v);});
    });
    return out.slice(0,4);
  }
  function extractState(value){
    if(value&&value.state&&typeof value.state==='object')return value.state;
    if(value&&typeof value==='object'&&(Array.isArray(value.tempPairs)||Array.isArray(value.members)))return value;
    return null;
  }
  function commitTempState(value){
    var st=extractState(value);if(!st||!Array.isArray(st.tempPairs))return false;
    var next={};
    st.tempPairs.forEach(function(group){tempIds(group).forEach(function(id){next[id]=1;});});
    tempIdsCache=next;
    try{if(typeof STATE!=='undefined'&&STATE)STATE.tempPairs=st.tempPairs.slice();}catch(_){}
    try{window.__JAYUMINTON_TEMP_TEAM_IDS_V2060__=Object.assign({},next);}catch(_){}
    paintTempTeams();
    return true;
  }
  function paintTempTeams(){
    actualCards().forEach(function(card){
      var id=idOf(card),want=!!tempIdsCache[String(id)],has=card.classList.contains('jm-temp-team-v2047');
      if(want&&!has)card.classList.add('jm-temp-team-v2047');
      if(!want&&has)card.classList.remove('jm-temp-team-v2047');
      if(!want&&card.classList.contains('jm-temp-pair'))card.classList.remove('jm-temp-pair');
    });
  }
  function seedFromState(){
    try{if(typeof STATE!=='undefined'&&STATE&&Array.isArray(STATE.tempPairs))commitTempState(STATE);}catch(_){}
  }
  function rpc(name,args){
    if(typeof window.server!=='function')return Promise.reject(new Error('Cloudflare 서버 연결을 찾을 수 없습니다.'));
    return window.server(String(name||''),Array.isArray(args)?args:[]);
  }
  function wrapServer(){
    var current=window.server;
    if(typeof current!=='function'||current.__jmTempStateWrappedV2060)return;
    var original=current;
    var wrapped=function(name,args){
      return Promise.resolve(original(String(name||''),Array.isArray(args)?args:[])).then(function(result){
        commitTempState(result);
        return result;
      });
    };
    wrapped.__jmTempStateWrappedV2060=true;
    wrapped.__jmOriginal=original;
    window.server=wrapped;
  }
  function toast(text,bad){
    var old=document.getElementById('jm-admin-v2060-toast');if(old)old.remove();
    var e=document.createElement('div');e.id='jm-admin-v2060-toast';e.textContent=String(text||'');
    e.style.cssText='position:fixed;left:50%;bottom:92px;transform:translateX(-50%);z-index:2147483647;padding:10px 14px;border-radius:12px;background:'+(bad?'#991b1b':'#111827')+';color:#fff;font-size:14px;font-weight:800;box-shadow:0 8px 26px rgba(0,0,0,.22)';
    document.body.appendChild(e);setTimeout(function(){e.remove();},1800);
  }
  function longPressIds(){
    try{return (typeof MEMBER_ACTION_IDS!=='undefined'&&Array.isArray(MEMBER_ACTION_IDS)?MEMBER_ACTION_IDS:[]).map(String).filter(Boolean);}catch(_){return [];}
  }
  function closeMessageComposer(){var old=document.getElementById('jm-message-anywhere-modal');if(old)old.remove();}
  function openMessageComposer(){
    var ids=longPressIds();if(!ids.length){toast('메시지를 보낼 사용자를 길게 눌러 주세요.',true);return;}
    closeMessageComposer();
    var overlay=document.createElement('div');overlay.id='jm-message-anywhere-modal';overlay.style.cssText='position:fixed;inset:0;z-index:2147483647;background:rgba(15,23,42,.46);display:flex;align-items:center;justify-content:center;padding:16px';
    var box=document.createElement('div');box.style.cssText='width:min(430px,100%);background:#fff;border-radius:18px;padding:16px;box-shadow:0 20px 60px rgba(0,0,0,.3);font-family:inherit';
    box.innerHTML='<div style="font-size:16px;font-weight:900;margin-bottom:8px">개인 메시지 보내기</div><div style="font-size:12px;color:#64748b;margin-bottom:10px">선택한 '+ids.length+'명에게 전송합니다.</div><textarea maxlength="300" rows="4" placeholder="메시지를 입력하세요" style="box-sizing:border-box;width:100%;resize:vertical;border:1px solid #cbd5e1;border-radius:12px;padding:11px;font:inherit"></textarea><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px"><button type="button" class="jm-msg-cancel" style="min-height:44px;border:0;border-radius:12px;font-weight:850">취소</button><button type="button" class="jm-msg-send" style="min-height:44px;border:0;border-radius:12px;background:#2563eb;color:#fff;font-weight:850">보내기</button></div>';
    overlay.appendChild(box);document.body.appendChild(overlay);
    var ta=box.querySelector('textarea');setTimeout(function(){ta.focus();},0);
    box.querySelector('.jm-msg-cancel').onclick=closeMessageComposer;
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
  function installStyle(){
    if(document.getElementById('jm-admin-v2060-style'))return;
    var s=document.createElement('style');s.id='jm-admin-v2060-style';
    s.textContent='#jm-admin-multi-action{pointer-events:none!important}#jm-admin-multi-action button{pointer-events:auto!important}#jm-admin-multi-action .jm-do-move,#jm-admin-multi-action .jm-do-move span{white-space:nowrap!important;word-break:keep-all!important;overflow-wrap:normal!important}#jm-admin-multi-action .jm-do-move{min-width:124px!important}#quickMoveBar .jm-message-anywhere-v2056{white-space:nowrap!important;word-break:keep-all!important}#adminApp .jm-temp-team-v2047,#adminApp .jm-temp-pair{box-shadow:inset 0 0 0 5px #d4a017!important;outline:0!important}';
    (document.head||document.documentElement).appendChild(s);
  }
  function boot(){
    installStyle();wrapServer();seedFromState();injectMessageButton();
    var root=app();
    if(root&&!root.__jmV2060Observer){
      var queued=false;root.__jmV2060Observer=new MutationObserver(function(){if(queued)return;queued=true;requestAnimationFrame(function(){queued=false;injectMessageButton();paintTempTeams();});});
      root.__jmV2060Observer.observe(root,{childList:true,subtree:true});
    }
  }
  window.addEventListener('jayuminton:state',function(e){if(!commitTempState(e&&e.detail))seedFromState();});
  window.addEventListener('jayuminton:court-finished',function(){setTimeout(function(){rpc('getPublicState',[null]).then(commitTempState).catch(function(){seedFromState();});},0);});
  setInterval(wrapServer,400);
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else setTimeout(boot,0);
})();
