#!/usr/bin/env python3
"""Bridge the web's own incoming-짝요청 alert (#jmPairIncomingAlert, added by
deployment/jayuminton/patch_member_pair_play_v1.py's member_addon) to native
vibration, the exact same way the wait/court foreground alert and admin
direct messages already are (see patch_user_native_foreground_alert_
vibration_v1.py and patch_user_native_v1642_md_final.py's onPageFinished
injection). The web side's own navigator.vibrate() call is unreliable
inside this WebView, so this reuses the proven native
AlertVibrationController bridge instead: vibration starts the moment
#jmPairIncomingAlert's 'hidden' class is removed (a 짝요청 has arrived) and
stops the instant it's added back (the member accepted or rejected it via
the alert's own buttons -- see showIncomingPairAlert in
patch_member_pair_play_v1.py, which always re-adds 'hidden' on either
choice). Per the user's own words: "같이 게임요청 하면 그 사람에게 진동알람
팝업 가는거야? 그렇게 해야해."
"""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')

anchor = '''                view.evaluateJavascript(
                    "window.__JAYUMINTON_USER_APK__=true;" +'''
if anchor not in source:
    raise SystemExit('second evaluateJavascript anchor missing')

insertion = '''                view.evaluateJavascript(
                    "(function(){if(window.__JM_NATIVE_PAIR_REQUEST_ALERT_VIBRATION__)return;window.__JM_NATIVE_PAIR_REQUEST_ALERT_VIBRATION__=1;var active='';" +
                    "function s(){var b=document.getElementById('jmPairIncomingAlert');if(!b)return;var visible=!b.classList.contains('hidden');" +
                    "try{if(visible&&!active&&window.NativeUserApp&&typeof NativeUserApp.startAdminMessageVibration==='function'){active=String(Date.now());NativeUserApp.startAdminMessageVibration('pair_request_'+active);}" +
                    "else if(!visible&&active&&window.NativeUserApp&&typeof NativeUserApp.stopAdminMessageVibration==='function'){active='';NativeUserApp.stopAdminMessageVibration();}}catch(e){}}" +
                    "function w(){var b=document.getElementById('jmPairIncomingAlert');if(!b){setTimeout(w,300);return;}new MutationObserver(s).observe(b,{attributes:true,attributeFilter:['class']});s();}" +
                    "if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',w,{once:true});}else{w();}" +
                    "window.addEventListener('pagehide',function(){try{active='';NativeUserApp.stopAdminMessageVibration();}catch(e){}});})();",
                    null
                );
''' + anchor

source = source.replace(anchor, insertion, 1)

required = (
    '__JM_NATIVE_PAIR_REQUEST_ALERT_VIBRATION__',
    "getElementById('jmPairIncomingAlert')",
    "NativeUserApp.startAdminMessageVibration('pair_request_'+active)",
)
for marker in required:
    if marker not in source:
        raise SystemExit('pair-request-alert-vibration patch failed: ' + marker)

path.write_text(source, encoding='utf-8')
print('PAIR_REQUEST_ALERT_VIBRATION_V1_OK')
