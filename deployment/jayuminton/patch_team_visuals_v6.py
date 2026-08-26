#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_team_visuals_v6.py <html>')
path = Path(sys.argv[1])
html = path.read_text(encoding='utf-8')
marker = 'JAYUMINTON_TEAM_VISUALS_V6'

addon = r'''
<style id="jayuminton-team-visuals-v6">
/* JAYUMINTON_TEAM_VISUALS_V6 */
/* Permanent team = double line + tiny bottom label. One-game pair = extra solid overlay. */
#memberApp [data-member-id].jm-has-team{
  border:2px solid var(--jm-team-color)!important;
  outline:2px solid var(--jm-team-color)!important;
  outline-offset:-5px!important;
  background-clip:padding-box!important;
  box-shadow:none!important;
}
#memberApp [data-member-id] .jm-team-badge,
#memberApp [data-member-id] [data-team-label]:not(.jm-team-bottom-label){
  display:none!important;visibility:hidden!important;width:0!important;height:0!important;
  margin:0!important;padding:0!important;border:0!important;overflow:hidden!important;
}
#memberApp [data-member-id] .jm-team-bottom-label{
  display:block!important;visibility:visible!important;position:static!important;width:100%!important;height:auto!important;
  margin:3px 0 0!important;padding:0!important;text-align:left!important;font-size:9px!important;font-weight:900!important;
  line-height:1.1!important;white-space:nowrap!important;color:var(--jm-team-color)!important;pointer-events:none!important;
}
#memberApp [data-member-id].jm-temp-pair{
  box-shadow:inset 0 0 0 3px var(--jm-temp-pair-color),0 0 0 2px var(--jm-temp-pair-color)!important;
}
</style>
<script id="jayuminton-team-visuals-v6-script">
(function(){
  'use strict';
  window.__JAYUMINTON_TEAM_VISUALS_V6__=true;
  function normalizeLabel(text){
    var s=String(text||'').replace(/\s+/g,'').trim();
    if(/^TEAM\d+$/i.test(s))s=s.replace(/^TEAM/i,'팀');
    return /^팀\d+$/.test(s)?s:'';
  }
  function syncTeamLabels(root){
    (root||document).querySelectorAll('[data-member-id]').forEach(function(card){
      var label=normalizeLabel(card.getAttribute('data-jm-team-text')||card.getAttribute('data-team-label')||'');
      if(!label){
        var source=card.querySelector('.member-team-badge,.jm-team-badge,.team-badge,.team-label,[data-team-label]');
        if(source)label=normalizeLabel((source.getAttribute&&source.getAttribute('data-team-label'))||source.textContent);
      }
      card.querySelectorAll('.member-team-badge,.jm-team-badge,.team-badge,.team-label,[data-team-label]:not(.jm-team-bottom-label)').forEach(function(node){node.style.setProperty('display','none','important');});
      var bottom=card.querySelector('.jm-team-bottom-label');
      if(label){
        card.setAttribute('data-jm-team-text',label);
        if(!bottom){bottom=document.createElement('small');bottom.className='jm-team-bottom-label';card.appendChild(bottom);}
        bottom.textContent=label;
        if(card.lastElementChild!==bottom)card.appendChild(bottom);
      }else if(bottom){bottom.remove();}
    });
  }
  var queued=false;function run(){queued=false;syncTeamLabels(document);}
  function schedule(){if(queued)return;queued=true;requestAnimationFrame(run);}
  new MutationObserver(schedule).observe(document.documentElement,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['data-team-label','data-jm-team-text','class']});
  document.addEventListener('DOMContentLoaded',schedule,{once:true});
  setInterval(schedule,1600);schedule();
})();
</script>
'''

html = re.sub(r'<style\s+id=["\']jayuminton-team-visuals-v6["\'][^>]*>[\s\S]*?</style>\s*','',html,flags=re.I)
html = re.sub(r'<script\s+id=["\']jayuminton-team-visuals-v6-script["\'][^>]*>[\s\S]*?</script>\s*','',html,flags=re.I)
if marker in html:
    raise SystemExit('stale V6 marker survived block replacement')
if '</body>' not in html:
    raise SystemExit('body closing tag missing')
html = html.replace('</body>', addon + '\n</body>', 1)
if len(re.findall(r'<style\s+id=["\']jayuminton-team-visuals-v6["\']', html, flags=re.I)) != 1:
    raise SystemExit('fresh V6 style block count mismatch')
if len(re.findall(r'<script\s+id=["\']jayuminton-team-visuals-v6-script["\']', html, flags=re.I)) != 1:
    raise SystemExit('fresh V6 script block count mismatch')
path.write_text(html, encoding='utf-8')
print('TEAM_VISUALS_V6_OFFICIAL_LABEL_PAIR_OVERLAY_OK')
