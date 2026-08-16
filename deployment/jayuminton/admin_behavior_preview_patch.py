#!/usr/bin/env python3
import re, sys
from pathlib import Path
p=Path(sys.argv[1]); s=p.read_text(encoding='utf-8')

s=s.replace('선택 위치 자동배정','자동배정').replace('위치 자동배정','자동배정').replace('위치자동배정','자동배정')
s=s.replace("VOICE_GUIDE_ENABLED &&\n    'speechSynthesis' in window &&\n    (STATE.courts[courtNo] || []).length === 4", "VOICE_GUIDE_ENABLED &&\n    'speechSynthesis' in window &&\n    (STATE.courts[courtNo] || []).length >= 1")

# Remove every pre-existing refresh button in the admin app by its visible label or refresh-ish id/title.
s=re.sub(r'<button\b(?=[^>]*(?:id=[\"\'][^\"\']*refresh[^\"\']*[\"\']|title=[\"\'][^\"\']*새로고침[^\"\']*[\"\']))[^>]*>.*?</button>', '', s, flags=re.I|re.S)
s=re.sub(r'<button\b[^>]*>\s*(?:↻|⟳|🔄)?\s*새로고침\s*</button>', '', s, flags=re.S)

# Replace the ACTUAL bottom mobile quick bar in Admin.html, instead of moving nodes later.
mobile_pat=re.compile(r'<div class="mobile-quick-bar">.*?</div>', re.S)
mobile_new='''<div class="mobile-quick-bar admin-bottom-controls" id="adminBottomControls">
    <button id="mobileUndoButton" class="ghost-button undo-button mobile-undo-button" onclick="undoLastAction()" disabled>실행취소</button>
    <button id="adminBottomRefresh" class="ghost-button" type="button" onclick="loadState()">새로고침</button>
    <button id="adminBottomAutoAssign" class="primary mobile-assign-button" type="button" onclick="smartAssignSelected()">자동배정</button>
  </div>'''
s,n=mobile_pat.subn(mobile_new,s,count=1)
if n != 1: raise SystemExit('actual mobile-quick-bar marker missing')

patch=r'''<style id="jayuminton-admin-bottom-controls-style">
#adminBottomControls{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;align-items:stretch!important;gap:8px!important;width:100%!important;position:sticky!important;bottom:0!important;z-index:120!important;padding:10px!important;margin:12px 0 0!important;background:rgba(255,255,255,.96)!important;box-sizing:border-box!important}
#adminBottomControls button{display:block!important;width:100%!important;min-width:0!important;margin:0!important;white-space:nowrap!important}
/* No other refresh control may remain visible in the authenticated admin app. */
#adminApp button[id*="refresh" i]:not(#adminBottomRefresh),#adminApp button[title*="새로고침"]{display:none!important}
</style>
<script id="jayuminton-admin-behavior-preview-v7">
(function(){
  var activated=false, selectedIds=new Set(), renderTimer=0;
  function app(){return document.getElementById('adminApp');}
  function visible(el){if(!el)return false;var cs=getComputedStyle(el);return !el.hidden&&cs.display!=='none'&&cs.visibility!=='hidden';}
  function adminVisible(){return visible(app());}
  function enforceBottomControls(){var row=document.getElementById('adminBottomControls');if(!row)return;var buttons=row.querySelectorAll('button');if(buttons.length!==3)return;buttons[0].textContent='실행취소';buttons[1].textContent='새로고침';buttons[2].textContent='자동배정';document.querySelectorAll('#adminApp button').forEach(function(b){if(b===buttons[1])return;var text=(b.textContent||'').replace(/\s+/g,'').trim();var id=String(b.id||'').toLowerCase();var title=String(b.title||'');if(text==='새로고침'||id.indexOf('refresh')>=0||title.indexOf('새로고침')>=0)b.style.setProperty('display','none','important');});}
  function memberId(card){return card&&(card.getAttribute('data-member-id')||(card.dataset&&card.dataset.memberId));}
  function paintSelections(){var a=app();if(!a)return;a.querySelectorAll('[data-member-id]').forEach(function(card){var id=String(memberId(card)||''),on=selectedIds.has(id);card.classList.toggle('jm-multi-selected',on);card.style.outline=on?'3px solid currentColor':'';card.style.outlineOffset=on?'2px':'';});}
  function fullNewNames(){if(typeof STATE==='undefined'||!STATE||!Array.isArray(STATE.members))return;STATE.members.forEach(function(m){if(!m||!(m.isNew||m.newMember||m.is_new))return;document.querySelectorAll('#adminApp [data-member-id="'+String(m.id)+'"]').forEach(function(card){var name=card.querySelector('.member-name,.quick-member-name,.partial-name,.name,strong');if(name&&name.textContent!==String(m.name||m.fullName||''))name.textContent=String(m.name||m.fullName||'');card.style.minWidth='max-content';});});}
  function afterRender(){if(!activated||!adminVisible())return;enforceBottomControls();fullNewNames();paintSelections();}
  function scheduleRender(){clearTimeout(renderTimer);renderTimer=setTimeout(afterRender,40);}
  function activate(){if(activated||!adminVisible())return false;activated=true;var a=app();a.addEventListener('click',function(ev){var card=ev.target&&ev.target.closest&&ev.target.closest('[data-member-id]');if(!card||ev.target.closest('button,input,select,a'))return;var id=String(memberId(card)||'');if(!id)return;ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();if(selectedIds.has(id))selectedIds.delete(id);else selectedIds.add(id);if(typeof SELECTED!=='undefined'&&SELECTED&&typeof SELECTED.clear==='function'){SELECTED.clear();selectedIds.forEach(function(x){SELECTED.add(x);});}paintSelections();},true);new MutationObserver(scheduleRender).observe(a,{childList:true,subtree:true});afterRender();return true;}
  function waitForAdmin(){if(activate())return;var timer=setInterval(function(){if(activate())clearInterval(timer);},250);setTimeout(function(){clearInterval(timer);},120000);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',waitForAdmin,{once:true});else setTimeout(waitForAdmin,0);
})();
</script>'''
if '</body>' not in s: raise SystemExit('body marker missing')
s=s.replace('</body>',patch+'\n</body>',1)

# Structural assertions: exact bottom row and no literal old auto-assign wording.
for required in ['id="adminBottomControls"','id="adminBottomRefresh"','id="adminBottomAutoAssign"','>실행취소</button>','>새로고침</button>','>자동배정</button>','jayuminton-admin-behavior-preview-v7','jm-multi-selected']:
    if required not in s: raise SystemExit('missing '+required)
if '위치 자동배정' in s or '선택 위치 자동배정' in s: raise SystemExit('old auto assign label remains')
p.write_text(s,encoding='utf-8')
