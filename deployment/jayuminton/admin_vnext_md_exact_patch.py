#!/usr/bin/env python3
"""Final MD-exact admin UI patch: registration controls and long-press actions."""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
admin_path = root / 'Admin.html'
script_path = root / 'Script.html'
admin = admin_path.read_text(encoding='utf-8')
script = script_path.read_text(encoding='utf-8')
MARKER = '__JAYUMINTON_ADMIN_MD_EXACT_V1__'

# Registration: gender is a two-choice radio UI while retaining a hidden canonical value
# consumed by the existing add/edit logic.
select_pat = re.compile(r'<select\s+id=["\']newGender["\'][^>]*>.*?</select>', re.S | re.I)
radio_html = '''<div class="member-gender-radio" role="radiogroup" aria-label="성별">
        <input id="newGender" type="hidden" value="">
        <label><input type="radio" name="newGenderChoice" value="male" onchange="syncNewMemberGender(this.value)"> 남자</label>
        <label><input type="radio" name="newGenderChoice" value="female" onchange="syncNewMemberGender(this.value)"> 여자</label>
      </div>'''
if select_pat.search(admin):
    admin = select_pat.sub(radio_html, admin, count=1)
elif 'class="member-gender-radio"' not in admin:
    raise SystemExit('newGender control missing')

# One visible grade/experience field as required by MD. Existing field IDs remain hidden
# so the backend continues to store grade and experience separately.
grade_pat = re.compile(r'<input\s+[^>]*id=["\']newGrade["\'][^>]*>\s*<input\s+[^>]*id=["\']newExperience["\'][^>]*>', re.S | re.I)
combined_html = '''<input id="newGradeExperience" maxlength="40" placeholder="급수 / 구력 (예: A급 / 3년)" oninput="syncNewMemberGradeExperience(this.value)">
      <input id="newGrade" type="hidden" value="">
      <input id="newExperience" type="hidden" value="">'''
if grade_pat.search(admin):
    admin = grade_pat.sub(combined_html, admin, count=1)
elif 'id="newGradeExperience"' not in admin:
    raise SystemExit('grade/experience controls missing')

# Compact registration count is explicitly total/male/female.
admin = re.sub(
    r'<span\s+id=["\']memberCount["\'][^>]*>.*?</span>',
    '<span id="memberCount" class="meta admin-member-counts">전체 0 · 남 0 · 여 0</span>',
    admin,
    count=1,
    flags=re.S | re.I,
)

# Long-press actions: exact six controls from the MD.
bar_pat = re.compile(r'<div\s+id=["\']quickMoveBar["\'][^>]*>.*?</div>', re.S | re.I)
bar_html = '''<div id="quickMoveBar" class="quick-move-bar hidden" aria-label="길게 누른 멤버 관리">
    <button type="button" onclick="setLongPressedMemberStatus('active')">코트배정</button>
    <button type="button" onclick="setLongPressedMemberStatus('before')">도착전</button>
    <button type="button" onclick="setLongPressedMemberStatus('rest')">휴식</button>
    <button type="button" onclick="setLongPressedMemberStatus('away')">귀가</button>
    <button type="button" class="danger" onclick="deleteLongPressedMembers()">삭제</button>
    <button type="button" class="ghost-button" onclick="closeMemberActionBar()">취소</button>
  </div>'''
if bar_pat.search(admin):
    admin = bar_pat.sub(bar_html, admin, count=1)
else:
    raise SystemExit('quickMoveBar missing')

# Keep the six multi-card actions on one compact line. On narrow screens the
# row scrolls horizontally instead of wrapping over the page title.
action_style = '''<style id="jayuminton-admin-multi-card-actions-v2">
#quickMoveBar.quick-move-bar{display:flex!important;flex-wrap:nowrap!important;align-items:center!important;gap:5px!important;overflow-x:auto!important;max-width:100%!important;padding:6px!important}
#quickMoveBar.quick-move-bar.hidden{display:none!important}
#quickMoveBar.quick-move-bar>button{flex:0 0 auto!important;min-width:58px!important;min-height:34px!important;height:34px!important;margin:0!important;padding:5px 9px!important;font-size:12px!important;line-height:1!important;white-space:nowrap!important}
</style>'''
if 'jayuminton-admin-multi-card-actions-v2' not in admin:
    admin = admin.replace('</body>', action_style + '\n</body>', 1)

if MARKER not in admin:
    admin = admin.replace('</body>', '<!-- ' + MARKER + ' -->\n</body>', 1)

# Helpers are appended before </script> so they run after all legacy functions and can
# safely use the existing runAction/STATE/MEMBER_ACTION_IDS contract.
helper_marker = '__JAYUMINTON_ADMIN_MD_EXACT_SCRIPT_V1__'
if helper_marker not in script:
    helper = r'''
// __JAYUMINTON_ADMIN_MD_EXACT_SCRIPT_V1__
function syncNewMemberGender(value) {
  const hidden = document.getElementById('newGender');
  if (hidden) hidden.value = value === 'female' ? 'female' : (value === 'male' ? 'male' : '');
}

function syncNewMemberGradeExperience(value) {
  const raw = String(value == null ? '' : value).trim();
  const pieces = raw.split('/');
  const grade = document.getElementById('newGrade');
  const experience = document.getElementById('newExperience');
  if (grade) grade.value = String(pieces.shift() || '').trim().slice(0, 12);
  if (experience) experience.value = pieces.join('/').trim().slice(0, 20);
}

function syncAdminMemberCounts() {
  const el = document.getElementById('memberCount');
  if (!el || typeof STATE === 'undefined' || !STATE || !Array.isArray(STATE.members)) return;
  const total = STATE.members.length;
  const male = STATE.members.filter(function(member) { return member && member.gender !== 'female'; }).length;
  const female = total - male;
  el.textContent = '전체 ' + total + ' · 남 ' + male + ' · 여 ' + female;
}

function resetMdExactRegistrationControls() {
  const combined = document.getElementById('newGradeExperience');
  if (combined) combined.value = '';
  document.querySelectorAll('input[name="newGenderChoice"]').forEach(function(input) { input.checked = false; });
  syncNewMemberGender('');
}

function setLongPressedMemberStatus(status) {
  const ids = (typeof MEMBER_ACTION_IDS !== 'undefined' ? MEMBER_ACTION_IDS : []).map(String).filter(Boolean);
  if (!ids.length) return;
  closeMemberActionBar();
  return runAction('setMemberStatus', [ADMIN_PIN_VALUE, ids, status]);
}

function deleteLongPressedMembers() {
  const ids = (typeof MEMBER_ACTION_IDS !== 'undefined' ? MEMBER_ACTION_IDS : []).map(String).filter(Boolean);
  if (!ids.length) return;
  if (!window.confirm('선택한 멤버를 삭제하시겠습니까?')) return;
  closeMemberActionBar();
  return runAction('deleteMembers', [ADMIN_PIN_VALUE, ids]);
}

(function installMdExactAdminObserver() {
  function sync() { syncAdminMemberCounts(); }
  document.addEventListener('DOMContentLoaded', sync, {once:true});
  const root = document.getElementById('adminApp') || document.body;
  if (root && window.MutationObserver) {
    const observer = new MutationObserver(function() { sync(); });
    observer.observe(root, {subtree:true, childList:true});
  }
  window.setInterval(sync, 1200);
})();
'''
    pos = script.rfind('</script>')
    if pos < 0:
        raise SystemExit('Script closing tag missing')
    script = script[:pos] + helper + '\n' + script[pos:]

# Hard validation against the requested MD contract.
for required in (
    'class="member-gender-radio"', 'id="newGradeExperience"', 'id="newPublicMemo"',
    'id="newIsNew"', 'id="newIsSponsor"', '전체 0 · 남 0 · 여 0',
    "setLongPressedMemberStatus('active')", "setLongPressedMemberStatus('before')",
    "setLongPressedMemberStatus('rest')", "setLongPressedMemberStatus('away')",
    'deleteLongPressedMembers()', '>코트배정</button>', '>취소</button>', 'jayuminton-admin-multi-card-actions-v2', MARKER,
):
    if required not in admin:
        raise SystemExit('MD exact admin marker missing: ' + required)
bar = bar_pat.search(admin)
if not bar or len(re.findall(r'<button\b', bar.group(0), re.I)) != 6:
    raise SystemExit('long-press menu must contain exactly six buttons')
for required in ('function syncNewMemberGender(', 'function syncNewMemberGradeExperience(',
                 'function syncAdminMemberCounts(', 'function setLongPressedMemberStatus(',
                 'function deleteLongPressedMembers(', helper_marker):
    if required not in script:
        raise SystemExit('MD exact script marker missing: ' + required)

admin_path.write_text(admin, encoding='utf-8')
script_path.write_text(script, encoding='utf-8')
print('ADMIN_VNEXT_MD_EXACT_V1_OK')
