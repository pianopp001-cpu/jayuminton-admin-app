from pathlib import Path
import re, runpy
runpy.run_path('deployment/jayuminton/patch_shared_temp_pairs_v2.py', run_name='__main__')
wp=Path('cloudflare/state-worker/worker.js'); w=wp.read_text()
w=re.sub(r"    const pairA = uniqueIds\(raw\.pairA, 2\);\n    if \(pairA\.length !== 2 \|\| new Set\(pairA\)\.size !== 2\) continue;\n    if \(pairA\.some\(id => used\.has\(id\)\)\) continue;\n    pairA\.forEach\(id => used\.add\(id\)\);\n    out\.push\(\{ pairA, pairB: \[\], zone: String\(raw\.zone\), createdAt: Math\.max\(0, Number\(raw\.createdAt\) \|\| Date\.now\(\)\) \}\);","    const pairA = uniqueIds(raw.pairA, 2);\n    const pairB = uniqueIds(raw.pairB, 2);\n    const ids = [...pairA, ...pairB];\n    if (pairA.length !== 2 || pairB.length !== 2 || new Set(ids).size !== 4) continue;\n    if (ids.some(id => used.has(id))) continue;\n    ids.forEach(id => used.add(id));\n    out.push({ pairA, pairB, zone: String(raw.zone), createdAt: Math.max(0, Number(raw.createdAt) || Date.now()) });",w,count=1)
w=w.replace('    const ids = group.pairA;\n    const first = locationOf(state, ids[0]);','    const ids = [...group.pairA, ...group.pairB];\n    const first = locationOf(state, ids[0]);',1)
if 'function applyTempPairOrdering(state)' not in w:
    anchor='export function normalizeState(input) {'
    helper="""function applyTempPairOrdering(state) {
  for (const group of normalizeTempPairs(state.tempPairs)) {
    const ids = [...group.pairA, ...group.pairB];
    const first = locationOf(state, ids[0]);
    if (!first || first.type !== group.zone) continue;
    const target = first.type === 'court' ? state.courts[first.key] : state.waitGroups[Number(first.key) - 1];
    if (!Array.isArray(target) || target.length !== 4 || !ids.every(id => target.includes(id))) continue;
    const ordered = group.zone === 'wait' ? [group.pairA[0], group.pairB[0], group.pairA[1], group.pairB[1]] : [group.pairA[0], group.pairA[1], group.pairB[0], group.pairB[1]];
    target.splice(0, target.length, ...ordered);
  }
  return state;
}

"""
    if anchor not in w: raise SystemExit('normalizeState anchor missing')
    w=w.replace(anchor,helper+anchor,1)
w=w.replace("  reconcileTempPairs(state);\n  return { state, event: { type: 'temp_pairs_set'","  reconcileTempPairs(state);\n  applyTempPairOrdering(state);\n  return { state, event: { type: 'temp_pairs_set'",1)
wp.write_text(w)

bp=Path('deployment/jayuminton/cloudflare_v6_frontend_bridge.js'); b=bp.read_text()
b=b.replace("if(!x||['wait','court'].indexOf(String(x.zone))<0||!Array.isArray(x.pairA)||x.pairA.length!==2)return false;\n      return new Set(x.pairA.map(String)).size===2;","if(!x||['wait','court'].indexOf(String(x.zone))<0||!Array.isArray(x.pairA)||!Array.isArray(x.pairB)||x.pairA.length!==2||x.pairB.length!==2)return false;\n      return new Set(x.pairA.concat(x.pairB).map(String)).size===4;")
b=b.replace("}).map(function(x){return {pairA:x.pairA.map(String),pairB:[],zone:String(x.zone),createdAt:Number(x.createdAt)||Date.now()};});","}).map(function(x){return {pairA:x.pairA.map(String),pairB:x.pairB.map(String),zone:String(x.zone),createdAt:Number(x.createdAt)||Date.now()};});")
b=b.replace("var pairA=[first.id,second.id],pairB=[];","var pairA=[first.id,second.id],pairB=ids.filter(function(id){return pairA.indexOf(id)<0;});\n      if(pairB.length!==2)return;")
# Fix both public/common renderer and admin-specific renderer: each temporary pair gets its own solid color.
old_common="var side=[group.pairA,TEMP_PAIR_COLORS[index%TEMP_PAIR_COLORS.length]];\n      Array.prototype.forEach.call(document.querySelectorAll(selector),function(card){var id=idOf(card);if(side[0].indexOf(id)>=0){card.classList.add('jm-temp-pair');if(card.style&&card.style.setProperty)card.style.setProperty('--jm-temp-pair-color',side[1]);}});"
new_common="[[group.pairA,TEMP_PAIR_COLORS[(index*2)%TEMP_PAIR_COLORS.length]],[group.pairB,TEMP_PAIR_COLORS[(index*2+1)%TEMP_PAIR_COLORS.length]]].forEach(function(side){Array.prototype.forEach.call(document.querySelectorAll(selector),function(card){var id=idOf(card);if(side[0].indexOf(id)>=0){card.classList.add('jm-temp-pair');if(card.style&&card.style.setProperty)card.style.setProperty('--jm-temp-pair-color',side[1]);}});});"
b=b.replace(old_common,new_common)
old_admin="var side=[group.pairA,TEMP_PAIR_COLORS[index%TEMP_PAIR_COLORS.length]];\n        side[0].forEach(function(id){\n          Array.prototype.forEach.call(app.querySelectorAll(cardSelector),function(el){var card=memberCard(el)||el;if(cardMemberId(card)===String(id)){card.classList.add('jm-temp-pair');card.style.setProperty('--jm-temp-pair-color',side[1]);}});\n        });"
new_admin="[[group.pairA,TEMP_PAIR_COLORS[(index*2)%TEMP_PAIR_COLORS.length]],[group.pairB,TEMP_PAIR_COLORS[(index*2+1)%TEMP_PAIR_COLORS.length]]].forEach(function(side){\n        side[0].forEach(function(id){Array.prototype.forEach.call(app.querySelectorAll(cardSelector),function(el){var card=memberCard(el)||el;if(cardMemberId(card)===String(id)){card.classList.add('jm-temp-pair');card.style.setProperty('--jm-temp-pair-color',side[1]);}});});\n      });"
b=b.replace(old_admin,new_admin)
if 'TEAM_TEXT_HARD_HIDE_V2041' not in b:
    b=b.replace("  window.__JM_RENDER_TEMP_PAIRS__=renderSharedTempPairs;","  if(typeof document!=='undefined'&&document.createElement&&!document.getElementById('TEAM_TEXT_HARD_HIDE_V2041')){var th=document.createElement('style');th.id='TEAM_TEXT_HARD_HIDE_V2041';th.textContent='.jm-team-bottom-label,.member-team-badge,.jm-team-badge,.team-badge,.team-label,[data-team-label]{display:none!important;visibility:hidden!important;width:0!important;height:0!important;overflow:hidden!important}';(document.head||document.documentElement).appendChild(th);}\n  window.__JM_RENDER_TEMP_PAIRS__=renderSharedTempPairs;")
bp.write_text(b)
print('SHARED_TEMP_PAIRS_V3_OK pairA+pairB=true admin_both=true wait=left-right court=top-bottom labels=none fixed=double-line')
