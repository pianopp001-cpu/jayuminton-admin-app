from pathlib import Path
import re
import runpy

runpy.run_path('deployment/jayuminton/patch_shared_temp_pairs_v2.py', run_name='__main__')
wp=Path('cloudflare/state-worker/worker.js'); w=wp.read_text()
old="""    const pairA = uniqueIds(raw.pairA, 2);\n    const pairB = uniqueIds(raw.pairB, 2);\n    const ids = [...pairA, ...pairB];\n    if (pairA.length !== 2 || pairB.length !== 2 || new Set(ids).size !== 4) continue;\n    if (ids.some(id => used.has(id))) continue;\n    ids.forEach(id => used.add(id));\n    out.push({ pairA, pairB, zone: String(raw.zone), createdAt: Math.max(0, Number(raw.createdAt) || Date.now()) });\n"""
new="""    const pairA = uniqueIds(raw.pairA, 2);\n    if (pairA.length !== 2 || new Set(pairA).size !== 2) continue;\n    if (pairA.some(id => used.has(id))) continue;\n    pairA.forEach(id => used.add(id));\n    out.push({ pairA, pairB: [], zone: String(raw.zone), createdAt: Math.max(0, Number(raw.createdAt) || Date.now()) });\n"""
if old in w:w=w.replace(old,new,1)
w=w.replace("    const ids = [...group.pairA, ...group.pairB];\n    const first = locationOf(state, ids[0]);","    const ids = group.pairA;\n    const first = locationOf(state, ids[0]);",1)
w=re.sub(r"\nfunction applyTempPairOrdering\(state\) \{.*?\n\}\n\nexport function normalizeState","\nexport function normalizeState",w,count=1,flags=re.S)
w=w.replace("  applyTempPairOrdering(state);\n","")
wp.write_text(w)

bp=Path('deployment/jayuminton/cloudflare_v6_frontend_bridge.js'); b=bp.read_text()
b=b.replace("if(!x||['wait','court'].indexOf(String(x.zone))<0||!Array.isArray(x.pairA)||!Array.isArray(x.pairB)||x.pairA.length!==2||x.pairB.length!==2)return false;\n      return new Set(x.pairA.concat(x.pairB).map(String)).size===4;","if(!x||['wait','court'].indexOf(String(x.zone))<0||!Array.isArray(x.pairA)||x.pairA.length!==2)return false;\n      return new Set(x.pairA.map(String)).size===2;")
b=b.replace("}).map(function(x){return {pairA:x.pairA.map(String),pairB:x.pairB.map(String),zone:String(x.zone),createdAt:Number(x.createdAt)||Date.now()};});","}).map(function(x){return {pairA:x.pairA.map(String),pairB:[],zone:String(x.zone),createdAt:Number(x.createdAt)||Date.now()};});")
b=b.replace("var pairA=[first.id,second.id],pairB=ids.filter(function(id){return pairA.indexOf(id)<0;});\n      if(pairB.length!==2)return;","var pairA=[first.id,second.id],pairB=[];")
# Never mutate Team1/Team2 nodes during rendering. CSS alone hides them, avoiding flicker loops.
b=re.sub(r"\n    Array\.prototype\.forEach\.call\(document\.querySelectorAll\('\.jm-team-bottom-label,\.member-team-badge,\.jm-team-badge,\.team-badge,\.team-label,\[data-team-label\]'\),function\(node\)\{.*?\n    \}\);","",b,count=1,flags=re.S)
pattern=re.compile(r"    function moveAdminTeamLabels\(root\)\{.*?\n    \}\n    function cardMemberId",re.S)
replacement="""    function moveAdminTeamLabels(root){
      var scope=root&&root.querySelectorAll?root:document;
      var cards=scope.querySelectorAll('#adminApp '+cardSelector.split(',').join(',#adminApp '));
      for(var i=0;i<cards.length;i++){
        var card=cards[i],teamText=normalizeTeamText(card.getAttribute('data-jm-team-text'));
        if(!teamText){var nodes=card.querySelectorAll('[data-team-label],.member-team-badge,.jm-team-badge,.team-badge,.team-label,.jm-team-bottom-label');for(var j=0;j<nodes.length&&!teamText;j++)teamText=normalizeTeamText(nodes[j].textContent||nodes[j].getAttribute('data-team-label'));}
        if(teamText){card.classList.add('has-member-team');card.setAttribute('data-jm-team-text',teamText);card.style.setProperty('border','2px solid var(--member-team-color)','important');card.style.setProperty('outline','2px solid var(--member-team-color)','important');card.style.setProperty('outline-offset','-5px','important');}
      }
    }
    function cardMemberId"""
b,n=pattern.subn(replacement,b,count=1)
if n!=1:raise SystemExit('moveAdminTeamLabels anchor missing')
b=b.replace("    setTimeout(renderSharedTempPairs,0);setTimeout(renderSharedTempPairs,80);setTimeout(renderSharedTempPairs,250);","    setTimeout(renderSharedTempPairs,0);")
b=b.replace("app.__jmTeamTextObserver.observe(app,{childList:true,subtree:true,characterData:true});","app.__jmTeamTextObserver.observe(app,{childList:true,subtree:true});")
if 'TEAM_TEXT_HARD_HIDE_V2041' not in b:
    b=b.replace("  window.__JM_RENDER_TEMP_PAIRS__=renderSharedTempPairs;","  if(typeof document!=='undefined'&&document.createElement&&!document.getElementById('TEAM_TEXT_HARD_HIDE_V2041')){var th=document.createElement('style');th.id='TEAM_TEXT_HARD_HIDE_V2041';th.textContent='.jm-team-bottom-label,.member-team-badge,.jm-team-badge,.team-badge,.team-label,[data-team-label]{display:none!important;visibility:hidden!important;width:0!important;height:0!important;overflow:hidden!important}';(document.head||document.documentElement).appendChild(th);}\n  window.__JM_RENDER_TEMP_PAIRS__=renderSharedTempPairs;")
bp.write_text(b)
print('SHARED_TEMP_PAIRS_V3_OK pairAOnly=true reorder=false labels=css-only stable=true prompt=true')
