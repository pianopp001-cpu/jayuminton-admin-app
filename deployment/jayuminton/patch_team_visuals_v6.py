#!/usr/bin/env python3
from pathlib import Path
import sys

# v6.1: final redeploy after admin inline border hardening.
if len(sys.argv) != 2:
    raise SystemExit('usage: patch_team_visuals_v6.py <html>')
path = Path(sys.argv[1])
html = path.read_text(encoding='utf-8')
marker = 'JAYUMINTON_TEAM_VISUALS_V6'
if marker in html:
    print('TEAM_VISUALS_V6_ALREADY_PRESENT')
    raise SystemExit(0)

addon = r'''
<style id="jayuminton-team-visuals-v6">
/* JAYUMINTON_TEAM_VISUALS_V6 */
/* Official teams: preserve the male/female background. No right-side badge and no left stripe. */
#adminApp .has-member-team{
  box-shadow:none!important;
  padding-left:inherit!important;
  border:2px solid var(--member-team-color)!important;
  outline:2px solid var(--member-team-color)!important;
  outline-offset:-5px!important;
  background-clip:padding-box!important;
}
#adminApp .member-team-badge,#adminApp .jm-team-badge,#adminApp .team-badge,#adminApp .team-label,#adminApp [data-team-label]{
  display:none!important;visibility:hidden!important;position:static!important;inset:auto!important;
}
#adminApp .jm-team-bottom-label{
  display:block!important;position:static!important;inset:auto!important;float:none!important;clear:both!important;
  width:100%!important;box-sizing:border-box!important;margin:3px 0 0!important;padding:0!important;
  text-align:left!important;font-size:9px!important;line-height:1.15!important;font-weight:900!important;
  white-space:nowrap!important;overflow:visible!important;color:var(--member-team-color)!important;
}
#memberApp [data-member-id].jm-has-team{
  box-shadow:none!important;
  border:2px solid var(--jm-team-color)!important;
  outline:2px solid var(--jm-team-color)!important;
  outline-offset:-5px!important;
  background-clip:padding-box!important;
}
#memberApp [data-member-id]>.jm-member-badges{
  order:999!important;position:static!important;inset:auto!important;transform:none!important;
  display:flex!important;align-items:center!important;justify-content:flex-start!important;
  width:100%!important;box-sizing:border-box!important;margin:3px 0 0!important;padding:0!important;
  text-align:left!important;overflow:visible!important;
}
#memberApp [data-member-id]>.jm-member-badges .jm-team-badge{
  position:static!important;inset:auto!important;transform:none!important;
  display:inline-flex!important;width:auto!important;max-width:100%!important;height:auto!important;
  margin:0!important;padding:1px 3px!important;border-radius:4px!important;
  font-size:9px!important;line-height:1.15!important;font-weight:900!important;
  white-space:nowrap!important;overflow:visible!important;text-overflow:clip!important;
  background:transparent!important;
}
</style>
<script id="jayuminton-team-visuals-v6-script">
(function(){
  'use strict';
  if(window.__JAYUMINTON_TEAM_VISUALS_V6__)return;
  window.__JAYUMINTON_TEAM_VISUALS_V6__=true;
  function normalizeLabel(text){
    var s=String(text||'').replace(/\s+/g,'').trim();
    if(/^TEAM\d+$/i.test(s))s=s.replace(/^TEAM/i,'팀');
    return /^팀\d+$/.test(s)?s:'';
  }
  function fixUser(){
    document.querySelectorAll('#memberApp [data-member-id]').forEach(function(card){
      var wrap=card.querySelector('.jm-member-badges');
      var badge=wrap&&wrap.querySelector('.jm-team-badge');
      if(!badge)return;
      var label=normalizeLabel(badge.textContent);if(label&&badge.textContent!==label)badge.textContent=label;
      if(wrap.parentElement!==card)card.appendChild(wrap);else if(card.lastElementChild!==wrap)card.appendChild(wrap);
    });
  }
  function fixAdmin(){
    document.querySelectorAll('#adminApp .has-member-team').forEach(function(card){
      var label=normalizeLabel(card.getAttribute('data-jm-team-text'));
      var nodes=card.querySelectorAll('.member-team-badge,.jm-team-badge,.team-badge,.team-label,[data-team-label]');
      nodes.forEach(function(node){
        var found=normalizeLabel(node.textContent||node.getAttribute('data-team-label'));
        if(!label&&found)label=found;
        node.style.setProperty('display','none','important');
        node.setAttribute('aria-hidden','true');
      });
      if(!label){
        card.querySelectorAll('span,small,b,strong,em,label').forEach(function(node){
          if(node.classList.contains('jm-team-bottom-label'))return;
          var found=normalizeLabel(node.textContent);if(found&&!label){label=found;node.style.setProperty('display','none','important');node.setAttribute('aria-hidden','true');}
        });
      }
      if(label){
        card.setAttribute('data-jm-team-text',label);
        var bottom=card.querySelector('.jm-team-bottom-label');
        if(!bottom){bottom=document.createElement('small');bottom.className='jm-team-bottom-label';}
        bottom.textContent=label;
        if(bottom.parentElement!==card||card.lastElementChild!==bottom)card.appendChild(bottom);
      }
    });
  }
  var queued=false;function run(){queued=false;fixUser();fixAdmin();}
  function schedule(){if(queued)return;queued=true;requestAnimationFrame(run);}
  new MutationObserver(schedule).observe(document.documentElement,{childList:true,subtree:true,characterData:true});
  document.addEventListener('DOMContentLoaded',schedule,{once:true});
  setInterval(schedule,1600);schedule();
})();
</script>
'''
if '</body>' not in html:
    raise SystemExit('body closing tag missing')
html = html.replace('</body>', addon + '\n</body>', 1)
path.write_text(html, encoding='utf-8')
print('TEAM_VISUALS_V6_OK')
