#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: admin_md_final_form_patch.py INDEX_HTML')
path=Path(sys.argv[1])
html=path.read_text(encoding='utf-8')
marker='__JAYUMINTON_ADMIN_MD_FINAL_FORM_V1__'
if marker not in html:
    select_pattern=re.compile(r'<select\s+id=["\']newGender["\'][^>]*>.*?</select>',re.S)
    m=select_pattern.search(html)
    if not m:
        raise SystemExit('newGender select missing')
    original=m.group(0)
    replacement='''<span class="md-gender-radio" role="radiogroup" aria-label="성별">
      <label><input type="radio" name="mdNewGender" value="male"> 남</label>
      <label><input type="radio" name="mdNewGender" value="female"> 여</label>
    </span>\n''' + original.replace('<select ', '<select class="md-gender-compat-select" aria-hidden="true" tabindex="-1" ')
    html=html[:m.start()]+replacement+html[m.end():]
    addon=r'''
<style id="jayuminton-admin-md-final-form-style-v1">
.md-gender-compat-select{display:none!important}
.md-gender-radio{display:inline-flex!important;align-items:center!important;gap:8px!important;min-height:43px!important;padding:4px 8px!important;border:1px solid #dce2ee!important;border-radius:12px!important;background:#fff!important}
.md-gender-radio label{display:inline-flex!important;align-items:center!important;gap:4px!important;font-weight:850!important;cursor:pointer!important;white-space:nowrap!important}
.md-gender-radio input{min-height:0!important;width:18px!important;height:18px!important;margin:0!important;accent-color:#315efb!important}
#mdMemberGenderSummary{display:inline-flex!important;align-items:center!important;min-height:32px!important;padding:6px 10px!important;border-radius:999px!important;background:#f5f7fb!important;border:1px solid #dce2ee!important;font-size:12px!important;font-weight:900!important;color:#334155!important;white-space:nowrap!important}
</style>
<script id="jayuminton-admin-md-final-form-script-v1">
(function(){
  'use strict';
  var select=document.getElementById('newGender');
  var radios=Array.prototype.slice.call(document.querySelectorAll('input[name="mdNewGender"]'));
  if(!select||radios.length!==2)return;
  function syncFromSelect(){
    var value=String(select.value||'');
    radios.forEach(function(r){r.checked=r.value===value;});
  }
  radios.forEach(function(r){r.addEventListener('change',function(){
    if(!r.checked)return;
    select.value=r.value;
    try{select.dispatchEvent(new Event('change',{bubbles:true}));}catch(e){}
  });});
  function ensureSummary(){
    var host=document.getElementById('memberCount');
    if(!host)return null;
    var node=document.getElementById('mdMemberGenderSummary');
    if(!node){node=document.createElement('span');node.id='mdMemberGenderSummary';host.parentNode.insertBefore(node,host.nextSibling);}
    return node;
  }
  function refreshSummary(){
    var node=ensureSummary(); if(!node)return;
    var members=[]; try{members=STATE&&Array.isArray(STATE.members)?STATE.members:[];}catch(e){}
    var male=0,female=0;
    members.forEach(function(m){if(m&&m.gender==='male')male++;else if(m&&m.gender==='female')female++;});
    node.textContent='총인원 '+members.length+'명 · 남: '+male+'명 · 여: '+female+'명';
    syncFromSelect();
  }
  syncFromSelect(); refreshSummary();
  window.setInterval(refreshSummary,500);
  window.__JAYUMINTON_ADMIN_MD_FINAL_FORM_V1__=true;
})();
</script>
'''
    if '</body>' not in html: raise SystemExit('body marker missing')
    html=html.replace('</body>',addon+'\n<!-- '+marker+' -->\n</body>',1)
for required in (marker,'md-gender-radio','name="mdNewGender"','value="male"','value="female"','mdMemberGenderSummary','총인원 ','남: ','여: '):
    if required not in html: raise SystemExit('MD final form marker missing: '+required)
path.write_text(html,encoding='utf-8')
print('ADMIN_MD_FINAL_FORM_V1_OK')
