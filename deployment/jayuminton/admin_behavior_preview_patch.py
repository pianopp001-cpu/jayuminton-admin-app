#!/usr/bin/env python3
import re, sys
from pathlib import Path
p=Path(sys.argv[1]); s=p.read_text(encoding='utf-8')
s=s.replace('선택 위치 자동배정','자동배정').replace('위치 자동배정','자동배정').replace('위치자동배정','자동배정')
s=s.replace("VOICE_GUIDE_ENABLED &&\n    'speechSynthesis' in window &&\n    (STATE.courts[courtNo] || []).length === 4", "VOICE_GUIDE_ENABLED &&\n    'speechSynthesis' in window &&\n    (STATE.courts[courtNo] || []).length >= 1")
s=re.sub(r'<button(?=[^>]*title=[\"\']현황 새로고침[\"\'])[^>]*>\s*↻?\s*새로고침\s*</button>', '', s, count=1, flags=re.S)
patch=r'''<style id="jayuminton-admin-bottom-controls-style">
#adminBottomControls{display:flex!important;align-items:center!important;justify-content:center!important;gap:8px!important;flex-wrap:nowrap!important;margin:12px auto 18px!important;width:100%!important}
#adminBottomControls button{flex:1 1 0!important;min-width:0!important;white-space:nowrap!important}
</style>
<script id="jayuminton-admin-behavior-preview-v6">
(function(){
  var activated=false, selectedIds=new Set(), renderTimer=0;
  function app(){return document.getElementById('adminApp');}
  function visible(el){if(!el)return false;var cs=getComputedStyle(el);return !el.hidden&&cs.display!=='none'&&cs.visibility!=='hidden';}
  function adminVisible(){return visible(app());}
  function findAuto(){var a=app();return a&&Array.from(a.querySelectorAll('button')).find(function(b){return /자동배정/.test((b.textContent||'').trim());});}
  function arrangeBottomButtons(){var a=app();if(!a)return;var mobile=document.querySelector('.mobile-quick-bar');var undo=document.getElementById('mobileUndoButton')||document.getElementById('undoButton');var auto=(mobile&&Array.from(mobile.querySelectorAll('button')).find(function(b){return /자동배정/.test((b.textContent||'').trim());}))||findAuto();if(auto)auto.textContent='자동배정';if(!undo||!auto)return;var row=document.getElementById('adminBottomControls');if(!row){row=document.createElement('div');row.id='adminBottomControls';var anchor=mobile||a.lastElementChild;a.insertBefore(row,anchor?anchor.nextSibling:null);}var refresh=document.getElementById('adminBottomRefresh');if(!refresh){refresh=document.createElement('button');refresh.id='adminBottomRefresh';refresh.type='button';refresh.textContent='새로고침';refresh.onclick=function(){if(typeof loadState==='function')return loadState();location.reload();};}row.appendChild(undo);row.appendChild(refresh);row.appendChild(auto);if(mobile)mobile.style.display='none';}
  function memberId(card){return card&&(card.getAttribute('data-member-id')||(card.dataset&&card.dataset.memberId));}
  function paintSelections(){var a=app();if(!a)return;a.querySelectorAll('[data-member-id]').forEach(function(card){var id=String(memberId(card)||''),on=selectedIds.has(id);card.classList.toggle('jm-multi-selected',on);card.style.outline=on?'3px solid currentColor':'';card.style.outlineOffset=on?'2px':'';});}
  function fullNewNames(){if(typeof STATE==='undefined'||!STATE||!Array.isArray(STATE.members))return;STATE.members.forEach(function(m){if(!m||!(m.isNew||m.newMember||m.is_new))return;document.querySelectorAll('#adminApp [data-member-id="'+String(m.id)+'"]').forEach(function(card){var name=card.querySelector('.member-name,.quick-member-name,.partial-name,.name,strong');if(name&&name.textContent!==String(m.name||m.fullName||''))name.textContent=String(m.name||m.fullName||'');card.style.minWidth='max-content';});});}
  function afterRender(){if(!activated||!adminVisible())return;arrangeBottomButtons();fullNewNames();paintSelections();}
  function scheduleRender(){clearTimeout(renderTimer);renderTimer=setTimeout(afterRender,40);}
  function activate(){if(activated||!adminVisible())return false;activated=true;var a=app();a.addEventListener('click',function(ev){var card=ev.target&&ev.target.closest&&ev.target.closest('[data-member-id]');if(!card||ev.target.closest('button,input,select,a'))return;var id=String(memberId(card)||'');if(!id)return;ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();if(selectedIds.has(id))selectedIds.delete(id);else selectedIds.add(id);if(typeof SELECTED!=='undefined'&&SELECTED&&typeof SELECTED.clear==='function'){SELECTED.clear();selectedIds.forEach(function(x){SELECTED.add(x);});}paintSelections();},true);new MutationObserver(scheduleRender).observe(a,{childList:true,subtree:true});afterRender();return true;}
  function waitForAdmin(){if(activate())return;var timer=setInterval(function(){if(activate())clearInterval(timer);},250);setTimeout(function(){clearInterval(timer);},120000);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',waitForAdmin,{once:true});else setTimeout(waitForAdmin,0);
})();
</script>'''
if '</body>' not in s: raise SystemExit('body marker missing')
s=s.replace('</body>',patch+'\n</body>',1)
for required in ['자동배정','adminBottomControls','adminBottomRefresh','jayuminton-admin-behavior-preview-v6','jm-multi-selected']:
    if required not in s: raise SystemExit('missing '+required)
p.write_text(s,encoding='utf-8')
