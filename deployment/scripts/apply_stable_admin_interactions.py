#!/usr/bin/env python3
from pathlib import Path
import sys


def replace_js_function(source: str, name: str, replacement: str) -> str:
    token = f"function {name}("
    start = source.find(token)
    if start < 0:
        raise RuntimeError(f"{name} missing")
    brace = source.find("{", start)
    if brace < 0:
        raise RuntimeError(f"{name} opening brace missing")

    depth = 0
    quote = None
    escaped = False
    i = brace
    while i < len(source):
        ch = source[i]
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
                return source[:start] + replacement + source[i + 1:]
        i += 1
    raise RuntimeError(f"{name} braces are unbalanced")


def remove_block(source: str, start_marker: str, end_marker: str) -> str:
    start = source.find(start_marker)
    if start < 0:
        return source
    end = source.find(end_marker, start)
    if end < 0:
        raise RuntimeError(f"end marker missing for {start_marker}")
    return source[:start] + source[end:]


def main(root: Path) -> None:
    admin_path = root / "Admin.html"
    script_path = root / "Script.html"
    code_path = root / "Code.js"
    if not admin_path.exists() or not script_path.exists() or not code_path.exists():
        raise RuntimeError("Admin.html, Script.html or Code.js missing")

    admin = admin_path.read_text(encoding="utf-8")

    # Obsolete admin push-app button must never return.
    button_start = admin.find('<button id="adminPushAppButton"')
    if button_start >= 0:
        button_end = admin.find("</button>", button_start)
        if button_end < 0:
            raise RuntimeError("adminPushAppButton closing tag missing")
        button_end += len("</button>")
        admin = admin[:button_start] + admin[button_end:]

    # Registration and editing share the same input fields, but have separate actions.
    admin = admin.replace("<h2>멤버 등록</h2>", "<h2>멤버 등록·수정</h2>", 1)
    add_button = '''      <button
        id="addMemberButton"
        class="primary"
        onclick="addMember()"
      >
        등록
      </button>'''
    edit_button = add_button + '''

      <button
        id="updateMemberButton"
        class="primary"
        type="button"
        onclick="applyMemberEdit()"
        disabled
      >
        수정
      </button>'''
    if 'id="updateMemberButton"' not in admin:
        if add_button not in admin:
            raise RuntimeError("add member button block missing")
        admin = admin.replace(add_button, edit_button, 1)

    # Remove the old separate edit modal; editing now happens in the registration panel.
    admin = remove_block(
        admin,
        "  <!-- JAYUMINTON_MEMBER_EDIT_MODAL_EXISTING_ONLY -->",
        '  <div\n    id="wholeSwapBar"',
    )

    # Add select-all next to the excluded-roster batch game controls.
    excluded_start = admin.find('<div\n      class="card excluded-panel"')
    excluded_end = admin.find('</div>\n  </section>', excluded_start)
    if excluded_start < 0 or excluded_end < 0:
        raise RuntimeError("excluded panel missing")
    excluded = admin[excluded_start:excluded_end]
    reset_button = '''        <button onclick="resetSelectedGames()">
          게임횟수 모두 0
        </button>'''
    select_all_button = reset_button + '''

        <button type="button" onclick="selectAllMembers()">
          멤버 모두 선택
        </button>'''
    if 'onclick="selectAllMembers()"' not in excluded:
        if reset_button not in excluded:
            raise RuntimeError("excluded reset games button missing")
        excluded = excluded.replace(reset_button, select_all_button, 1)
        admin = admin[:excluded_start] + excluded + admin[excluded_end:]

    if "adminPushAppButton" in admin or "📱 푸시앱" in admin:
        raise RuntimeError("admin push-app button still present")
    admin_path.write_text(admin, encoding="utf-8")

    script = script_path.read_text(encoding="utf-8")

    # Preserve requested member vibration behavior.
    script = replace_js_function(
        script,
        "memberAlertRepeatCount",
        """function memberAlertRepeatCount(type) {
  if (type === 'court_assignment') return 4;
  if (type === 'wait1_ready') return 2;
  return 1;
}""",
    )
    script = replace_js_function(
        script,
        "memberVibrationPattern",
        """function memberVibrationPattern(type) {
  if (type === 'wait1_ready') return [320, 180, 320, 180, 320];
  if (type === 'court_assignment') return [320, 180, 320, 180, 320];
  return [320, 180, 320, 180, 320];
}""",
    )
    script = script.replace("}, index * 1300);", "}, index * 1700);")

    # Excluded roster double tap -> court-assignment waiting pool.
    if "let LAST_EXCLUDED_MEMBER_TAP" not in script:
        anchor = "let LAST_COURT_MEMBER_TAP = {"
        pos = script.find(anchor)
        if pos < 0:
            raise RuntimeError("court tap tracker anchor missing")
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
        script = replace_js_function(script, "handleExcludedMemberTap", excluded_handler)
    else:
        anchor = "function handleCourtMemberTap("
        pos = script.find(anchor)
        if pos < 0:
            raise RuntimeError("handleCourtMemberTap anchor missing")
        script = script[:pos] + excluded_handler + "\n\n" + script[pos:]

    render_start = script.find("function renderExcluded()")
    render_end = script.find("function renderInactive()", render_start)
    if render_start < 0 or render_end < 0:
        raise RuntimeError("renderExcluded block missing")
    render_block = script[render_start:render_end]
    if "handleExcludedMemberTap" not in render_block:
        if "handleSelectableMemberClick" not in render_block:
            raise RuntimeError("renderExcluded selectable click handler missing")
        render_block = render_block.replace("handleSelectableMemberClick", "handleExcludedMemberTap", 1)
    script = script[:render_start] + render_block + script[render_end:]

    # Court and wait-group double tap: bypass swap state and always return to active pool.
    script = replace_js_function(
        script,
        "handleCourtMemberTap",
        """function handleCourtMemberTap(courtNo, memberId, event) {
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
}""",
    )
    script = replace_js_function(
        script,
        "handleWaitMemberTap",
        """function handleWaitMemberTap(groupIndex, memberId, event) {
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
}""",
    )

    # Long-press Edit opens the existing registration panel and fills its fields.
    script = replace_js_function(
        script,
        "startMemberEdit",
        """function startMemberEdit() {
  if (!IS_ADMIN) return;
  if (MEMBER_ACTION_IDS.length !== 1) {
    alert('편집할 멤버 한 명을 길게 눌러 주세요.');
    return;
  }
  const memberId = String(MEMBER_ACTION_IDS[0] || '');
  const member = (STATE.members || []).find(function(item) {
    return String(item.id || '') === memberId;
  });
  if (!member) {
    alert('멤버 정보를 찾을 수 없습니다.');
    return;
  }

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
  updateButton.textContent = '수정';

  closeMemberActionBar();
  const details = document.querySelector('.admin-setup-details');
  if (details) details.open = true;
  setTimeout(function() {
    try { name.scrollIntoView({ behavior:'smooth', block:'center' }); } catch (error) {}
    try { name.focus(); name.select(); } catch (error) {}
  }, 60);
}""",
    )

    # Edit overwrites the selected member record; it never calls addMember.
    script = replace_js_function(
        script,
        "applyMemberEdit",
        """function applyMemberEdit() {
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
    .catch(function(error) {
      alert(error.message || error);
    })
    .finally(function() {
      ACTION_IN_FLIGHT = false;
      if (button) {
        button.textContent = '수정';
        button.disabled = !EDIT_MEMBER_ID;
      }
    });
}""",
    )

    # Select every registered member for batch operations.
    select_all = """function selectAllMembers() {
  if (!IS_ADMIN) return;
  cancelQuickPick();
  SELECTED = new Set(
    (STATE.members || [])
      .map(function(member) { return String(member.id || ''); })
      .filter(Boolean)
  );
  renderState();
}"""
    if "function selectAllMembers(" in script:
        script = replace_js_function(script, "selectAllMembers", select_all)
    else:
        anchor = "function setSelectedStatus("
        pos = script.find(anchor)
        if pos < 0:
            raise RuntimeError("setSelectedStatus anchor missing")
        script = script[:pos] + select_all + "\n\n" + script[pos:]

    # User mode keeps admin-only long-press actions disabled.
    script_path.write_text(script, encoding="utf-8")

    code = code_path.read_text(encoding="utf-8")
    checks = {
        "push button removed": "adminPushAppButton" not in admin and "📱 푸시앱" not in admin,
        "inline update button": 'id="updateMemberButton"' in admin and 'onclick="applyMemberEdit()"' in admin,
        "old edit modal removed": 'id="memberEditModal"' not in admin,
        "select all button": 'onclick="selectAllMembers()"' in admin,
        "edit uses registration fields": "document.getElementById('newName')" in script,
        "edit server update only": "server('updateMemberProfile'" in script,
        "server overwrites existing member": "members[index].name = name;" in code,
        "court direct double tap": "function handleCourtMemberTap" in script and "runAction('setMemberStatus', [ADMIN_PIN_VALUE, [memberId], 'active'])" in script,
        "wait direct double tap": "function handleWaitMemberTap" in script,
        "select all function": "function selectAllMembers()" in script,
        "user long press guard": "if (!IS_ADMIN) return '';" in script,
        "court vibration x4": "if (type === 'court_assignment') return 4;" in script,
        "wait1 vibration x2": "if (type === 'wait1_ready') return 2;" in script,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise RuntimeError("post-patch checks failed: " + ", ".join(failed))

    print("Stable admin interaction patch validated: inline edit, double tap, select all")


if __name__ == "__main__":
    try:
        main(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
