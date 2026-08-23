#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: admin_top_controls_final_patch.py INDEX_HTML')

path = Path(sys.argv[1])
html = path.read_text(encoding='utf-8')
if '</body>' not in html:
    raise SystemExit('body marker missing')

# Remove prior V2 addon if input came from an older final build.
old_start = html.find('<style id="jayuminton-admin-bottom-controls-final-v2">')
if old_start >= 0:
    old_end = html.find('</script>', old_start)
    if old_end >= 0:
        html = html[:old_start] + html[old_end + len('</script>'):]
html = html.replace('<!-- __JAYUMINTON_ADMIN_BOTTOM_CONTROLS_FINAL_V2__ -->', '')

marker='__JAYUMINTON_ADMIN_BOTTOM_CONTROLS_FIXED_V3__'
addon=r'''
<style id="jayuminton-admin-bottom-controls-fixed-v3">
#adminApp>header .header-undo-button{display:none!important}
body{padding-bottom:calc(76px + env(safe-area-inset-bottom))!important}
#adminApp>.admin-vnext-bottom-bar{
  position:fixed!important;
  left:0!important;right:0!important;bottom:0!important;top:auto!important;
  z-index:2147483000!important;
  display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;
  gap:7px!important;align-items:stretch!important;
  width:100%!important;max-width:none!important;
  margin:0!important;
  padding:7px max(8px,env(safe-area-inset-right)) calc(7px + env(safe-area-inset-bottom)) max(8px,env(safe-area-inset-left))!important;
  box-sizing:border-box!important;
  background:rgba(255,255,255,.97)!important;
  border-top:1px solid #dce2ee!important;
  box-shadow:0 -8px 24px rgba(15,23,42,.14)!important;
  backdrop-filter:blur(12px)!important;
}
#adminApp>.admin-vnext-bottom-bar>span{display:none!important}
#adminApp>.admin-vnext-bottom-bar>button{
  display:flex!important;align-items:center!important;justify-content:center!important;
  width:100%!important;min-width:0!important;min-height:50px!important;height:50px!important;
  margin:0!important;padding:7px 3px!important;
  font-size:14px!important;line-height:1.05!important;font-weight:950!important;
  text-align:center!important;white-space:nowrap!important;overflow:hidden!important;
  border-radius:12px!important;
}
#adminApp>.admin-vnext-bottom-bar>.mobile-assign-button{background:#315efb!important;color:#fff!important;border-color:#315efb!important}
.admin-save-notice{z-index:2147483647!important;touch-action:none!important;overscroll-behavior:none!important}
.admin-save-notice.is-visible{pointer-events:all!important}
@media(max-width:380px){#adminApp>.admin-vnext-bottom-bar{gap:5px!important;padding-left:5px!important;padding-right:5px!important}#adminApp>.admin-vnext-bottom-bar>button{font-size:12px!important;padding:5px 1px!important}}
</style>
<script id="jayuminton-admin-bottom-controls-fixed-script-v3">
(function(){
  'use strict';
  var scheduled=false;
  function apply(){
    scheduled=false;
    var app=document.getElementById('adminApp'); if(!app)return;
    var bar=app.querySelector('.admin-vnext-bottom-bar');
    if(!bar)return;
    if(bar.parentElement!==app)app.appendChild(bar);
    bar.removeAttribute('data-jm-top-controls');
    bar.setAttribute('data-jm-bottom-controls','fixed');
    var buttons=bar.querySelectorAll(':scope>button');
    if(buttons.length===3){
      buttons[0].textContent='실행취소';
      if(!buttons[1].disabled)buttons[1].textContent='새로고침';
      buttons[2].textContent='자동배정';
    }
    window.__JAYUMINTON_ADMIN_BOTTOM_CONTROLS_FIXED_V3__=true;
  }
  function schedule(){if(scheduled)return;scheduled=true;requestAnimationFrame(apply);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply,{once:true});else apply();
  new MutationObserver(schedule).observe(document.documentElement,{childList:true,subtree:true});
})();
</script>
<!-- __JAYUMINTON_ADMIN_BOTTOM_CONTROLS_FINAL_V2__ -->
<!-- __JAYUMINTON_ADMIN_BOTTOM_CONTROLS_FIXED_V3__ -->
'''
html=html.replace('</body>',addon+'\n</body>',1)

required=['admin-vnext-bottom-bar','data-jm-bottom-controls','position:fixed!important','bottom:0!important','실행취소','새로고침','자동배정','__JAYUMINTON_ADMIN_BOTTOM_CONTROLS_FIXED_V3__','z-index:2147483000']
for item in required:
    if item not in html:
        raise SystemExit('fixed bottom controls patch missing: '+item)
path.write_text(html,encoding='utf-8')
print('ADMIN_BOTTOM_CONTROLS_FIXED_V3_OK')
