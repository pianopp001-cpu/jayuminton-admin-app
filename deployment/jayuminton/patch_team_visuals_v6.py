#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_team_visuals_v6.py <html>')
path = Path(sys.argv[1])
html = path.read_text(encoding='utf-8')
marker = 'JAYUMINTON_TEAM_VISUALS_V7'

addon = r'''
<style id="jayuminton-team-visuals-v7">
/* JAYUMINTON_TEAM_VISUALS_V7 */
/* Permanent team = two thin lines outside the card. Never draw over card content. */
#memberApp [data-member-id].jm-has-team{
  border-color:transparent!important;
  outline:1px solid var(--jm-team-color,#6d28d9)!important;
  outline-offset:2px!important;
  box-shadow:0 0 0 4px rgba(255,255,255,.98),0 0 0 5px var(--jm-team-color,#6d28d9)!important;
  overflow:visible!important;
  contain:none!important;
  background-clip:padding-box!important;
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
<script id="jayuminton-team-visuals-v7-script">
(function(){
  'use strict';
  window.__JAYUMINTON_TEAM_VISUALS_V7__=true;
  function normalizeLabel(text){
    var s=String(text||'').replace(/\s+/g,'').trim();
    if(/^TEAM\d+$/i.test(s))s=s.replace(/^TEAM/i,'팀');
    return /^팀\d+$/.test(s)?s:'';
  }
  function colorFor(label){
    var match=/([0-9]+)$/.exec(String(label||''));
    var seed=match?Number(match[1]):0;
    if(!seed){String(label||'').split('').forEach(function(ch){seed=((seed*31)+ch.charCodeAt(0))>>>0;});}
    var hue=Math.round((Math.max(1,seed)*137.508)%360);
    return 'hsl('+hue+' 72% 38%)';
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
      if(label){
        card.setAttribute('data-jm-team-text',label);
        card.classList.add('jm-has-team');
        card.style.setProperty('--jm-team-color',colorFor(label));
      }else{
        card.classList.remove('jm-has-team');
        card.style.removeProperty('--jm-team-color');
      }
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

for version in ('v6','v7'):
    html = re.sub(r'<style\s+id=["\']jayuminton-team-visuals-'+version+r'["\'][^>]*>[\s\S]*?</style>\s*','',html,flags=re.I)
    html = re.sub(r'<script\s+id=["\']jayuminton-team-visuals-'+version+r'-script["\'][^>]*>[\s\S]*?</script>\s*','',html,flags=re.I)
html = html.replace('#memberApp [data-member-id].jm-has-team{box-shadow:inset 4px 0 0 var(--jm-team-color)!important}', '')
if 'JAYUMINTON_TEAM_VISUALS_V6' in html or marker in html:
    raise SystemExit('stale team visual marker survived block replacement')
if '</body>' not in html:
    raise SystemExit('body closing tag missing')
html = html.replace('</body>', addon + '\n</body>', 1)
if len(re.findall(r'<style\s+id=["\']jayuminton-team-visuals-v7["\']', html, flags=re.I)) != 1:
    raise SystemExit('fresh V7 style block count mismatch')
if len(re.findall(r'<script\s+id=["\']jayuminton-team-visuals-v7-script["\']', html, flags=re.I)) != 1:
    raise SystemExit('fresh V7 script block count mismatch')
for forbidden in ('box-shadow:inset 4px 0 0 var(--jm-team-color)', 'outline-offset:-5px'):
    if forbidden in html:
        raise SystemExit('member team line still overlays card content: '+forbidden)
path.write_text(html, encoding='utf-8')
print('TEAM_VISUALS_V7_DISTINCT_OUTER_DOUBLE_LINES_OK')
# DEPLOY_TRIGGER: distinct-outer-double-team-lines-20260827
