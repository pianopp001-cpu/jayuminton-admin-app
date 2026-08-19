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

metadata_payload = """{
        isNew: !!(document.getElementById('newIsNew') && document.getElementById('newIsNew').checked),
        publicMemo: String(document.getElementById('newPublicMemo') && document.getElementById('newPublicMemo').value || '').trim(),
        isSponsor: !!(document.getElementById('newIsSponsor') && document.getElementById('newIsSponsor').checked)
      }"""

def matching_end(text, start, opener, closer):
    depth = 0
    quote = ''
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if quote:
            if escape:
                escape = False
            elif ch == '\\\\':
                escape = True
            elif ch == quote:
                quote = ''
            continue
        if ch in ("'", '"', '\x60'):
            quote = ch
        elif ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return i
    return -1

def split_top_level(value):
    parts, start, stack, quote, escape = [], 0, [], '', False
    pairs = {')': '(', ']': '[', '}': '{'}
    for i, ch in enumerate(value):
        if quote:
            if escape:
                escape = False
            elif ch == '\\\\':
                escape = True
            elif ch == quote:
                quote = ''
            continue
        if ch in ("'", '"', '\x60'):
            quote = ch
        elif ch in '([{':
            stack.append(ch)
        elif ch in ')]}':
            if stack and stack[-1] == pairs[ch]:
                stack.pop()
        elif ch == ',' and not stack:
            parts.append(value[start:i].strip())
            start = i + 1
    parts.append(value[start:].strip())
    return [part for part in parts if part]

def patch_server_args(text, method, keep):
    for quote in ("'", '"'):
        needle = 'server(' + quote + method + quote + ', ['
        hit = text.find(needle)
        if hit >= 0:
            start = text.find('[', hit)
            end = matching_end(text, start, '[', ']')
            if end < 0:
                raise SystemExit(method + ' server argument boundary missing')
            args = split_top_level(text[start + 1:end])
            if len(args) < keep:
                raise SystemExit(method + ' server arguments incomplete')
            replacement = ',\n      '.join(args[:keep] + [metadata_payload])
            return text[:start + 1] + replacement + text[end:]
    return None

def patch_direct_args(text, method, keep):
    needle = '.' + method + '('
    hit = text.find(needle)
    if hit < 0:
        return None
    start = text.find('(', hit)
    end = matching_end(text, start, '(', ')')
    if end < 0:
        raise SystemExit(method + ' direct argument boundary missing')
    args = split_top_level(text[start + 1:end])
    if len(args) < keep:
        raise SystemExit(method + ' direct arguments incomplete')
    replacement = ',\n          '.join(args[:keep] + [metadata_payload])
    return text[:start + 1] + replacement + text[end:]

patched = patch_server_args(s, 'addMember', 5)
if patched is None:
    patched = patch_direct_args(s, 'addMember', 5)
if patched is None:
    raise SystemExit('addMember call not found')
s = patched

# Normalize persisted sheet flags before any card rendering.
normalize_anchor = """function normalizeMemberProfile(member) {
  if (!member) return member;"""
normalize_replacement = """function normalizeMemberProfile(member) {
  if (!member) return member;
  member.isNew = member.isNew === true || ['true','1'].indexOf(String(member.isNew || '').toLowerCase()) >= 0;
  member.isSponsor = member.isSponsor === true || ['true','1'].indexOf(String(member.isSponsor || '').toLowerCase()) >= 0;"""
if normalize_anchor in s:
 s=s.replace(normalize_anchor,normalize_replacement,1)
elif "member.isNew = member.isNew === true" not in s:
 raise SystemExit('member flag normalization anchor not found')

# Ensure the optimistic card uses the checkbox state immediately.
temporary_anchor = """    experience: experience,
    createdAt: new Date().toISOString()
  };"""
temporary_replacement = """    experience: experience,
    isNew: !!(document.getElementById('newIsNew') && document.getElementById('newIsNew').checked),
    publicMemo: String(document.getElementById('newPublicMemo') && document.getElementById('newPublicMemo').value || '').trim(),
    isSponsor: !!(document.getElementById('newIsSponsor') && document.getElementById('newIsSponsor').checked),
    createdAt: new Date().toISOString()
  };"""
if temporary_anchor in s:
 s=s.replace(temporary_anchor,temporary_replacement,1)
elif "id: temporaryId" in s and "isNew: !!(document.getElementById('newIsNew')" not in s[s.find("id: temporaryId"):s.find("id: temporaryId")+900]:
 raise SystemExit('temporary member metadata anchor not found')

# Clear metadata inputs only when the current admin script has not already
# implemented the same reset variables.
if "const newMemo=document.getElementById('newPublicMemo')" not in s:
 for anchor in [
  "    document.getElementById('newExperience').value = '';",
  "    experienceInput.value = '';"
 ]:
  if anchor in s:
   s=s.replace(anchor,anchor+"\n    const newMemo=document.getElementById('newPublicMemo'); if(newMemo) newMemo.value='';\n    const newFlag=document.getElementById('newIsNew'); if(newFlag) newFlag.checked=false;\n    const sponsorFlag=document.getElementById('newIsSponsor'); if(sponsorFlag) sponsorFlag.checked=false;",1)
   break

# Populate metadata inputs only when the existing edit flow does not already
# declare these variables. This avoids duplicate const declarations.
edit_metadata_marker = "const memo=document.getElementById('newPublicMemo')"
if edit_metadata_marker not in s:
 for edit_anchor in [
  "  document.getElementById('newExperience').value = member.experience || '';",
  "  experience.value = String(member.experience || '');"
 ]:
  if edit_anchor in s:
   s=s.replace(edit_anchor,edit_anchor+"\n  const memo=document.getElementById('newPublicMemo'); if(memo) memo.value=member.publicMemo||'';\n  const isNew=document.getElementById('newIsNew'); if(isNew) isNew.checked=!!member.isNew;\n  const sponsor=document.getElementById('newIsSponsor'); if(sponsor) sponsor.checked=!!member.isSponsor;",1)
   break

patched = patch_server_args(s, 'updateMemberProfile', 6)
if patched is None:
    patched = patch_direct_args(s, 'updateMemberProfile', 6)
if patched is None:
    raise SystemExit('updateMemberProfile call not found')
s = patched

insert='''
function refreshAdminState() {
  const button = document.querySelector('.mobile-refresh-button');
  if (button) { button.disabled = true; button.textContent = '갱신 중…'; }
  return loadState()
    .then(function() {
      if (button) button.textContent = '✓ 완료';
      window.setTimeout(function() {
        if (button) { button.disabled = false; button.textContent = '↻ 새로고침'; }
      }, 700);
    })
    .catch(function(error) {
      if (button) { button.disabled = false; button.textContent = '↻ 새로고침'; }
      alert(error && error.message ? error.message : error);
    });
}

function increaseSelectedGames() {
  const ids = Array.from(SELECTED);
  if (!ids.length) { alert('게임횟수를 올릴 멤버를 선택하세요.'); return; }
  Promise.all(ids.map(function(id) { return server('adjustMemberGames', [ADMIN_PIN_VALUE, id, 1]); }))
    .then(function(states) { SELECTED.clear(); if (states.length) renderState(states[states.length-1]); })
    .catch(function(error) { alert(error.message || error); });
}
function setSelectedBundle() {
  const ids=Array.from(SELECTED); if(ids.length!==2){alert('묶음으로 지정할 멤버를 정확히 2명 선택하세요.');return;}
  runAction('setBundle',[ADMIN_PIN_VALUE,ids]);
}
function clearSelectedBundle() {
  const ids=Array.from(SELECTED); if(!ids.length){alert('묶음을 해제할 멤버를 선택하세요.');return;}
  runAction('clearBundle',[ADMIN_PIN_VALUE,ids]);
}
'''
marker='function decreaseSelectedGames() {'
if marker not in s: raise SystemExit('decrease marker not found')
if 'function refreshAdminState()' not in s:
 s=s.replace(marker,insert+'\n'+marker,1)

# Admin cards always show the full stored nickname. Canonicalize nested results
# left by earlier deployments before replacing remaining compact render calls.
while "(member.isNew ? escapeMemberInfo(member.name) : (member.isNew ? escapeMemberInfo(member.name) : compactMemberName(member.name)))" in s:
 s=s.replace("(member.isNew ? escapeMemberInfo(member.name) : (member.isNew ? escapeMemberInfo(member.name) : compactMemberName(member.name)))", "adminVnextCardName(member)")
s=s.replace("(member.isNew ? escapeMemberInfo(member.name) : compactMemberName(member.name))", "adminVnextCardName(member)")
s=s.replace("compactMemberName(member.name)", "adminVnextCardName(member)")

# Add visible badges/details without inventing '미입력' text. Blank grade/experience remain absent.
card_marker = "function memberInfoDetailHtml(member, contextLabel) {"
if card_marker not in s:
 card_marker = "function memberInfoDetailHtml(member, locationOverride) {"
if card_marker not in s: raise SystemExit('memberInfoDetailHtml marker not found')
name_helper='''function adminVnextCardName(member) {
  if (!member) return '';
  const storedName = String(member.name || '').trim();
  if (!member.isNew) return compactMemberName(storedName);
  const open = storedName.indexOf('(');
  if (open < 0) return '<span class="member-vnext-full-name">' + escapeMemberInfo(storedName) + '</span>';
  const firstLine = storedName.slice(0, open).trim();
  const parenthetical = storedName.slice(open).trim();
  return '<span class="member-vnext-full-name"><span>' + escapeMemberInfo(firstLine) +
    '</span><br><small>' + escapeMemberInfo(parenthetical) + '</small></span>';
}

'''
# Always replace the previously deployed helper body; merely checking for its
# existence left the old "full name for everyone" behavior in production.
name_start = s.find('function adminVnextCardName(member)')
if name_start >= 0:
 name_brace = s.find('{', name_start)
 name_end = matching_end(s, name_brace, '{', '}')
 if name_end < 0: raise SystemExit('admin card name helper boundary missing')
 s = s[:name_start] + s[name_end + 1:].lstrip('\n')
s=s.replace(card_marker,name_helper+card_marker,1)

# Lightweight edit response: merge only the saved member instead of waiting
# for and rendering a complete state snapshot.
edit_start = s.find('async function applyMemberEdit()')
edit_end = s.find('\nasync function addMember()', edit_start)
if edit_start < 0 or edit_end < 0: raise SystemExit('member edit flow boundary missing')
edit_block = s[edit_start:edit_end]
edit_block = edit_block.replace('.then(function(state) {', '.then(function(result) {', 1)
edit_block = edit_block.replace('      renderState(state);', '''      if (result && result.member) {
        const savedMember = normalizeMemberProfile(result.member);
        const savedIndex = STATE.members.findIndex(function(item) { return String(item.id) === String(savedMember.id); });
        if (savedIndex >= 0) STATE.members[savedIndex] = savedMember;
        renderState();
      } else {
        renderState(result);
      }''', 1)
s = s[:edit_start] + edit_block + s[edit_end:]

helper='''function adminVnextMemberBadges(member) {
  if (!member) return '';
  let html = '';
  if (member.isNew) html += '<span class="member-vnext-badge new-badge" aria-label="신규 회원">NEW</span>';
  if (member.isSponsor) html += '<span class="member-vnext-badge sponsor-badge">🎁 찬조</span>';
  if (member.publicMemo) html += '<span class="member-vnext-memo">' + escapeMemberInfo(member.publicMemo) + '</span>';
  return html;
}

'''
badge_start = s.find('function adminVnextMemberBadges(member)')
while badge_start >= 0:
 badge_brace = s.find('{', badge_start)
 badge_end = matching_end(s, badge_brace, '{', '}')
 if badge_end < 0: raise SystemExit('admin member badge helper boundary missing')
 s = s[:badge_start] + s[badge_end + 1:].lstrip('\n')
 badge_start = s.find('function adminVnextMemberBadges(member)')
s=s.replace(card_marker,helper+card_marker,1)

# The card is rendered optimistically; do not leave the large primary button
# displaying a long-running "saving" label while Apps Script confirms it.
s=s.replace("  renderStats();\n  const count = document.getElementById('memberCount');", "  renderStats();\n  if (button) button.textContent = '등록 확인 중';\n  const count = document.getElementById('memberCount');", 1)

# Admin cards must omit absent grade/experience instead of printing placeholders.
missing_detail_old = """  if (!grade && !experience) {
    return '<span class="member-info-detail is-missing">급수·구력 미입력</span>';
  }

  const gradeText = grade || '급수 미입력';
  const experienceText = experience ? '구력 ' + experience : '구력 미입력';

  return '<span class="member-info-detail' +
    ((!grade || !experience) ? ' is-missing' : '') + '">' +
    escapeMemberInfo(gradeText) + ' · ' + escapeMemberInfo(experienceText) +
    '</span>';"""
missing_detail_new = """  const adminParts = [];
  if (grade) adminParts.push(escapeMemberInfo(grade));
  if (experience) adminParts.push(escapeMemberInfo(experience));
  if (!adminParts.length) return '';
  return '<span class="member-info-detail">' + adminParts.join(' · ') + '</span>';"""
if missing_detail_old in s:
 s=s.replace(missing_detail_old,missing_detail_new,1)
elif '급수·구력 미입력' in s or '구력 미입력' in s or '급수 미입력' in s:
 raise SystemExit('admin missing-value rendering normalization failed')
s=s.replace("if (experience) adminParts.push(escapeMemberInfo('구력 ' + experience));", "if (experience) adminParts.push(escapeMemberInfo(experience));")

# Court finish voice must run for every non-empty court, including partial
# 2-person and 3-person games. The server already promotes wait group 1 and
# publishes the authenticated transition event for any non-empty court.
s=s.replace("(STATE.courts[courtNo] || []).length === 4", "(STATE.courts[courtNo] || []).length > 0")

# Append badges to every detail block through the function's final return when identifiable.
# Safer fallback: inject badges next to game count in standard cards and quick roster.
s=s.replace("memberInfoDetailHtml(member) +", "memberInfoDetailHtml(member) + adminVnextMemberBadges(member) +")
s=s.replace("memberInfoDetailHtml(member, '코트배정 대기') +", "memberInfoDetailHtml(member, '코트배정 대기') + adminVnextMemberBadges(member) +")
s=s.replace("memberInfoDetailHtml(member, courtNo + '번코트') +", "memberInfoDetailHtml(member, courtNo + '번코트') + adminVnextMemberBadges(member) +")
s=s.replace("memberInfoDetailHtml(member, '대기' + (groupIndex + 1)) +", "memberInfoDetailHtml(member, '대기' + (groupIndex + 1)) + adminVnextMemberBadges(member) +")
while 'adminVnextMemberBadges(member) + adminVnextMemberBadges(member) +' in s:
 s=s.replace('adminVnextMemberBadges(member) + adminVnextMemberBadges(member) +', 'adminVnextMemberBadges(member) +')

p.write_text(s,encoding='utf-8')
print('admin vNext Script API + card rendering patch prepared')
