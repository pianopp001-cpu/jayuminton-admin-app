from pathlib import Path
import re
import runpy

# Start from current v3 generated state, then enforce the MD-final contract.
runpy.run_path('deployment/jayuminton/patch_shared_temp_pairs_v3.py', run_name='__main__')

wp=Path('cloudflare/state-worker/worker.js')
w=wp.read_text()
w=re.sub(
    r"    const pairA = uniqueIds\(raw\.pairA, 2\);\n    const pairB = uniqueIds\(raw\.pairB, 2\);\n    const ids = \[\.\.\.pairA, \.\.\.pairB\];\n    if \(pairA\.length !== 2 \|\| pairB\.length !== 2 \|\| new Set\(ids\)\.size !== 4\) continue;\n    if \(ids\.some\(id => used\.has\(id\)\)\) continue;\n    ids\.forEach\(id => used\.add\(id\)\);\n    out\.push\(\{ pairA, pairB, zone: String\(raw\.zone\), createdAt: Math\.max\(0, Number\(raw\.createdAt\) \|\| Date\.now\(\)\) \}\);",
    "    const pairA = uniqueIds(raw.pairA, 2);\n    if (pairA.length !== 2 || new Set(pairA).size !== 2) continue;\n    if (pairA.some(id => used.has(id))) continue;\n    pairA.forEach(id => used.add(id));\n    out.push({ pairA, pairB: [], zone: String(raw.zone), createdAt: Math.max(0, Number(raw.createdAt) || Date.now()) });",
    w,
    count=1,
)
w=w.replace("    const ids = [...group.pairA, ...group.pairB];\n    const first = locationOf(state, ids[0]);","    const ids = group.pairA;\n    const first = locationOf(state, ids[0]);",1)
w=re.sub(r"\nfunction applyTempPairOrdering\(state\) \{.*?\n\}\n\nexport function normalizeState","\nexport function normalizeState",w,count=1,flags=re.S)
w=w.replace("  applyTempPairOrdering(state);\n","")
wp.write_text(w)

bp=Path('deployment/jayuminton/cloudflare_v6_frontend_bridge.js')
b=bp.read_text()

# Selected two only. The other two never receive an automatic border.
b=b.replace("if(!x||['wait','court'].indexOf(String(x.zone))<0||!Array.isArray(x.pairA)||!Array.isArray(x.pairB)||x.pairA.length!==2||x.pairB.length!==2)return false;\n      return new Set(x.pairA.concat(x.pairB).map(String)).size===4;","if(!x||['wait','court'].indexOf(String(x.zone))<0||!Array.isArray(x.pairA)||x.pairA.length!==2)return false;\n      return new Set(x.pairA.map(String)).size===2;")
b=b.replace("}).map(function(x){return {pairA:x.pairA.map(String),pairB:x.pairB.map(String),zone:String(x.zone),createdAt:Number(x.createdAt)||Date.now()};});","}).map(function(x){return {pairA:x.pairA.map(String),pairB:[],zone:String(x.zone),createdAt:Number(x.createdAt)||Date.now()};});")
b=re.sub(r"\[\[group\.pairA,TEMP_PAIR_COLORS\[\(index\*2\)%TEMP_PAIR_COLORS\.length\]\],\[group\.pairB,TEMP_PAIR_COLORS\[\(index\*2\+1\)%TEMP_PAIR_COLORS\.length\]\]\]\.forEach\(function\(side\)\{Array\.prototype\.forEach\.call\(document\.querySelectorAll\(selector\),function\(card\)\{var id=idOf\(card\);if\(side\[0\]\.indexOf\(id\)>=0\)\{card\.classList\.add\('jm-temp-pair'\);if\(card\.style&&card\.style\.setProperty\)card\.style\.setProperty\('--jm-temp-pair-color',side\[1\]\);\}\}\);\}\);","var side=[group.pairA,TEMP_PAIR_COLORS[index%TEMP_PAIR_COLORS.length]];\n      Array.prototype.forEach.call(document.querySelectorAll(selector),function(card){var id=idOf(card);if(side[0].indexOf(id)>=0){card.classList.add('jm-temp-pair');if(card.style&&card.style.setProperty)card.style.setProperty('--jm-temp-pair-color',side[1]);}});",b,count=1)
b=b.replace("var pairA=[first.id,second.id],pairB=ids.filter(function(id){return pairA.indexOf(id)<0;});\n      if(pairB.length!==2)return;","var pairA=[first.id,second.id],pairB=[];")

# Same court/wait can form a temporary team with 2, 3, or 4 currently present members.
b=b.replace("if(items.length===4&&items.some(function(x){return x.card===card||x.card.contains(card)||card.contains(x.card);})){return {zone:zone,node:node,items:items};}","if(items.length>=2&&items.length<=4&&items.some(function(x){return x.card===card||x.card.contains(card)||card.contains(x.card);})){return {zone:zone,node:node,items:items};}")

# Make permanent-team decoration idempotent so DOM refreshes do not repeatedly force layout.
pattern=re.compile(r"    function moveAdminTeamLabels\(root\)\{.*?\n    \}\n    function cardMemberId",re.S)
replacement="""    function moveAdminTeamLabels(root){
      var scope=root&&root.querySelectorAll?root:document;
      var cards=scope.querySelectorAll('#adminApp '+cardSelector.split(',').join(',#adminApp '));
      for(var i=0;i<cards.length;i++){
        var card=cards[i],teamText=normalizeTeamText(card.getAttribute('data-jm-team-text'));
        if(!teamText){var nodes=card.querySelectorAll('[data-team-label],.member-team-badge,.jm-team-badge,.team-badge,.team-label,.jm-team-bottom-label');for(var j=0;j<nodes.length&&!teamText;j++)teamText=normalizeTeamText(nodes[j].textContent||nodes[j].getAttribute('data-team-label'));}
        if(teamText){
          if(card.getAttribute('data-jm-team-text')!==teamText)card.setAttribute('data-jm-team-text',teamText);
          if(!card.classList.contains('has-member-team'))card.classList.add('has-member-team');
          if(card.style.getPropertyValue('border')!=='2px solid var(--member-team-color)')card.style.setProperty('border','2px solid var(--member-team-color)','important');
          if(card.style.getPropertyValue('outline')!=='2px solid var(--member-team-color)')card.style.setProperty('outline','2px solid var(--member-team-color)','important');
          if(card.style.getPropertyValue('outline-offset')!=='-5px')card.style.setProperty('outline-offset','-5px','important');
        }
      }
    }
    function cardMemberId"""
b,n=pattern.subn(replacement,b,count=1)
if n!=1: raise SystemExit('moveAdminTeamLabels anchor missing')

# Stable shared rendering: do not remove/re-add all borders on every state refresh.
shared_pattern=re.compile(r"  function renderSharedTempPairs\(\)\{.*?\n  \}\n  if\(typeof document",re.S)
shared_replacement="""  function renderSharedTempPairs(){
    if(typeof document==='undefined'||typeof document.querySelectorAll!=='function')return;
    var selector='.member,.person,.quick-member,.member-card,.member-item,.wait-card,.wait-item,.player-card,.court-player,[data-member-id],[data-memberid],[data-player-id]';
    var attrs=['data-member-id','data-memberid','data-player-id','data-id','data-member'];
    function idOf(card){
      if(!card)return '';
      for(var i=0;i<attrs.length;i++){var v=card.getAttribute&&card.getAttribute(attrs[i]);if(v)return String(v);}
      var nested=card.querySelector&&card.querySelector('[data-member-id],[data-memberid],[data-player-id],[data-id],[data-member]');
      if(nested){for(var j=0;j<attrs.length;j++){var nv=nested.getAttribute(attrs[j]);if(nv)return String(nv);}}
      var onclick=(card.getAttribute&&card.getAttribute('onclick'))||'';
      var hit=onclick.match(/[\"']([0-9a-f]{8}-[0-9a-f-]{27,})[\"']/i);
      return hit?String(hit[1]):'';
    }
    var desired={};
    loadTempPairs().forEach(function(group,index){var color=TEMP_PAIR_COLORS[index%TEMP_PAIR_COLORS.length];group.pairA.forEach(function(id){desired[String(id)]=color;});});
    Array.prototype.forEach.call(document.querySelectorAll(selector),function(card){
      var id=idOf(card),want=id&&desired[id]||'',has=card.classList.contains('jm-temp-pair');
      var current=card.style&&card.style.getPropertyValue?card.style.getPropertyValue('--jm-temp-pair-color'):'';
      if(want){if(!has)card.classList.add('jm-temp-pair');if(current!==want&&card.style&&card.style.setProperty)card.style.setProperty('--jm-temp-pair-color',want);}
      else if(has){card.classList.remove('jm-temp-pair');if(card.style&&card.style.removeProperty)card.style.removeProperty('--jm-temp-pair-color');}
    });
    if(document.getElementById&&!document.getElementById('jayuminton-shared-temp-pair-style')){
      var style=document.createElement('style');style.id='jayuminton-shared-temp-pair-style';
      style.textContent='.jm-temp-pair{box-shadow:0 0 0 3px var(--jm-temp-pair-color)!important}#adminApp .member.jm-team-card.has-member-team.jm-temp-pair,#adminApp .member.jm-team-card.jm-temp-pair,#adminApp .has-member-team.jm-temp-pair,#adminApp .jm-temp-pair{box-shadow:0 0 0 3px var(--jm-temp-pair-color)!important}.jm-team-bottom-label{display:none!important;visibility:hidden!important;width:0!important;height:0!important;overflow:hidden!important}';
      (document.head||document.documentElement).appendChild(style);
    }
  }
  if(typeof document"""
b,n=shared_pattern.subn(shared_replacement,b,count=1)
if n!=1: raise SystemExit('renderSharedTempPairs anchor missing')

# Stable admin rendering, including pending-selection outline.
admin_pattern=re.compile(r"    function renderTempPairs\(\)\{.*?\n    \}\n    window\.__JM_RENDER_TEMP_PAIRS__=renderTempPairs;",re.S)
admin_replacement="""    function renderTempPairs(){
      var app=document.getElementById('adminApp');if(!app)return;
      var desired={};
      loadTempPairs().forEach(function(group,index){var color=TEMP_PAIR_COLORS[index%TEMP_PAIR_COLORS.length];group.pairA.forEach(function(id){desired[String(id)]=color;});});
      var pendingId=pendingPair?String(pendingPair.id):'';
      Array.prototype.forEach.call(app.querySelectorAll(cardSelector),function(el){
        var card=memberCard(el)||el,id=cardMemberId(card),want=id&&desired[id]||'';
        var has=card.classList.contains('jm-temp-pair'),current=card.style.getPropertyValue('--jm-temp-pair-color');
        if(want){if(!has)card.classList.add('jm-temp-pair');if(current!==want)card.style.setProperty('--jm-temp-pair-color',want);}
        else if(has){card.classList.remove('jm-temp-pair');card.style.removeProperty('--jm-temp-pair-color');}
        var shouldPending=!!pendingId&&id===pendingId;
        if(shouldPending&&!card.classList.contains('jm-temp-pair-pending'))card.classList.add('jm-temp-pair-pending');
        else if(!shouldPending&&card.classList.contains('jm-temp-pair-pending'))card.classList.remove('jm-temp-pair-pending');
      });
    }
    window.__JM_RENDER_TEMP_PAIRS__=renderTempPairs;"""
b,n=admin_pattern.subn(admin_replacement,b,count=1)
if n!=1: raise SystemExit('renderTempPairs anchor missing')

# Coalesce bursts of DOM changes into one paint-cycle update.
b=b.replace("var scheduled=false;\n      app.__jmTeamTextObserver=new MutationObserver(function(){if(scheduled)return;scheduled=true;setTimeout(function(){scheduled=false;moveAdminTeamLabels(app);renderTempPairs();},0);});","var scheduled=false;\n      app.__jmTeamTextObserver=new MutationObserver(function(){if(scheduled)return;scheduled=true;var run=function(){scheduled=false;moveAdminTeamLabels(app);renderTempPairs();};if(typeof requestAnimationFrame==='function')requestAnimationFrame(run);else setTimeout(run,16);});")
b=b.replace("app.__jmTeamTextObserver.observe(app,{childList:true,subtree:true,characterData:true});","app.__jmTeamTextObserver.observe(app,{childList:true,subtree:true});")

bp.write_text(b)
print('SHARED_TEMP_PAIRS_V4_OK clickedTwoOnly=true remainingTwoPlain=true reorder=false fixedTeamDouble=true tempOverlay=true group2to4=true flickerStable=true promptMoveOrTeam=true')
