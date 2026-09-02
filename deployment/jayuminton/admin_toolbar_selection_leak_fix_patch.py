#!/usr/bin/env python3
"""Fix a phantom-selection bug in the "멤버선택 · 상태변경 · 회원삭제" bulk toolbar
(the jmUnifiedSwapMoveFixV1 IIFE's capturing click listener on #adminApp).

User-reported symptoms, all traced to the same root cause:
  1) "대기2에 있는 사람이나 대기1에 있는 사람 임시팀 설정을 했는데 선택하지도 않는
     사람 대기에 있는 사람과 임시팀이 같이 설정됐어" -- 임시팀설정 ends up pairing an
     unselected member together with the intended one.
  2) "체크표시의 선택이 되더니 안없어진다" -- a selection checkmark appears and never
     goes away no matter what the user does afterwards.

ROOT CAUSE: handleClick() is registered with addEventListener(..., true) directly on
#adminApp, so it fires in the CAPTURE phase for every click anywhere inside the app --
including clicks on unrelated per-member action buttons that live INSIDE a member card,
such as the wait-group "빼기" (remove) button. handleClick() always resolves the click's
nearest ancestor member-card via cardFrom() and, finding one, calls
ev.stopImmediatePropagation() and silently toggles that card's member id into the
toolbar's own `selected` Set -- even when the user actually clicked a specific button for
an unrelated purpose. Because stopImmediatePropagation() in the capture phase prevents the
button's own onclick from ever running in some cases, and because this toggle happens
completely invisibly (no confirmation, easy to miss a single small checkmark badge), a
member can end up "selected" in this Set without the user ever intending it.

That phantom selection then lingers indefinitely: ordinary actions that go through the
base app's runAction() (used by 빼기/상태변경/코트배정 등 대부분의 기본 동작) only clear
the OLD `SELECTED` (uppercase) Set -- a different, largely-superseded selection mechanism
-- and never the toolbar's own lowercase `selected` Set, nor do they repaint it. So the
phantom stays selected across renders and reappears (this file's own MutationObserver
re-applies the checkmark badge after every DOM update) until the user happens to click
that exact card again. If the user then selects 1 more member intentionally and clicks
임시팀설정, setTemporary() reads `Array.from(selected)` and unknowingly includes the
still-phantom-selected member too.

FIX (two minimal, surgical changes, no behavior change for intentional clicks):
  1) handleClick(): right after resolving `c = cardFrom(ev.target)`, discard `c` (treat it
     as "no card") whenever the actual click landed on a nested interactive control
     (button/select/input/textarea/a[href]/[role=button]) that is NOT the card element
     itself. This lets a card's own body still toggle selection normally (its own root
     element matches `closest()` immediately, so intentional selection clicks are
     unaffected), while a nested action button like 빼기 now falls through untouched and
     its own onclick runs exactly as before.
  2) runAction(): right after the existing `SELECTED.clear();` (the base app's own,
     unrelated selection Set), also invoke the toolbar's already-exposed
     `window.__jmClearUnlimitedSelectedV1()` cleanup hook (added earlier specifically for
     this purpose) so that any ordinary action that clears selection also clears and
     repaints the toolbar's shadow selection state, instead of leaving stale phantom
     checkmarks around.

Operates on the fully-built admin index.html (same file build-admin-native-session-fix.yml
extracts from the latest release APK)."""
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
html = path.read_text(encoding='utf-8')

MARKER = 'jmToolbarSelectionLeakFixV1'
if MARKER in html:
    print('ADMIN_TOOLBAR_SELECTION_LEAK_FIX_ALREADY_OK')
    raise SystemExit(0)

# 1) handleClick(): discard `c` when the click landed on a nested interactive control
#    that isn't the card itself.
OLD_HANDLE_CLICK_HEAD = "function handleClick(ev){/* jmUnifiedSwapMoveFixV1 */if(busy)return;var r=root();if(!r||!r.contains(ev.target))return;var c=cardFrom(ev.target);if(mode==='swap'){"
if html.count(OLD_HANDLE_CLICK_HEAD) != 1:
    raise SystemExit(f'handleClick anchor not found or not unique, found {html.count(OLD_HANDLE_CLICK_HEAD)} -- HTML has drifted')

NEW_HANDLE_CLICK_HEAD = (
    "function handleClick(ev){/* jmUnifiedSwapMoveFixV1 */if(busy)return;var r=root();if(!r||!r.contains(ev.target))return;"
    "var c=cardFrom(ev.target);"
    "/* " + MARKER + ": a nested action control (button/select/input/textarea/link) inside "
    "the card is not the card itself -- don't hijack that click into a selection toggle, "
    "let its own onclick run untouched. */"
    "if(c){var __jmNestedCtl=ev.target&&ev.target.closest&&ev.target.closest('button,select,input,textarea,a[href],[role=\"button\"]');"
    "if(__jmNestedCtl&&__jmNestedCtl!==c)c=null;}"
    "if(mode==='swap'){"
)
html = html.replace(OLD_HANDLE_CLICK_HEAD, NEW_HANDLE_CLICK_HEAD, 1)

# 2) runAction(): also clear the toolbar's own shadow selection whenever the base app
#    clears its own SELECTED set.
OLD_RUN_ACTION = (
    "async function runAction(name, args) {\n"
    "  const previousState =\n"
    "    JSON.parse(JSON.stringify(STATE));\n"
    "\n"
    "  try {\n"
    "    const state =\n"
    "      await server(name, args);\n"
    "\n"
    "    SELECTED.clear();\n"
)
if html.count(OLD_RUN_ACTION) != 1:
    raise SystemExit(f'runAction anchor not found or not unique, found {html.count(OLD_RUN_ACTION)} -- HTML has drifted')

NEW_RUN_ACTION = OLD_RUN_ACTION + (
    "    /* " + MARKER + ": keep the bulk-toolbar's own shadow selection Set in sync -- "
    "otherwise a phantom member stays \"selected\" there forever and can silently ride "
    "along into a later bulk action (e.g. 임시팀설정). */\n"
    "    if(typeof window.__jmClearUnlimitedSelectedV1==='function')window.__jmClearUnlimitedSelectedV1();\n"
)
html = html.replace(OLD_RUN_ACTION, NEW_RUN_ACTION, 1)

if MARKER not in html:
    raise SystemExit('marker missing after patch -- replacement silently failed')
if html.count("if(__jmNestedCtl&&__jmNestedCtl!==c)c=null;") != 1:
    raise SystemExit('nested-control guard missing after patch')
if html.count("if(typeof window.__jmClearUnlimitedSelectedV1==='function')window.__jmClearUnlimitedSelectedV1();") != 1:
    raise SystemExit('runAction sync-clear call missing after patch')

path.write_text(html, encoding='utf-8')
print('ADMIN_TOOLBAR_SELECTION_LEAK_FIX_OK')
