from pathlib import Path
import re
import runpy

# v3 is legacy 2+2 behavior. Run it first, then enforce the latest MD contract:
# clicked two only = temporary pair, remaining members plain, no seat reorder.
runpy.run_path('deployment/jayuminton/patch_shared_temp_pairs_v3.py', run_name='__main__')

wp=Path('cloudflare/state-worker/worker.js')
w=wp.read_text()
w=re.sub(
    r"    const pairA = uniqueIds\(raw\.pairA, 2\);\n    const pairB = uniqueIds\(raw\.pairB, 2\);\n    const ids = \[\.\.\.pairA, \.\.\.pairB\];\n    if \(pairA\.length !== 2 \|\| pairB\.length !== 2 \|\| new Set\(ids\)\.size !== 4\) continue;\n    if \(ids\.some\(id => used\.has\(id\)\)\) continue;\n    ids\.forEach\(id => used\.add\(id\)\);\n    out\.push\(\{ pairA, pairB, zone: String\(raw\.zone\), createdAt: Math\.max\(0, Number\(raw\.createdAt\) \|\| Date\.now\(\)\) \}\);",
    "    const pairA = uniqueIds(raw.pairA, 2);\n    if (pairA.length !== 2 || new Set(pairA).size !== 2) continue;\n    if (pairA.some(id => used.has(id))) continue;\n    pairA.forEach(id => used.add(id));\n    out.push({ pairA, pairB: [], zone: String(raw.zone), createdAt: Math.max(0, Number(raw.createdAt) || Date.now()) });",
    w, count=1)
w=w.replace("    const ids = [...group.pairA, ...group.pairB];\n    const first = locationOf(state, ids[0]);","    const ids = group.pairA;\n    const first = locationOf(state, ids[0]);",1)
w=re.sub(r"\nfunction applyTempPairOrdering\(state\) \{.*?\n\}\n\nexport function normalizeState","\nexport function normalizeState",w,count=1,flags=re.S)
w=w.replace("  applyTempPairOrdering(state);\n","")
wp.write_text(w)

bp=Path('deployment/jayuminton/cloudflare_v6_frontend_bridge.js')
b=bp.read_text()
b=b.replace("if(!x||['wait','court'].indexOf(String(x.zone))<0||!Array.isArray(x.pairA)||!Array.isArray(x.pairB)||x.pairA.length!==2||x.pairB.length!==2)return false;\n      return new Set(x.pairA.concat(x.pairB).map(String)).size===4;","if(!x||['wait','court'].indexOf(String(x.zone))<0||!Array.isArray(x.pairA)||x.pairA.length!==2)return false;\n      return new Set(x.pairA.map(String)).size===2;")
b=b.replace("}).map(function(x){return {pairA:x.pairA.map(String),pairB:x.pairB.map(String),zone:String(x.zone),createdAt:Number(x.createdAt)||Date.now()};});","}).map(function(x){return {pairA:x.pairA.map(String),pairB:[],zone:String(x.zone),createdAt:Number(x.createdAt)||Date.now()};});")
b=b.replace("var pairA=[first.id,second.id],pairB=ids.filter(function(id){return pairA.indexOf(id)<0;});\n      if(pairB.length!==2)return;","var pairA=[first.id,second.id],pairB=[];")
b=b.replace("if(items.length===4&&items.some(function(x){return x.card===card||x.card.contains(card)||card.contains(x.card);})){return {zone:zone,node:node,items:items};}","if(items.length>=2&&items.length<=4&&items.some(function(x){return x.card===card||x.card.contains(card)||card.contains(x.card);})){return {zone:zone,node:node,items:items};}")

# Shared temp border rendering: update only changed cards instead of clearing/re-adding all.
shared=re.compile(r"  function renderSharedTempPairs\(\)\{.*?\n  \}\n  if\(typeof document",re.S)
shared_body="""  function renderSharedTempPairs(){
    if(typeof document==='undefined'||typeof document.querySelectorAll!=='function')return;
    var selector='.member,.person,.quick-member,.member-card,.member-item,.wait-card,.wait-item,.player-card,.court-player,[data-member-id],[data-memberid],[data-player-id]';
    var attrs=['data-member-id','data-memberid','data-player-id','data-id','data-member'];
    function idOf(card){if(!card)return '';for(var i=0;i<attrs.length;i++){var v=card.getAttribute&&card.getAttribute(attrs[i]);if(v)return String(v);}var nested=card.querySelector&&card.querySelector('[data-member-id],[data-memberid],[data-player-id],[data-id],[data-member]');if(nested){for(var j=0;j<attrs.length;j++){var nv=nested.getAttribute(attrs[j]);if(nv)return String(nv);}}return '';}
    var desired={};
    loadTempPairs().forEach(function(group,index){var color=TEMP_PAIR_COLORS[index%TEMP_PAIR_COLORS.length];group.pairA.forEach(function(id){desired[String(id)]=color;});});
    Array.prototype.forEach.call(document.querySelectorAll(selector),function(card){var id=idOf(card),want=id&&desired[id]||'',has=card.classList.contains('jm-temp-pair'),cur=card.style&&card.style.getPropertyValue?card.style.getPropertyValue('--jm-temp-pair-color'):'';if(want){if(!has)card.classList.add('jm-temp-pair');if(cur!==want&&card.style&&card.style.setProperty)card.style.setProperty('--jm-temp-pair-color',want);}else if(has){card.classList.remove('jm-temp-pair');if(card.style&&card.style.removeProperty)card.style.removeProperty('--jm-temp-pair-color');}});
    if(document.getElementById&&!document.getElementById('jayuminton-shared-temp-pair-style')){var style=document.createElement('style');style.id='jayuminton-shared-temp-pair-style';style.textContent='.jm-temp-pair{box-shadow:0 0 0 3px var(--jm-temp-pair-color)!important}#adminApp .has-member-team.jm-temp-pair{box-shadow:0 0 0 3px var(--jm-temp-pair-color)!important}.jm-team-bottom-label{display:none!important}';(document.head||document.documentElement).appendChild(style);}
  }
  if(typeof document"""
b,n=shared.subn(shared_body,b,count=1)
if n!=1: raise SystemExit('renderSharedTempPairs anchor missing')

# Admin render: same stable diff-only behavior.
admin=re.compile(r"    function renderTempPairs\(\)\{.*?\n    \}\n    window\.__JM_RENDER_TEMP_PAIRS__=renderTempPairs;",re.S)
admin_body="""    function renderTempPairs(){
      var app=document.getElementById('adminApp');if(!app)return;var desired={};
      loadTempPairs().forEach(function(group,index){var color=TEMP_PAIR_COLORS[index%TEMP_PAIR_COLORS.length];group.pairA.forEach(function(id){desired[String(id)]=color;});});
      var pendingId=pendingPair?String(pendingPair.id):'';
      Array.prototype.forEach.call(app.querySelectorAll(cardSelector),function(el){var card=memberCard(el)||el,id=cardMemberId(card),want=id&&desired[id]||'',has=card.classList.contains('jm-temp-pair'),cur=card.style.getPropertyValue('--jm-temp-pair-color');if(want){if(!has)card.classList.add('jm-temp-pair');if(cur!==want)card.style.setProperty('--jm-temp-pair-color',want);}else if(has){card.classList.remove('jm-temp-pair');card.style.removeProperty('--jm-temp-pair-color');}var p=!!pendingId&&id===pendingId;if(p&&!card.classList.contains('jm-temp-pair-pending'))card.classList.add('jm-temp-pair-pending');else if(!p&&card.classList.contains('jm-temp-pair-pending'))card.classList.remove('jm-temp-pair-pending');});
    }
    window.__JM_RENDER_TEMP_PAIRS__=renderTempPairs;"""
b,n=admin.subn(admin_body,b,count=1)
if n!=1: raise SystemExit('renderTempPairs anchor missing')

# Avoid layout-thrashing observer loops.
b=b.replace("app.__jmTeamTextObserver.observe(app,{childList:true,subtree:true,characterData:true});","app.__jmTeamTextObserver.observe(app,{childList:true,subtree:true});")
b=b.replace("setTimeout(function(){scheduled=false;moveAdminTeamLabels(app);renderTempPairs();},0);","(typeof requestAnimationFrame==='function'?requestAnimationFrame:setTimeout)(function(){scheduled=false;moveAdminTeamLabels(app);renderTempPairs();},16);")

bp.write_text(b)
print('SHARED_TEMP_PAIRS_V4_OK clickedTwoOnly=true remainingPlain=true reorder=false fixedDouble=true tempOverlay=true stableRender=true')
