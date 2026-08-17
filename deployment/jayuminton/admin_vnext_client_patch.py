#!/usr/bin/env python3
"""Admin-only client behavior additions. User rendering is intentionally untouched."""
from pathlib import Path
import sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('source-snapshot/current-main')
p=root/'Script.html'; s=p.read_text(encoding='utf-8')

def rep(a,b,label):
 global s
 if a not in s: raise SystemExit(label+' anchor not found')
 s=s.replace(a,b,1)

anchor='let SELECTED = new Set();'
rep(anchor,anchor+r'''

function adminVNextSelectedIds_() { return Array.from(SELECTED || []); }
function adminVNextToggleSelection_(memberId) {
  memberId=String(memberId||''); if(!memberId)return;
  if(SELECTED.has(memberId)) SELECTED.delete(memberId); else SELECTED.add(memberId);
  QUICK_PICK=null;
  if(typeof renderState==='function') renderState();
}
function adminVNextSelectionLabel_(){ return SELECTED.size+'명 선택'; }
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
function adminVNextMemberMeta_(member){
  const parts=[];
  if(member&&member.grade) parts.push(String(member.grade));
  if(member&&member.experience) parts.push('구력 '+String(member.experience).replace(/^구력\s*/i,''));
  parts.push('게임 '+String(Math.max(0,Number(member&&member.games)||0))+'회');
  if(member&&member.publicMemo) parts.push(String(member.publicMemo));
  return parts.join(' · ');
}
function adminVNextMemberBadges_(member){
  const badges=[];
  if(member&&member.isNew) badges.push('신규');
  if(member&&member.isSponsor) badges.push('🎁 찬조');
  if(member&&member.bundleId) badges.push('🔗 묶음');
  return badges;
}
''','selection')

marker='let EDIT_MEMBER_ID = null;'
rep(marker,marker+r'''
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
''','edit marker')

# New members keep full stored name anywhere compactMemberName is used.
rep("""function compactMemberName(name) {
  const baseName =
    String(name || '')
      .split('(')[0]
      .trim();

  return Array.from(baseName || String(name || '').trim())
    .slice(0, 2)
    .join('');
}""","""function compactMemberName(name, member) {
  const fullName=String(name || '').trim();
  if(member && member.isNew) return fullName;
  const baseName=fullName.split('(')[0].trim();
  return Array.from(baseName || fullName).slice(0,2).join('');
}""",'compact name')

# Admin cards: no missing placeholders; games always visible; optional badges/memo.
start="""  if (!grade && !experience) {
    return '<span class=\"member-info-detail is-missing\">급수·구력 미입력</span>';
  }

  const gradeText = grade || '급수 미입력';
  const experienceText = experience ? '구력 ' + experience : '구력 미입력';

  return '<span class=\"member-info-detail' +
    ((!grade || !experience) ? ' is-missing' : '') + '\">' +
    escapeMemberInfo(gradeText) + ' · ' + escapeMemberInfo(experienceText) +
    '</span>';"""
replacement="""  const parts=[];
  if (grade) parts.push(escapeMemberInfo(grade));
  if (experience) parts.push(escapeMemberInfo('구력 ' + experience));
  parts.push(escapeMemberInfo('게임 ' + String(Math.max(0, Number(member.games) || 0)) + '회'));
  if (member.publicMemo) parts.push(escapeMemberInfo(String(member.publicMemo)));
  const badges=adminVNextMemberBadges_(member).map(escapeMemberInfo);
  return '<span class=\"member-info-detail\">' +
    (badges.length ? badges.join(' · ') + ' · ' : '') + parts.join(' · ') + '</span>';"""
rep(start,replacement,'member detail')

# Avoid duplicate game label: admin detail already always contains it.
s=s.replace("showGames\n      ? '<span class=\"meta\">' +", "showGames && !IS_ADMIN\n      ? '<span class=\"meta\">' +",1)

oldcourt="""  quickPickMember('court', courtNo, memberId, event);
}"""
newcourt="""  // Same court taps accumulate selection; second tap never auto-swaps.
  QUICK_PICK = null;
  adminVNextToggleSelection_(memberId);
}"""
rep(oldcourt,newcourt,'court tap')
oldwait="""  quickPickMember('wait', groupIndex, memberId, event);
}"""
newwait="""  // Same wait-group taps accumulate selection; move happens only on an explicit target/action.
  QUICK_PICK = null;
  adminVNextToggleSelection_(memberId);
}"""
rep(oldwait,newwait,'wait tap')

p.write_text(s,encoding='utf-8')
print('admin vNext client multi-select patch prepared')
