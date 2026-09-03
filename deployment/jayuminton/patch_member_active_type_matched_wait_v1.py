#!/usr/bin/env python3
"""Double-tapping your own card while in 코트배정대기 should land you in the
earliest wait group that can still become a proper 남복/여복/혼복 game, not
just whichever slot happens to have room first.

Bug report: "나 자신이 코트배정 대기에 있는데 더블클릭하면 대기1부터 대기
5중에서 가장 가까운 곳에 배정돼. 하지만 남복과 혼복 혹은 여복이 맞는 곳에
가장 빠른 대기 순서에 배치가 돼."

patch_member_active_nearest_wait_v1.py (JAYUMINTON_MEMBER_ACTIVE_NEAREST_WAIT_V1)
already ships this double-tap gesture, but its nearestEmptyWaitGroup() only
checks group SIZE (<4), ignoring gender composition entirely -- a wait group
sitting at 3 women + 0 men would happily accept a man next, stranding the
group at 3-1 with no way to complete a standard doubles match (남복=4 men,
여복=4 women, 혼복=2 men + 2 women; anything else, like 3-1, can never finish
as a playable game without someone moving again). That existing marker is
already baked into a previously deployed live page, so editing its function
in place would not take effect -- this instead installs a second, later
click listener on the ancestor `document` (capture phase fires ancestors
before descendants, so this always runs before the existing listener bound
directly on #activeMembersMember) that does its own double-tap detection and
calls event.stopPropagation() on every self-card click, fully superseding
the old handler without touching its code.

Placement rule: scan 대기1..대기5 in order (same priority the user asked
for -- "가장 빠른 대기 순서") and skip any full group. For each group with
room, given its current male/female counts (m, f), adding this member of
gender G keeps the group on a path to SOME valid final composition
{4M, 4F, 2M+2F} if and only if:
  - member is male:   f===0  OR  (m<=1 AND f<=2)
  - member is female: m===0  OR  (f<=1 AND m<=2)
An empty group (m=0, f=0) always qualifies for anyone, so this only ever
steers a member past a group that would otherwise have led to a stuck
composition -- it never blocks placement outright. If literally no wait
group of the five satisfies this (every one already skewed against this
member's gender), this falls back to the first group with room at all,
preserving the old "always let them in somewhere" guarantee rather than
leaving the member stuck with an error.
"""

from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_member_active_type_matched_wait_v1.py INDEX_HTML")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

MARKER = "JAYUMINTON_MEMBER_ACTIVE_TYPE_MATCHED_WAIT_V1"

if MARKER not in text:
    anchor = '<script id="jayuminton-team-visuals-v8-script">'
    count = text.count(anchor)
    if count != 1:
        raise SystemExit(
            "team-visuals-v8 anchor not found exactly once (found %d) -- "
            "live source has drifted, aborting to avoid corrupting the page" % count
        )

    addon = (
        '<script id="jayuminton-member-active-type-matched-wait-v1">\n'
        "/* " + MARKER + ": supersedes JAYUMINTON_MEMBER_ACTIVE_NEAREST_WAIT_V1's "
        "plain nearest-empty-slot double-tap with a gender-composition-aware pick, "
        "via an ancestor capture-phase listener (see module docstring for why). */\n"
        "(function(){\n"
        "  if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;\n"
        "  if(window.__JM_MEMBER_ACTIVE_TYPE_MATCHED_WAIT_V1__)return;\n"
        "  window.__JM_MEMBER_ACTIVE_TYPE_MATCHED_WAIT_V1__=true;\n"
        "  var lastTap={id:'',at:0};\n"
        "  var moving=false;\n"
        "  function session(){\n"
        "    try{return typeof memberWaitSeatSessionArgs==='function'"
        "?memberWaitSeatSessionArgs():null;}catch(e){return null;}\n"
        "  }\n"
        "  function state(){try{return window.STATE||(typeof STATE!=='undefined'?STATE:null);}catch(e){return null;}}\n"
        "  function genderOf(members,id){\n"
        "    var m=(members||[]).find(function(x){return x&&String(x.id)===String(id);});\n"
        "    var g=m?String(m.gender||'').toLowerCase():'';\n"
        "    return (g==='female'||g==='여')?'female':'male';\n"
        "  }\n"
        "  function pickTargetWaitGroup(selfId){\n"
        "    var s=state();if(!s)return -1;\n"
        "    var groups=s.waitGroups||[],members=s.members||[];\n"
        "    var isMale=genderOf(members,selfId)==='male';\n"
        "    var fallback=-1;\n"
        "    for(var i=0;i<groups.length;i++){\n"
        "      var grp=groups[i]||[];\n"
        "      if(grp.length>=4)continue;\n"
        "      if(fallback<0)fallback=i;\n"
        "      var m=0,f=0;\n"
        "      for(var j=0;j<grp.length;j++){if(genderOf(members,grp[j])==='male')m++;else f++;}\n"
        "      var ok=isMale?(f===0||(m<=1&&f<=2)):(m===0||(f<=1&&m<=2));\n"
        "      if(ok)return i;\n"
        "    }\n"
        "    return fallback;\n"
        "  }\n"
        "  async function moveToMatchingType(){\n"
        "    if(moving)return;\n"
        "    var a=session();if(!a)return;\n"
        "    var idx=pickTargetWaitGroup(a.member.id);\n"
        "    if(idx<0){\n"
        "      if(typeof showMemberSettingMessage==='function')"
        "showMemberSettingMessage('아직 빈 자리가 없습니다.',true);\n"
        "      return;\n"
        "    }\n"
        "    moving=true;\n"
        "    try{\n"
        "      var next=await server('memberMoveToWaitGroup',"
        "[a.token,String(a.member.id),idx]);\n"
        "      if(next&&typeof renderState==='function')renderState(next);\n"
        "    }catch(e){\n"
        "      if(typeof showMemberSettingMessage==='function')"
        "showMemberSettingMessage('아직 빈 자리가 없습니다.',true);\n"
        "    }finally{moving=false;}\n"
        "  }\n"
        "  document.addEventListener('click',function(event){\n"
        "    var card=event.target&&event.target.closest"
        "?event.target.closest('[data-member-id]'):null;\n"
        "    if(!card)return;\n"
        "    var root=document.getElementById('activeMembersMember');\n"
        "    if(!root||!root.contains(card))return;\n"
        "    var id=String(card.getAttribute('data-member-id')||'');\n"
        "    if(!id)return;\n"
        "    var selfId=(typeof storedSelfMemberId==='function')"
        "?storedSelfMemberId():'';\n"
        "    if(!selfId||id!==selfId)return;\n"
        "    event.stopPropagation();\n"
        "    var now=Date.now(),dbl=lastTap.id===id&&now-lastTap.at<=420;\n"
        "    lastTap=dbl?{id:'',at:0}:{id:id,at:now};\n"
        "    if(!dbl)return;\n"
        "    if(event.preventDefault)event.preventDefault();\n"
        "    moveToMatchingType();\n"
        "  },true);\n"
        "})();\n"
        "</script>\n"
        + anchor
    )

    text = text.replace(anchor, addon, 1)

if MARKER not in text:
    raise SystemExit("active type-matched wait double-tap patch did not apply")

path.write_text(text, encoding="utf-8")
print("MEMBER_ACTIVE_TYPE_MATCHED_WAIT_OK")
