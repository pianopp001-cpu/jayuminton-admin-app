#!/usr/bin/env python3
"""Double-tapping your own card while in 코트배정대기 moves you into the
nearest open wait slot -- or says so nicely if there isn't one.

Bug report: "코트배정대기에서 더블클릭하면 가장 가까운 대기1~대기5 빈곳으로
가고 대기칸 빈곳이 없으면 아직 빈 자리가 없습니다. 나오면 돼."

Before this patch, a member's own card in the 코트배정대기 (status 'active',
not yet placed in any specific wait group) list rendered with no click
handler at all (memberCard(member, false, false) -- clickable=false), so
nothing app-specific could happen there; whatever a member tapped into
instead fell through to unrelated/legacy code paths. This adds the missing,
explicitly-requested behavior using the same memberMoveToWaitGroup RPC that
already powers the equivalent action inside a wait group (proven working --
it's in the Cloudflare worker's supported memberNames set), so it carries
none of the "legacy RPC no longer recognized" risk that has bitten other
member-swap code paths in this app before.

Scoped narrowly: the click listener only reacts when the tapped card's own
data-member-id matches the member's own stored id, so tapping any other
member's card in the same list is completely unaffected.
"""

from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_member_active_nearest_wait_v1.py INDEX_HTML")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

MARKER = "JAYUMINTON_MEMBER_ACTIVE_NEAREST_WAIT_V1"

if MARKER not in text:
    anchor = '<script id="jayuminton-team-visuals-v8-script">'
    count = text.count(anchor)
    if count != 1:
        raise SystemExit(
            "team-visuals-v8 anchor not found exactly once (found %d) -- "
            "live source has drifted, aborting to avoid corrupting the page" % count
        )

    addon = (
        '<script id="jayuminton-member-active-nearest-wait-v1">\n'
        "/* " + MARKER + ": while a member is in 코트배정대기 (status "
        "'active', not yet in a specific wait group), double-tapping their "
        "own card moves them into the nearest empty slot among 대기1~대기5, "
        "or says so nicely if none are free. */\n"
        "(function(){\n"
        "  if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;\n"
        "  if(window.__JM_MEMBER_ACTIVE_NEAREST_WAIT_V1__)return;\n"
        "  window.__JM_MEMBER_ACTIVE_NEAREST_WAIT_V1__=true;\n"
        "  var lastTap={id:'',at:0};\n"
        "  var moving=false;\n"
        "  function session(){\n"
        "    try{return typeof memberWaitSeatSessionArgs==='function'"
        "?memberWaitSeatSessionArgs():null;}catch(e){return null;}\n"
        "  }\n"
        "  function nearestEmptyWaitGroup(){\n"
        "    try{\n"
        "      var s=window.STATE||(typeof STATE!=='undefined'?STATE:null);\n"
        "      var groups=(s&&s.waitGroups)||[];\n"
        "      for(var i=0;i<groups.length;i++){"
        "if((groups[i]||[]).length<4)return i;}\n"
        "    }catch(e){}\n"
        "    return -1;\n"
        "  }\n"
        "  async function moveToNearest(){\n"
        "    if(moving)return;\n"
        "    var a=session();if(!a)return;\n"
        "    var idx=nearestEmptyWaitGroup();\n"
        "    if(idx<0){\n"
        "      if(typeof showMemberSettingMessage==='function')"
        "showMemberSettingMessage('아직 빈 자리가 없습니다.',true);\n"
        "      return;\n"
        "    }\n"
        "    moving=true;\n"
        "    try{\n"
        "      var state=await server('memberMoveToWaitGroup',"
        "[a.token,String(a.member.id),idx]);\n"
        "      if(state&&typeof renderState==='function')renderState(state);\n"
        "    }catch(e){\n"
        "      if(typeof showMemberSettingMessage==='function')"
        "showMemberSettingMessage('아직 빈 자리가 없습니다.',true);\n"
        "    }finally{moving=false;}\n"
        "  }\n"
        "  function onCardClick(event){\n"
        "    var card=event.target&&event.target.closest"
        "?event.target.closest('[data-member-id]'):null;\n"
        "    if(!card)return;\n"
        "    var id=String(card.getAttribute('data-member-id')||'');\n"
        "    if(!id)return;\n"
        "    var selfId=(typeof storedSelfMemberId==='function')"
        "?storedSelfMemberId():'';\n"
        "    if(!selfId||id!==selfId)return;\n"
        "    var now=Date.now(),dbl=lastTap.id===id&&now-lastTap.at<=420;\n"
        "    lastTap=dbl?{id:'',at:0}:{id:id,at:now};\n"
        "    if(!dbl)return;\n"
        "    if(event.preventDefault)event.preventDefault();\n"
        "    if(event.stopPropagation)event.stopPropagation();\n"
        "    moveToNearest();\n"
        "  }\n"
        "  function wire(){\n"
        "    var root=document.getElementById('activeMembersMember');\n"
        "    if(!root||root.__jmActiveNearestWaitV1)return;\n"
        "    root.__jmActiveNearestWaitV1=true;\n"
        "    root.addEventListener('click',onCardClick,true);\n"
        "  }\n"
        "  if(typeof MutationObserver!=='undefined')"
        "new MutationObserver(wire).observe(document.documentElement,"
        "{childList:true,subtree:true});\n"
        "  document.addEventListener('DOMContentLoaded',wire,{once:true});\n"
        "  setInterval(wire,1800);\n"
        "  wire();\n"
        "})();\n"
        "</script>\n"
        + anchor
    )

    text = text.replace(anchor, addon, 1)

if MARKER not in text:
    raise SystemExit("active nearest-wait double-tap patch did not apply")

path.write_text(text, encoding="utf-8")
print("MEMBER_ACTIVE_NEAREST_WAIT_OK")
