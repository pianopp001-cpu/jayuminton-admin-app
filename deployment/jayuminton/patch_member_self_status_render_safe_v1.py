#!/usr/bin/env python3
"""Stop a spurious error toast from appearing after a successful self status
change (e.g. long-press card -> "코트배정대기로 가기").

Bug report: "나자신을 더블클릭하면 코트배정대기로 가는데 오류가 발생했습니다
하면서 동작은 돼." -- the member move itself (memberMoveSelf) already succeeds
on the server, but applySelfStatus's single try/catch also wraps the local
renderState(state) call that follows it. If that local re-render throws for
any reason, the SAME catch block fires alert(...), so the member sees an
error message despite the underlying status change having already saved.
This is the known "cannot read properties of undefined (reading '1')" popup
also referenced in patch_member_safe_alert_v1.py's own bug report -- that
patch only made the popup non-technical, it never separated a render hiccup
from an actual mutation failure.

Fix: split the try/catch. Only a failure of the memberMoveSelf call itself
(the thing that can actually not have happened) shows an error. A failure of
the follow-up local renderState(state) call is swallowed silently -- the
mutation already completed server-side, and the page's own periodic
pollRevision refresh (every few seconds) will pick up the fresh state
regardless, so showing an error there would only be misleading.
"""

from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_member_self_status_render_safe_v1.py INDEX_HTML")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

MARKER = "JAYUMINTON_MEMBER_SELF_STATUS_RENDER_SAFE_V1"

if MARKER not in text:
    anchor = (
        "async function applySelfStatus(memberId, action){\n"
        "    var a=sessionArgs(); if(!a) return;\n"
        "    var map={'코트배정대기로 가기':'active','도착전':'before','휴식':'rest','귀가':'away'};\n"
        "    var status = map[action]; if(!status) return;\n"
        "    try{\n"
        "      var state = await server('memberMoveSelf',[a.token,String(a.member.id),{type:'status',status:status}]);\n"
        "      if(state&&typeof renderState==='function') renderState(state);\n"
        "    }catch(e){ alert(String(e&&e.message||e||'변경 실패')); }\n"
        "  }"
    )
    count = text.count(anchor)
    if count != 1:
        raise SystemExit(
            "applySelfStatus anchor not found exactly once (found %d) -- "
            "live source has drifted, aborting to avoid corrupting the page" % count
        )

    replacement = (
        "async function applySelfStatus(memberId, action){\n"
        "    var a=sessionArgs(); if(!a) return;\n"
        "    var map={'코트배정대기로 가기':'active','도착전':'before','휴식':'rest','귀가':'away'};\n"
        "    var status = map[action]; if(!status) return;\n"
        "    /* " + MARKER + ": a render hiccup after a successful move must never look like a\n"
        "       failed move -- only an actual memberMoveSelf failure is user-facing. */\n"
        "    var state=null, moveError=null;\n"
        "    try{ state = await server('memberMoveSelf',[a.token,String(a.member.id),{type:'status',status:status}]); }\n"
        "    catch(e){ moveError=e; }\n"
        "    if(moveError){ alert(String(moveError&&moveError.message||moveError||'변경 실패')); return; }\n"
        "    try{ if(state&&typeof renderState==='function') renderState(state); }\n"
        "    catch(e){ /* mutation already saved server-side; the next periodic poll refreshes the view. */ }\n"
        "  }"
    )

    text = text.replace(anchor, replacement, 1)

if MARKER not in text:
    raise SystemExit("self status render-safe patch did not apply")

path.write_text(text, encoding="utf-8")
print("MEMBER_SELF_STATUS_RENDER_SAFE_OK")
