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
  if(typeof window.showAdminSaving_!=='function'){
    window.showAdminSaving_=function(text){
      var el=document.getElementById('adminSavingOverlay');
      if(!el){
        el=document.createElement('div');
        el.id='adminSavingOverlay';
        el.className='admin-saving-overlay';
        el.innerHTML='<div class="admin-saving-card"><div class="admin-saving-spinner"></div><strong id="adminSavingText">저장 중...</strong><small>변경 내용을 저장하고 있습니다.</small></div>';
        document.body.appendChild(el);
      }
      var t=document.getElementById('adminSavingText');
      if(t)t.textContent=String(text||'저장 중...');
      el.classList.add('show');
    };
  }
  if(typeof window.hideAdminSaving_!=='function'){
    window.hideAdminSaving_=function(){
      var el=document.getElementById('adminSavingOverlay');
      if(el)el.classList.remove('show');
    };
  }
})();
'''
if 'JAYUMINTON_ADMIN_SAVING_GUARANTEE_V1' not in s:
    pos=s.rfind('</script>')
    if pos<0: raise SystemExit('Script closing tag missing')
    s=s[:pos]+addon+'\n'+s[pos:]
script.write_text(s,encoding='utf-8')
css=style.read_text(encoding='utf-8')
if '@keyframes adminSavingSpin' not in css:
    css += '\n@keyframes adminSavingSpin{to{transform:rotate(360deg)}}\n'
if '.admin-saving-spinner{' in css and 'animation:adminSavingSpin' not in css:
    css += '\n.admin-saving-spinner{border-style:solid!important;border-color:#e2e8f0!important;border-top-color:#475569!important;border-radius:50%!important;animation:adminSavingSpin .75s linear infinite!important}\n'
style.write_text(css,encoding='utf-8')
for needle in ['JAYUMINTON_ADMIN_SAVING_GUARANTEE_V1','window.showAdminSaving_','window.hideAdminSaving_']:
    if needle not in script.read_text(encoding='utf-8'): raise SystemExit('missing '+needle)
print('ADMIN_SAVING_GUARANTEE_OK')
