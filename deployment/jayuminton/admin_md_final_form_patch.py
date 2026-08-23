#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: admin_md_final_form_patch.py INDEX_HTML')
path=Path(sys.argv[1])
html=path.read_text(encoding='utf-8')
marker='__JAYUMINTON_ADMIN_MD_FINAL_FORM_V2__'
compat_marker='__JAYUMINTON_ADMIN_MD_FINAL_FORM_V1__'

if 'name="mdNewGender"' not in html:
    select_pattern=re.compile(r'<select\s+id=["\']newGender["\'][^>]*>.*?</select>',re.S)
    m=select_pattern.search(html)
    if not m: raise SystemExit('newGender select missing')
    original=m.group(0)
    replacement='''<span class="md-gender-radio" role="radiogroup" aria-label="성별">
      <label><input type="radio" name="mdNewGender" value="male"> 남</label>
      <label><input type="radio" name="mdNewGender" value="female"> 여</label>
    </span>\n''' + original.replace('<select ', '<select class="md-gender-compat-select" aria-hidden="true" tabindex="-1" ')
    html=html[:m.start()]+replacement+html[m.end():]

if 'mdQuickMoveStatus(\'before\')' not in html:
    quick_start=html.find('id="quickMoveBar"')
    if quick_start < 0: raise SystemExit('quickMoveBar missing')
    delete_pos=html.find('<button', quick_start)
    while delete_pos >= 0:
        button_end=html.find('</button>',delete_pos)
        if button_end < 0: break
        block=html[delete_pos:button_end+9]
        if 'deleteQuickPickedMembers()' in block: break
        delete_pos=html.find('<button',button_end+9)
    if delete_pos < 0: raise SystemExit('quick move delete button missing')
    extra='''<button type="button" onclick="mdQuickMoveStatus('before')">도착전</button>
    <button type="button" onclick="mdQuickMoveStatus('rest')">휴식</button>
    <button type="button" onclick="mdQuickMoveStatus('away')">귀가</button>
    '''
    html=html[:delete_pos]+extra+html[delete_pos:]

for old_style in ('jayuminton-admin-md-final-form-style-v1','jayuminton-admin-md-final-form-style-v2'):
    start=html.find('<style id="'+old_style+'">')
    if start>=0:
        end=html.find('</script>',start)
        if end>=0: html=html[:start]+html[end+len('</script>'):]
html=html.replace('<!-- '+compat_marker+' -->','')
html=html.replace('<!-- '+marker+' -->','')

addon=r'''
<style id="jayuminton-admin-md-final-form-style-v2">
.md-gender-compat-select{display:none!important}
.md-gender-radio{display:inline-flex!important;align-items:center!important;gap:8px!important;min-height:43px!important;padding:4px 8px!important;border:1px solid #dce2ee!important;border-radius:12px!important;background:#fff!important}
.md-gender-radio label{display:inline-flex!important;align-items:center!important;gap:4px!important;font-weight:850!important;cursor:pointer!important;white-space:nowrap!important}
.md-gender-radio input{min-height:0!important;width:18px!important;height:18px!important;margin:0!important;accent-color:#315efb!important}
#mdMemberGenderSummary{display:inline-flex!important;align-items:center!important;min-height:32px!important;padding:6px 10px!important;border-radius:999px!important;background:#f5f7fb!important;border:1px solid #dce2ee!important;font-size:12px!important;font-weight:900!important;color:#334155!important;white-space:nowrap!important}
#quickMoveBar{flex-wrap:wrap!important}
</style>
<script id="jayuminton-admin-md-final-form-script-v2">
(function(){
  'use strict';
  var select=document.getElementById('newGender');
  var radios=Array.prototype.slice.call(document.querySelectorAll('input[name="mdNewGender"]'));
  function syncFromSelect(){
    if(!select)return;
    var value=String(select.value||'');
    radios.forEach(function(r){r.checked=r.value===value;});
  }
  radios.forEach(function(r){r.addEventListener('change',function(){
    if(!r.checked||!select)return;
    select.value=r.value;
    try{select.dispatchEvent(new Event('change',{bubbles:true}));}catch(e){}
  });});
  window.mdQuickMoveStatus=function(status){
    var ids=[];
    try{ids=MEMBER_ACTION_IDS.slice();}catch(e){}
    if(!ids.length)return;
    try{closeMemberActionBar();}catch(e){}
    return runAction('setMemberStatus',[ADMIN_PIN_VALUE,ids,status]);
  };
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
  window.__JAYUMINTON_ADMIN_MD_FINAL_FORM_V2__=true;
})();
</script>
'''
if '</body>' not in html: raise SystemExit('body marker missing')
html=html.replace('</body>',addon+'\n<!-- '+compat_marker+' -->\n<!-- '+marker+' -->\n</body>',1)
for required in (
    compat_marker,marker,'md-gender-radio','name="mdNewGender"','value="male"','value="female"',
    'mdMemberGenderSummary','총인원 ','남: ','여: ',
    "mdQuickMoveStatus('before')","mdQuickMoveStatus('rest')","mdQuickMoveStatus('away')",
    '>도착전</button>','>휴식</button>','>귀가</button>','deleteQuickPickedMembers()','closeMemberActionBar()'
):
    if required not in html: raise SystemExit('MD final form marker missing: '+required)
path.write_text(html,encoding='utf-8')
print('ADMIN_MD_FINAL_FORM_V2_OK')
