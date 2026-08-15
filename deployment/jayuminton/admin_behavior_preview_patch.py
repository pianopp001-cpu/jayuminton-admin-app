#!/usr/bin/env python3
import re, sys
from pathlib import Path

p=Path(sys.argv[1])
s=p.read_text(encoding='utf-8')

# Safe source-level changes only: wording and finish announcement condition.
s=s.replace('선택 위치 자동배정','자동배정').replace('위치 자동배정','자동배정').replace('위치자동배정','자동배정')
s=s.replace("VOICE_GUIDE_ENABLED &&\n    'speechSynthesis' in window &&\n    (STATE.courts[courtNo] || []).length === 4", "VOICE_GUIDE_ENABLED &&\n    'speechSynthesis' in window &&\n    (STATE.courts[courtNo] || []).length >= 1")

# Remove only the known header refresh markup. Runtime DOM work is deferred until adminApp is actually visible.
s=re.sub(r'<button(?=[^>]*title=[\"\']현황 새로고침[\"\'])[^>]*>\s*↻?\s*새로고침\s*</button>', '', s, count=1, flags=re.S)

patch=r'''<script id="jayuminton-admin-behavior-preview-v3">
(function(){
  var activated=false, observer=null;
  function adminVisible(){
    var app=document.getElementById('adminApp');
    if(!app)return false;
    var cs=window.getComputedStyle?getComputedStyle(app):null;
    return !(app.hidden || (cs && (cs.display==='none'||cs.visibility==='hidden')));
  }
  function buttonByText(text){return Array.from(document.querySelectorAll('#adminApp button')).find(function(b){return (b.textContent||'').trim()===text;});}
  function arrangeBottomButtons(){
    if(!activated)return;
    var undo=buttonByText('실행취소');
    var auto=Array.from(document.querySelectorAll('#adminApp button')).find(function(b){return /자동배정/.test((b.textContent||'').trim());});
    if(auto)auto.textContent='자동배정';
    if(!undo||!undo.parentElement)return;
    var row=undo.parentElement;
    var refresh=document.getElementById('adminBottomRefresh');
    if(!refresh){
      refresh=document.createElement('button');refresh.id='adminBottomRefresh';refresh.type='button';refresh.textContent='새로고침';
      refresh.onclick=function(){if(typeof refreshAdminState==='function')return refreshAdminState();if(typeof loadState==='function')return loadState();location.reload();};
    }
    row.insertBefore(refresh,undo.nextSibling);
    if(auto)row.insertBefore(auto,refresh.nextSibling);
  }
  function fullNewNames(){
    if(!activated||typeof STATE==='undefined'||!STATE||!Array.isArray(STATE.members))return;
    STATE.members.forEach(function(m){
      if(!m||!m.isNew)return;
      document.querySelectorAll('#adminApp [data-member-id="'+String(m.id)+'"]').forEach(function(card){
        var name=card.querySelector('.member-name,.quick-member-name,.partial-name,.name,strong');
        if(name)name.textContent=String(m.name||'');
        card.style.minWidth='max-content';
      });
    });
  }
  function afterRender(){if(!activated)return;arrangeBottomButtons();fullNewNames();}
  function activate(){
    if(activated||!adminVisible())return false;
    activated=true;
    var oldRender=window.renderState;
    if(typeof oldRender==='function'&&!oldRender.__jmBehaviorV3){
      var wrapped=function(){var r=oldRender.apply(this,arguments);setTimeout(afterRender,0);return r;};
      wrapped.__jmBehaviorV3=true;window.renderState=wrapped;
    }
    document.addEventListener('click',function(ev){
      if(!activated)return;
      var card=ev.target&&ev.target.closest&&ev.target.closest('#adminApp [data-member-id]');
      if(!card||ev.target.closest('button,input,select,a'))return;
      var id=card.getAttribute('data-member-id');
      if(!id||typeof toggleSelected!=='function')return;
      ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();
      if(typeof QUICK_PICK!=='undefined')QUICK_PICK=null;
      toggleSelected(id);setTimeout(afterRender,0);
    },true);
    afterRender();
    return true;
  }
  function watchForLogin(){
    if(activate()){if(observer)observer.disconnect();return;}
    if(!observer){observer=new MutationObserver(function(){activate();});observer.observe(document.body||document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['style','class','hidden']});}
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',watchForLogin,{once:true});else setTimeout(watchForLogin,0);
  window.addEventListener('jayuminton-admin-login-success',watchForLogin);
})();
</script>'''
if '</body>' not in s: raise SystemExit('body marker missing')
s=s.replace('</body>',patch+'\n</body>',1)
for required in ['자동배정','adminBottomRefresh','jayuminton-admin-behavior-preview-v3','adminVisible']:
    if required not in s: raise SystemExit('missing '+required)
p.write_text(s,encoding='utf-8')
