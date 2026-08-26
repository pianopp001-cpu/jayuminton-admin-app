(function installJayumintonAdminMultiActionV2053(){
  'use strict';
  if(typeof IS_ADMIN==='undefined'||!IS_ADMIN||window.__JAYUMINTON_ADMIN_MULTI_ACTION_V2053__)return;
  window.__JAYUMINTON_ADMIN_MULTI_ACTION_V2047__=true;
  window.__JAYUMINTON_ADMIN_MULTI_ACTION_V2052__=true;
  window.__JAYUMINTON_ADMIN_MULTI_ACTION_V2053__=true;

  var CARD_SELECTOR='.member,.person,.quick-member,.member-card,.member-item,.wait-card,.wait-item,.player-card,.court-player,[data-member-id],[data-memberid],[data-player-id]';
  var selected=[],group=null,phase='source',targets=[],targetKind='',yellow={};

  function app(){return document.getElementById('adminApp');}
  function ensureStyle(){
    var old=document.getElementById('jayuminton-admin-team-safety-v2037');if(old)old.remove();
    if(document.getElementById('jayuminton-admin-multi-action-v2053-style'))return;
    var s=document.createElement('style');s.id='jayuminton-admin-multi-action-v2053-style';
    s.textContent=''
      +'#adminApp .jm-source-selected,#adminApp .jm-target-selected{box-shadow:0 0 0 4px #16a34a!important;outline:2px solid rgba(22,163,74,.22)!important;outline-offset:1px!important}'
      +'#adminApp .jm-temp-team-v2047,#adminApp .jm-temp-pair{box-shadow:0 0 0 4px #d4a017!important;outline:2px solid rgba(212,160,23,.24)!important;outline-offset:1px!important}'
      +'.jm-multi-action{position:fixed;left:50%;bottom:18px;transform:translateX(-50%);z-index:2147483645;width:min(520px,calc(100vw - 24px));background:#fff;border:1px solid #e2e8f0;border-radius:20px;padding:14px;box-shadow:0 18px 55px rgba(15,23,42,.28);font-family:inherit}'
      +'.jm-multi-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px}.jm-multi-title{font-size:15px;font-weight:900;color:#111827}.jm-multi-count{font-size:12px;font-weight:800;color:#15803d;background:#f0fdf4;border-radius:999px;padding:5px 9px}.jm-multi-help{font-size:12.5px;color:#64748b;line-height:1.45;margin-bottom:10px}.jm-multi-actions{display:grid;grid-template-columns:1fr 1fr 72px;gap:8px}.jm-multi-action button{border:0;border-radius:12px;min-height:44px;font-size:14px;font-weight:850;font-family:inherit}.jm-do-move{background:#dcfce7;color:#166534}.jm-do-team{background:#d4a017;color:#fff}.jm-do-cancel{background:#f1f5f9;color:#475569}.jm-do-team:disabled{opacity:.38}';
    (document.head||document.documentElement).appendChild(s);
  }
  function card(target){if(!target||!target.closest)return null;var c=target.closest(CARD_SELECTOR);if(!c||!c.closest('#adminApp')||c.classList.contains('empty')||c.classList.contains('quick-empty-slot'))return null;return c;}
  function idOf(c){if(!c)return '';var a=['data-member-id','data-memberid','data-player-id','data-id','data-member'];for(var i=0;i<a.length;i++){var v=c.getAttribute&&c.getAttribute(a[i]);if(v)return String(v);}var n=c.querySelector&&c.querySelector('[data-member-id],[data-memberid],[data-player-id],[data-id],[data-member]');if(n){for(var j=0;j<a.length;j++){var x=n.getAttribute(a[j]);if(x)return String(x);}}var raw=String(c.getAttribute&&c.getAttribute('onclick')||''),m=raw.match(/[0-9a-f]{8}-[0-9a-f-]{27,}/i);return m?m[0]:'';}
  function each(id,fn){var a=app();if(!a)return;var seen=[];Array.prototype.forEach.call(a.querySelectorAll(CARD_SELECTOR),function(e){if(idOf(e)!==String(id))return;var c=card(e)||e;if(seen.indexOf(c)<0){seen.push(c);fn(c);}});}
  function clearClass(name){var a=app();if(a)Array.prototype.forEach.call(a.querySelectorAll('.'+name),function(e){e.classList.remove(name);});}
  function renderGreen(){clearClass('jm-source-selected');clearClass('jm-target-selected');selected.forEach(function(id){each(id,function(c){c.classList.add('jm-source-selected');});});targets.forEach(function(t){if(t.kind==='member')each(t.id,function(c){c.classList.add('jm-target-selected');});else if(t.el&&document.contains(t.el))t.el.classList.add('jm-target-selected');});}
  function tempIds(p){var a=[];[p&&p.members,p&&p.pairA,p&&p.pairB].forEach(function(v){(Array.isArray(v)?v:[]).forEach(function(x){x=String(x||'');if(x&&a.indexOf(x)<0)a.push(x);});});return a.slice(0,4);}
  function absorb(state){yellow={};(Array.isArray(state&&state.tempPairs)?state.tempPairs:[]).forEach(function(p){tempIds(p).forEach(function(id){yellow[id]=1;});});renderYellow();}
  function renderYellow(){var a=app();if(!a)return;Array.prototype.forEach.call(a.querySelectorAll('.jm-temp-team-v2047,.jm-temp-pair'),function(e){e.classList.remove('jm-temp-team-v2047');e.classList.remove('jm-temp-pair');});Object.keys(yellow).forEach(function(id){if(yellow[id])each(id,function(c){c.classList.add('jm-temp-team-v2047');});});}
  function rpc(name,args){if(typeof window.server!=='function')return Promise.reject(new Error('Cloudflare 서버 연결을 찾을 수 없습니다.'));return window.server(String(name||''),Array.isArray(args)?args:[]);}
  function toast(t,bad){var o=document.getElementById('jm-admin-multi-toast');if(o)o.remove();var e=document.createElement('div');e.id='jm-admin-multi-toast';e.textContent=String(t||'');e.style.cssText='position:fixed;left:50%;bottom:92px;transform:translateX(-50%);z-index:2147483647;padding:10px 14px;border-radius:12px;background:'+(bad?'#991b1b':'#111827')+';color:#fff;font-size:14px;font-weight:800;box-shadow:0 8px 26px rgba(0,0,0,.22)';document.body.appendChild(e);setTimeout(function(){e.remove();},1800);}
  function state(){try{return typeof STATE!=='undefined'?STATE:null;}catch(_){return null;}}
  function locate(id){var st=state();if(!st)return null;var cs=st.courts||{};for(var k in cs)if(Array.isArray(cs[k])&&cs[k].map(String).indexOf(String(id))>=0)return {type:'court',key:String(k)};var ws=st.waitGroups||[];for(var i=0;i<ws.length;i++)if(Array.isArray(ws[i])&&ws[i].map(String).indexOf(String(id))>=0)return {type:'wait',key:String(i+1)};return null;}
  function signature(id){var l=locate(id);return l?l.type+'|'+l.key:'';}
  function samePlace(ids){if(!ids.length)return true;var s=signature(ids[0]);return !!s&&ids.every(function(id){return signature(id)===s;});}
  function reset(){selected=[];group=null;phase='source';targets=[];targetKind='';renderGreen();renderPanel();renderYellow();}
  function panel(){var p=document.getElementById('jm-admin-multi-action');if(!p){p=document.createElement('div');p.id='jm-admin-multi-action';p.className='jm-multi-action';document.body.appendChild(p);}return p;}
  function renderPanel(){
    var p=document.getElementById('jm-admin-multi-action');
    if(!selected.length){if(p)p.remove();return;}
    if(phase==='target'){
      p=panel();
      p.innerHTML='<div class="jm-multi-head"><div class="jm-multi-title">'+selected.length+'명 이동/교환</div><div class="jm-multi-count">대상 '+targets.length+'/'+selected.length+'</div></div><div class="jm-multi-help">빈자리 '+selected.length+'곳 또는 바꿀 사람 '+selected.length+'명을 선택하세요.</div><div class="jm-multi-actions" style="grid-template-columns:1fr 90px"><button type="button" class="jm-back-source">사람 다시 선택</button><button type="button" class="jm-do-cancel">취소</button></div>';
      p.querySelector('.jm-back-source').onclick=function(e){e.stopPropagation();phase='source';targets=[];targetKind='';renderGreen();renderPanel();};
      p.querySelector('.jm-do-cancel').onclick=function(e){e.stopPropagation();reset();};
      return;
    }
    // Only exactly two selected members need the move-vs-team decision.
    // 1, 3 and 4 members are movement-only and therefore show no popup.
    if(selected.length!==2){if(p)p.remove();return;}
    var canTeam=samePlace(selected);
    p=panel();
    p.innerHTML='<div class="jm-multi-head"><div class="jm-multi-title">2명 선택</div><div class="jm-multi-count">녹색 = 이동선택</div></div><div class="jm-multi-help">2명일 때만 이동/교환인지 팀설정인지 선택합니다. 1명·3명·4명은 자동으로 이동/교환입니다.</div><div class="jm-multi-actions"><button type="button" class="jm-do-move">이동/교환</button><button type="button" class="jm-do-team" '+(canTeam?'':'disabled')+'>팀설정</button><button type="button" class="jm-do-cancel">취소</button></div>';
    p.querySelector('.jm-do-move').onclick=function(e){e.stopPropagation();phase='target';targets=[];targetKind='';renderPanel();};
    p.querySelector('.jm-do-team').onclick=function(e){e.stopPropagation();if(canTeam)saveTeam(selected.slice());};
    p.querySelector('.jm-do-cancel').onclick=function(e){e.stopPropagation();reset();};
  }
  async function saveTeam(ids){try{if(ids.length!==2)throw new Error('팀설정은 2명 선택일 때만 사용할 수 있습니다.');var loc=locate(ids[0]);if(!loc||!samePlace(ids))throw new Error('같은 대기번호 또는 같은 코트의 2명만 팀설정할 수 있습니다.');var st=await rpc('getPublicState',[null]);var existing=Array.isArray(st&&st.tempPairs)?st.tempPairs.slice():[];existing=existing.filter(function(p){var all=tempIds(p);return !ids.some(function(id){return all.indexOf(String(id))>=0;});});existing.push({members:ids.map(String),pairA:ids.map(String),pairB:[],zone:loc.type,createdAt:Date.now()});var saved=await rpc('setTempPairs',[null,existing]);absorb(saved||{});ids.forEach(function(id){yellow[String(id)]=1;});reset();renderYellow();toast('2명 팀설정 완료',false);}catch(e){toast(String(e&&e.message||e||'팀설정 실패'),true);}}
  function emptyTarget(el){if(!el)return null;var raw=String(el.getAttribute('onclick')||'');var m=raw.match(/handleEmptySlotTap\(['\"]([^'\"]+)['\"],['\"]([^'\"]+)['\"],\s*(\d+)/);if(!m)return null;var type=String(m[1]),idx=String(m[2]);return {kind:'empty',type:type,key:type==='wait'?String(Number(idx)+1):idx,slotIndex:Number(m[3]),el:el,id:'e|'+type+'|'+idx+'|'+m[3]};}
  async function executeSwap(src,dst){try{await rpc('swapMembers',[null,src.map(String),dst.map(String)]);reset();if(typeof renderState==='function')renderState();toast(src.length+'명 교환 완료',false);}catch(e){toast(String(e&&e.message||e||'교환 실패'),true);}}
  async function executeMove(){var src=selected.slice(),dst=targets.slice();if(src.length!==dst.length)return;try{if(targetKind==='member'){await rpc('swapMembers',[null,src,dst.map(function(t){return String(t.id);})]);}else{for(var i=0;i<src.length;i++){var t=dst[i];await rpc('moveOrSwapMember',[null,String(src[i]),String(t.type),String(t.type==='wait'?Number(t.key)-1:t.key),'']);}}reset();if(typeof renderState==='function')renderState();toast(src.length+'명 이동/교환 완료',false);}catch(e){toast(String(e&&e.message||e||'이동/교환 실패'),true);phase='source';targets=[];targetKind='';renderGreen();renderPanel();}}
  function addTarget(t){if(!t)return;if(targetKind&&targetKind!==t.kind){toast('빈자리와 사람은 섞어서 선택할 수 없습니다.',true);return;}var key=t.kind==='member'?'m|'+t.id:t.id;var at=targets.findIndex(function(x){return (x.kind==='member'?'m|'+x.id:x.id)===key;});if(at>=0){targets.splice(at,1);if(!targets.length)targetKind='';renderGreen();renderPanel();return;}if(targets.length>=selected.length)return;targetKind=t.kind;targets.push(t);renderGreen();renderPanel();if(targets.length===selected.length)executeMove();}
  function beginAutoTarget(t){phase='target';targets=[];targetKind='';addTarget(t);}
  function onClick(event){if(event.button>0)return;if(event.target&&event.target.closest&&event.target.closest('#jm-admin-multi-action'))return;ensureStyle();
    if(phase==='target'){
      var ee=event.target&&event.target.closest&&event.target.closest('.quick-empty-slot,.person.empty');if(ee&&ee.closest('#adminApp')){var et=emptyTarget(ee);if(et){event.preventDefault();event.stopPropagation();if(event.stopImmediatePropagation)event.stopImmediatePropagation();addTarget(et);return;}}
      var tc=card(event.target);if(tc){var tid=idOf(tc);if(!tid||selected.indexOf(tid)>=0)return;event.preventDefault();event.stopPropagation();if(event.stopImmediatePropagation)event.stopImmediatePropagation();addTarget({kind:'member',id:tid});return;}return;
    }
    // Movement-only counts (1,3,4): tapping an empty destination starts movement immediately.
    var sourceEmpty=event.target&&event.target.closest&&event.target.closest('.quick-empty-slot,.person.empty');
    if(sourceEmpty&&sourceEmpty.closest('#adminApp')&&selected.length&&selected.length!==2){var sourceEt=emptyTarget(sourceEmpty);if(sourceEt){event.preventDefault();event.stopPropagation();if(event.stopImmediatePropagation)event.stopImmediatePropagation();beginAutoTarget(sourceEt);return;}}
    if(event.target&&event.target.closest&&event.target.closest('button,input,textarea,select,a,[role="button"]'))return;
    var c=card(event.target);if(!c)return;var id=idOf(c);if(!id)return;var loc=locate(id);if(!loc)return;
    event.preventDefault();event.stopPropagation();if(event.stopImmediatePropagation)event.stopImmediatePropagation();
    var at=selected.indexOf(id);if(at>=0){selected.splice(at,1);if(!selected.length)group=null;renderGreen();renderPanel();return;}
    if(!selected.length){selected=[id];group=signature(id);renderGreen();renderPanel();return;}
    var same=signature(id)===group;
    if(same){
      if(selected.length<4){selected.push(id);renderGreen();renderPanel();return;}
      toast('한 번에 최대 4명까지 선택할 수 있습니다.',true);return;
    }
    // One selected member moves/swaps immediately without any choice popup.
    if(selected.length===1){var left=selected[0];renderGreen();executeSwap([left],[id]);return;}
    // Three/four selected members are movement-only. A different-location tap
    // becomes the first destination automatically, with no move/team popup.
    if(selected.length===3||selected.length===4){beginAutoTarget({kind:'member',id:id});return;}
    // Exactly two selected members intentionally keep the decision popup.
    toast('2명 선택 시 이동/교환 또는 팀설정을 먼저 선택하세요.',false);
  }
  async function refreshTeams(){try{var s=await rpc('getPublicState',[null]);absorb(s);}catch(_){} }
  function watch(){var a=app();if(!a){setTimeout(watch,120);return;}ensureStyle();if(!a.__jmV2053Observer){var busy=false;a.__jmV2053Observer=new MutationObserver(function(){if(busy)return;busy=true;(window.requestAnimationFrame||setTimeout)(function(){busy=false;renderGreen();renderYellow();},16);});a.__jmV2053Observer.observe(a,{childList:true,subtree:true});}refreshTeams();}
  ensureStyle();window.addEventListener('click',onClick,true);if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',watch,{once:true});else setTimeout(watch,0);
})();