#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: admin_top_controls_final_patch.py INDEX_HTML')

path = Path(sys.argv[1])
html = path.read_text(encoding='utf-8')
if '</body>' not in html:
    raise SystemExit('body marker missing')

marker='__JAYUMINTON_ADMIN_BOTTOM_CONTROLS_FINAL_V2__'
if marker not in html:
    addon=r'''
<style id="jayuminton-admin-bottom-controls-final-v2">
#adminApp>header .header-undo-button{display:none!important}
#adminApp>.admin-vnext-bottom-bar{position:static!important;left:auto!important;right:auto!important;bottom:auto!important;top:auto!important;z-index:auto!important;display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:8px!important;align-items:stretch!important;width:100%!important;max-width:1180px!important;margin:14px auto max(14px,env(safe-area-inset-bottom))!important;padding:6px 12px 10px!important;box-sizing:border-box!important;background:transparent!important;border:0!important;box-shadow:none!important}
#adminApp>.admin-vnext-bottom-bar>span{display:none!important}
#adminApp>.admin-vnext-bottom-bar>button{display:flex!important;align-items:center!important;justify-content:center!important;width:100%!important;min-width:0!important;min-height:44px!important;height:44px!important;margin:0!important;padding:7px 4px!important;font-size:14px!important;line-height:1.05!important;font-weight:900!important;text-align:center!important;white-space:nowrap!important;overflow:hidden!important}
.admin-save-notice{z-index:2147483647!important;touch-action:none!important;overscroll-behavior:none!important}
.admin-save-notice.is-visible{pointer-events:all!important}
@media(max-width:620px){body{padding-bottom:0!important}#adminApp>.admin-vnext-bottom-bar{padding:5px 8px 8px!important}}
@media(max-width:380px){#adminApp>.admin-vnext-bottom-bar{gap:5px!important}#adminApp>.admin-vnext-bottom-bar>button{font-size:12px!important;padding:6px 2px!important}}
</style>
<script id="jayuminton-admin-bottom-controls-final-script-v2">
(function(){
  'use strict';
  var scheduled=false;
  function apply(){
    scheduled=false;
    var app=document.getElementById('adminApp'); if(!app)return;
    var bar=app.querySelector('.admin-vnext-bottom-bar');
    if(!bar)return;
    if(bar.parentElement!==app || bar!==app.lastElementChild)app.appendChild(bar);
    bar.removeAttribute('data-jm-top-controls');
    if(bar.getAttribute('data-jm-bottom-controls')!=='1')bar.setAttribute('data-jm-bottom-controls','1');
    var buttons=bar.querySelectorAll(':scope>button');
    if(buttons.length===3){
      if(buttons[0].textContent!=='실행취소')buttons[0].textContent='실행취소';
      if(!buttons[1].disabled&&buttons[1].textContent!=='새로고침')buttons[1].textContent='새로고침';
      if(buttons[2].textContent!=='자동배정')buttons[2].textContent='자동배정';
    }
    window.__JAYUMINTON_ADMIN_BOTTOM_CONTROLS_FINAL_V2__=true;
  }
  function schedule(){if(scheduled)return;scheduled=true;requestAnimationFrame(apply);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply,{once:true});else apply();
  new MutationObserver(schedule).observe(document.documentElement,{childList:true,subtree:true});
})();
</script>
'''
    html=html.replace('</body>',addon+'\n</body>',1)

required=['admin-vnext-bottom-bar','data-jm-bottom-controls','실행취소','새로고침','자동배정','z-index:2147483647',marker]
for item in required:
    if item not in html:
        raise SystemExit('bottom controls final patch missing: '+item)
path.write_text(html,encoding='utf-8')
print('ADMIN_BOTTOM_CONTROLS_FINAL_V2_OK')
