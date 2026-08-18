#!/usr/bin/env python3
"""Wire admin-vNext controls and card rendering. Admin Script only; no user Index edits."""
from pathlib import Path
import sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('source-snapshot/current-main')
p=root/'Script.html'; s=p.read_text(encoding='utf-8')

def rep(a,b,label):
 global s
 if a not in s: raise SystemExit(label+' anchor not found')
 s=s.replace(a,b,1)

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
if old in s:
 s=s.replace(old,new,1)
else:
 direct_old="""        .addMember(
          ADMIN_PIN_VALUE,
          name,
          gender,
          grade,
          experience
        );"""
 direct_new="""        .addMember(
          ADMIN_PIN_VALUE,
          name,
          gender,
          grade,
          experience,
          {
            isNew: !!(document.getElementById('newIsNew') && document.getElementById('newIsNew').checked),
            publicMemo: String(document.getElementById('newPublicMemo') && document.getElementById('newPublicMemo').value || '').trim(),
            isSponsor: !!(document.getElementById('newIsSponsor') && document.getElementById('newIsSponsor').checked)
          }
        );"""
 if direct_old not in s: raise SystemExit('add metadata call anchor not found')
 s=s.replace(direct_old,direct_new,1)

# Clear metadata inputs after either add or update completes.
for anchor in [
 "    document.getElementById('newExperience').value = '';",
 "    experienceInput.value = '';"
]:
 if anchor in s:
  s=s.replace(anchor,anchor+"\n    const newMemo=document.getElementById('newPublicMemo'); if(newMemo) newMemo.value='';\n    const newFlag=document.getElementById('newIsNew'); if(newFlag) newFlag.checked=false;\n    const sponsorFlag=document.getElementById('newIsSponsor'); if(sponsorFlag) sponsorFlag.checked=false;",1)

# Populate metadata inputs when the existing long-press edit flow opens.
for edit_anchor in [
 "  document.getElementById('newExperience').value = member.experience || '';",
 "  experience.value = String(member.experience || '');"
]:
 if edit_anchor in s:
  s=s.replace(edit_anchor,edit_anchor+"\n  const memo=document.getElementById('newPublicMemo'); if(memo) memo.value=member.publicMemo||'';\n  const isNew=document.getElementById('newIsNew'); if(isNew) isNew.checked=!!member.isNew;\n  const sponsor=document.getElementById('newIsSponsor'); if(sponsor) sponsor.checked=!!member.isSponsor;",1)
  break

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
else:
 direct_update_old="server('updateMemberProfile', [ADMIN_PIN_VALUE, targetId, name, gender, grade, experience])"
 direct_update_new="""server('updateMemberProfile', [
    ADMIN_PIN_VALUE, targetId, name, gender, grade, experience,
    {
      isNew: !!(document.getElementById('newIsNew') && document.getElementById('newIsNew').checked),
      publicMemo: String(document.getElementById('newPublicMemo') && document.getElementById('newPublicMemo').value || '').trim(),
      isSponsor: !!(document.getElementById('newIsSponsor') && document.getElementById('newIsSponsor').checked)
    }
  ])"""
 if direct_update_old not in s: raise SystemExit('update metadata call anchor not found')
 s=s.replace(direct_update_old,direct_update_new,1)

insert='''
function increaseSelectedGames() {
  const ids = Array.from(SELECTED);
  if (!ids.length) { alert('게임횟수를 올릴 멤버를 선택하세요.'); return; }
  Promise.all(ids.map(function(id) { return server('adjustMemberGames', [ADMIN_PIN_VALUE, id, 1]); }))
    .then(function(states) { SELECTED.clear(); if (states.length) renderState(states[states.length-1]); })
    .catch(function(error) { alert(error.message || error); });
}
function setSelectedBundle() {
  const ids=Array.from(SELECTED); if(ids.length<2){alert('묶음으로 지정할 멤버를 2명 이상 선택하세요.');return;}
  runAction('setBundle',[ADMIN_PIN_VALUE,ids]);
}
function clearSelectedBundle() {
  const ids=Array.from(SELECTED); if(!ids.length){alert('묶음을 해제할 멤버를 선택하세요.');return;}
  runAction('clearBundle',[ADMIN_PIN_VALUE,ids]);
}
'''
marker='function decreaseSelectedGames() {'
if marker not in s: raise SystemExit('decrease marker not found')
s=s.replace(marker,insert+'\n'+marker,1)

# Admin card policy: 신규는 괄호까지 포함한 저장된 이름 전체를 표시한다.
# 비신규는 기존 compactMemberName 동작을 유지한다.
s=s.replace("compactMemberName(member.name)", "(member.isNew ? escapeMemberInfo(member.name) : compactMemberName(member.name))")

# Add visible badges/details without inventing '미입력' text. Blank grade/experience remain absent.
card_marker = "function memberInfoDetailHtml(member, contextLabel) {"
if card_marker not in s:
 card_marker = "function memberInfoDetailHtml(member, locationOverride) {"
if card_marker not in s: raise SystemExit('memberInfoDetailHtml marker not found')
helper='''function adminVnextMemberBadges(member) {
  if (!member) return '';
  let html = '';
  if (member.isNew) html += '<span class="member-vnext-badge new-badge">신규</span>';
  if (member.isSponsor) html += '<span class="member-vnext-badge sponsor-badge">🎁 찬조</span>';
  if (member.publicMemo) html += '<span class="member-vnext-memo">' + escapeMemberInfo(member.publicMemo) + '</span>';
  return html;
}

'''
s=s.replace(card_marker,helper+card_marker,1)

# Append badges to every detail block through the function's final return when identifiable.
# Safer fallback: inject badges next to game count in standard cards and quick roster.
s=s.replace("memberInfoDetailHtml(member) +", "memberInfoDetailHtml(member) + adminVnextMemberBadges(member) +")
s=s.replace("memberInfoDetailHtml(member, '코트배정 대기') +", "memberInfoDetailHtml(member, '코트배정 대기') + adminVnextMemberBadges(member) +")

p.write_text(s,encoding='utf-8')
print('admin vNext Script API + card rendering patch prepared')
