#!/usr/bin/env python3
import re, sys
from pathlib import Path
p=Path(sys.argv[1]); s=p.read_text(encoding='utf-8')
s=s.replace('선택 위치 자동배정','자동배정').replace('위치 자동배정','자동배정').replace('위치자동배정','자동배정')
s=s.replace("VOICE_GUIDE_ENABLED &&\n    'speechSynthesis' in window &&\n    (STATE.courts[courtNo] || []).length === 4", "VOICE_GUIDE_ENABLED &&\n    'speechSynthesis' in window &&\n    (STATE.courts[courtNo] || []).length >= 1")
s=re.sub(r'<button(?=[^>]*title=[\"\']현황 새로고침[\"\'])[^>]*>\s*↻?\s*새로고침\s*</button>', '', s, count=1, flags=re.S)
patch=r'''<script id="jayuminton-admin-behavior-preview-v4">
(function(){
  var activated=false, observer=null, selectedIds=new Set();
  function app(){return document.getElementById('adminApp');}
  function adminVisible(){var a=app();if(!a)return false;var cs=getComputedStyle(a);return !(a.hidden||cs.display==='none'||cs.visibility==='hidden');}
  function buttonByText(text){var a=app();return a&&Array.from(a.querySelectorAll('button')).find(function(b){return (b.textContent||'').trim()===text;});}
  function arrangeBottomButtons(){var a=app();if(!a)return;var undo=buttonByText('실행취소');var auto=Array.from(a.querySelectorAll('button')).find(function(b){return /자동배정/.test((b.textContent||'').trim());});if(auto)auto.textContent='자동배정';if(!undo||!undo.parentElement)return;var row=undo.parentElement,refresh=document.getElementById('adminBottomRefresh');if(!refresh){refresh=document.createElement('button');refresh.id='adminBottomRefresh';refresh.type='button';refresh.textContent='새로고침';refresh.onclick=function(){if(typeof refreshAdminState==='function')return refreshAdminState();if(typeof loadState==='function')return loadState();location.reload();};}row.insertBefore(refresh,undo.nextSibling);if(auto)row.insertBefore(auto,refresh.nextSibling);}
  function memberId(card){return card&&(card.getAttribute('data-member-id')||card.dataset&&card.dataset.memberId);}
  function paintSelections(){var a=app();if(!a)return;a.querySelectorAll('[data-member-id]').forEach(function(card){var id=String(memberId(card)||'');card.classList.toggle('jm-multi-selected',selectedIds.has(id));if(selectedIds.has(id)){card.style.outline='3px solid currentColor';card.style.outlineOffset='2px';}else{card.style.outline='';card.style.outlineOffset='';}});}
  function fullNewNames(){if(typeof STATE==='undefined'||!STATE||!Array.isArray(STATE.members))return;STATE.members.forEach(function(m){if(!m||!(m.isNew||m.newMember||m.is_new))return;document.querySelectorAll('#adminApp [data-member-id="'+String(m.id)+'"]').forEach(function(card){var name=card.querySelector('.member-name,.quick-member-name,.partial-name,.name,strong');if(name)name.textContent=String(m.name||m.fullName||'');card.style.minWidth='max-content';});});}
  function afterRender(){if(!activated)return;arrangeBottomButtons();fullNewNames();paintSelections();}
  function activate(){if(activated||!adminVisible())return false;activated=true;document.addEventListener('click',function(ev){var card=ev.target&&ev.target.closest&&ev.target.closest('#adminApp [data-member-id]');if(!card||ev.target.closest('button,input,select,a'))return;var id=String(memberId(card)||'');if(!id)return;ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();if(selectedIds.has(id))selectedIds.delete(id);else selectedIds.add(id);if(typeof SELECTED_MEMBER_IDS!=='undefined'&&SELECTED_MEMBER_IDS&&typeof SELECTED_MEMBER_IDS.clear==='function'){SELECTED_MEMBER_IDS.clear();selectedIds.forEach(function(x){SELECTED_MEMBER_IDS.add(x);});}else if(typeof toggleSelected==='function')toggleSelected(id);paintSelections();},true);afterRender();return true;}
  function watch(){if(activate()){}if(!observer){observer=new MutationObserver(function(){if(!activated)activate();else afterRender();});observer.observe(document.body||document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['style','class','hidden']});}}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',watch,{once:true});else setTimeout(watch,0);window.addEventListener('jayuminton-admin-login-success',watch);
})();
</script>'''
if '</body>' not in s: raise SystemExit('body marker missing')
s=s.replace('</body>',patch+'\n</body>',1)
for required in ['자동배정','adminBottomRefresh','jayuminton-admin-behavior-preview-v4','adminVisible','jm-multi-selected']:
    if required not in s: raise SystemExit('missing '+required)
p.write_text(s,encoding='utf-8')
