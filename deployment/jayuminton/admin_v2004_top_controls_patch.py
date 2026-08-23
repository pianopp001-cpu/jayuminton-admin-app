#!/usr/bin/env python3
from pathlib import Path
import sys
p=Path(sys.argv[1])
s=p.read_text(encoding='utf-8')
if 'data-jm-top-controls' in s:
    print('V2004_TOP_CONTROLS_ALREADY_PRESENT')
    raise SystemExit(0)
marker='</body>'
if marker not in s:
    raise SystemExit('body marker missing')
patch=r'''<style id="jayuminton-v2004-top-controls-style">
[data-jm-top-controls]{position:sticky;top:0;z-index:99990;display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;padding:7px 8px;background:rgba(255,255,255,.97);box-shadow:0 2px 8px rgba(0,0,0,.08)}
[data-jm-top-controls] button{min-height:38px;border:0;border-radius:10px;font-weight:800;font-size:14px;white-space:nowrap}
</style>
<div data-jm-top-controls="v2004">
  <button type="button" data-jm-top-refresh>새로고침</button>
  <button type="button" data-jm-top-auto>자동배정</button>
  <button type="button" data-jm-top-undo>실행취소</button>
</div>
<script id="jayuminton-v2004-top-controls-script">
(function(){
 function clickAny(selectors,texts){
   var list=[]; selectors.forEach(function(q){try{document.querySelectorAll(q).forEach(function(x){list.push(x);});}catch(e){}});
   if(!list.length){document.querySelectorAll('button').forEach(function(x){var t=(x.textContent||'').trim();if(texts.indexOf(t)>=0)list.push(x);});}
   var el=list.find(function(x){return x&&x.offsetParent!==null;})||list[0]; if(el){el.click();return true;} return false;
 }
 var r=document.querySelector('[data-jm-top-refresh]'),a=document.querySelector('[data-jm-top-auto]'),u=document.querySelector('[data-jm-top-undo]');
 if(r)r.onclick=function(){if(typeof window.refreshState==='function')window.refreshState();else clickAny(['#mobile-refresh-button','.mobile-refresh-button','[data-action="refresh"]'],['새로고침']);};
 if(a)a.onclick=function(){if(typeof window.autoAssign==='function')window.autoAssign();else clickAny(['#autoAssignButton','[data-action="auto-assign"]'],['자동배정','자동 배정']);};
 if(u)u.onclick=function(){if(typeof window.undoLastAction==='function')window.undoLastAction();else clickAny(['#undoButton','[data-action="undo"]'],['실행취소','실행 취소']);};
 window.__JAYUMINTON_ADMIN_TOP_CONTROLS_V2004__=true;
})();
</script>'''
s=s.replace(marker,patch+'\n'+marker,1)
for x in ['data-jm-top-controls','data-jm-top-refresh','data-jm-top-auto','data-jm-top-undo','__JAYUMINTON_ADMIN_TOP_CONTROLS_V2004__']:
    if x not in s: raise SystemExit('missing '+x)
p.write_text(s,encoding='utf-8')
print('V2004_TOP_CONTROLS_OK')
