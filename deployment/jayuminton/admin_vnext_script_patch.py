#!/usr/bin/env python3
"""Wire admin-vNext controls to backend APIs. Admin Script only; no user Index edits."""
from pathlib import Path
import sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('source-snapshot/current-main')
p=root/'Script.html'; s=p.read_text(encoding='utf-8')

def rep(a,b,label):
 global s
 if a not in s: raise SystemExit(label+' anchor not found')
 s=s.replace(a,b,1)

# Existing addMember UI calls the server with the legacy five fields. Extend that
# call with a sixth optional metadata object while preserving compatibility.
old="""      ADMIN_PIN_VALUE,
      name,
      gender,
      grade,
      experience
    ]);"""
new="""      ADMIN_PIN_VALUE,
      name,
      gender,
      grade,
      experience,
      {
        isNew: !!(document.getElementById('newIsNew') && document.getElementById('newIsNew').checked),
        publicMemo: String(document.getElementById('newPublicMemo') && document.getElementById('newPublicMemo').value || '').trim(),
        isSponsor: !!(document.getElementById('newIsSponsor') && document.getElementById('newIsSponsor').checked)
      }
    ]);"""
if old not in s:
    raise SystemExit('add/update metadata call anchor not found')
# Replace first occurrence only: addMember path. Edit path is handled by function-specific anchor below.
s=s.replace(old,new,1)

# Clear metadata controls after successful registration if the legacy clear block exists.
anchor="""    document.getElementById('newExperience').value = '';"""
if anchor in s:
    s=s.replace(anchor, anchor+"\n    const newMemo=document.getElementById('newPublicMemo'); if(newMemo) newMemo.value='';\n    const newFlag=document.getElementById('newIsNew'); if(newFlag) newFlag.checked=false;\n    const sponsorFlag=document.getElementById('newIsSponsor'); if(sponsorFlag) sponsorFlag.checked=false;",1)

# When edit starts, populate the three vNext fields from the selected member.
edit_anchor="""  document.getElementById('newExperience').value = member.experience || '';"""
if edit_anchor in s:
    s=s.replace(edit_anchor, edit_anchor+"\n  const memo=document.getElementById('newPublicMemo'); if(memo) memo.value=member.publicMemo||'';\n  const isNew=document.getElementById('newIsNew'); if(isNew) isNew.checked=!!member.isNew;\n  const sponsor=document.getElementById('newIsSponsor'); if(sponsor) sponsor.checked=!!member.isSponsor;",1)

# Extend updateMemberProfile call if present.
update_old="""      ADMIN_PIN_VALUE,
      EDIT_MEMBER_ID,
      name,
      gender,
      grade,
      experience
    ]);"""
update_new="""      ADMIN_PIN_VALUE,
      EDIT_MEMBER_ID,
      name,
      gender,
      grade,
      experience,
      {
        isNew: !!(document.getElementById('newIsNew') && document.getElementById('newIsNew').checked),
        publicMemo: String(document.getElementById('newPublicMemo') && document.getElementById('newPublicMemo').value || '').trim(),
        isSponsor: !!(document.getElementById('newIsSponsor') && document.getElementById('newIsSponsor').checked)
      }
    ]);"""
if update_old in s:
    s=s.replace(update_old,update_new,1)

# Add concrete handlers used by the new Admin.html buttons.
insert='''
function increaseSelectedGames() {
  const ids = Array.from(SELECTED);
  if (!ids.length) { alert('게임횟수를 올릴 멤버를 선택하세요.'); return; }
  Promise.all(ids.map(function(id) {
    return server('adjustMemberGames', [ADMIN_PIN_VALUE, id, 1]);
  })).then(function(states) {
    SELECTED.clear();
    if (states.length) renderState(states[states.length - 1]);
  }).catch(function(error) { alert(error.message || error); });
}

function setSelectedBundle() {
  const ids = Array.from(SELECTED);
  if (ids.length < 2) { alert('묶음으로 지정할 멤버를 2명 이상 선택하세요.'); return; }
  runAction('setBundle', [ADMIN_PIN_VALUE, ids]);
}

function clearSelectedBundle() {
  const ids = Array.from(SELECTED);
  if (!ids.length) { alert('묶음을 해제할 멤버를 선택하세요.'); return; }
  runAction('clearBundle', [ADMIN_PIN_VALUE, ids]);
}

'''
marker='function decreaseSelectedGames() {'
if marker not in s: raise SystemExit('decreaseSelectedGames marker not found')
s=s.replace(marker,insert+marker,1)

p.write_text(s,encoding='utf-8')
print('admin vNext Script API wiring patch prepared')
