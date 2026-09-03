#!/usr/bin/env python3
"""짝요청하기 ("같이 게임하기" 요청): tapping another member's card now asks
whether you want to swap seats (existing behavior, untouched) or request to
play together as a pair.

User's own words describing the desired behavior, kept verbatim for the
record: "상대방 클릭하면 바꾸기 요청 혹은 같이 맨 아래 대기 빈자리로 가서라도
같이 게임하자고 요청하기 둘중에 하나 선택하는 거라고, 같이 게임한다고 수락을
하면 맨 아래 대기조에 빈자리 비어 있으면 들어가고 빈자리가 없으면 관리자에게
나중에 오래기다려도 되니 누구랑 같이 게임짜달라고 부탁하게 해달라고." and
"자리 맞바꾸기는 ... 자리 바꿈 요청은 예전 그대로 돌려놔라" -- i.e. the
pre-existing anywhere-swap feature must be left completely alone.

This patch deliberately does NOT edit the existing
installMemberAnywhereSwapV1 script block at all (its exact source has to
keep matching the anywhere-swap patch above it in the deploy pipeline byte
for byte). Instead, following this codebase's own established pattern
(see patch_member_safe_alert_v1, which overrides window.alert the same
way), it wraps the *global* window.handleAnywhereMemberTap function after
the fact: tapping another member's card still goes through the original
function first for the "no self identity yet" / "tapped own card" cases
(so that behavior is byte-for-byte unchanged), and only when a real
other-member tap would have gone straight to a swap request does this
patch step in first with a small choice popup.

The backend RPCs this calls (memberRequestPairPlay, memberGetPairPlayRequest,
memberAcceptPairPlay, memberRejectPairPlay) are added to the Cloudflare
worker's memberNames allowlist in the same change that adds this patch to
the deploy pipeline; see cloudflare/state-worker/worker.js's
JAYUMINTON_MEMBER_PAIR_PLAY_V1 mutations.
"""

from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_member_pair_play_v1.py INDEX_HTML")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

MARKER = "JAYUMINTON_MEMBER_PAIR_PLAY_V1"

if MARKER not in text:
    # This must load AFTER window.handleAnywhereMemberTap is defined (by the
    # JAYUMINTON_MEMBER_ANYWHERE_SWAP_V1 script block) and after every later
    # patch that further edits that same function's source in place
    # (self-identify, no-double-confirm, etc). All of those are inserted
    # right before the closing </body> tag, in pipeline order, by earlier
    # steps in this same deploy job -- so anchoring on </body> here too,
    # and running this patch step after all of them, guarantees this wrapper
    # captures the final, fully-patched swap handler as originalHandleTap
    # rather than an earlier stub that later gets clobbered. (An earlier
    # version of this patch anchored on the jayuminton-team-visuals-v8-script
    # tag instead, which sits much earlier in the document than </body> --
    # that ordering silently broke the whole feature, since the real
    # handleAnywhereMemberTap assignment runs afterward and overwrites
    # whatever this wrapper installs.)
    if 'window.handleAnywhereMemberTap' not in text:
        raise SystemExit(
            "handleAnywhereMemberTap not found -- the anywhere-swap feature "
            "this patch builds on top of is missing, aborting"
        )

    member_addon = (
        '<script id="jayuminton-member-pair-play-v1">\n'
        "/* " + MARKER + " */\n"
        "(function(){\n"
        "  if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;\n"
        "  if(window.__JM_MEMBER_PAIR_PLAY_V1__)return;\n"
        "  window.__JM_MEMBER_PAIR_PLAY_V1__=true;\n"
        "\n"
        "  function sessionArgs(){\n"
        "    try{return (typeof memberWaitSeatSessionArgs==='function')"
        "?memberWaitSeatSessionArgs():null;}catch(e){return null;}\n"
        "  }\n"
        "  function findMember(id){\n"
        "    try{\n"
        "      var s=window.STATE||(typeof STATE!=='undefined'?STATE:null);\n"
        "      return ((s&&s.members)||[]).find(function(m){"
        "return m&&String(m.id)===String(id);})||null;\n"
        "    }catch(e){return null;}\n"
        "  }\n"
        "\n"
        "  function showPairChoice(targetName){\n"
        "    return new Promise(function(resolve){\n"
        "      var old=document.getElementById('jmPairChoiceModal');\n"
        "      if(old)old.remove();\n"
        "      var box=document.createElement('div');\n"
        "      box.id='jmPairChoiceModal';\n"
        "      box.style.cssText='position:fixed;inset:0;z-index:2147483646;"
        "background:rgba(15,23,42,.45);display:flex;align-items:center;"
        "justify-content:center;padding:16px';\n"
        "      box.innerHTML="
        "'<div style=\"background:#fff;border-radius:16px;max-width:320px;"
        "width:100%;padding:18px;text-align:center;"
        "box-shadow:0 10px 30px rgba(0,0,0,.25)\">'+\n"
        "        '<div style=\"font-weight:800;font-size:16px;"
        "margin-bottom:14px\">'+String(targetName||'선택한 회원')"
        "+'님과 뭘 할까요?</div>'+\n"
        "        '<button type=\"button\" data-choice=\"pair\" "
        "style=\"width:100%;min-height:44px;border:0;border-radius:10px;"
        "background:#2563eb;color:#fff;font-weight:800;margin-bottom:8px\">"
        "같이 게임하기 (짝 요청)</button>'+\n"
        "        '<button type=\"button\" data-choice=\"swap\" "
        "style=\"width:100%;min-height:44px;border:1px solid #cbd5e1;"
        "border-radius:10px;background:#f8fafc;color:#0f172a;"
        "font-weight:800;margin-bottom:8px\">자리 바꾸기 요청</button>'+\n"
        "        '<button type=\"button\" data-choice=\"\" "
        "style=\"width:100%;min-height:40px;border:0;background:transparent;"
        "color:#64748b\">취소</button>'+\n"
        "      '</div>';\n"
        "      document.body.appendChild(box);\n"
        "      box.addEventListener('click',function(e){\n"
        "        if(e.target===box){box.remove();resolve(null);return;}\n"
        "        var btn=e.target.closest&&e.target.closest('[data-choice]');\n"
        "        if(!btn)return;\n"
        "        var choice=btn.getAttribute('data-choice')||null;\n"
        "        box.remove();\n"
        "        resolve(choice||null);\n"
        "      });\n"
        "    });\n"
        "  }\n"
        "\n"
        "  async function requestPairPlay(targetId){\n"
        "    var a=sessionArgs();if(!a)return;\n"
        "    var target=findMember(targetId);\n"
        "    if(!target)return;\n"
        "    try{\n"
        "      await server('memberRequestPairPlay',"
        "[a.token,String(a.member.id),String(targetId)]);\n"
        "      if(typeof showMemberSettingMessage==='function')"
        "showMemberSettingMessage("
        "String(target.name||'선택한 회원')"
        "+'님에게 짝 요청을 보냈어요. 5분 내 응답이 없으면 요청이 사라져요.');\n"
        "    }catch(e){\n"
        "      var errMsg=(e&&e.message)||e||'짝 요청 실패';\n"
        "      if(String(errMsg)==='invalid_pair_request')"
        "errMsg='요청할 수 없는 상대예요.';\n"
        "      alert(String(errMsg));\n"
        "    }\n"
        "  }\n"
        "\n"
        "  var originalHandleTap=window.handleAnywhereMemberTap;\n"
        "  window.handleAnywhereMemberTap=async function(memberId,event){\n"
        "    if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;\n"
        "    if(typeof originalHandleTap!=='function')return;\n"
        "    var self=(typeof currentStoredWebPushMember==='function')"
        "?currentStoredWebPushMember():null;\n"
        "    var a=sessionArgs();\n"
        "    if(!self||!self.id||!a||"
        "String(memberId)===String(a&&a.member&&a.member.id)){\n"
        "      return originalHandleTap(memberId,event);\n"
        "    }\n"
        "    if(event){try{event.preventDefault();"
        "event.stopPropagation();}catch(e){}}\n"
        "    var target=findMember(memberId);\n"
        "    var choice=await showPairChoice(target&&target.name);\n"
        "    if(choice==='pair')requestPairPlay(memberId);\n"
        "    else if(choice==='swap')return originalHandleTap(memberId,event);\n"
        "  };\n"
        "\n"
        "  var PAIR_CHECKING=false,PAIR_LAST_SHOWN_ID='';\n"
        "  var PAIR_ALERT_ID='jmPairIncomingAlert';\n"
        "  function ensurePairAlert(){\n"
        "    var box=document.getElementById(PAIR_ALERT_ID);\n"
        "    if(box)return box;\n"
        "    box=document.createElement('div');\n"
        "    box.id=PAIR_ALERT_ID;\n"
        "    box.className='hidden';\n"
        "    box.style.cssText='position:fixed;inset:0;z-index:2147483646;"
        "background:rgba(15,23,42,.55);display:flex;align-items:center;"
        "justify-content:center;padding:16px';\n"
        "    box.innerHTML="
        "'<div style=\"background:#fff;border-radius:16px;max-width:340px;"
        "width:100%;padding:20px;text-align:center;"
        "box-shadow:0 10px 30px rgba(0,0,0,.3)\">'+\n"
        "      '<div style=\"font-size:34px;margin-bottom:8px\">🤝</div>'+\n"
        "      '<div id=\"jmPairIncomingAlertText\" style=\"font-weight:800;"
        "font-size:16px;margin-bottom:16px;line-height:1.5\"></div>'+\n"
        "      '<button type=\"button\" data-pair-choice=\"accept\" "
        "style=\"width:100%;min-height:46px;border:0;border-radius:10px;"
        "background:#2563eb;color:#fff;font-weight:800;margin-bottom:8px\">"
        "수락하기</button>'+\n"
        "      '<button type=\"button\" data-pair-choice=\"reject\" "
        "style=\"width:100%;min-height:40px;border:1px solid #cbd5e1;"
        "border-radius:10px;background:#f8fafc;color:#0f172a;"
        "font-weight:800\">거절하기</button>'+\n"
        "    '</div>';\n"
        "    document.body.appendChild(box);\n"
        "    return box;\n"
        "  }\n"
        "  function showIncomingPairAlert(text){\n"
        "    return new Promise(function(resolve){\n"
        "      var box=ensurePairAlert();\n"
        "      box.querySelector('#jmPairIncomingAlertText').textContent="
        "text;\n"
        "      function onClick(e){\n"
        "        var btn=e.target.closest&&e.target.closest("
        "'[data-pair-choice]');\n"
        "        if(!btn)return;\n"
        "        box.removeEventListener('click',onClick);\n"
        "        box.classList.add('hidden');\n"
        "        resolve(btn.getAttribute('data-pair-choice')==='accept');\n"
        "      }\n"
        "      box.addEventListener('click',onClick);\n"
        "      box.classList.remove('hidden');\n"
        "    });\n"
        "  }\n"
        "  async function pollIncomingPair(){\n"
        "    if((typeof IS_ADMIN!=='undefined'&&IS_ADMIN)||PAIR_CHECKING)"
        "return;\n"
        "    var a=sessionArgs();if(!a)return;\n"
        "    PAIR_CHECKING=true;\n"
        "    try{\n"
        "      var req=await server('memberGetPairPlayRequest',"
        "[a.token,String(a.member.id)]);\n"
        "      if(!req||!req.id||String(req.id)===PAIR_LAST_SHOWN_ID)return;\n"
        "      PAIR_LAST_SHOWN_ID=String(req.id);\n"
        "      var requester=findMember(req.requesterId);\n"
        "      var incomingMessage=String(requester&&requester.name"
        "||'다른 회원')+'님이 함께 게임하자고 요청했어요.\\n\\n수락하면 대기 "
        "맨 뒤 자리로 함께 이동해요 (자리가 없으면 관리자에게 자동으로 "
        "전달돼요).';\n"
        "      var accepted=await showIncomingPairAlert(incomingMessage);\n"
        "      var result=await server("
        "accepted?'memberAcceptPairPlay':'memberRejectPairPlay',"
        "[a.token,String(a.member.id),String(req.requesterId),"
        "Number(req.createdAt||0)]);\n"
        "      if(result&&result.state&&typeof renderState==='function')"
        "renderState(result.state);\n"
        "      if(accepted){\n"
        "        if(typeof showMemberSettingMessage==='function'){\n"
        "          if(result&&result.outcome==='joined')"
        "showMemberSettingMessage('대기 맨 뒤 자리로 함께 배정됐어요!');\n"
        "          else showMemberSettingMessage("
        "'지금은 빈자리가 없어서 관리자에게 전달했어요. "
        "자리가 나면 배정해 드릴게요.');\n"
        "        }\n"
        "      }else if(typeof showMemberSettingMessage==='function'){\n"
        "        showMemberSettingMessage('짝 요청을 거절했습니다.');\n"
        "      }\n"
        "    }catch(e){try{console.warn(e);}catch(err){}}"
        "finally{PAIR_CHECKING=false;}\n"
        "  }\n"
        "  setInterval(pollIncomingPair,9500);\n"
        "})();\n"
        "</script>\n"
    )

    admin_addon = (
        '<script id="jayuminton-admin-pair-notice-v1">\n'
        "/* " + MARKER + ": admin-facing list of 짝요청 that could not be "
        "seated automatically because 대기5 had no room for both members -- "
        "the member already got the '나중에 부탁' message, this is where the "
        "admin actually sees and clears that request. */\n"
        "(function(){\n"
        "  if(typeof IS_ADMIN==='undefined'||!IS_ADMIN)return;\n"
        "  if(window.__JM_ADMIN_PAIR_NOTICE_V1__)return;\n"
        "  window.__JM_ADMIN_PAIR_NOTICE_V1__=true;\n"
        "\n"
        "  function memberName(list,id){\n"
        "    var m=(list||[]).find(function(x){"
        "return x&&String(x.id)===String(id);});\n"
        "    return m&&m.name?String(m.name):'알 수 없음';\n"
        "  }\n"
        "  function render(state){\n"
        "    var pending=((state&&state.pairRequests)||[]).filter("
        "function(r){return r&&r.status==='accepted_awaiting_seat';});\n"
        "    var badge=document.getElementById('jmAdminPairNoticeBadge');\n"
        "    if(!pending.length){if(badge)badge.remove();return;}\n"
        "    if(!badge){\n"
        "      badge=document.createElement('button');\n"
        "      badge.id='jmAdminPairNoticeBadge';\n"
        "      badge.type='button';\n"
        "      badge.style.cssText='position:fixed;right:14px;bottom:14px;"
        "z-index:2147483000;min-height:44px;padding:0 16px;border:0;"
        "border-radius:999px;background:#2563eb;color:#fff;font-weight:800;"
        "box-shadow:0 4px 14px rgba(0,0,0,.3)';\n"
        "      document.body.appendChild(badge);\n"
        "      badge.addEventListener('click',function(){\n"
        "        openList(badge.__jmPending||[]);\n"
        "      });\n"
        "    }\n"
        "    badge.__jmPending=pending;\n"
        "    badge.textContent='🤝 짝 요청 '+pending.length+'건';\n"
        "  }\n"
        "  function openList(pending){\n"
        "    var old=document.getElementById('jmAdminPairNoticeModal');\n"
        "    if(old)old.remove();\n"
        "    var box=document.createElement('div');\n"
        "    box.id='jmAdminPairNoticeModal';\n"
        "    box.style.cssText='position:fixed;inset:0;z-index:2147483647;"
        "background:rgba(15,23,42,.5);display:flex;align-items:center;"
        "justify-content:center;padding:16px';\n"
        "    var rowsHtml=pending.map(function(r){\n"
        "      var names=memberName(STATE.members,r.requesterId)+' · '"
        "+memberName(STATE.members,r.targetId);\n"
        "      return '<div style=\"display:flex;align-items:center;"
        "justify-content:space-between;gap:10px;padding:10px 0;"
        "border-bottom:1px solid #e2e8f0\">'+\n"
        "        '<span style=\"font-weight:700\">'+names+"
        "'</span>'+\n"
        "        '<button type=\"button\" data-request-id=\"'+r.id+'\" "
        "style=\"min-height:36px;padding:0 12px;border:0;border-radius:8px;"
        "background:#16a34a;color:#fff;font-weight:800\">완료</button>'+\n"
        "      '</div>';\n"
        "    }).join('');\n"
        "    box.innerHTML='<div style=\"background:#fff;border-radius:16px;"
        "max-width:360px;width:100%;max-height:70vh;overflow:auto;"
        "padding:18px;box-shadow:0 10px 30px rgba(0,0,0,.25)\">'+\n"
        "      '<div style=\"font-weight:800;font-size:16px;"
        "margin-bottom:10px\">자리 나면 같이 배정해달라는 요청</div>'+\n"
        "      rowsHtml+\n"
        "      '<button type=\"button\" data-close=\"1\" "
        "style=\"width:100%;min-height:40px;margin-top:12px;border:0;"
        "background:transparent;color:#64748b\">닫기</button>'+\n"
        "    '</div>';\n"
        "    document.body.appendChild(box);\n"
        "    box.addEventListener('click',async function(e){\n"
        "      if(e.target===box||e.target.getAttribute('data-close')){"
        "box.remove();return;}\n"
        "      var btn=e.target.closest&&"
        "e.target.closest('[data-request-id]');\n"
        "      if(!btn)return;\n"
        "      var requestId=btn.getAttribute('data-request-id');\n"
        "      btn.disabled=true;\n"
        "      try{\n"
        "        await server('dismissPairNotice',[ADMIN_PIN_VALUE,requestId]);\n"
        "        await poll();\n"
        "        box.remove();\n"
        "      }catch(err){btn.disabled=false;alert((err&&err.message)||err);}\n"
        "    });\n"
        "  }\n"
        "  async function poll(){\n"
        "    try{\n"
        "      var state=await server('getPublicState',[ADMIN_PIN_VALUE]);\n"
        "      window.STATE=state;\n"
        "      render(state);\n"
        "    }catch(e){}\n"
        "  }\n"
        "  setInterval(poll,7000);\n"
        "  setTimeout(poll,2000);\n"
        "})();\n"
        "</script>\n"
    )

    close = text.lower().rfind('</body>')
    if close < 0:
        raise SystemExit('body close not found for pair-play script injection')
    text = text[:close] + member_addon + admin_addon + text[close:]

if MARKER not in text:
    raise SystemExit("pair-play patch did not apply")

path.write_text(text, encoding="utf-8")
print("MEMBER_PAIR_PLAY_OK")
