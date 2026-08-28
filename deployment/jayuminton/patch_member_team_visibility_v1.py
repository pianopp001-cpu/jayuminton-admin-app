#!/usr/bin/env python3
from pathlib import Path
import sys

MARK='JAYUMINTON_MEMBER_TEAM_VISIBILITY_V2'
ADDON=r'''
<style id="jayuminton-member-team-visibility-v2">
/* JAYUMINTON_MEMBER_TEAM_VISIBILITY_V2 */
#memberApp [data-member-id].jm-user-permanent-team{border:2px solid var(--jm-user-team-color,#7c3aed)!important;outline:none!important;box-shadow:0 0 0 2px #fff,0 0 0 4px var(--jm-user-team-color,#7c3aed)!important;overflow:visible!important}
#memberApp [data-member-id].jm-user-temp-team{border:2px solid #d4a017!important;outline:none!important;box-shadow:0 0 0 2px #fff,0 0 0 4px #d4a017!important;overflow:visible!important}
#memberApp [data-member-id].jm-user-permanent-team.jm-user-temp-team{box-shadow:0 0 0 2px #fff,0 0 0 4px var(--jm-user-team-color,#7c3aed),0 0 0 6px #fff,0 0 0 8px #d4a017!important}
#memberApp [data-member-id] .jm-user-card-flags{display:flex!important;justify-content:center!important;align-items:center!important;gap:3px!important;flex-wrap:wrap!important;width:100%!important;margin:2px 0 0!important;pointer-events:none!important}
#memberApp [data-member-id] .jm-user-card-flag{display:inline-flex!important;align-items:center!important;justify-content:center!important;min-height:15px!important;padding:1px 5px!important;border-radius:999px!important;font-size:8px!important;font-weight:950!important;line-height:1.15!important;white-space:nowrap!important;box-sizing:border-box!important}
#memberApp [data-member-id] .jm-user-card-flag-new{background:#fff1f2!important;color:#be123c!important;border:1px solid #fda4af!important}
#memberApp [data-member-id] .jm-user-card-flag-sponsor{background:#fff7ed!important;color:#c2410c!important;border:1px solid #fdba74!important}
</style>
<script id="jayuminton-member-team-visibility-v2-script">
(function(){
 if(window.__JAYUMINTON_MEMBER_TEAM_VISIBILITY_V2__)return;window.__JAYUMINTON_MEMBER_TEAM_VISIBILITY_V2__=true;
 var palette=['#7c3aed','#0891b2','#ea580c','#059669','#db2777','#2563eb','#ca8a04','#dc2626','#4f46e5','#0d9488','#9333ea','#65a30d','#e11d48','#0284c7','#a21caf','#16a34a'];
 function getState(){try{return window.STATE||(typeof STATE!=='undefined'?STATE:null);}catch(e){return null;}}
 function color(label){var h=0;String(label||'').split('').forEach(function(c){h=((h*31)+c.charCodeAt(0))>>>0;});return palette[h%palette.length];}
 function truthy(v){return v===true||v===1||v==='1'||String(v||'').toLowerCase()==='true'||String(v||'').toLowerCase()==='yes';}
 function isNew(m){return !!m&&(truthy(m.isNew)||truthy(m.newMember)||truthy(m.new)||truthy(m.isNewMember));}
 function isSponsor(m){return !!m&&(truthy(m.sponsor)||truthy(m.isSponsor)||truthy(m.sponsored)||truthy(m.donation)||truthy(m.isDonation)||truthy(m.contribution));}
 function flags(card,m){
  var old=card.querySelector('.jm-user-card-flags'),html='';
  if(isNew(m))html+='<span class="jm-user-card-flag jm-user-card-flag-new">NEW 신규</span>';
  if(isSponsor(m))html+='<span class="jm-user-card-flag jm-user-card-flag-sponsor">🎁 찬조</span>';
  if(!html){if(old)old.remove();return;}
  if(!old){old=document.createElement('span');old.className='jm-user-card-flags';card.appendChild(old);}
  if(old.innerHTML!==html)old.innerHTML=html;
 }
 function sync(){
  var s=getState();if(!s||!Array.isArray(s.members))return;
  var members={};s.members.forEach(function(m){members[String(m.id)]=m;});
  var temp={};(Array.isArray(s.tempPairs)?s.tempPairs:[]).forEach(function(g){var ids=Array.isArray(g.members)&&g.members.length?g.members:[].concat(g.pairA||[],g.pairB||[]);ids.forEach(function(id){temp[String(id)]=true;});});
  document.querySelectorAll('#memberApp [data-member-id]').forEach(function(card){
   var id=String(card.getAttribute('data-member-id')||''),m=members[id],team=m&&String(m.teamLabel||'').trim();
   card.classList.toggle('jm-user-permanent-team',!!team);card.classList.toggle('jm-user-temp-team',!!temp[id]);
   if(team)card.style.setProperty('--jm-user-team-color',color(team));else card.style.removeProperty('--jm-user-team-color');
   flags(card,m);
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
 # Remove our older V1 overlay so the production page cannot keep stale team-only behavior.
 import re
 text=re.sub(r'<style id="jayuminton-member-team-visibility-v1">[\s\S]*?</style>\s*','',text,flags=re.I)
 text=re.sub(r'<script id="jayuminton-member-team-visibility-v1-script">[\s\S]*?</script>\s*','',text,flags=re.I)
 if MARK not in text:
  if '</body>' not in text: raise SystemExit('body closing tag missing')
  text=text.replace('</body>',ADDON+'\n</body>',1)
 for needle in (MARK,'s.tempPairs','m.teamLabel','jm-user-permanent-team','jm-user-temp-team','jm-user-card-flag-new','jm-user-card-flag-sponsor','NEW 신규','🎁 찬조'):
  if needle not in text: raise SystemExit('user card visibility marker missing: '+needle)
 p.write_text(text,encoding='utf-8')
if __name__=='__main__':
 if len(sys.argv)!=2: raise SystemExit('usage: patch_member_team_visibility_v1.py INDEX_HTML')
 main(sys.argv[1])
