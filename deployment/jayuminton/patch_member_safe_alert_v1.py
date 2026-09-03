#!/usr/bin/env python3
"""Never show a member a raw browser alert() again.

Bug report: "사용자 웹앱에서 더블탭 하면 http://jayuminton-push.web.app 페이지
내용: cannot read properties of undefined (reading '1') 팝업 뜨고 코트배정대기로
이동한다... 제발 주소나오는 팝업이나 에러문구 없애줘."

A native alert() always shows the page's own URL in its title bar -- there is
no way to suppress that chrome once a native dialog is used, on a page opened
in a normal browser tab (unlike the Android app's WebView, which can override
onJsAlert). The only fix that actually removes "주소 나오는 팝업" for good,
regardless of which code path throws, is to stop using native alert()
entirely for members and replace it with an in-page toast -- and to swap any
raw technical-looking message (a JS TypeError, an unsupported-RPC name, etc.)
for a friendly Korean sentence instead of leaking it verbatim.

This mirrors the admin app's own existing installSafeAlert() precedent
(deployment/jayuminton/admin_multiaction_v2054_hotfix.js), except it keeps
showing a message (as a toast) instead of silently swallowing it, since a
member tapping their own card should always see SOME feedback.
"""

from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_member_safe_alert_v1.py INDEX_HTML")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

MARKER = "JAYUMINTON_MEMBER_SAFE_ALERT_V1"

if MARKER not in text:
    anchor = '<script id="jayuminton-team-visuals-v8-script">'
    count = text.count(anchor)
    if count != 1:
        raise SystemExit(
            "team-visuals-v8 anchor not found exactly once (found %d) -- "
            "live source has drifted, aborting to avoid corrupting the page" % count
        )

    addon = (
        '<script id="jayuminton-member-safe-alert-v1">\n'
        "/* " + MARKER + ": a member-facing alert() must never show a raw "
        "technical error or the page's own URL (which the browser's native "
        "dialog always prepends) -- replace it with a small in-page toast, "
        "and swap genuinely technical-looking text for a friendly Korean "
        "message instead of leaking it verbatim. */\n"
        "(function(){\n"
        "  if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;\n"
        "  if(window.__JM_MEMBER_SAFE_ALERT_V1__)return;\n"
        "  window.__JM_MEMBER_SAFE_ALERT_V1__=true;\n"
        "  var TECH=/cannot read propert|undefined|null is not an object|"
        "is not a function|unsupported_legacy_rpc|typeerror|referenceerror|"
        "syntaxerror|networkerror|failed to fetch/i;\n"
        "  function toast(text){\n"
        "    var old=document.getElementById('jm-member-safe-alert');\n"
        "    if(old)old.remove();\n"
        "    var box=document.createElement('div');\n"
        "    box.id='jm-member-safe-alert';\n"
        "    box.textContent=text;\n"
        "    box.style.cssText='position:fixed;left:50%;bottom:24px;"
        "transform:translateX(-50%);z-index:2147483647;max-width:88vw;"
        "padding:11px 16px;border-radius:12px;background:rgba(20,20,20,.92);"
        "color:#fff;font-size:14px;line-height:1.35;text-align:center;"
        "box-shadow:0 3px 14px rgba(0,0,0,.25);pointer-events:none';\n"
        "    (document.body||document.documentElement).appendChild(box);\n"
        "    setTimeout(function(){"
        "if(box&&box.parentNode)box.parentNode.removeChild(box);"
        "},2400);\n"
        "  }\n"
        "  window.alert=function(message){\n"
        "    var text=String(message==null?'':message).trim();\n"
        "    if(!text)return;\n"
        "    if(TECH.test(text))text='처리 중 문제가 발생했어요. 잠시 후 다시 "
        "시도해 주세요.';\n"
        "    toast(text);\n"
        "  };\n"
        "})();\n"
        "</script>\n"
        + anchor
    )

    text = text.replace(anchor, addon, 1)

if MARKER not in text:
    raise SystemExit("member safe-alert patch did not apply")

path.write_text(text, encoding="utf-8")
print("MEMBER_SAFE_ALERT_OK")
