#!/usr/bin/env python3
"""Admin-only client behavior additions. User rendering is intentionally untouched."""
from pathlib import Path
import sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('source-snapshot/current-main')
p=root/'Script.html'; s=p.read_text(encoding='utf-8')

anchor='let SELECTED = new Set();'
if anchor not in s: raise SystemExit('selection anchor not found')
s=s.replace(anchor,anchor+r'''

function adminVNextSelectedIds_() { return Array.from(SELECTED || []); }
function increaseSelectedGames() {
  const ids=adminVNextSelectedIds_();
  if(!ids.length){ alert('게임횟수를 올릴 멤버를 선택하세요.'); return; }
  runSequentialAdminVNext_(ids,function(id){ return ['adjustMemberGames',[ADMIN_PIN_VALUE,id,1]]; });
}
function setSelectedBundle() {
  const ids=adminVNextSelectedIds_();
  if(ids.length!==2){ alert('묶음으로 지정할 2명을 선택하세요.'); return; }
  callServer_('setBundle',[ADMIN_PIN_VALUE,ids],function(state){ SELECTED.clear(); applyState_(state); });
}
function clearSelectedBundle() {
  const ids=adminVNextSelectedIds_();
  if(!ids.length){ alert('묶음을 해제할 멤버를 선택하세요.'); return; }
  callServer_('clearBundle',[ADMIN_PIN_VALUE,ids],function(state){ SELECTED.clear(); applyState_(state); });
}
function runSequentialAdminVNext_(ids,builder) {
  const queue=ids.slice();
  function next(lastState){
    if(!queue.length){ SELECTED.clear(); if(lastState) applyState_(lastState); else loadState(); return; }
    const id=queue.shift(), spec=builder(id);
    callServer_(spec[0],spec[1],function(state){ next(state); });
  }
  next(null);
}
''',1)

# Extend add/edit payload at DOM level without altering user frontend. Existing addMember/applyMemberEdit can consume these after backend payload wiring.
marker='let EDIT_MEMBER_ID = null;'
s=s.replace(marker,marker+r'''
function adminVNextMemberExtraPayload_(){
  const memo=document.getElementById('newPublicMemo');
  const isNew=document.getElementById('newIsNew');
  const sponsor=document.getElementById('newIsSponsor');
  return {publicMemo:memo?memo.value.trim():'',isNew:!!(isNew&&isNew.checked),isSponsor:!!(sponsor&&sponsor.checked)};
}
function adminVNextFillMemberExtras_(member){
  const memo=document.getElementById('newPublicMemo'),isNew=document.getElementById('newIsNew'),sponsor=document.getElementById('newIsSponsor');
  if(memo)memo.value=String(member&&member.publicMemo||'');
  if(isNew)isNew.checked=!!(member&&member.isNew);
  if(sponsor)sponsor.checked=!!(member&&member.isSponsor);
}
function adminVNextClearMemberExtras_(){ adminVNextFillMemberExtras_(null); }
''',1)

p.write_text(s,encoding='utf-8')
print('admin vNext client behavior patch prepared')
