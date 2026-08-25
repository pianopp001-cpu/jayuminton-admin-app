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
/* Official team identity is lines only. Never render 팀1/팀2 text. */
#adminApp .has-member-team{
  padding-left:inherit!important;
  border:2px solid var(--member-team-color)!important;
  outline:2px solid var(--member-team-color)!important;
  outline-offset:-5px!important;
  background-clip:padding-box!important;
  box-shadow:none!important;
}
#adminApp .member-team-badge,#adminApp .jm-team-badge,#adminApp .team-badge,#adminApp .team-label,#adminApp .jm-team-bottom-label,#adminApp [data-team-label]{
  display:none!important;visibility:hidden!important;width:0!important;height:0!important;min-width:0!important;max-width:0!important;
  margin:0!important;padding:0!important;border:0!important;overflow:hidden!important;font-size:0!important;line-height:0!important;pointer-events:none!important;
}
#adminApp .has-member-team.jm-temp-pair{
  box-shadow:inset 0 0 0 3px var(--jm-temp-pair-color),0 0 0 2px var(--jm-temp-pair-color)!important;
}
#memberApp [data-member-id].jm-has-team{
  border:2px solid var(--jm-team-color)!important;
  outline:2px solid var(--jm-team-color)!important;
  outline-offset:-5px!important;
  background-clip:padding-box!important;
  box-shadow:none!important;
}
#memberApp [data-member-id]>.jm-member-badges,
#memberApp [data-member-id] .jm-team-badge,
#memberApp [data-member-id] [data-team-label]{
  display:none!important;visibility:hidden!important;width:0!important;height:0!important;min-width:0!important;max-width:0!important;
  margin:0!important;padding:0!important;border:0!important;overflow:hidden!important;font-size:0!important;line-height:0!important;pointer-events:none!important;
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
  function hideTeamText(root){
    (root||document).querySelectorAll('.member-team-badge,.jm-team-badge,.team-badge,.team-label,.jm-team-bottom-label,[data-team-label]').forEach(function(node){
      var label=normalizeLabel((node.getAttribute&&node.getAttribute('data-team-label'))||node.textContent);
      if(label){
        var card=node.closest&&node.closest('[data-member-id],.member,.person,.quick-member,.member-card,.member-item,.wait-card,.wait-item,.player-card,.court-player');
        if(card&&!card.getAttribute('data-jm-team-text'))card.setAttribute('data-jm-team-text',label);
      }
      node.style.setProperty('display','none','important');
      node.style.setProperty('visibility','hidden','important');
      node.setAttribute('aria-hidden','true');
    });
    (root||document).querySelectorAll('.jm-team-bottom-label').forEach(function(node){node.remove();});
  }
  var queued=false;function run(){queued=false;hideTeamText(document);}
  function schedule(){if(queued)return;queued=true;requestAnimationFrame(run);}
  new MutationObserver(schedule).observe(document.documentElement,{childList:true,subtree:true,characterData:true});
  document.addEventListener('DOMContentLoaded',schedule,{once:true});
  setInterval(schedule,1600);schedule();
})();
</script>
'''

html, style_count = re.subn(
    r'<style\s+id=["\']jayuminton-team-visuals-v6["\'][^>]*>[\s\S]*?</style>\s*',
    '', html, flags=re.I
)
html, script_count = re.subn(
    r'<script\s+id=["\']jayuminton-team-visuals-v6-script["\'][^>]*>[\s\S]*?</script>\s*',
    '', html, flags=re.I
)
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
print(f'TEAM_VISUALS_V6_REPLACED style={style_count} script={script_count}')
