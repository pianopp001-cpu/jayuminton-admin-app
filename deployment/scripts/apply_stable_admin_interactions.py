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
                return source[:start] + replacement + source[i + 1 :]
        i += 1

    raise RuntimeError(f"{name} braces are unbalanced")


def main(root: Path) -> None:
    admin_path = root / "Admin.html"
    script_path = root / "Script.html"
    if not admin_path.exists() or not script_path.exists():
        raise RuntimeError("Admin.html or Script.html missing")

    # 1) Admin header: the obsolete push-app launcher must stay removed.
    admin = admin_path.read_text(encoding="utf-8")
    button_start = admin.find('<button id="adminPushAppButton"')
    if button_start >= 0:
        button_end = admin.find("</button>", button_start)
        if button_end < 0:
            raise RuntimeError("adminPushAppButton closing tag missing")
        button_end += len("</button>")
        while button_end < len(admin) and admin[button_end] in " \t\r\n":
            button_end += 1
        admin = admin[:button_start] + admin[button_end:]

    if "adminPushAppButton" in admin or "📱 푸시앱" in admin:
        raise RuntimeError("admin push-app button still present")
    admin_path.write_text(admin, encoding="utf-8")

    script = script_path.read_text(encoding="utf-8")

    # 2) Keep foreground vibration semantics aligned with the requested behavior.
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

    # 3) Excluded members (before/rest/away): restore double tap -> active waiting pool.
    if "let LAST_EXCLUDED_MEMBER_TAP" not in script:
        anchor = "let LAST_COURT_MEMBER_TAP = {"
        pos = script.find(anchor)
        if pos < 0:
            raise RuntimeError("court tap tracker anchor missing")
        script = (
            script[:pos]
            + "let LAST_EXCLUDED_MEMBER_TAP = { memberId:'', tappedAt:0 };\n"
            + script[pos:]
        )

    excluded_handler = """function handleExcludedMemberTap(memberId, event) {
  if (!IS_ADMIN) return;
  if (consumeLongPressClick(memberId, event)) return;
  if (assignMemberToChosenEmpty(memberId, event)) return;

  const now = Date.now();
  const isDoubleTap =
    LAST_EXCLUDED_MEMBER_TAP.memberId === memberId &&
    now - LAST_EXCLUDED_MEMBER_TAP.tappedAt <= 420;

  LAST_EXCLUDED_MEMBER_TAP = isDoubleTap
    ? { memberId:'', tappedAt:0 }
    : { memberId:memberId, tappedAt:now };

  if (isDoubleTap) {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
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
        render_block = render_block.replace(
            "handleSelectableMemberClick", "handleExcludedMemberTap", 1
        )
    script = script[:render_start] + render_block + script[render_end:]

    script_path.write_text(script, encoding="utf-8")

    # 4) Deterministic post-patch assertions.
    final_admin = admin_path.read_text(encoding="utf-8")
    final_script = script_path.read_text(encoding="utf-8")
    checks = {
        "admin push button removed": "adminPushAppButton" not in final_admin and "📱 푸시앱" not in final_admin,
        "excluded handler exists": "function handleExcludedMemberTap(memberId, event)" in final_script,
        "excluded handler wired": "handleExcludedMemberTap" in final_script[render_start:render_end + 600],
        "excluded double tap returns active": "runAction('setMemberStatus', [ADMIN_PIN_VALUE, [memberId], 'active'])" in final_script,
        "court vibration x4": "if (type === 'court_assignment') return 4;" in final_script,
        "wait1 vibration x2": "if (type === 'wait1_ready') return 2;" in final_script,
        "user long-press guard": "if (!IS_ADMIN) return '';" in final_script,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise RuntimeError("post-patch checks failed: " + ", ".join(failed))

    print("Stable admin interaction patch validated")


if __name__ == "__main__":
    try:
        main(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
