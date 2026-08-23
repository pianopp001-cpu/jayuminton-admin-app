#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv)!=2:
    raise SystemExit('usage: v3_admin_overlay_guarantee.py WORKDIR')
work=Path(sys.argv[1])
script=work/'Script.html'
style=work/'Style.html'
s=script.read_text(encoding='utf-8')
addon=r'''

/* JAYUMINTON_ADMIN_SAVING_GUARANTEE_V1 */
(function(){
  if(typeof IS_ADMIN!=='undefined'&&!IS_ADMIN)return;
  if(window.__JAYUMINTON_ADMIN_SAVING_GUARANTEE_V2__)return;
  window.__JAYUMINTON_ADMIN_SAVING_GUARANTEE_V2__=true;

  function ensureAdminSavingOverlay_(){
    var el=document.getElementById('adminSavingOverlay');
    if(!el){
      el=document.createElement('div');
      el.id='adminSavingOverlay';
      el.className='admin-saving-overlay';
      el.setAttribute('role','status');
      el.setAttribute('aria-live','polite');
      el.innerHTML='<div class="admin-saving-card"><div class="admin-saving-spinner"></div><strong id="adminSavingText">저장 중...</strong><small>변경 내용을 저장하고 있습니다.</small></div>';
      var block=function(event){
        event.preventDefault();
        event.stopPropagation();
        if(event.stopImmediatePropagation)event.stopImmediatePropagation();
        return false;
      };
      el.addEventListener('pointerdown',block,true);
      el.addEventListener('click',block,true);
      el.addEventListener('touchstart',block,{capture:true,passive:false});
      el.addEventListener('touchmove',block,{capture:true,passive:false});
      document.body.appendChild(el);
    }
    return el;
  }

  window.showAdminSaving_=function(text){
    var el=ensureAdminSavingOverlay_();
    var t=document.getElementById('adminSavingText');
    if(t)t.textContent=String(text||'저장 중...');
    document.body.classList.add('admin-saving-active');
    el.classList.add('show');
  };
  window.hideAdminSaving_=function(){
    var el=document.getElementById('adminSavingOverlay');
    if(el)el.classList.remove('show');
    document.body.classList.remove('admin-saving-active');
  };
})();
'''
if 'JAYUMINTON_ADMIN_SAVING_GUARANTEE_V1' not in s:
    pos=s.rfind('</script>')
    if pos<0: raise SystemExit('Script closing tag missing')
    s=s[:pos]+addon+'\n'+s[pos:]
elif '__JAYUMINTON_ADMIN_SAVING_GUARANTEE_V2__' not in s:
    pos=s.rfind('</script>')
    if pos<0: raise SystemExit('Script closing tag missing')
    s=s[:pos]+addon+'\n'+s[pos:]
script.write_text(s,encoding='utf-8')
css=style.read_text(encoding='utf-8')
blocking_css='''
/* JAYUMINTON_ADMIN_SAVING_BLOCKING_CSS_V2 */
.admin-saving-overlay{
  position:fixed!important;
  inset:0!important;
  z-index:2147483647!important;
  display:none!important;
  align-items:center!important;
  justify-content:center!important;
  background:rgba(15,23,42,.40)!important;
  pointer-events:auto!important;
  touch-action:none!important;
  overscroll-behavior:contain!important;
}
.admin-saving-overlay.show{display:flex!important;pointer-events:auto!important}
.admin-saving-overlay.show .admin-saving-card{pointer-events:none!important}
body.admin-saving-active{overflow:hidden!important;touch-action:none!important}
'''
if 'JAYUMINTON_ADMIN_SAVING_BLOCKING_CSS_V2' not in css:
    css += '\n'+blocking_css+'\n'
if '@keyframes adminSavingSpin' not in css:
    css += '\n@keyframes adminSavingSpin{to{transform:rotate(360deg)}}\n'
if '.admin-saving-spinner{' in css and 'animation:adminSavingSpin' not in css:
    css += '\n.admin-saving-spinner{border-style:solid!important;border-color:#e2e8f0!important;border-top-color:#475569!important;border-radius:50%!important;animation:adminSavingSpin .75s linear infinite!important}\n'
style.write_text(css,encoding='utf-8')
for needle in ['JAYUMINTON_ADMIN_SAVING_GUARANTEE_V1','__JAYUMINTON_ADMIN_SAVING_GUARANTEE_V2__','window.showAdminSaving_','window.hideAdminSaving_']:
    if needle not in script.read_text(encoding='utf-8'): raise SystemExit('missing '+needle)
for needle in ['JAYUMINTON_ADMIN_SAVING_BLOCKING_CSS_V2','z-index:2147483647!important','pointer-events:auto!important','body.admin-saving-active']:
    if needle not in style.read_text(encoding='utf-8'): raise SystemExit('missing '+needle)
print('ADMIN_SAVING_GUARANTEE_OK')
