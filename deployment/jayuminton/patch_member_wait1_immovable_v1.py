#!/usr/bin/env python3
"""자신이 대기 1에 배정된 경우는 옮기지 못하게: block ANY swap or pair-play
request, in either direction, that would move a member out of (or the
tapped target out of) 대기1 (wait group index 0 -- the "next up for a court"
slot).

User's request, verbatim: "그리고 자신이 대기 1에 배정된 경우는 옮기지 못하게
사용자쪽 어플도 고쳐줘." -- once someone reaches 대기1, nobody should be able
to swap or pair-request them out of that seat, and a 대기1 member shouldn't
be able to swap/pair-request themselves out of it either -- both directions
matter, since JAYUMINTON_MEMBER_ANYWHERE_SWAP_V1's swap is symmetric (it
moves BOTH parties) and so is JAYUMINTON_MEMBER_PAIR_PLAY_V1's pair-join.

Every member-facing path that can start one of these requests -- tapping any
other card system-wide (JAYUMINTON_MEMBER_ANYWHERE_SWAP_V1's document-level
click listener) and tapping a wait-group card (handleMemberWaitOtherTap,
JAYUMINTON_MEMBER_WAIT_TAP_PAIR_CHOICE_V1) -- already funnels through one
single function by the time this patch runs: window.handleAnywhereMemberTap
(JAYUMINTON_MEMBER_PAIR_PLAY_V1's wrapper around
JAYUMINTON_MEMBER_ANYWHERE_SWAP_SELF_IDENTIFY_V1's version, itself wrapping
the original JAYUMINTON_MEMBER_ANYWHERE_SWAP_V1 definition). That is already
a real `window.X` property, established well before this file's own script
block runs (this patch must be applied AFTER patch_member_pair_play_v1.py in
the deploy pipeline so it wraps the fully-patched, final version rather than
being clobbered by a later reassignment -- see
deploy-unified-member-web-production.yml's ordering), so the same
supersede-by-reassignment technique already used throughout this codebase
(patch_member_safe_alert_v1's window.alert override,
patch_member_pair_play_v1's own wrap of window.handleAnywhereMemberTap)
applies cleanly here too: no already-deployed function body needs editing in
place.

The self-identify branch (device hasn't picked "이게 나예요" yet) and a tap on
one's own card are passed straight through untouched -- neither one ever
starts a real move, so there is nothing to block and no reason to interrupt
first-time setup for someone whose own card happens to already be sitting in
대기1.

This is a client-side UX guard only (shows a friendly message instantly,
before any request is even sent). The authoritative enforcement lives
server-side in cloudflare/state-worker/worker.js's
JAYUMINTON_WAIT1_SWAP_LOCK_V1 addition to requestSwapMutation /
respondSwapMutation / requestPairPlayMutation / respondPairPlayMutation,
which rejects the same cases even from a stale/uncached client, and also
covers the case where a member is promoted into 대기1 by a court finishing
while a request against them is still pending.
"""

from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_member_wait1_immovable_v1.py INDEX_HTML")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

MARKER = "JAYUMINTON_MEMBER_WAIT1_IMMOVABLE_V1"

if MARKER not in text:
    if "window.handleAnywhereMemberTap" not in text:
        raise SystemExit(
            "handleAnywhereMemberTap not found -- the swap/pair-play feature "
            "this patch guards is missing, aborting"
        )

    addon = (
        '<script id="jayuminton-member-wait1-immovable-v1">\n'
        "/* " + MARKER + " */\n"
        "(function(){\n"
        "  if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;\n"
        "  if(window.__JM_MEMBER_WAIT1_IMMOVABLE_V1__)return;\n"
        "  window.__JM_MEMBER_WAIT1_IMMOVABLE_V1__=true;\n"
        "\n"
        "  function isWait1(id){\n"
        "    try{\n"
        "      var s=window.STATE||(typeof STATE!=='undefined'?STATE:null);\n"
        "      var g0=(s&&Array.isArray(s.waitGroups)&&Array.isArray(s.waitGroups[0]))"
        "?s.waitGroups[0]:[];\n"
        "      return g0.some(function(x){return String(x)===String(id);});\n"
        "    }catch(e){return false;}\n"
        "  }\n"
        "\n"
        "  var originalHandleTap=window.handleAnywhereMemberTap;\n"
        "  window.handleAnywhereMemberTap=async function(memberId,event){\n"
        "    if(typeof originalHandleTap!=='function')return;\n"
        "    if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)"
        "return originalHandleTap(memberId,event);\n"
        "    var self=(typeof currentStoredWebPushMember==='function')"
        "?currentStoredWebPushMember():null;\n"
        "    if(!self||!self.id)return originalHandleTap(memberId,event);\n"
        "    if(String(memberId)===String(self.id))"
        "return originalHandleTap(memberId,event);\n"
        "    if(isWait1(memberId)||isWait1(self.id)){\n"
        "      if(event){try{event.preventDefault();"
        "event.stopPropagation();}catch(e){}}\n"
        "      if(typeof showMemberSettingMessage==='function')"
        "showMemberSettingMessage('대기1 순위인 회원은 자리를 옮길 수 없어요.',true);\n"
        "      return;\n"
        "    }\n"
        "    return originalHandleTap(memberId,event);\n"
        "  };\n"
        "})();\n"
        "</script>\n"
    )

    close = text.lower().rfind("</body>")
    if close < 0:
        raise SystemExit("body close not found for wait1-immovable script injection")
    text = text[:close] + addon + text[close:]

if MARKER not in text:
    raise SystemExit("wait1-immovable patch did not apply")

path.write_text(text, encoding="utf-8")
print("MEMBER_WAIT1_IMMOVABLE_OK")
