#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: admin_top_controls_final_patch.py INDEX_HTML')

path = Path(sys.argv[1])
html = path.read_text(encoding='utf-8')
if '</body>' not in html:
    raise SystemExit('body marker missing')

marker='__JAYUMINTON_ADMIN_TOP_CONTROLS_FINAL_V1__'
if marker not in html:
    addon=r'''
<style id="jayuminton-admin-top-controls-final-v1">
#adminApp>header .admin-vnext-bottom-bar{position:static!important;left:auto!important;right:auto!important;bottom:auto!important;top:auto!important;z-index:auto!important;display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:8px!important;align-items:stretch!important;width:100%!important;max-width:1180px!important;margin:0 auto!important;padding:6px 12px 10px!important;box-sizing:border-box!important;background:transparent!important;border:0!important;box-shadow:none!important}
#adminApp>header .admin-vnext-bottom-bar>span{display:none!important}
#adminApp>header .admin-vnext-bottom-bar>button{display:flex!important;align-items:center!important;justify-content:center!important;width:100%!important;min-width:0!important;min-height:44px!important;height:44px!important;margin:0!important;padding:7px 4px!important;font-size:14px!important;line-height:1.05!important;font-weight:900!important;text-align:center!important;white-space:nowrap!important;overflow:hidden!important}
@media(max-width:620px){body{padding-bottom:0!important}#adminApp>header .admin-vnext-bottom-bar{padding:5px 8px 8px!important}}
@media(max-width:380px){#adminApp>header .admin-vnext-bottom-bar{gap:5px!important}#adminApp>header .admin-vnext-bottom-bar>button{font-size:12px!important;padding:6px 2px!important}}
</style>
<script id="jayuminton-admin-top-controls-final-script-v1">
(function(){
  'use strict';
  function apply(){
    var app=document.getElementById('adminApp'); if(!app)return;
    var header=app.querySelector(':scope>header');
    var bar=app.querySelector('.admin-vnext-bottom-bar');
    if(!header||!bar)return;
    if(bar.parentElement!==header)header.appendChild(bar);
    bar.setAttribute('data-jm-top-controls','1');
    var buttons=bar.querySelectorAll(':scope>button');
    if(buttons.length===3){
      buttons[0].textContent='실행취소';
      if(!buttons[1].disabled)buttons[1].textContent='새로고침';
      buttons[2].textContent='자동배정';
    }
    window.__JAYUMINTON_ADMIN_TOP_CONTROLS_FINAL_V1__=true;
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply,{once:true});else apply();
  new MutationObserver(apply).observe(document.documentElement,{childList:true,subtree:true});
})();
</script>
'''
    html=html.replace('</body>',addon+'\n</body>',1)

required=['admin-vnext-bottom-bar','data-jm-top-controls','실행취소','새로고침','자동배정',marker]
for item in required:
    if item not in html:
        raise SystemExit('top controls final patch missing: '+item)
path.write_text(html,encoding='utf-8')
print('ADMIN_TOP_CONTROLS_FINAL_V1_OK')
