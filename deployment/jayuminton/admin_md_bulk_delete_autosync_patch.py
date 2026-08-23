#!/usr/bin/env python3
"""MD requirement: multi-select member deletion + automatic admin state sync."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: admin_md_bulk_delete_autosync_patch.py INDEX_HTML')

path = Path(sys.argv[1])
html = path.read_text(encoding='utf-8')
if '</body>' not in html:
    raise SystemExit('body marker missing')
if 'id="quickActiveRoster"' not in html:
    raise SystemExit('quickActiveRoster missing')

marker = '__JAYUMINTON_ADMIN_BULK_DELETE_AUTOSYNC_V1__'
if marker in html:
    print('ADMIN_BULK_DELETE_AUTOSYNC_V1_ALREADY_PRESENT')
    raise SystemExit(0)

bulk_button = '''<div class="md-bulk-delete-row" id="mdBulkDeleteRow">
          <button id="mdBulkDeleteButton" class="danger" type="button" onclick="deleteMdSelectedMembers()" disabled>선택 멤버 삭제</button>
          <span id="mdBulkDeleteCount" class="meta">0명 선택</span>
        </div>\n'''
html = html.replace('<div id="quickActiveRoster"', bulk_button + '<div id="quickActiveRoster"', 1)

addon = r'''
<style id="jayuminton-admin-bulk-delete-autosync-v1">
.md-bulk-delete-row{display:flex!important;align-items:center!important;gap:8px!important;margin:8px 0!important;flex-wrap:wrap!important}
#mdBulkDeleteButton{min-height:42px!important;padding:8px 14px!important;font-weight:900!important;border-radius:11px!important}
#mdBulkDeleteButton:disabled{opacity:.45!important;cursor:not-allowed!important}
#mdBulkDeleteCount{font-weight:850!important}
</style>
<script id="jayuminton-admin-bulk-delete-autosync-script-v1">
(function(){
  'use strict';
  window.__JAYUMINTON_ADMIN_BULK_DELETE_AUTOSYNC_V1__=true;
  var syncBusy=false;
  var lastSeenRevision=-1;

  function selectedIds(){
    try{return Array.from(SELECTED||[]).map(String).filter(Boolean);}catch(e){return [];}
  }
  function selectedNames(ids){
    var wanted=new Set(ids);
    var members=[];
    try{members=STATE&&Array.isArray(STATE.members)?STATE.members:[];}catch(e){}
    return members.filter(function(m){return m&&wanted.has(String(m.id));}).map(function(m){return String(m.name||'');}).filter(Boolean);
  }
  function refreshBulkDeleteButton(){
    var ids=selectedIds();
    var button=document.getElementById('mdBulkDeleteButton');
    var count=document.getElementById('mdBulkDeleteCount');
    if(button)button.disabled=!ids.length;
    if(count)count.textContent=ids.length+'명 선택';
  }
  window.deleteMdSelectedMembers=function(){
    var ids=selectedIds();
    if(!ids.length){alert('삭제할 멤버를 먼저 선택해 주세요.');return;}
    var names=selectedNames(ids);
    var label=names.length?names.join(', '):ids.length+'명';
    if(!confirm('선택한 '+ids.length+'명의 멤버를 완전히 삭제할까요?\n'+label))return;
    try{if(typeof closeMemberActionBar==='function')closeMemberActionBar();}catch(e){}
    try{SELECTED.clear();}catch(e){}
    refreshBulkDeleteButton();
    return runAction('deleteMembers',[ADMIN_PIN_VALUE,ids]);
  };

  async function autoSyncAdmin(){
    if(syncBusy||document.hidden)return;
    var app=document.getElementById('adminApp');
    if(!app||app.classList.contains('hidden'))return;
    try{if(typeof ACTION_IN_FLIGHT!=='undefined'&&ACTION_IN_FLIGHT)return;}catch(e){}
    syncBusy=true;
    try{
      var next=await server('getPublicState',[]);
      if(!next||!Array.isArray(next.members))return;
      var nextRevision=Number(next.revision||0);
      var currentRevision=0;
      try{currentRevision=Number(STATE&&STATE.revision||0);}catch(e){}
      if(lastSeenRevision<0)lastSeenRevision=currentRevision;
      if(nextRevision!==currentRevision){
        renderState(next);
        lastSeenRevision=nextRevision;
      }
    }catch(e){console.warn('admin auto sync failed',e);}
    finally{syncBusy=false;refreshBulkDeleteButton();}
  }

  document.addEventListener('click',function(){setTimeout(refreshBulkDeleteButton,0);},true);
  document.addEventListener('visibilitychange',function(){if(!document.hidden)autoSyncAdmin();});
  setInterval(autoSyncAdmin,1500);
  setInterval(refreshBulkDeleteButton,500);
  setTimeout(function(){refreshBulkDeleteButton();autoSyncAdmin();},0);
})();
</script>
<!-- __JAYUMINTON_ADMIN_BULK_DELETE_AUTOSYNC_V1__ -->
'''
html = html.replace('</body>', addon + '\n</body>', 1)

for required in (
    marker,
    'id="mdBulkDeleteButton"',
    '선택 멤버 삭제',
    'deleteMdSelectedMembers()',
    "runAction('deleteMembers',[ADMIN_PIN_VALUE,ids])",
    "server('getPublicState',[])",
    'setInterval(autoSyncAdmin,1500)',
    'nextRevision!==currentRevision',
):
    if required not in html:
        raise SystemExit('bulk delete/autosync requirement missing: ' + required)

path.write_text(html, encoding='utf-8')
print('ADMIN_BULK_DELETE_AUTOSYNC_V1_OK')
