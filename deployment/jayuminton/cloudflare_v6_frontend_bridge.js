(function installJayumintonCloudflareV6Bridge(){
  'use strict';
  var ENDPOINT='https://jayuminton-state.pianopp001.workers.dev/api/compat/rpc';
  var TEMP_PAIR_KEY='jayuminton_admin_temp_pair_sides_v1';
  var TEMP_PAIR_COLORS=['#7c3aed','#059669','#ea580c','#0891b2','#be123c','#4f46e5','#65a30d','#c026d3'];

  function storedToken(){
    try {
      if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return String(localStorage.getItem('jayuminton_admin_session_v1')||'');
      return String(localStorage.getItem('jayuminton_member_session_token_v1')||localStorage.getItem('jayuminton_member_session_token_v164')||'');
    } catch (_) { return ''; }
  }
  function loadTempPairs(){
    try{
      var value=JSON.parse(localStorage.getItem(TEMP_PAIR_KEY)||'[]');
      return Array.isArray(value)?value.filter(function(x){return x&&Array.isArray(x.pairA)&&x.pairA.length===2&&Array.isArray(x.pairB)&&x.pairB.length===2&&(x.zone==='wait'||x.zone==='court');}):[];
    }catch(_){return [];}
  }
  function saveTempPairs(value){try{localStorage.setItem(TEMP_PAIR_KEY,JSON.stringify(Array.isArray(value)?value:[]));}catch(_) {}}
  function zoneOfState(state,id){
    id=String(id||'');if(!state||!id)return '';
    var courts=state.courts||{};
    for(var no in courts){if(Array.isArray(courts[no])&&courts[no].map(String).indexOf(id)>=0)return 'court';}
    var waits=Array.isArray(state.waitGroups)?state.waitGroups:[];
    for(var i=0;i<waits.length;i++){if(Array.isArray(waits[i])&&waits[i].map(String).indexOf(id)>=0)return 'wait';}
    return '';
  }
  function reconcileTempPairs(state){
    if(typeof IS_ADMIN==='undefined'||!IS_ADMIN||!state)return;
    var old=loadTempPairs(),next=[];
    old.forEach(function(group){
      var ids=group.pairA.concat(group.pairB);
      if(ids.every(function(id){return zoneOfState(state,id)===group.zone;}))next.push(group);
    });
    if(JSON.stringify(old)!==JSON.stringify(next))saveTempPairs(next);
    if(typeof window.__JM_RENDER_TEMP_PAIRS__==='function')setTimeout(window.__JM_RENDER_TEMP_PAIRS__,0);
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
      if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN&&packet.result){
        var candidate=packet.result.state&&typeof packet.result.state==='object'?packet.result.state:packet.result;
        if(candidate&&candidate.courts&&candidate.waitGroups)reconcileTempPairs(candidate);
      }
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
    var pendingPair=null;
    var cardSelector='.member,.person,.quick-member,.member-card,.member-item,.wait-card,.wait-item,.player-card,.court-player,[data-member-id],[data-memberid],[data-player-id]';

    function installAdminTeamSafetyStyle(){
      if(document.getElementById('jayuminton-admin-team-safety-v2037'))return;
      var style=document.createElement('style');
      style.id='jayuminton-admin-team-safety-v2037';
      style.textContent='#adminApp .member-team-badge,#adminApp .jm-team-badge,#adminApp .team-badge,#adminApp .team-label,#adminApp [data-team-label]{display:none!important;visibility:hidden!important;width:0!important;height:0!important;min-width:0!important;max-width:0!important;margin:0!important;padding:0!important;border:0!important;overflow:hidden!important;pointer-events:none!important}#adminApp .jm-team-bottom-label{display:block!important;visibility:visible!important;width:100%!important;height:auto!important;min-width:0!important;max-width:none!important;margin:3px 0 0!important;padding:0!important;border:0!important;overflow:visible!important;position:static!important;float:none!important;clear:both!important;text-align:left!important;font-size:9px!important;font-weight:900!important;line-height:1.15!important;white-space:nowrap!important;color:var(--member-team-color)!important;pointer-events:none!important}#adminApp .has-member-team{position:relative!important;border:2px solid var(--member-team-color)!important;outline:2px solid var(--member-team-color)!important;outline-offset:-5px!important;box-shadow:none!important;overflow:visible!important;height:auto!important;min-height:0!important;padding-bottom:5px!important;background-clip:padding-box!important}#adminApp .member-card,#adminApp .member-item,#adminApp .wait-card,#adminApp .wait-item,#adminApp .player-card,#adminApp .court-player,#adminApp .member,#adminApp .person,#adminApp .quick-member{height:auto!important;min-height:0!important;max-height:none!important;overflow:visible!important}#adminApp .member-card .member-info,#adminApp .member-card .member-meta,#adminApp .member-card .member-detail,#adminApp .member-card .member-sub,#adminApp .member-card .member-memo,#adminApp .member-item .member-info,#adminApp .member-item .member-meta,#adminApp .member-item .member-detail,#adminApp .member-item .member-sub,#adminApp .member-item .member-memo,#adminApp .wait-card .member-info,#adminApp .wait-card .member-meta,#adminApp .wait-card .member-detail,#adminApp .wait-card .member-sub,#adminApp .wait-card .member-memo,#adminApp .wait-item .member-info,#adminApp .wait-item .member-meta,#adminApp .wait-item .member-detail,#adminApp .wait-item .member-sub,#adminApp .wait-item .member-memo{height:auto!important;min-height:0!important;max-height:none!important;overflow:visible!important;white-space:normal!important;line-height:1.25!important;word-break:keep-all!important}#adminApp .jm-temp-pair{box-shadow:0 0 0 3px var(--jm-temp-pair-color)!important}#adminApp .has-member-team.jm-temp-pair{box-shadow:0 0 0 3px var(--jm-temp-pair-color)!important}#adminApp .jm-temp-pair-pending{box-shadow:0 0 0 2px #111827!important}';
      (document.head||document.documentElement).appendChild(style);
    }
    function normalizeTeamText(value){
      var text=String(value||'').replace(/\s+/g,'').trim();
      if(/^TEAM\d+$/i.test(text))text=text.replace(/^TEAM/i,'팀');
      return /^팀\d+$/.test(text)?text:'';
    }
    function moveAdminTeamLabels(root){
      var scope=root&&root.querySelectorAll?root:document;
      var cards=scope.querySelectorAll('#adminApp '+cardSelector.split(',').join(',#adminApp '));
      for(var i=0;i<cards.length;i++){
        var card=cards[i],teamText=normalizeTeamText(card.getAttribute('data-jm-team-text'));
        var nodes=card.querySelectorAll('span,div,small,b,strong,em,i,label');
        for(var j=0;j<nodes.length;j++){
          var node=nodes[j];if(node.classList&&node.classList.contains('jm-team-bottom-label'))continue;
          var found=normalizeTeamText(node.textContent||node.getAttribute('data-team-label'));
          if(found){if(!teamText)teamText=found;node.textContent='';node.style.setProperty('display','none','important');node.setAttribute('aria-hidden','true');}
        }
        if(teamText){
          card.classList.add('has-member-team');
          card.setAttribute('data-jm-team-text',teamText);
          card.style.setProperty('box-shadow','none','important');
          card.style.setProperty('border','2px solid var(--member-team-color)','important');
          card.style.setProperty('outline','2px solid var(--member-team-color)','important');
          card.style.setProperty('outline-offset','-5px','important');
          var bottom=card.querySelector('.jm-team-bottom-label');
          if(!bottom){bottom=document.createElement('small');bottom.className='jm-team-bottom-label';}
          if(bottom.textContent!==teamText)bottom.textContent=teamText;
          if(bottom.parentElement!==card||card.lastElementChild!==bottom)card.appendChild(bottom);
        }
      }
    }
    function cardMemberId(card){
      if(!card)return '';
      var attrs=['data-member-id','data-memberid','data-player-id','data-id','data-member'];
      for(var i=0;i<attrs.length;i++){var v=card.getAttribute&&card.getAttribute(attrs[i]);if(v)return String(v);}
      var nested=card.querySelector&&card.querySelector('[data-member-id],[data-memberid],[data-player-id],[data-id],[data-member]');
      if(nested){for(var j=0;j<attrs.length;j++){var nv=nested.getAttribute(attrs[j]);if(nv)return String(nv);}}
      var raw=String(card.getAttribute&&card.getAttribute('onclick')||'');
      var uuid=raw.match(/[0-9a-f]{8}-[0-9a-f-]{27,}/i);if(uuid)return uuid[0];
      var quoted=raw.match(/['\"]([^'\"]{2,100})['\"]/);return quoted?String(quoted[1]):'';
    }
    function memberCard(target){
      if(!target||!target.closest)return null;
      var card=target.closest(cardSelector);return card&&card.closest('#adminApp')?card:null;
    }
    function inferZone(node){
      for(var cur=node,depth=0;cur&&depth<9;cur=cur.parentElement,depth++){
        var attrs=['data-court','data-court-no','data-court-number'];
        for(var i=0;i<attrs.length;i++){if(cur.getAttribute&&cur.getAttribute(attrs[i])!=null)return 'court';}
        attrs=['data-wait','data-wait-no','data-wait-group'];
        for(var j=0;j<attrs.length;j++){if(cur.getAttribute&&cur.getAttribute(attrs[j])!=null)return 'wait';}
        var ident=String((cur.id||'')+' '+(typeof cur.className==='string'?cur.className:''));
        if(/court|코트/i.test(ident))return 'court';
        if(/wait|대기/i.test(ident))return 'wait';
      }
      return '';
    }
    function uniqueCards(root){
      var map={};if(!root||!root.querySelectorAll)return [];
      Array.prototype.forEach.call(root.querySelectorAll(cardSelector),function(el){
        var card=memberCard(el)||el,id=cardMemberId(card);if(id&&!map[id])map[id]=card;
      });
      return Object.keys(map).map(function(id){return {id:id,card:map[id]};});
    }
    function groupForCard(card){
      for(var node=card&&card.parentElement,depth=0;node&&depth<9;node=node.parentElement,depth++){
        var zone=inferZone(node);if(!zone)continue;
        var items=uniqueCards(node);
        if(items.length===4&&items.some(function(x){return x.card===card||x.card.contains(card)||card.contains(x.card);})){return {zone:zone,node:node,items:items};}
      }
      return null;
    }
    function renderTempPairs(){
      var app=document.getElementById('adminApp');if(!app)return;
      Array.prototype.forEach.call(app.querySelectorAll('.jm-temp-pair,.jm-temp-pair-pending'),function(card){card.classList.remove('jm-temp-pair','jm-temp-pair-pending');card.style.removeProperty('--jm-temp-pair-color');});
      loadTempPairs().forEach(function(group,index){
        [[group.pairA,TEMP_PAIR_COLORS[(index*2)%TEMP_PAIR_COLORS.length]],[group.pairB,TEMP_PAIR_COLORS[(index*2+1)%TEMP_PAIR_COLORS.length]]].forEach(function(side){
          side[0].forEach(function(id){
            Array.prototype.forEach.call(app.querySelectorAll(cardSelector),function(el){var card=memberCard(el)||el;if(cardMemberId(card)===String(id)){card.classList.add('jm-temp-pair');card.style.setProperty('--jm-temp-pair-color',side[1]);}});
          });
        });
      });
      if(pendingPair&&pendingPair.card){pendingPair.card.classList.add('jm-temp-pair-pending');}
    }
    window.__JM_RENDER_TEMP_PAIRS__=renderTempPairs;
    function recordTempPair(first,second,group){
      var ids=group.items.map(function(x){return x.id;});
      var pairA=[first.id,second.id],pairB=ids.filter(function(id){return pairA.indexOf(id)<0;});
      if(pairB.length!==2)return;
      var old=loadTempPairs().filter(function(saved){var all=saved.pairA.concat(saved.pairB);return !ids.some(function(id){return all.indexOf(id)>=0;});});
      old.push({pairA:pairA,pairB:pairB,zone:group.zone,createdAt:Date.now()});saveTempPairs(old);pendingPair=null;renderTempPairs();
    }
    function handlePairClick(event){
      if(event.defaultPrevented||event.button>0)return;
      if(event.target&&event.target.closest&&event.target.closest('button,input,textarea,select,a,[role="button"]'))return;
      var card=memberCard(event.target);if(!card)return;
      var group=groupForCard(card);if(!group)return;
      var id=cardMemberId(card);if(!id)return;
      if(!pendingPair||pendingPair.zone!==group.zone||pendingPair.node!==group.node){pendingPair={id:id,card:card,zone:group.zone,node:group.node};renderTempPairs();return;}
      if(pendingPair.id===id){pendingPair=null;renderTempPairs();return;}
      var first={id:pendingPair.id,card:pendingPair.card};recordTempPair(first,{id:id,card:card},group);
    }
    function watchAdminTeamText(){
      moveAdminTeamLabels(document);renderTempPairs();
      var app=document.getElementById('adminApp');if(!app||app.__jmTeamTextObserver)return;
      var scheduled=false;
      app.__jmTeamTextObserver=new MutationObserver(function(){if(scheduled)return;scheduled=true;setTimeout(function(){scheduled=false;moveAdminTeamLabels(app);renderTempPairs();},0);});
      app.__jmTeamTextObserver.observe(app,{childList:true,subtree:true,characterData:true});
      if(!app.__jmPairClickBound){app.__jmPairClickBound=true;app.addEventListener('click',handlePairClick,true);}
    }
    function loginBox(){return document.getElementById('adminLoginBox');}
    function adminApp(){return document.getElementById('adminApp');}
    function hideApp(){var a=adminApp(),b=loginBox();if(a){a.classList.add('hidden');a.hidden=true;a.style.setProperty('display','none','important');}if(b){b.classList.remove('hidden');b.hidden=false;b.removeAttribute('hidden');b.style.setProperty('display','block','important');}}
    function revealApp(){var a=adminApp(),b=loginBox();if(a){a.hidden=false;a.removeAttribute('hidden');a.style.removeProperty('display');a.classList.remove('hidden');watchAdminTeamText();}if(b){b.classList.add('hidden');b.hidden=true;b.style.setProperty('display','none','important');}}
    function ensureStatus(){var box=loginBox();if(!box||document.getElementById('adminCloudflareLoginStatus'))return;var el=document.createElement('div');el.id='adminCloudflareLoginStatus';el.setAttribute('role','status');el.setAttribute('aria-live','polite');el.style.cssText='margin-top:10px;font-size:13px;font-weight:700;text-align:center';box.appendChild(el);}
    function status(text,isError){var el=document.getElementById('adminCloudflareLoginStatus');if(el){el.textContent=String(text||'');el.style.color=isError?'#b42318':'#667085';}}
    function reset(){var b=document.getElementById('adminCloudflareLoginButton');if(b){b.disabled=false;b.textContent='로그인';}}
    function clearAdminSession(){try{localStorage.removeItem('jayuminton_admin_session_v1');}catch(_) {}}
    function resumeSavedSession(){var token=storedToken();if(!token)return false;status('저장된 관리자 인증으로 연결하고 있습니다.',false);if(typeof window.openAdminApp!=='function'){clearAdminSession();hideApp();return false;}Promise.resolve(window.openAdminApp(token)).then(function(){installAdminTeamSafetyStyle();revealApp();status('',false);}).catch(function(){clearAdminSession();hideApp();status('관리자 PIN을 한 번 입력해 주세요.',false);});return true;}
    function submit(event){if(event){event.preventDefault();event.stopPropagation();}var input=document.getElementById('adminPinInput'),pin=String(input&&input.value||'').trim();if(!pin){status('관리자 PIN을 입력하세요.',true);return;}var b=document.getElementById('adminCloudflareLoginButton');if(b){b.disabled=true;b.textContent='확인 중…';}status('관리자 서버에 연결하고 있습니다.',false);invoke('createAdminSession',[pin],function(result){if(!result||!result.ok){status('관리자 PIN이 틀렸습니다.',true);reset();return;}var token=String(result.token||'');try{localStorage.setItem('jayuminton_admin_session_v1',token);}catch(_){}if(typeof window.openAdminApp!=='function'){status('관리자 화면 초기화 함수가 없습니다.',true);reset();return;}Promise.resolve(window.openAdminApp(token)).then(function(){installAdminTeamSafetyStyle();revealApp();status('',false);reset();}).catch(function(error){hideApp();status(String(error&&error.message||error||'관리자 화면을 불러오지 못했습니다.'),true);reset();});},function(error){hideApp();status(String(error&&error.message||error||'서버에 연결할 수 없습니다.'),true);reset();});}
    function bind(){hideApp();ensureStatus();installAdminTeamSafetyStyle();var box=loginBox(),b=document.getElementById('adminCloudflareLoginButton'),input=document.getElementById('adminPinInput');if(!b&&box)b=box.querySelector('button.primary,button[type="submit"],button');if(b){b.id='adminCloudflareLoginButton';b.type='button';b.removeAttribute('onclick');}if(box){box.style.setProperty('position','relative','important');box.style.setProperty('z-index','2147483000','important');box.style.setProperty('pointer-events','auto','important');}if(b&&!b.__jmBound){b.__jmBound=true;b.style.setProperty('pointer-events','auto','important');b.addEventListener('click',submit);}if(input&&!input.__jmBound){input.__jmBound=true;input.disabled=false;input.readOnly=false;input.setAttribute('inputmode','numeric');input.setAttribute('enterkeyhint','done');input.style.setProperty('pointer-events','auto','important');input.addEventListener('click',function(){try{input.focus();}catch(_) {}});input.addEventListener('keydown',function(event){if(event.key==='Enter'){event.preventDefault();submit();}});}resumeSavedSession();}
    window.__JAYUMINTON_ADMIN_PIN_INPUT_READY__=function(){var i=document.getElementById('adminPinInput'),b=document.getElementById('adminCloudflareLoginButton');return !!(i&&b&&!i.disabled&&!i.readOnly&&i.__jmBound&&b.__jmBound);};
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bind,{once:true});else setTimeout(bind,0);
  }
})();
