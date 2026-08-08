#!/usr/bin/env python3
from pathlib import Path
import re
import sys


def replace_function(src: str, name: str, replacement: str) -> str:
    token = "function " + name + "("
    start = src.find(token)
    if start < 0:
        raise RuntimeError(name + " missing")
    brace = src.find("{", start)
    if brace < 0:
        raise RuntimeError(name + " opening brace missing")
    depth = 0
    quote = None
    escaped = False
    i = brace
    while i < len(src):
        ch = src[i]
        if quote is not None:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"', "`"):
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[:start] + replacement + src[i + 1:]
        i += 1
    raise RuntimeError(name + " braces unbalanced")


def remove_modal(admin: str) -> str:
    marker = "<!-- JAYUMINTON_MEMBER_EDIT_MODAL_EXISTING_ONLY -->"
    start = admin.find(marker)
    if start < 0:
        return admin
    match = re.search(r'<div\s+id="wholeSwapBar"', admin[start:])
    if not match:
        raise RuntimeError("wholeSwapBar anchor missing after edit modal")
    return admin[:start] + admin[start + match.start():]


def main(root: Path) -> None:
    admin_path = root / "Admin.html"
    script_path = root / "Script.html"
    code_path = root / "Code.js"
    admin = admin_path.read_text(encoding="utf-8")
    script = script_path.read_text(encoding="utf-8")
    code = code_path.read_text(encoding="utf-8")

    # Admin UI: no push-app button.
    admin = re.sub(
        r'\s*<button[^>]*id="adminPushAppButton"[^>]*>.*?</button>\s*',
        "\n",
        admin,
        count=1,
        flags=re.S,
    )
    admin = admin.replace("<h2>멤버 등록</h2>", "<h2>멤버 등록·수정</h2>", 1)

    # Add a separate Modify action beside Register.
    if 'id="updateMemberButton"' not in admin:
        add_pos = admin.find('id="addMemberButton"')
        if add_pos < 0:
            raise RuntimeError("addMemberButton missing")
        close = admin.find("</button>", add_pos)
        if close < 0:
            raise RuntimeError("addMemberButton closing tag missing")
        close += len("</button>")
        update_html = (
            '\n\n      <button id="updateMemberButton" class="primary" type="button" '
            'onclick="applyMemberEdit()" disabled>수정</button>'
        )
        admin = admin[:close] + update_html + admin[close:]

    # Old modal is removed; edit uses the registration fields above.
    admin = remove_modal(admin)

    # Add Select All beside the excluded-roster batch controls.
    if 'onclick="selectAllMembers()"' not in admin:
        excluded = admin.find("코트배정 제외")
        if excluded < 0:
            raise RuntimeError("excluded panel missing")
        reset = admin.find('onclick="resetSelectedGames()"', excluded)
        if reset < 0:
            raise RuntimeError("excluded resetSelectedGames button missing")
        close = admin.find("</button>", reset)
        if close < 0:
            raise RuntimeError("excluded reset button closing tag missing")
        close += len("</button>")
        admin = admin[:close] + (
            '\n\n        <button type="button" onclick="selectAllMembers()">멤버 모두 선택</button>'
        ) + admin[close:]

    admin_path.write_text(admin, encoding="utf-8")

    # Keep the requested vibration counts/patterns.
    script = replace_function(script, "memberAlertRepeatCount", """function memberAlertRepeatCount(type) {
  if (type === 'court_assignment') return 4;
  if (type === 'wait1_ready') return 2;
  return 1;
}""")
    script = replace_function(script, "memberVibrationPattern", """function memberVibrationPattern(type) {
  return [320, 180, 320, 180, 320];
}""")
    script = script.replace("}, index * 1300);", "}, index * 1700);")

    # Excluded members: double tap -> court-assignment waiting.
    if "let LAST_EXCLUDED_MEMBER_TAP" not in script:
        pos = script.find("let LAST_COURT_MEMBER_TAP = {")
        if pos < 0:
            raise RuntimeError("court tap tracker missing")
        script = script[:pos] + "let LAST_EXCLUDED_MEMBER_TAP = { memberId:'', tappedAt:0 };\n" + script[pos:]

    excluded_handler = """function handleExcludedMemberTap(memberId, event) {
  if (!IS_ADMIN) return;
  if (consumeLongPressClick(memberId, event)) return;
  if (assignMemberToChosenEmpty(memberId, event)) return;
  const now = Date.now();
  const isDoubleTap = LAST_EXCLUDED_MEMBER_TAP.memberId === memberId &&
    now - LAST_EXCLUDED_MEMBER_TAP.tappedAt <= 420;
  LAST_EXCLUDED_MEMBER_TAP = isDoubleTap
    ? { memberId:'', tappedAt:0 }
    : { memberId:memberId, tappedAt:now };
  if (isDoubleTap) {
    if (event) { event.preventDefault(); event.stopPropagation(); }
    cancelQuickPick();
    runAction('setMemberStatus', [ADMIN_PIN_VALUE, [memberId], 'active']);
    return;
  }
  toggleSelected(memberId);
}"""
    if "function handleExcludedMemberTap(" in script:
        script = replace_function(script, "handleExcludedMemberTap", excluded_handler)
    else:
        pos = script.find("function handleCourtMemberTap(")
        if pos < 0:
            raise RuntimeError("handleCourtMemberTap anchor missing")
        script = script[:pos] + excluded_handler + "\n\n" + script[pos:]

    rs = script.find("function renderExcluded()")
    re_ = script.find("function renderInactive()", rs)
    if rs < 0 or re_ < 0:
        raise RuntimeError("renderExcluded block missing")
    block = script[rs:re_]
    if "handleExcludedMemberTap" not in block:
        if "handleSelectableMemberClick" not in block:
            raise RuntimeError("excluded click handler missing")
        block = block.replace("handleSelectableMemberClick", "handleExcludedMemberTap", 1)
        script = script[:rs] + block + script[re_:]

    # Court and wait double tap bypass QuickPick swap/cancel state.
    script = replace_function(script, "handleCourtMemberTap", """function handleCourtMemberTap(courtNo, memberId, event) {
  if (event && event.target && event.target.closest('button.small')) return;
  if (consumeLongPressClick(memberId, event)) return;
  if (assignMemberToChosenEmpty(memberId, event)) return;
  const now = Date.now();
  const isDoubleTap = LAST_COURT_MEMBER_TAP.memberId === memberId &&
    now - LAST_COURT_MEMBER_TAP.tappedAt <= 420;
  LAST_COURT_MEMBER_TAP = isDoubleTap
    ? { memberId:'', tappedAt:0 }
    : { memberId:memberId, tappedAt:now };
  if (isDoubleTap) {
    if (event) { event.preventDefault(); event.stopPropagation(); }
    cancelQuickPick();
    runAction('setMemberStatus', [ADMIN_PIN_VALUE, [memberId], 'active']);
    return;
  }
  quickPickMember('court', courtNo, memberId, event);
}""")

    script = replace_function(script, "handleWaitMemberTap", """function handleWaitMemberTap(groupIndex, memberId, event) {
  if (event && event.target && event.target.closest('button.small')) return;
  if (consumeLongPressClick(memberId, event)) return;
  if (assignMemberToChosenEmpty(memberId, event)) return;
  const now = Date.now();
  const isDoubleTap = LAST_WAIT_MEMBER_TAP.memberId === memberId &&
    now - LAST_WAIT_MEMBER_TAP.tappedAt <= 420;
  LAST_WAIT_MEMBER_TAP = isDoubleTap
    ? { memberId:'', tappedAt:0 }
    : { memberId:memberId, tappedAt:now };
  if (isDoubleTap) {
    if (event) { event.preventDefault(); event.stopPropagation(); }
    cancelQuickPick();
    runAction('setMemberStatus', [ADMIN_PIN_VALUE, [memberId], 'active']);
    return;
  }
  quickPickMember('wait', groupIndex, memberId, event);
}""")

    # Long press Edit opens the setup panel and fills the registration fields.
    script = replace_function(script, "startMemberEdit", """function startMemberEdit() {
  if (!IS_ADMIN) return;
  if (MEMBER_ACTION_IDS.length !== 1) {
    alert('편집할 멤버 한 명을 길게 눌러 주세요.');
    return;
  }
  const memberId = String(MEMBER_ACTION_IDS[0] || '');
  const member = (STATE.members || []).find(function(item) {
    return String(item.id || '') === memberId;
  });
  if (!member) { alert('멤버 정보를 찾을 수 없습니다.'); return; }
  EDIT_MEMBER_ID = memberId;
  const name = document.getElementById('newName');
  const gender = document.getElementById('newGender');
  const grade = document.getElementById('newGrade');
  const experience = document.getElementById('newExperience');
  const updateButton = document.getElementById('updateMemberButton');
  if (!name || !gender || !grade || !experience || !updateButton) {
    alert('멤버 등록·수정 입력칸을 찾을 수 없습니다.');
    return;
  }
  name.value = String(member.name || '');
  gender.value = member.gender === 'female' ? 'female' : 'male';
  grade.value = String(member.grade || '');
  experience.value = String(member.experience || '');
  updateButton.disabled = false;
  closeMemberActionBar();
  const details = document.querySelector('.admin-setup-details');
  if (details) details.open = true;
  setTimeout(function() {
    try { name.scrollIntoView({behavior:'smooth', block:'center'}); } catch (error) {}
    try { name.focus(); name.select(); } catch (error) {}
  }, 60);
}""")

    # Modify always updates the existing record; Register remains add-only.
    script = replace_function(script, "applyMemberEdit", """function applyMemberEdit() {
  if (!IS_ADMIN || ACTION_IN_FLIGHT) return;
  if (!EDIT_MEMBER_ID) {
    alert('먼저 멤버를 길게 눌러 편집을 선택해 주세요.');
    return;
  }
  const targetId = String(EDIT_MEMBER_ID);
  const name = String(document.getElementById('newName')?.value || '').trim();
  const gender = String(document.getElementById('newGender')?.value || '').trim();
  const grade = String(document.getElementById('newGrade')?.value || '').trim();
  const experience = String(document.getElementById('newExperience')?.value || '').trim();
  if (!name) { alert('이름 또는 닉네임을 입력하세요.'); return; }
  if (gender !== 'male' && gender !== 'female') { alert('성별을 선택하세요.'); return; }
  const button = document.getElementById('updateMemberButton');
  ACTION_IN_FLIGHT = true;
  if (button) { button.disabled = true; button.textContent = '수정 중…'; }
  server('updateMemberProfile', [ADMIN_PIN_VALUE, targetId, name, gender, grade, experience])
    .then(function(state) {
      EDIT_MEMBER_ID = '';
      document.getElementById('newName').value = '';
      document.getElementById('newGender').value = '';
      document.getElementById('newGrade').value = '';
      document.getElementById('newExperience').value = '';
      renderState(state);
    })
    .catch(function(error) { alert(error.message || error); })
    .finally(function() {
      ACTION_IN_FLIGHT = false;
      if (button) { button.textContent = '수정'; button.disabled = !EDIT_MEMBER_ID; }
    });
}""")

    select_all = """function selectAllMembers() {
  if (!IS_ADMIN) return;
  cancelQuickPick();
  SELECTED = new Set((STATE.members || [])
    .map(function(member) { return String(member.id || ''); })
    .filter(Boolean));
  renderState();
}"""
    if "function selectAllMembers(" in script:
        script = replace_function(script, "selectAllMembers", select_all)
    else:
        pos = script.find("function setSelectedStatus(")
        if pos < 0:
            raise RuntimeError("setSelectedStatus anchor missing")
        script = script[:pos] + select_all + "\n\n" + script[pos:]

    script_path.write_text(script, encoding="utf-8")

    checks = {
        "push removed": "adminPushAppButton" not in admin and "📱 푸시앱" not in admin,
        "inline modify": 'id="updateMemberButton"' in admin and 'onclick="applyMemberEdit()"' in admin,
        "modal removed": 'id="memberEditModal"' not in admin,
        "select all UI": 'onclick="selectAllMembers()"' in admin,
        "inline edit fields": "document.getElementById('newName')" in script,
        "server update": "server('updateMemberProfile'" in script,
        "existing row overwrite": "members[index].name = name;" in code,
        "court double tap": "quickPickMember('court'" in script,
        "wait double tap": "quickPickMember('wait'" in script,
        "direct active move": "runAction('setMemberStatus', [ADMIN_PIN_VALUE, [memberId], 'active'])" in script,
        "select all function": "function selectAllMembers()" in script,
        "user long press guard": "if (!IS_ADMIN) return '';" in script,
        "court vibration x4": "if (type === 'court_assignment') return 4;" in script,
        "wait1 vibration x2": "if (type === 'wait1_ready') return 2;" in script,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise RuntimeError("post-patch checks failed: " + ", ".join(failed))
    print("admin v2 patch validated")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve())
