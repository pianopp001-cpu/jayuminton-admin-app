#!/usr/bin/env python3
from pathlib import Path
import sys

MARK='JAYUMINTON_MEMBER_TEAM_VISIBILITY_V1'
ADDON=r'''
<style id="jayuminton-member-team-visibility-v1">
/* JAYUMINTON_MEMBER_TEAM_VISIBILITY_V1 */
#memberApp [data-member-id].jm-user-permanent-team{border:2px solid var(--jm-user-team-color,#7c3aed)!important;outline:none!important;box-shadow:0 0 0 2px #fff,0 0 0 4px var(--jm-user-team-color,#7c3aed)!important;overflow:visible!important}
#memberApp [data-member-id].jm-user-temp-team{border:2px solid #d4a017!important;outline:none!important;box-shadow:0 0 0 2px #fff,0 0 0 4px #d4a017!important;overflow:visible!important}
#memberApp [data-member-id].jm-user-permanent-team.jm-user-temp-team{box-shadow:0 0 0 2px #fff,0 0 0 4px var(--jm-user-team-color,#7c3aed),0 0 0 6px #fff,0 0 0 8px #d4a017!important}
</style>
<script id="jayuminton-member-team-visibility-v1-script">
(function(){
 if(window.__JAYUMINTON_MEMBER_TEAM_VISIBILITY_V1__)return;window.__JAYUMINTON_MEMBER_TEAM_VISIBILITY_V1__=true;
 var palette=['#7c3aed','#0891b2','#ea580c','#059669','#db2777','#2563eb','#ca8a04','#dc2626','#4f46e5','#0d9488','#9333ea','#65a30d','#e11d48','#0284c7','#a21caf','#16a34a'];
 function getState(){try{return window.STATE||(typeof STATE!=='undefined'?STATE:null);}catch(e){return null;}}
 function color(label){var h=0;String(label||'').split('').forEach(function(c){h=((h*31)+c.charCodeAt(0))>>>0;});return palette[h%palette.length];}
 function sync(){
  var s=getState();if(!s||!Array.isArray(s.members))return;
  var members={};s.members.forEach(function(m){members[String(m.id)]=m;});
  var temp={};(Array.isArray(s.tempPairs)?s.tempPairs:[]).forEach(function(g){var ids=Array.isArray(g.members)&&g.members.length?g.members:[].concat(g.pairA||[],g.pairB||[]);ids.forEach(function(id){temp[String(id)]=true;});});
  document.querySelectorAll('#memberApp [data-member-id]').forEach(function(card){
   var id=String(card.getAttribute('data-member-id')||''),m=members[id],team=m&&String(m.teamLabel||'').trim();
   card.classList.toggle('jm-user-permanent-team',!!team);card.classList.toggle('jm-user-temp-team',!!temp[id]);
   if(team)card.style.setProperty('--jm-user-team-color',color(team));else card.style.removeProperty('--jm-user-team-color');
  });
 }
 var q=false;function schedule(){if(q)return;q=true;requestAnimationFrame(function(){q=false;sync();});}
 new MutationObserver(schedule).observe(document.documentElement,{childList:true,subtree:true});
 document.addEventListener('DOMContentLoaded',schedule,{once:true});document.addEventListener('click',function(){setTimeout(schedule,80);},true);setInterval(schedule,1200);schedule();
})();
</script>
'''

def main(path):
 p=Path(path); text=p.read_text(encoding='utf-8')
 if MARK not in text:
  if '</body>' not in text: raise SystemExit('body closing tag missing')
  text=text.replace('</body>',ADDON+'\n</body>',1)
 for needle in (MARK,'s.tempPairs','m.teamLabel','jm-user-permanent-team','jm-user-temp-team'):
  if needle not in text: raise SystemExit('team visibility marker missing: '+needle)
 p.write_text(text,encoding='utf-8')
if __name__=='__main__':
 if len(sys.argv)!=2: raise SystemExit('usage: patch_member_team_visibility_v1.py INDEX_HTML')
 main(sys.argv[1])
