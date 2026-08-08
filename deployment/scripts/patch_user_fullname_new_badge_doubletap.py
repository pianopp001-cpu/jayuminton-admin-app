#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')


def once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 match, found {count}')
    return text.replace(old, new, 1)


index_path = root / 'Index.html'
index = index_path.read_text(encoding='utf-8')
index = index.replace('oninput="renderMemberSelfMatches()"',
                      'oninput="handleMemberSelfSearchInput()"', 1)
if 'autocorrect="off"' not in index:
    index = once(index, '          autocomplete="off"\n',
                 '          autocomplete="off"\n          autocorrect="off"\n          autocapitalize="off"\n          spellcheck="false"\n',
                 'search anti-autofill attributes')
index_path.write_text(index, encoding='utf-8')


script_path = root / 'Script.html'
s = script_path.read_text(encoding='utf-8')

# User mode always shows the stored full name. Admin mode keeps its compact layout.
old = "  return member.isNew ? String(member.name || '').trim() : compactMemberName(member.name);"
new = "  return (!IS_ADMIN || member.isNew) ? String(member.name || '').trim() : compactMemberName(member.name);"
if old in s:
    s = once(s, old, new, 'user full name')

# NEW is a badge, not a reason to shorten or expand a name.
if 'function memberNewBadgeHtml(member)' not in s:
    anchor = 'function memberInfoDetailHtml(member, locationOverride) {'
    helper = """function memberNewBadgeHtml(member) {
  return member && member.isNew
    ? '<span class="member-new-badge" aria-label="신규 멤버">NEW</span>'
    : '';
}

"""
    s = once(s, anchor, helper + anchor, 'new badge helper')

old = """  if (!parts.length) return '';
  return '<span class="member-info-detail">' + parts.join(' · ') + '</span>';"""
new = """  const badge = memberNewBadgeHtml(member);
  if (!parts.length) return badge;
  return badge + '<span class="member-info-detail">' + parts.join(' · ') + '</span>';"""
if 'const badge = memberNewBadgeHtml(member);' not in s:
    s = once(s, old, new, 'badge in every card')

# Typing only filters. It never silently selects the first or sole result.
if 'function handleMemberSelfSearchInput()' not in s:
    anchor = 'function handleMemberSelfSearchKey(event) {'
    helper = """function handleMemberSelfSearchInput() {
  const input = document.getElementById('memberSelfSearchInput');
  if (input) input.dataset.userEditing = '1';
  renderMemberSelfMatches();
}

"""
    s = once(s, anchor, helper + anchor, 'manual search input')

old = """function handleMemberSelfSearchKey(event) {
  if (!event || event.key !== 'Enter') return;
  event.preventDefault();
  const matches = memberSelfSearchMatches();
  if (matches.length) selectMemberSelf(matches[0].id);
}"""
new = """function handleMemberSelfSearchKey(event) {
  if (!event || event.key !== 'Enter') return;
  event.preventDefault();
  renderMemberSelfMatches();
  showMemberSettingMessage('검색 결과에서 내 이름을 직접 눌러 주세요.', false);
}"""
if old in s:
    s = once(s, old, new, 'disable enter auto select')

# Every explicit selection enables both preferences and asks the outer shell/APK to connect.
old = """  unlockMemberAlertAudio();
  postUnifiedMemberMessage('JAYUMINTON_MEMBER_SELECTED', {
    member: {id: String(member.id), name: String(member.name || '').trim()}
  });
  renderCourts();"""
new = """  try {
    localStorage.setItem(MEMBER_ALERT_ENABLED_KEY, 'true');
    localStorage.setItem(MEMBER_VIBRATION_ENABLED_KEY, 'true');
  } catch (error) {}
  unlockMemberAlertAudio();
  const selectedMember = {id: String(member.id), name: String(member.name || '').trim()};
  postUnifiedMemberMessage('JAYUMINTON_MEMBER_SELECTED', {member: selectedMember});
  postUnifiedMemberMessage('JAYUMINTON_MEMBER_ALERT_PREFERENCE', {enabled: true});
  postUnifiedMemberMessage('JAYUMINTON_MEMBER_VIBRATION_PREFERENCE', {enabled: true});
  postUnifiedMemberMessage('JAYUMINTON_PUSH_SETUP_REQUEST', {
    member: selectedMember,
    authVersion: currentMemberAuthVersion()
  });
  renderCourts();"""
if 'const selectedMember = {id: String(member.id)' not in s:
    s = once(s, old, new, 'explicit selection enables push')

# Remove the old completion-time implicit selection block.
old = """  // member-complete-auto-select-v12
  // If the user typed another name, never reuse the previously stored member silently.
  if (input && input.dataset.userEditing === '1' && typed) {
    const matches = memberSelfSearchMatches();
    const typedLower = typed.toLocaleLowerCase('ko-KR');
    const exact = matches.find(function(member) {
      return member && String(member.name || '').trim().toLocaleLowerCase('ko-KR') === typedLower;
    });
    const candidate = exact || (matches.length === 1 ? matches[0] : null);
    if (candidate) {
      selectMemberSelf(candidate.id);
      selected = {id:String(candidate.id), name:String(candidate.name || '').trim()};
    } else {
      showMemberSettingMessage('검색 결과에서 본인 이름을 선택하세요.', true);
      if (input) input.focus();
      return;
    }
  }
"""
new = """  // Typing never selects a member. A result button or a double-tapped card must be used.
  if (input && input.dataset.userEditing === '1' && typed) {
    showMemberSettingMessage('검색 결과에서 내 이름을 직접 눌러 주세요.', true);
    input.focus();
    return;
  }
"""
if old in s:
    s = once(s, old, new, 'remove completion auto select')

# Reliable mobile double tap without depending on the browser dblclick event.
if 'function memberSelfDoubleTapAttributes(memberId)' not in s:
    anchor = 'function memberLongPressAttributes(memberId) {'
    helper = """let MEMBER_SELF_LAST_TAP_ID = '';
let MEMBER_SELF_LAST_TAP_AT = 0;

function handleMemberSelfCardTap(memberId, event) {
  if (IS_ADMIN) return;
  const now = Date.now();
  const same = MEMBER_SELF_LAST_TAP_ID === String(memberId) && now - MEMBER_SELF_LAST_TAP_AT <= 520;
  MEMBER_SELF_LAST_TAP_ID = String(memberId);
  MEMBER_SELF_LAST_TAP_AT = now;
  if (!same) return;
  MEMBER_SELF_LAST_TAP_ID = '';
  MEMBER_SELF_LAST_TAP_AT = 0;
  if (event) { event.preventDefault(); event.stopPropagation(); }
  selectMemberSelf(memberId);
  showMemberSettingMessage('내 이름·알림 ON·진동 ON으로 저장했습니다.', false);
}

function memberSelfDoubleTapAttributes(memberId) {
  if (IS_ADMIN || !memberId) return '';
  return ' onpointerup="handleMemberSelfCardTap(\\'' + memberId + '\\',event)"';
}

"""
    s = once(s, anchor, helper + anchor, 'double tap helper')

old = """    (clickable ? memberLongPressAttributes(member.id) : '') +
    onclick +"""
new = """    (clickable ? memberLongPressAttributes(member.id) : memberSelfDoubleTapAttributes(member.id)) +
    onclick +"""
if 'memberSelfDoubleTapAttributes(member.id)' not in s:
    s = once(s, old, new, 'double tap card attributes')

script_path.write_text(s, encoding='utf-8')


style_path = root / 'Style.html'
style = style_path.read_text(encoding='utf-8')
if '/* NEW member badge */' not in style:
    style += """

/* NEW member badge */
#adminApp .member-new-badge,
#memberApp .member-new-badge{
  display:inline-flex!important;
  align-items:center!important;
  justify-content:center!important;
  width:max-content!important;
  min-height:13px!important;
  margin:2px auto 0!important;
  padding:1px 5px!important;
  border-radius:999px!important;
  background:#ff3b30!important;
  color:#fff!important;
  font-size:8px!important;
  font-weight:950!important;
  line-height:1!important;
  letter-spacing:.3px!important;
}
#adminApp .person:has(.member-new-badge) .name,
#adminApp .member:has(.member-new-badge) .name,
#adminApp .quick-member:has(.member-new-badge) .quick-member-name{
  max-width:100%!important;
  font-size:clamp(7px,1.8vw,10px)!important;
  line-height:1.05!important;
  white-space:normal!important;
  overflow-wrap:anywhere!important;
  word-break:keep-all!important;
  text-overflow:clip!important;
}
"""
style_path.write_text(style, encoding='utf-8')

checks = {
    index_path: ['handleMemberSelfSearchInput()', 'autocorrect="off"'],
    script_path: ['(!IS_ADMIN || member.isNew) ? String(member.name', 'member-new-badge',
                  'handleMemberSelfCardTap', 'JAYUMINTON_PUSH_SETUP_REQUEST'],
    style_path: ['/* NEW member badge */'],
}
for path, needles in checks.items():
    value = path.read_text(encoding='utf-8')
    for needle in needles:
        if needle not in value:
            raise SystemExit(f'verification failed in {path.name}: {needle}')

print('Patched user full names, NEW badge, manual search, and double-tap self selection only.')
