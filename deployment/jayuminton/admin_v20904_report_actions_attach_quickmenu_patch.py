#!/usr/bin/env python3
from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'app/src/main/assets/admin/index.html')
s=p.read_text(encoding='utf-8')
MARKER='JAYUMINTON_GAME_REPORT_ACTIONS_ATTACH_QUICKMENU_V20904'
if MARKER in s:
    print('V20904_ALREADY_OK'); raise SystemExit(0)
for token in ('JAYUMINTON_GAME_REPORT_HARD_APPLY_V20903','JAYUMINTON_GAME_REPORT_EXPAND_EXPORT_V20901','#jmAdminFixedQuickMenu'):
    if token not in s: raise SystemExit('v209.04 prerequisite missing: '+token)

STYLE=r'''
<style id="jmReportActionsAttachQuickMenuV20904Style">
/* JAYUMINTON_GAME_REPORT_ACTIONS_ATTACH_QUICKMENU_V20904 */
:root{--jm-quick-menu-h:82px;--jm-report-action-h:54px}
#pairStatisticsModal .j95-actions{
  position:fixed!important;
  left:max(8px,env(safe-area-inset-left))!important;
  right:max(8px,env(safe-area-inset-right))!important;
  bottom:var(--jm-quick-menu-h)!important;
  margin:0!important;
  transform:none!important;
  z-index:2147482999!important;
  justify-content:center!important;
  align-items:center!important;
  gap:6px!important;
  padding:7px 8px 8px!important;
  border-radius:16px 16px 0 0!important;
  background:linear-gradient(180deg,rgba(226,250,239,.96),rgba(213,247,231,1))!important;
  box-shadow:0 -3px 12px rgba(15,70,55,.10)!important;
}
#pairStatisticsModal .pair-statistics-modal{
  padding-bottom:calc(var(--jm-quick-menu-h) + var(--jm-report-action-h) + 6px)!important;
}
@media(max-width:720px){
  #pairStatisticsModal .j95-actions{left:5px!important;right:5px!important;gap:4px!important;padding:6px 5px 7px!important}
}
</style>
'''

SCRIPT=r'''
<script id="jayumintonReportActionsAttachQuickMenuV20904Script">
/* JAYUMINTON_GAME_REPORT_ACTIONS_ATTACH_QUICKMENU_V20904_JS */
(function(){'use strict';
if(window.__JM_REPORT_ACTIONS_ATTACH_V20904__)return;
window.__JM_REPORT_ACTIONS_ATTACH_V20904__=true;
var ro=null,mo=null,lastQuick=null,lastAction=null;
function visible(el){if(!el)return false;var cs=getComputedStyle(el);return cs.display!=='none'&&cs.visibility!=='hidden';}
function sync(){
  var quick=document.getElementById('jmAdminFixedQuickMenu');
  var qh=82;
  if(visible(quick)){
    var qr=quick.getBoundingClientRect();
    qh=Math.max(0,Math.ceil(window.innerHeight-qr.top));
    if(qh<40)qh=Math.max(40,Math.ceil(qr.height||82));
  }
  document.documentElement.style.setProperty('--jm-quick-menu-h',qh+'px');
  var act=document.querySelector('#pairStatisticsModal .j95-actions');
  if(act&&visible(act)){
    var ah=Math.max(42,Math.ceil(act.getBoundingClientRect().height||54));
    document.documentElement.style.setProperty('--jm-report-action-h',ah+'px');
  }
  if(window.ResizeObserver){
    if(!ro)ro=new ResizeObserver(function(){requestAnimationFrame(sync);});
    if(quick&&quick!==lastQuick){if(lastQuick)try{ro.unobserve(lastQuick);}catch(_){};try{ro.observe(quick);}catch(_){};lastQuick=quick;}
    if(act&&act!==lastAction){if(lastAction)try{ro.unobserve(lastAction);}catch(_){};try{ro.observe(act);}catch(_){};lastAction=act;}
  }
}
function install(){
  sync();requestAnimationFrame(sync);setTimeout(sync,80);setTimeout(sync,350);
  var quick=document.getElementById('jmAdminFixedQuickMenu');
  if(quick&&!quick.__jmV20904Observed){
    quick.__jmV20904Observed=true;
    mo=new MutationObserver(function(){requestAnimationFrame(sync);});
    mo.observe(quick,{attributes:true,childList:true,subtree:true,attributeFilter:['class','style','hidden']});
  }
}
window.addEventListener('resize',sync,{passive:true});
document.addEventListener('click',function(ev){
  if(ev.target&&ev.target.closest&&ev.target.closest('#jmAdminFixedQuickMenu,#pairStatisticsModal'))setTimeout(sync,0);
},true);
install();
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});
setTimeout(install,700);setTimeout(install,1800);
})();
</script>
'''

if '</head>' not in s or '</body>' not in s: raise SystemExit('html anchor missing')
s=s.replace('</head>',STYLE+'\n</head>',1)
s=s.replace('</body>',SCRIPT+'\n</body>',1)
for token in (MARKER,'--jm-quick-menu-h','position:fixed!important','bottom:var(--jm-quick-menu-h)!important','jmAdminFixedQuickMenu','ResizeObserver'):
    if token not in s: raise SystemExit('v209.04 contract missing: '+token)
p.write_text(s,encoding='utf-8')
print('V20904_OK')
