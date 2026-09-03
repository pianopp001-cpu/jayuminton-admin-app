#!/usr/bin/env python3
"""Admin-only 짝요청 알림 위젯 -- for the *native admin app's* bundled page.

The native admin app (see build-current-admin.yml) builds its WebView
content from its own separate, frozen HTML lineage: it starts from
assets/admin/index.html extracted out of an old already-built APK
(jayuminton-admin-v200.8-webview-js-fixed.apk) and has since only been
moved forward by admin-only feature patches run in that same workflow.
It is NOT the same $PUBLIC/index.html that
deploy-unified-member-web-production.yml maintains for the live member
site, and it is not guaranteed to contain window.handleAnywhereMemberTap
(the member-side tap-to-swap handler that patch_member_pair_play_v1.py's
member_addon wraps) -- that function only matters for members deciding
between "자리 바꾸기 요청" and "같이 게임하기" on their own phones, which is
not something the admin app's screen does at all.

So rather than reuse patch_member_pair_play_v1.py's script (which would
raise if window.handleAnywhereMemberTap were ever missing here, and would
carry along member-only logic the admin app has no use for), this script
carries only the admin-facing half: a small floating badge that shows how
many 짝요청 are waiting for a seat (pairRequests with
status === 'accepted_awaiting_seat', written by the Cloudflare worker's
JAYUMINTON_MEMBER_PAIR_PLAY_V1 mutations -- see cloudflare/state-worker/
worker.js), a tap-to-open list of who is waiting to be seated together,
and a "완료" button per request that calls the same dismissPairNotice RPC
the browser-based admin view uses.
"""

from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_admin_pair_notice_v1.py INDEX_HTML")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

MARKER = "JAYUMINTON_ADMIN_PAIR_NOTICE_V1"

if MARKER not in text:
    addon = (
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
        raise SystemExit('body close not found for admin pair-notice injection')
    text = text[:close] + addon + text[close:]

if MARKER not in text:
    raise SystemExit("admin pair-notice patch did not apply")

path.write_text(text, encoding="utf-8")
print("ADMIN_PAIR_NOTICE_OK")
