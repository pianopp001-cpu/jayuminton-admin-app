(function installJayumintonAdminCardInteractionV2043(){
  'use strict';
  if(typeof IS_ADMIN==='undefined'||!IS_ADMIN||window.__JAYUMINTON_ADMIN_CARD_INTERACTION_V2043__)return;
  window.__JAYUMINTON_ADMIN_CARD_INTERACTION_V2043__=true;
  var CARD_SELECTOR='.member,.person,.quick-member,.member-card,.member-item,.wait-card,.wait-item,.player-card,.court-player,[data-member-id],[data-memberid],[data-player-id]';
  var moveSelection=null,dialogOpen=false,bypass=false;

  function ensureStyle(){
    if(document.getElementById('jayuminton-admin-card-interaction-v2043-style'))return;
    var style=document.createElement('style');style.id='jayuminton-admin-card-interaction-v2043-style';
    style.textContent='#adminApp .jm-move-selected{box-shadow:0 0 0 4px #16a34a!important}#adminApp .jm-temp-pair,#adminApp .has-member-team.jm-temp-pair,#adminApp .member.jm-temp-pair{box-shadow:0 0 0 4px #d4a017!important}.jm-team-confirm-backdrop{position:fixed;inset:0;z-index:2147483646;background:rgba(15,23,42,.28);display:flex;align-items:center;justify-content:center;padding:24px;backdrop-filter:blur(2px)}.jm-team-confirm{width:min(360px,92vw);background:#fff;border-radius:18px;padding:22px 20px 18px;box-shadow:0 20px 60px rgba(15,23,42,.28);text-align:center;font-family:inherit}.jm-team-confirm-title{font-size:20px;font-weight:800;color:#111827;margin:0 0 8px}.jm-team-confirm-sub{font-size:14px;line-height:1.45;color:#64748b;margin:0 0 18px}.jm-team-confirm-actions{display:grid;grid-template-columns:1fr 1fr;gap:10px}.jm-team-confirm button{border:0;border-radius:12px;padding:13px 10px;font-size:15px;font-weight:800}.jm-team-confirm .jm-team-yes{background:#d4a017;color:#fff}.jm-team-confirm .jm-team-no{background:#ecfdf5;color:#15803d;border:1px solid #bbf7d0}';
    (document.head||document.documentElement).appendChild(style);
  }
  function memberCard(target){if(!target||!target.closest)return null;var card=target.closest(CARD_SELECTOR);return card&&card.closest('#adminApp')?card:null;}
  function cardId(card){if(!card)return '';var attrs=['data-member-id','data-memberid','data-player-id','data-id','data-member'];for(var i=0;i<attrs.length;i++){var v=card.getAttribute&&card.getAttribute(attrs[i]);if(v)return String(v);}var nested=card.querySelector&&card.querySelector('[data-member-id],[data-memberid],[data-player-id],[data-id],[data-member]');if(nested){for(var j=0;j<attrs.length;j++){var n=nested.getAttribute(attrs[j]);if(n)return String(n);}}var raw=String(card.getAttribute&&card.getAttribute('onclick')||''),uuid=raw.match(/[0-9a-f]{8}-[0-9a-f-]{27,}/i);if(uuid)return uuid[0];var q=raw.match(/['\"]([^'\"]{2,100})['\"]/);return q?String(q[1]):'';}
  function uniqueCards(root){var found={};if(!root||!root.querySelectorAll)return [];Array.prototype.forEach.call(root.querySelectorAll(CARD_SELECTOR),function(el){var c=memberCard(el)||el,id=cardId(c);if(id&&!found[id])found[id]=c;});return Object.keys(found).map(function(id){return {id:id,card:found[id]};});}
  function inferZone(node){for(var cur=node,depth=0;cur&&depth<9;cur=cur.parentElement,depth++){for(var i=0;i<3;i++){var ca=['data-court','data-court-no','data-court-number'][i];if(cur.getAttribute&&cur.getAttribute(ca)!=null)return 'court';var wa=['data-wait','data-wait-no','data-wait-group'][i];if(cur.getAttribute&&cur.getAttribute(wa)!=null)return 'wait';}var s=String((cur.id||'')+' '+(typeof cur.className==='string'?cur.className:''));if(/court|코트/i.test(s))return 'court';if(/wait|대기/i.test(s))return 'wait';}return '';}
  function compactGroup(card){for(var node=card&&card.parentElement,depth=0;node&&depth<9;node=node.parentElement,depth++){var zone=inferZone(node),items=uniqueCards(node);if(zone&&items.length>=2&&items.length<=4&&items.some(function(x){return x.id===cardId(card);})){return {node:node,zone:zone};}}return null;}
  function clearGreen(){var app=document.getElementById('adminApp');if(app)Array.prototype.forEach.call(app.querySelectorAll('.jm-move-selected'),function(el){el.classList.remove('jm-move-selected');});}
  function renderGreen(){clearGreen();if(!moveSelection)return;var app=document.getElementById('adminApp');if(!app)return;Array.prototype.forEach.call(app.querySelectorAll(CARD_SELECTOR),function(el){var c=memberCard(el)||el;if(cardId(c)===moveSelection.id)c.classList.add('jm-move-selected');});}
  function setMove(card,id){moveSelection={id:String(id),group:compactGroup(card)};renderGreen();}
  function clearMove(){moveSelection=null;renderGreen();}
  function toast(text,bad){var old=document.getElementById('jm-admin-card-toast-v2043');if(old)old.remove();var t=document.createElement('div');t.id='jm-admin-card-toast-v2043';t.textContent=String(text||'');t.style.cssText='position:fixed;left:50%;bottom:28px;transform:translateX(-50%);z-index:2147483647;padding:10px 14px;border-radius:12px;background:'+(bad?'#991b1b':'#111827')+';color:#fff;font-size:14px;font-weight:800;box-shadow:0 8px 26px rgba(0,0,0,.22)';document.body.appendChild(t);setTimeout(function(){t.remove();},1600);}
  function rpc(name,args,ok,fail){var run=window.google&&window.google.script&&window.google.script.run;if(!run){if(fail)fail(new Error('서버 연결을 찾을 수 없습니다.'));return;}var chain=run.withSuccessHandler(function(r){if(ok)ok(r);}).withFailureHandler(function(e){if(fail)fail(e);});chain[name].apply(chain,args);}
  function saveTeam(first,second){
    rpc('getPublicState',[null],function(state){
      var existing=Array.isArray(state&&state.tempPairs)?state.tempPairs.slice():[];
      existing=existing.filter(function(p){var ids=(Array.isArray(p.pairA)?p.pairA:[]).concat(Array.isArray(p.pairB)?p.pairB:[]).map(String);return ids.indexOf(first.id)<0&&ids.indexOf(second.id)<0;});
      existing.push({pairA:[first.id,second.id],pairB:[],zone:first.group.zone,createdAt:Date.now()});
      rpc('setTempPairs',[null,existing],function(){clearMove();if(typeof window.__JM_RENDER_TEMP_PAIRS__==='function')window.__JM_RENDER_TEMP_PAIRS__();setTimeout(function(){if(typeof window.__JM_RENDER_TEMP_PAIRS__==='function')window.__JM_RENDER_TEMP_PAIRS__();},80);toast('같은 팀으로 표시했습니다.',false);},function(e){toast(String(e&&e.message||e||'팀 설정에 실패했습니다.'),true);});
    },function(e){toast(String(e&&e.message||e||'현재 팀 정보를 불러오지 못했습니다.'),true);});
  }
  function openDialog(first,second){if(dialogOpen)return;dialogOpen=true;var b=document.createElement('div');b.className='jm-team-confirm-backdrop';b.innerHTML='<div class="jm-team-confirm" role="dialog" aria-modal="true"><div class="jm-team-confirm-title">팀 설정하시겠습니까?</div><div class="jm-team-confirm-sub">팀 설정은 진한 노란색 테두리로 표시됩니다.<br>아니오를 누르면 기존 이동·교환 선택을 유지합니다.</div><div class="jm-team-confirm-actions"><button type="button" class="jm-team-no">아니오</button><button type="button" class="jm-team-yes">팀 설정</button></div></div>';function close(){dialogOpen=false;b.remove();}b.querySelector('.jm-team-no').addEventListener('click',function(){close();renderGreen();});b.querySelector('.jm-team-yes').addEventListener('click',function(){close();saveTeam(first,second);});b.addEventListener('click',function(e){if(e.target===b){close();renderGreen();}});document.body.appendChild(b);}
  function onClick(event){
    if(bypass||dialogOpen||event.button>0)return;
    if(event.target&&event.target.closest&&event.target.closest('button,input,textarea,select,a,[role="button"]'))return;
    var card=memberCard(event.target);
    if(!card){if(moveSelection&&event.target&&event.target.closest&&event.target.closest('#adminApp'))setTimeout(clearMove,250);return;}
    var id=cardId(card);if(!id)return;
    var group=compactGroup(card);
    if(!moveSelection){setMove(card,id);return;}
    if(moveSelection.id===String(id)){setTimeout(clearMove,0);return;}
    var first={id:moveSelection.id,group:moveSelection.group},second={id:String(id),group:group};
    if(first.group&&second.group&&first.group.node===second.group.node){event.preventDefault();event.stopPropagation();if(event.stopImmediatePropagation)event.stopImmediatePropagation();openDialog(first,second);return;}
    setTimeout(clearMove,250);
  }
  function watch(){var app=document.getElementById('adminApp');if(!app||app.__jmV2043Observer)return;var pending=false;app.__jmV2043Observer=new MutationObserver(function(){if(pending)return;pending=true;(window.requestAnimationFrame||setTimeout)(function(){pending=false;renderGreen();},16);});app.__jmV2043Observer.observe(app,{childList:true,subtree:true});}
  ensureStyle();window.addEventListener('click',onClick,true);if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){ensureStyle();watch();},{once:true});else setTimeout(watch,0);
})();
