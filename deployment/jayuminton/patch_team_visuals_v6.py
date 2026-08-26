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
/* Permanent team = double line only. One-game pair = separate solid overlay. No team1/team2 text. */
#memberApp [data-member-id].jm-has-team{
  border:2px solid var(--jm-team-color)!important;
  outline:2px solid var(--jm-team-color)!important;
  outline-offset:-5px!important;
  background-clip:padding-box!important;
  box-shadow:none!important;
}
#memberApp [data-member-id] .member-team-badge,
#memberApp [data-member-id] .jm-team-badge,
#memberApp [data-member-id] .team-badge,
#memberApp [data-member-id] .team-label,
#memberApp [data-member-id] [data-team-label],
#memberApp [data-member-id] .jm-team-bottom-label{
  display:none!important;visibility:hidden!important;width:0!important;height:0!important;
  margin:0!important;padding:0!important;border:0!important;overflow:hidden!important;
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
  function syncTeamBorders(root){
    (root||document).querySelectorAll('[data-member-id]').forEach(function(card){
      var label=normalizeLabel(card.getAttribute('data-jm-team-text')||card.getAttribute('data-team-label')||'');
      if(!label){
        var source=card.querySelector('.member-team-badge,.jm-team-badge,.team-badge,.team-label,[data-team-label]');
        if(source)label=normalizeLabel((source.getAttribute&&source.getAttribute('data-team-label'))||source.textContent);
      }
      card.querySelectorAll('.member-team-badge,.jm-team-badge,.team-badge,.team-label,[data-team-label],.jm-team-bottom-label').forEach(function(node){
        var t=normalizeLabel((node.getAttribute&&node.getAttribute('data-team-label'))||node.textContent);
        if(t&&!label)label=t;
        if(t){node.textContent='';node.style.setProperty('display','none','important');}
      });
      if(label){card.setAttribute('data-jm-team-text',label);card.classList.add('jm-has-team');}
      card.querySelectorAll('.jm-team-bottom-label').forEach(function(node){node.remove();});
    });
  }
  var queued=false;function run(){queued=false;syncTeamBorders(document);}
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
print('TEAM_VISUALS_V6_BORDER_ONLY_PAIR_OVERLAY_OK')
# DEPLOY_TRIGGER: border-only-team-state-20260826
