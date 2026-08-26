(function installJayumintonAdminCardInteractionV2043(){
  'use strict';
  if(typeof IS_ADMIN==='undefined'||!IS_ADMIN||window.__JAYUMINTON_ADMIN_CARD_INTERACTION_V2043__)return;
  window.__JAYUMINTON_ADMIN_CARD_INTERACTION_V2043__=true;
  window.__JAYUMINTON_ADMIN_CARD_VISUAL_FIX_V2044__=true;

  var CARD_SELECTOR='.member,.person,.quick-member,.member-card,.member-item,.wait-card,.wait-item,.player-card,.court-player,[data-member-id],[data-memberid],[data-player-id]';
  var moveSelection=null,dialogOpen=false,tempPairIds={};

  function ensureStyle(){
    if(document.getElementById('jayuminton-admin-card-interaction-v2044-style'))return;
    var style=document.createElement('style');
    style.id='jayuminton-admin-card-interaction-v2044-style';
    style.textContent=''
      +'#adminApp .jm-move-selected{position:relative!important;box-shadow:0 0 0 4px #16a34a!important;outline:2px solid rgba(22,163,74,.18)!important;outline-offset:2px!important;z-index:3!important}'
      +'#adminApp .jm-temp-pair-v2044{position:relative!important;box-shadow:0 0 0 4px #d4a017!important;outline:2px solid rgba(212,160,23,.20)!important;outline-offset:2px!important;z-index:2!important}'
      +'#adminApp .jm-temp-pair,#adminApp .has-member-team.jm-temp-pair,#adminApp .member.jm-temp-pair{box-shadow:0 0 0 4px #d4a017!important}'
      +'.jm-team-confirm-backdrop{position:fixed;inset:0;z-index:2147483646;background:rgba(15,23,42,.38);display:flex;align-items:center;justify-content:center;padding:24px;backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px)}'
      +'.jm-team-confirm{width:min(370px,92vw);background:#fff;border:1px solid rgba(226,232,240,.9);border-radius:24px;padding:24px 22px 20px;box-shadow:0 28px 80px rgba(15,23,42,.30);text-align:center;font-family:inherit;animation:jmTeamPop .16s ease-out}'
      +'@keyframes jmTeamPop{from{opacity:0;transform:translateY(8px) scale(.98)}to{opacity:1;transform:none}}'
      +'.jm-team-confirm-icon{width:50px;height:50px;margin:0 auto 12px;border-radius:16px;display:flex;align-items:center;justify-content:center;background:#fff8db;border:1px solid #fde68a;font-size:25px;line-height:1}'
      +'.jm-team-confirm-title{font-size:20px;font-weight:900;color:#111827;margin:0 0 8px;letter-spacing:-.3px}'
      +'.jm-team-confirm-sub{font-size:13.5px;line-height:1.55;color:#64748b;margin:0 0 20px}'
      +'.jm-team-confirm-actions{display:grid;grid-template-columns:1fr 1fr;gap:10px}'
      +'.jm-team-confirm button{border:0;border-radius:14px;padding:13px 10px;font-size:15px;font-weight:850;min-height:46px;font-family:inherit}'
      +'.jm-team-confirm .jm-team-yes{background:linear-gradient(180deg,#e4b52a,#c9970d);color:#fff;box-shadow:0 6px 16px rgba(201,151,13,.24)}'
      +'.jm-team-confirm .jm-team-no{background:#f0fdf4;color:#15803d;border:1px solid #bbf7d0}'
      +'.jm-team-confirm .jm-team-note{display:inline-flex;align-items:center;gap:5px;margin-top:13px;padding:6px 9px;border-radius:999px;background:#f8fafc;color:#64748b;font-size:11.5px;font-weight:700}';
    (document.head||document.documentElement).appendChild(style);
  }

  function memberCard(target){
    if(!target||!target.closest)return null;
    var card=target.closest(CARD_SELECTOR);
    return card&&card.closest('#adminApp')?card:null;
  }

  function cardId(card){
    if(!card)return '';
    var attrs=['data-member-id','data-memberid','data-player-id','data-id','data-member'];
    for(var i=0;i<attrs.length;i++){
      var v=card.getAttribute&&card.getAttribute(attrs[i]);
      if(v)return String(v);
    }
    var nested=card.querySelector&&card.querySelector('[data-member-id],[data-memberid],[data-player-id],[data-id],[data-member]');
    if(nested){
      for(var j=0;j<attrs.length;j++){
        var n=nested.getAttribute(attrs[j]);
        if(n)return String(n);
      }
    }
    var raw=String(card.getAttribute&&card.getAttribute('onclick')||'');
    var uuid=raw.match(/[0-9a-f]{8}-[0-9a-f-]{27,}/i);
    if(uuid)return uuid[0];
    var q=raw.match(/['\"]([^'\"]{2,100})['\"]/);
    return q?String(q[1]):'';
  }

  function idsInside(root){
    var found={};
    if(!root||!root.querySelectorAll)return [];
    var own=cardId(root);if(own)found[own]=true;
    Array.prototype.forEach.call(root.querySelectorAll(CARD_SELECTOR),function(el){var id=cardId(el);if(id)found[id]=true;});
    return Object.keys(found);
  }

  function inferZone(node){
    for(var cur=node,depth=0;cur&&depth<10;cur=cur.parentElement,depth++){
      var attrsCourt=['data-court','data-court-no','data-court-number'];
      var attrsWait=['data-wait','data-wait-no','data-wait-group'];
      for(var i=0;i<attrsCourt.length;i++)if(cur.getAttribute&&cur.getAttribute(attrsCourt[i])!=null)return 'court';
      for(var j=0;j<attrsWait.length;j++)if(cur.getAttribute&&cur.getAttribute(attrsWait[j])!=null)return 'wait';
      var s=String((cur.id||'')+' '+(typeof cur.className==='string'?cur.className:''));
      if(/court|코트/i.test(s))return 'court';
      if(/wait|대기/i.test(s))return 'wait';
    }
    return '';
  }

  function visualCard(card){
    if(!card)return null;
    var id=cardId(card),node=card,best=card;
    for(var depth=0;node&&node.parentElement&&depth<7;depth++){
      var parent=node.parentElement;
      if(!parent.closest||!parent.closest('#adminApp'))break;
      var ids=idsInside(parent);
      if(ids.length===1&&ids[0]===id){best=parent;node=parent;continue;}
      break;
    }
    return best;
  }

  function compactGroup(card){
    var id=cardId(card);
    for(var node=visualCard(card)&&visualCard(card).parentElement,depth=0;node&&depth<9;node=node.parentElement,depth++){
      var ids=idsInside(node),zone=inferZone(node);
      if(zone&&ids.length>=2&&ids.length<=4&&ids.indexOf(id)>=0){
        ids=ids.map(String).sort();
        return {zone:zone,ids:ids,signature:zone+'|'+ids.join('|')};
      }
    }
    return null;
  }

  function eachVisualForId(id,fn){
    var app=document.getElementById('adminApp');if(!app)return;
    var seen=[];
    Array.prototype.forEach.call(app.querySelectorAll(CARD_SELECTOR),function(el){
      if(cardId(el)!==String(id))return;
      var v=visualCard(el)||el;
      if(seen.indexOf(v)<0){seen.push(v);fn(v);}
    });
  }

  function clearGreen(){
    var app=document.getElementById('adminApp');
    if(app)Array.prototype.forEach.call(app.querySelectorAll('.jm-move-selected'),function(el){el.classList.remove('jm-move-selected');});
  }
  function renderGreen(){
    clearGreen();if(!moveSelection)return;
    eachVisualForId(moveSelection.id,function(v){v.classList.add('jm-move-selected');});
  }
  function setMove(card,id){moveSelection={id:String(id),group:compactGroup(card)};renderGreen();}
  function clearMove(){moveSelection=null;renderGreen();}

  function clearYellowVisual(){
    var app=document.getElementById('adminApp');
    if(app)Array.prototype.forEach.call(app.querySelectorAll('.jm-temp-pair-v2044'),function(el){el.classList.remove('jm-temp-pair-v2044');});
  }
  function renderYellow(){
    clearYellowVisual();
    Object.keys(tempPairIds).forEach(function(id){if(tempPairIds[id])eachVisualForId(id,function(v){v.classList.add('jm-temp-pair-v2044');});});
  }
  function absorbTempPairs(state){
    tempPairIds={};
    var pairs=Array.isArray(state&&state.tempPairs)?state.tempPairs:[];
    pairs.forEach(function(p){
      var ids=[];
      if(Array.isArray(p&&p.pairA))ids=ids.concat(p.pairA);
      if(Array.isArray(p&&p.pairB))ids=ids.concat(p.pairB);
      if(Array.isArray(p&&p.members))ids=ids.concat(p.members);
      ids.map(String).forEach(function(id){if(id)tempPairIds[id]=true;});
    });
    renderYellow();
  }

  function toast(text,bad){
    var old=document.getElementById('jm-admin-card-toast-v2043');if(old)old.remove();
    var t=document.createElement('div');t.id='jm-admin-card-toast-v2043';t.textContent=String(text||'');
    t.style.cssText='position:fixed;left:50%;bottom:28px;transform:translateX(-50%);z-index:2147483647;padding:10px 14px;border-radius:12px;background:'+(bad?'#991b1b':'#111827')+';color:#fff;font-size:14px;font-weight:800;box-shadow:0 8px 26px rgba(0,0,0,.22)';
    document.body.appendChild(t);setTimeout(function(){t.remove();},1600);
  }

  function rpc(name,args,ok,fail){
    var run=window.google&&window.google.script&&window.google.script.run;
    if(!run){if(fail)fail(new Error('서버 연결을 찾을 수 없습니다.'));return;}
    var chain=run.withSuccessHandler(function(r){if(ok)ok(r);}).withFailureHandler(function(e){if(fail)fail(e);});
    chain[name].apply(chain,args);
  }

  function refreshTempPairs(){rpc('getPublicState',[null],function(state){absorbTempPairs(state);},function(){});}

  function saveTeam(first,second){
    rpc('getPublicState',[null],function(state){
      var existing=Array.isArray(state&&state.tempPairs)?state.tempPairs.slice():[];
      existing=existing.filter(function(p){
        var ids=(Array.isArray(p&&p.pairA)?p.pairA:[]).concat(Array.isArray(p&&p.pairB)?p.pairB:[]).concat(Array.isArray(p&&p.members)?p.members:[]).map(String);
        return ids.indexOf(first.id)<0&&ids.indexOf(second.id)<0;
      });
      existing.push({pairA:[first.id,second.id],pairB:[],zone:(first.group&&first.group.zone)||'',createdAt:Date.now()});
      rpc('setTempPairs',[null,existing],function(){
        tempPairIds[first.id]=true;tempPairIds[second.id]=true;
        clearMove();renderYellow();
        if(typeof window.__JM_RENDER_TEMP_PAIRS__==='function')try{window.__JM_RENDER_TEMP_PAIRS__();}catch(_){}
        setTimeout(function(){renderYellow();refreshTempPairs();},120);
        toast('같은 팀으로 표시했습니다.',false);
      },function(e){toast(String(e&&e.message||e||'팀 설정에 실패했습니다.'),true);});
    },function(e){toast(String(e&&e.message||e||'현재 팀 정보를 불러오지 못했습니다.'),true);});
  }

  function openDialog(first,second){
    if(dialogOpen)return;dialogOpen=true;
    var b=document.createElement('div');b.className='jm-team-confirm-backdrop';
    b.innerHTML='<div class="jm-team-confirm" role="dialog" aria-modal="true"><div class="jm-team-confirm-icon">🤝</div><div class="jm-team-confirm-title">같은 팀으로 설정할까요?</div><div class="jm-team-confirm-sub">선택한 두 사람을 같은 팀으로 묶습니다.<br>설정 후 카드에 <b style="color:#b58105">노란색 테두리</b>가 표시됩니다.</div><div class="jm-team-confirm-actions"><button type="button" class="jm-team-no">취소</button><button type="button" class="jm-team-yes">같은 팀 설정</button></div><div class="jm-team-note">● 노란 테두리 = 같은 팀</div></div>';
    function close(){dialogOpen=false;b.remove();}
    b.querySelector('.jm-team-no').addEventListener('click',function(e){e.preventDefault();e.stopPropagation();close();renderGreen();});
    b.querySelector('.jm-team-yes').addEventListener('click',function(e){e.preventDefault();e.stopPropagation();close();saveTeam(first,second);});
    b.addEventListener('click',function(e){if(e.target===b){e.preventDefault();e.stopPropagation();close();renderGreen();}});
    document.body.appendChild(b);
  }

  function onClick(event){
    if(dialogOpen||event.button>0)return;
    if(event.target&&event.target.closest&&event.target.closest('.jm-team-confirm-backdrop'))return;
    if(event.target&&event.target.closest&&event.target.closest('button,input,textarea,select,a,[role="button"]'))return;
    var card=memberCard(event.target);
    if(!card){if(moveSelection&&event.target&&event.target.closest&&event.target.closest('#adminApp'))setTimeout(clearMove,250);return;}
    var id=cardId(card);if(!id)return;
    var group=compactGroup(card);
    if(!moveSelection){
      setMove(card,id);
      setTimeout(function(){renderGreen();renderYellow();},0);
      return; // IMPORTANT: native administrator move/swap click continues untouched.
    }
    if(moveSelection.id===String(id)){setTimeout(clearMove,0);return;}

    var first={id:moveSelection.id,group:moveSelection.group};
    var second={id:String(id),group:group};
    var sameGroup=!!(first.group&&second.group&&first.group.signature===second.group.signature);
    if(!sameGroup&&first.group&&second.group&&first.group.zone===second.group.zone){
      sameGroup=first.group.ids.indexOf(second.id)>=0&&second.group.ids.indexOf(first.id)>=0;
    }
    if(sameGroup){
      event.preventDefault();event.stopPropagation();if(event.stopImmediatePropagation)event.stopImmediatePropagation();
      openDialog(first,second);
      return;
    }

    setTimeout(clearMove,250); // Cross-location move/swap remains owned by the original administrator app.
  }

  function watch(){
    var app=document.getElementById('adminApp');if(!app){setTimeout(watch,120);return;}
    if(app.__jmV2044Observer)return;
    var pending=false;
    app.__jmV2044Observer=new MutationObserver(function(){
      if(pending)return;pending=true;
      (window.requestAnimationFrame||setTimeout)(function(){pending=false;renderGreen();renderYellow();},16);
    });
    app.__jmV2044Observer.observe(app,{childList:true,subtree:true,attributes:true,attributeFilter:['class','data-member-id','data-memberid','data-player-id']});
    refreshTempPairs();
  }

  ensureStyle();
  window.addEventListener('click',onClick,true);
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){ensureStyle();watch();},{once:true});
  else setTimeout(watch,0);
})();
