from pathlib import Path

WORKER = Path('cloudflare/state-worker/worker.js')
BRIDGE = Path('deployment/jayuminton/cloudflare_v6_frontend_bridge.js')


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 anchor, found {count}')
    return text.replace(old, new, 1)


w = WORKER.read_text()
if "export function setTempPairsMutation" not in w:
    w = replace_once(w,
        "    swapRequests: [], memberMessages: [], actionHistory: [], updatedAt: new Date(0).toISOString(),\n",
        "    swapRequests: [], memberMessages: [], tempPairs: [], actionHistory: [], updatedAt: new Date(0).toISOString(),\n",
        'emptyState tempPairs')

    anchor = "function uniqueIds(value, limit = 4) { return [...new Set((Array.isArray(value) ? value : []).map(String).filter(Boolean))].slice(0, limit); }\n\n"
    helper = r'''function uniqueIds(value, limit = 4) { return [...new Set((Array.isArray(value) ? value : []).map(String).filter(Boolean))].slice(0, limit); }

export function normalizeTempPairs(value) {
  const used = new Set();
  const out = [];
  for (const raw of (Array.isArray(value) ? value : []).slice(-100)) {
    if (!raw || !['wait', 'court'].includes(String(raw.zone))) continue;
    const pairA = uniqueIds(raw.pairA, 2); const pairB = uniqueIds(raw.pairB, 2);
    const ids = [...pairA, ...pairB];
    if (pairA.length !== 2 || pairB.length !== 2 || new Set(ids).size !== 4) continue;
    if (ids.some(id => used.has(id))) continue;
    ids.forEach(id => used.add(id));
    out.push({ pairA, pairB, zone: String(raw.zone), createdAt: Math.max(0, Number(raw.createdAt) || Date.now()) });
  }
  return out;
}

export function reconcileTempPairs(state) {
  state.tempPairs = normalizeTempPairs(state.tempPairs).filter(group => {
    const ids = [...group.pairA, ...group.pairB];
    const first = locationOf(state, ids[0]);
    if (!first || first.type !== group.zone || !['wait', 'court'].includes(first.type)) return false;
    return ids.every(id => {
      const loc = locationOf(state, id);
      return loc && loc.type === first.type && loc.key === first.key;
    });
  });
  return state;
}

function applyTempPairOrdering(state) {
  for (const group of normalizeTempPairs(state.tempPairs)) {
    const ids = [...group.pairA, ...group.pairB];
    const first = locationOf(state, ids[0]);
    if (!first || first.type !== group.zone) continue;
    const target = first.type === 'court' ? state.courts[first.key] : state.waitGroups[Number(first.key) - 1];
    if (!Array.isArray(target) || target.length !== 4 || !ids.every(id => target.includes(id))) continue;
    const ordered = group.zone === 'wait'
      ? [group.pairA[0], group.pairB[0], group.pairA[1], group.pairB[1]]
      : [group.pairA[0], group.pairA[1], group.pairB[0], group.pairB[1]];
    target.splice(0, target.length, ...ordered);
  }
  return state;
}

'''
    w = replace_once(w, anchor, helper, 'worker helpers')
    w = replace_once(w,
        "  state.memberMessages = Array.isArray(state.memberMessages) ? state.memberMessages.slice(-50) : [];\n  state.actionHistory = Array.isArray(state.actionHistory) ? state.actionHistory.slice(-50) : [];\n",
        "  state.memberMessages = Array.isArray(state.memberMessages) ? state.memberMessages.slice(-50) : [];\n  state.tempPairs = normalizeTempPairs(state.tempPairs);\n  state.actionHistory = Array.isArray(state.actionHistory) ? state.actionHistory.slice(-50) : [];\n",
        'normalize tempPairs')
    w = replace_once(w, "  return syncMemberStatuses(state);\n}\n\nfunction locationOf", "  syncMemberStatuses(state);\n  return reconcileTempPairs(state);\n}\n\nfunction locationOf", 'normalize reconcile')
    w = replace_once(w, "export function sendMemberMessageMutation(input, memberIds, message) {\n", r'''export function setTempPairsMutation(input, tempPairs) {
  const state = normalizeState(input);
  state.tempPairs = normalizeTempPairs(tempPairs);
  reconcileTempPairs(state);
  applyTempPairOrdering(state);
  return { state, event: { type: 'temp_pairs_set', tempPairs: state.tempPairs } };
}

export function sendMemberMessageMutation(input, memberIds, message) {
''', 'setTempPairs mutation')
    w = replace_once(w,
        "      else if (action === 'clearBundle') result = clearBundleMutation(current, body.memberIds);\n      else if (action === 'sendMemberMessage')",
        "      else if (action === 'clearBundle') result = clearBundleMutation(current, body.memberIds);\n      else if (action === 'setTempPairs') result = setTempPairsMutation(current, body.tempPairs);\n      else if (action === 'sendMemberMessage')",
        'coordinator setTempPairs')
    admin_names = "const adminNames = new Set(['getCurrentMemberPassword','getSystemStatus','addMember','updateMemberProfile','setMemberStatus','setBundle','clearBundle','sendMemberMessage','deleteMembers','assignMembersToCourt','assignMembersToWaitGroup','smartAssignSelected','finishCourt','swapMembers','swapCourts','swapWaitGroups','moveOrSwapMember','undoLastAction','adjustMemberGames','decreaseSelectedGameCounts','resetSelectedGameCounts','resetAllOperationData','createManualBackup','restoreManualBackup','changeMemberPassword']);"
    admin_names_new = admin_names.replace("'clearBundle','sendMemberMessage'", "'clearBundle','setTempPairs','sendMemberMessage'")
    w = replace_once(w, admin_names, admin_names_new, 'adminNames setTempPairs')
    w = replace_once(w,
        "    else if (name === 'clearBundle') { action = 'clearBundle'; body.memberIds = values[1]; }\n    else if (name === 'sendMemberMessage')",
        "    else if (name === 'clearBundle') { action = 'clearBundle'; body.memberIds = values[1]; }\n    else if (name === 'setTempPairs') { action = 'setTempPairs'; body.tempPairs = values[1]; }\n    else if (name === 'sendMemberMessage')",
        'legacy setTempPairs mapping')
    w = replace_once(w,
        "'setBundle','clearBundle','sendMemberMessage','adjustGames'",
        "'setBundle','clearBundle','setTempPairs','sendMemberMessage','adjustGames'",
        'admin rpc allowed')
WORKER.write_text(w)

b = BRIDGE.read_text()
if "var sharedTempPairs=[];" not in b:
    old_block = r'''  function loadTempPairs(){
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
'''
    new_block = r'''  var sharedTempPairs=[];
  var legacyTempPairsChecked=false;
  function validTempPairs(value){
    return (Array.isArray(value)?value:[]).filter(function(x){
      if(!x||['wait','court'].indexOf(String(x.zone))<0||!Array.isArray(x.pairA)||!Array.isArray(x.pairB)||x.pairA.length!==2||x.pairB.length!==2)return false;
      return new Set(x.pairA.concat(x.pairB).map(String)).size===4;
    }).map(function(x){return {pairA:x.pairA.map(String),pairB:x.pairB.map(String),zone:String(x.zone),createdAt:Number(x.createdAt)||Date.now()};});
  }
  function loadLegacyTempPairs(){try{return validTempPairs(JSON.parse(localStorage.getItem(TEMP_PAIR_KEY)||'[]'));}catch(_){return [];}}
  function loadTempPairs(){return sharedTempPairs.slice();}
  function renderSharedTempPairs(){
    if(typeof document==='undefined'||typeof document.querySelectorAll!=='function')return;
    var selector='.member,.person,.quick-member,.member-card,.member-item,.wait-card,.wait-item,.player-card,.court-player,[data-member-id],[data-memberid],[data-player-id]';
    var attrs=['data-member-id','data-memberid','data-player-id','data-id','data-member'];
    function idOf(card){
      if(!card)return '';
      for(var i=0;i<attrs.length;i++){var v=card.getAttribute&&card.getAttribute(attrs[i]);if(v)return String(v);}
      var nested=card.querySelector&&card.querySelector('[data-member-id],[data-memberid],[data-player-id],[data-id],[data-member]');
      if(nested){for(var j=0;j<attrs.length;j++){var nv=nested.getAttribute(attrs[j]);if(nv)return String(nv);}}
      return '';
    }
    Array.prototype.forEach.call(document.querySelectorAll('.jm-temp-pair'),function(card){card.classList.remove('jm-temp-pair');card.style.removeProperty('--jm-temp-pair-color');});
    loadTempPairs().forEach(function(group,index){
      [[group.pairA,TEMP_PAIR_COLORS[(index*2)%TEMP_PAIR_COLORS.length]],[group.pairB,TEMP_PAIR_COLORS[(index*2+1)%TEMP_PAIR_COLORS.length]]].forEach(function(side){
        Array.prototype.forEach.call(document.querySelectorAll(selector),function(card){var id=idOf(card);if(side[0].indexOf(id)>=0){card.classList.add('jm-temp-pair');card.style.setProperty('--jm-temp-pair-color',side[1]);}});
      });
    });
    if(document.getElementById&&document.createElement&&!document.getElementById('jayuminton-shared-temp-pair-style')){
      var style=document.createElement('style');style.id='jayuminton-shared-temp-pair-style';
      style.textContent='.jm-temp-pair{box-shadow:0 0 0 3px var(--jm-temp-pair-color)!important}.jm-team-bottom-label{display:none!important}';
      (document.head||document.documentElement).appendChild(style);
    }
  }
  window.__JM_RENDER_TEMP_PAIRS__=renderSharedTempPairs;
  function consumeSharedState(state){
    if(!state||typeof state!=='object'||!state.courts||!state.waitGroups)return;
    sharedTempPairs=validTempPairs(state.tempPairs);
    if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN&&!legacyTempPairsChecked){
      legacyTempPairsChecked=true;
      var legacy=loadLegacyTempPairs();
      if(!sharedTempPairs.length&&legacy.length){
        invoke('setTempPairs',[null,legacy],function(saved){try{localStorage.removeItem(TEMP_PAIR_KEY);}catch(_){} consumeSharedState(saved);},function(){});
      }else{try{localStorage.removeItem(TEMP_PAIR_KEY);}catch(_){}}
    }
    setTimeout(renderSharedTempPairs,0);setTimeout(renderSharedTempPairs,80);setTimeout(renderSharedTempPairs,250);
  }
  function persistTempPairs(value,success,failure){invoke('setTempPairs',[null,validTempPairs(value)],success,failure);}
'''
    b = replace_once(b, old_block, new_block, 'bridge shared temp state')
    old_invoke = r'''      if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN&&packet.result){
        var candidate=packet.result.state&&typeof packet.result.state==='object'?packet.result.state:packet.result;
        if(candidate&&candidate.courts&&candidate.waitGroups)reconcileTempPairs(candidate);
      }
      if(typeof success==='function')success(packet.result);
'''
    new_invoke = r'''      if(packet.result){
        var candidate=packet.result.state&&typeof packet.result.state==='object'?packet.result.state:packet.result;
        if(candidate&&candidate.courts&&candidate.waitGroups)consumeSharedState(candidate);
      }
      if(typeof success==='function')success(packet.result);
      setTimeout(renderSharedTempPairs,0);
'''
    b = replace_once(b, old_invoke, new_invoke, 'bridge invoke state consume')
    b = replace_once(b,
        "      old.push({pairA:pairA,pairB:pairB,zone:group.zone,createdAt:Date.now()});saveTempPairs(old);pendingPair=null;renderTempPairs();\n",
        "      old.push({pairA:pairA,pairB:pairB,zone:group.zone,createdAt:Date.now()});persistTempPairs(old,function(saved){consumeSharedState(saved);pendingPair=null;renderTempPairs();},function(){pendingPair=null;renderTempPairs();});\n",
        'bridge record temp pair')
    old_label = r'''          var bottom=card.querySelector('.jm-team-bottom-label');
          if(!bottom){bottom=document.createElement('small');bottom.className='jm-team-bottom-label';}
          if(bottom.textContent!==teamText)bottom.textContent=teamText;
          if(bottom.parentElement!==card||card.lastElementChild!==bottom)card.appendChild(bottom);
'''
    b = replace_once(b, old_label, "          Array.prototype.forEach.call(card.querySelectorAll('.jm-team-bottom-label'),function(bottom){bottom.remove();});\n", 'remove visible team label creator')
    b = b.replace("#adminApp .jm-team-bottom-label{display:block!important;visibility:visible!important;", "#adminApp .jm-team-bottom-label{display:none!important;visibility:hidden!important;")
BRIDGE.write_text(b)
print('SHARED_TEMP_PAIRS_PATCH_OK')
