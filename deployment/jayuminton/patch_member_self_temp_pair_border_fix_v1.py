#!/usr/bin/env python3
"""Restore the yellow dashed temp-team ring on a member's own ("나") card.

Bug report (from the club admin): "그리고 나라고 표시하느라고 임시팀 설정
되었는데도 노란 점선이 안나와" -- when a member without a permanent team is
put into a temporary pairing, every OTHER member's card gets the yellow
dashed outline (#memberApp [data-member-id].jm-temp-pair, added by
patch_member_user_requirements_v1.py's JAYUMINTON_MEMBER_TEAM_BORDER_THICK_V1
rule), but the member's own card never shows it.

Root cause: both of these selectors have the exact same CSS specificity
(1 id + 1 attribute + 1 class = 0,1,1,1 either way):
  #memberApp [data-member-id].jm-temp-pair            (outline: 4px dashed #facc15)
  #memberApp [data-member-id].is-self-member          (outline: 4px solid #2563eb)
The self-member rule (JAYUMINTON_MEMBER_REQUIREMENTS_COMPLETION_V1) was added
later in the stylesheet, so on a card that carries BOTH classes -- the
member's own card while temp-paired -- its solid blue outline wins the
cascade and silently replaces the dashed yellow one. This never depended on
IS_ADMIN or on any paint/render logic; it is a pure CSS specificity tie,
broken by source order.

Fix: add two higher-specificity combo rules (1 id + 1 attribute + 2 classes)
that fire only when both classes are present, keeping the self card's blue
border while restoring the dashed yellow outline on top of it.
"""

from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_member_self_temp_pair_border_fix_v1.py INDEX_HTML")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

MARKER = "JAYUMINTON_MEMBER_SELF_TEMP_PAIR_BORDER_FIX_V1"

if MARKER not in text:
    anchor = (
        "box-shadow:0 1px 3px rgba(15,23,42,.35)!important}\n"
        "#memberApp [data-member-id]>.member-public-memo{"
    )
    count = text.count(anchor)
    if count != 1:
        raise SystemExit(
            "self-double-ring anchor not found exactly once (found %d) -- "
            "live source has drifted, aborting to avoid corrupting the page" % count
        )

    addon = (
        "box-shadow:0 1px 3px rgba(15,23,42,.35)!important}\n"
        "/* " + MARKER + ": a temp-team pairing on the member's own card must "
        "still show its yellow dashed ring -- the self card's own blue outline "
        "was winning the CSS cascade (identical specificity, declared later) "
        "and hiding it. */\n"
        "#memberApp [data-member-id].is-self-member.jm-temp-pair{"
        "border:2px solid #2563eb!important;"
        "outline:4px dashed #facc15!important;"
        "outline-offset:2px!important;"
        "box-shadow:none!important;"
        "overflow:visible!important;"
        "background-clip:padding-box!important"
        "}\n"
        "#memberApp [data-member-id].is-self-member.jm-has-team.jm-temp-pair{"
        "border:2px solid var(--jm-team-color,#6d28d9)!important;"
        "outline:4px dashed #facc15!important;"
        "outline-offset:2px!important;"
        "box-shadow:none!important;"
        "overflow:visible!important;"
        "background-clip:padding-box!important"
        "}\n"
        "#memberApp [data-member-id]>.member-public-memo{"
    )

    text = text.replace(anchor, addon, 1)

if MARKER not in text:
    raise SystemExit("self temp-pair border fix did not apply")

path.write_text(text, encoding="utf-8")
print("MEMBER_SELF_TEMP_PAIR_BORDER_FIX_OK")
