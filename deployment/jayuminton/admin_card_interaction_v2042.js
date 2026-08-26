(function installJayumintonAdminCardInteractionV2042(){
  'use strict';
  if(typeof IS_ADMIN==='undefined'||!IS_ADMIN||window.__JAYUMINTON_ADMIN_CARD_INTERACTION_V2042__)return;
  window.__JAYUMINTON_ADMIN_CARD_INTERACTION_V2042__=true;
  var CARD_SELECTOR='.member,.person,.quick-member,.member-card,.member-item,.wait-card,.wait-item,.player-card,.court-player,[data-member-id],[data-memberid],[data-player-id]';
  var moveSelection=null;
  var dialogOpen=false;

  function ensureStyle(){
    if(document.getElementById('jayuminton-admin-card-interaction-v2042-style'))return;
    var style=document.createElement('style');
    style.id='jayuminton-admin-card-interaction-v2042-style';
    style.textContent=[
      '#adminApp .jm-move-selected{box-shadow:0 0 0 4px #16a34a!important;outline:none!important}',
      '#adminApp .jm-temp-pair{box-shadow:0 0 0 4px #d4a017!important}',
      '#adminApp .has-member-team.jm-temp-pair{box-shadow:0 0 0 4px #d4a017!important}',
      '.jm-team-confirm-backdrop{position:fixed;inset:0;z-index:2147483646;background:rgba(15,23,42,.28);display:flex;align-items:center;justify-content:center;padding:24px;backdrop-filter:blur(2px)}',
      '.jm-team-confirm{width:min(360px,92vw);background:#fff;border-radius:18px;padding:22px 20px 18px;box-shadow:0 20px 60px rgba(15,23,42,.28);text-align:center;font-family:inherit}',
      '.jm-team-confirm-title{font-size:20px;font-weight:800;color:#111827;margin:0 0 8px}',
      '.jm-team-confirm-sub{font-size:14px;line-height:1.45;color:#64748b;margin:0 0 18px}',
      '.jm-team-confirm-actions{display:grid;grid-template-columns:1fr 1fr;gap:10px}',
      '.jm-team-confirm button{border:0;border-radius:12px;padding:13px 10px;font-size:15px;font-weight:800;cursor:pointer}',
      '.jm-team-confirm .jm-team-yes{background:#d4a017;color:#fff}',
      '.jm-team-confirm .jm-team-no{background:#ecfdf5;color:#15803d;border:1px solid #bbf7d0}'
    ].join('');
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
    for(var i=0;i<attrs.length;i++){var value=card.getAttribute&&card.getAttribute(attrs[i]);if(value)return String(value);}
    var nested=card.querySelector&&card.querySelector('[data-member-id],[data-memberid],[data-player-id],[data-id],[data-member]');
    if(nested){for(var j=0;j<attrs.length;j++){var nestedValue=nested.getAttribute(attrs[j]);if(nestedValue)return String(nestedValue);}}
    var raw=String(card.getAttribute&&card.getAttribute('onclick')||'');
    var uuid=raw.match(/[0-9a-f]{8}-[0-9a-f-]{27,}/i);if(uuid)return uuid[0];
    var quoted=raw.match(/['\"]([^'\"]{2,100})['\"]/);return quoted?String(quoted[1]):'';
  }
  function uniqueCards(root){
    var found={};
    if(!root||!root.querySelectorAll)return [];
    Array.prototype.forEach.call(root.querySelectorAll(CARD_SELECTOR),function(el){var card=memberCard(el)||el,id=cardId(card);if(id&&!found[id])found[id]=card;});
    return Object.keys(found).map(function(id){return {id:id,card:found[id]};});
  }
  function compactGroup(card){
    for(var node=card&&card.parentElement,depth=0;node&&depth<9;node=node.parentElement,depth++){
      var items=uniqueCards(node);
      if(items.length>=2&&items.length<=4&&items.some(function(x){return x.id===cardId(card);})){return node;}
    }
    return null;
  }
  function clearMoveSelection(){
    var app=document.getElementById('adminApp');
    if(app)Array.prototype.forEach.call(app.querySelectorAll('.jm-move-selected'),function(el){el.classList.remove('jm-move-selected');});
    moveSelection=null;
  }
  function selectForMove(card,id){
    clearMoveSelection();
    moveSelection={id:String(id),card:card,group:compactGroup(card)};
    card.classList.add('jm-move-selected');
  }
  function refreshAdminCards(){
    setTimeout(function(){
      var buttons=document.querySelectorAll('#adminApp button');
      for(var i=0;i<buttons.length;i++){
        if(String(buttons[i].textContent||'').trim()==='새로고침'){try{buttons[i].click();}catch(_){}break;}
      }
    },90);
  }
  function showToast(text,isError){
    var old=document.getElementById('jm-admin-card-toast-v2042');if(old)old.remove();
    var toast=document.createElement('div');toast.id='jm-admin-card-toast-v2042';toast.textContent=String(text||'');
    toast.style.cssText='position:fixed;left:50%;bottom:28px;transform:translateX(-50%);z-index:2147483647;padding:10px 14px;border-radius:12px;background:'+(isError?'#991b1b':'#111827')+';color:#fff;font-size:14px;font-weight:800;box-shadow:0 8px 26px rgba(0,0,0,.22)';
    document.body.appendChild(toast);setTimeout(function(){toast.remove();},1500);
  }
  function rpc(name,args,success,failure){
    var run=window.google&&window.google.script&&window.google.script.run;
    if(!run){if(failure)failure(new Error('서버 연결을 찾을 수 없습니다.'));return;}
    var chain=run.withSuccessHandler(function(result){if(success)success(result);}).withFailureHandler(function(error){if(failure)failure(error);});
    chain[name].apply(chain,args);
  }
  function swapMembers(first,second){
    rpc('swapMembers',[null,[String(first.id)],[String(second.id)]],function(){clearMoveSelection();refreshAdminCards();showToast('두 사람의 위치를 바꿨습니다.',false);},function(error){selectForMove(second.card,second.id);showToast(String(error&&error.message||error||'교환하지 못했습니다.'),true);});
  }
  function recordTeam(first,second){
    var existing=[];
    try{existing=Array.isArray(window.__JM_LAST_TEMP_PAIRS__)?window.__JM_LAST_TEMP_PAIRS__:[];}catch(_){}
    var pair={pairA:[String(first.id),String(second.id)],pairB:[],zone:'wait',createdAt:Date.now()};
    var run=window.google&&window.google.script&&window.google.script.run;
    if(!run)return;
    run.withSuccessHandler(function(){clearMoveSelection();refreshAdminCards();showToast('같은 팀으로 표시했습니다.',false);}).withFailureHandler(function(error){selectForMove(second.card,second.id);showToast(String(error&&error.message||error||'팀 설정에 실패했습니다.'),true);}).setTempPairs(null,existing.concat([pair]));
  }
  function currentTempPairsFromDom(first,second){
    var pairs=[];
    var seen={};
    var app=document.getElementById('adminApp');if(!app)return pairs;
    Array.prototype.forEach.call(app.querySelectorAll('.jm-temp-pair'),function(card){var id=cardId(card);if(!id||seen[id])return;seen[id]=true;});
    return pairs;
  }
  function setTempPairDirect(first,second){
    var run=window.google&&window.google.script&&window.google.script.run;
    if(!run)return;
    var pair={pairA:[String(first.id),String(second.id)],pairB:[],zone:(String((first.group&&first.group.className)||'').match(/court|코트/i)?'court':'wait'),createdAt:Date.now()};
    run.withSuccessHandler(function(saved){clearMoveSelection();refreshAdminCards();showToast('같은 팀으로 표시했습니다.',false);}).withFailureHandler(function(error){selectForMove(second.card,second.id);showToast(String(error&&error.message||error||'팀 설정에 실패했습니다.'),true);}).setTempPairs(null,[pair]);
  }
  function openTeamDialog(first,second){
    if(dialogOpen)return;dialogOpen=true;
    var backdrop=document.createElement('div');backdrop.className='jm-team-confirm-backdrop';
    backdrop.innerHTML='<div class="jm-team-confirm" role="dialog" aria-modal="true"><div class="jm-team-confirm-title">팀 설정하시겠습니까?</div><div class="jm-team-confirm-sub">팀 설정은 진한 노란색 테두리로 표시됩니다.<br>이동 선택을 누르면 녹색 선택 상태로 계속됩니다.</div><div class="jm-team-confirm-actions"><button type="button" class="jm-team-no">이동 선택</button><button type="button" class="jm-team-yes">팀 설정</button></div></div>';
    function close(){dialogOpen=false;backdrop.remove();}
    backdrop.querySelector('.jm-team-no').addEventListener('click',function(){close();selectForMove(second.card,second.id);});
    backdrop.querySelector('.jm-team-yes').addEventListener('click',function(){close();setTempPairDirect(first,second);});
    backdrop.addEventListener('click',function(e){if(e.target===backdrop){close();selectForMove(second.card,second.id);}});
    document.body.appendChild(backdrop);
  }

  function interceptCardClick(event){
    if(dialogOpen||event.button>0)return;
    if(event.target&&event.target.closest&&event.target.closest('button,input,textarea,select,a,[role="button"]'))return;
    var card=memberCard(event.target);if(!card)return;
    var id=cardId(card);if(!id)return;
    event.preventDefault();event.stopPropagation();if(event.stopImmediatePropagation)event.stopImmediatePropagation();
    if(!moveSelection){selectForMove(card,id);return;}
    if(moveSelection.id===String(id)){clearMoveSelection();return;}
    var first={id:moveSelection.id,card:moveSelection.card,group:moveSelection.group};
    var second={id:String(id),card:card,group:compactGroup(card)};
    if(first.group&&second.group&&first.group===second.group){openTeamDialog(first,second);return;}
    swapMembers(first,second);
  }

  ensureStyle();
  window.addEventListener('click',interceptCardClick,true);
  document.addEventListener('DOMContentLoaded',ensureStyle,{once:true});
})();
