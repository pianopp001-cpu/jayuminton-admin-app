#!/usr/bin/env python3
"""Bridge the web's own in-page wait1/court alert (#memberForegroundAlert)
to native vibration, the same way admin direct messages already are (see
patch_user_native_v1642_md_final.py's onPageFinished injection). The web
side's own navigator.vibrate() call is unreliable inside this WebView, so
this reuses the proven native AlertVibrationController bridge instead:
vibration starts when #memberForegroundAlert's 'hidden' class is removed
and stops the moment it's added back (the user closes it), matching the
explicit "예쁜 창 닫으면 진동도 꺼지게" decision. Paired with
patch_user_native_foreground_suppress_v1.py, which stops the native
full-screen alert from ALSO firing for the same event while the app is
foregrounded.
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
                    "(function(){if(window.__JM_NATIVE_WAIT_COURT_ALERT_VIBRATION__)return;window.__JM_NATIVE_WAIT_COURT_ALERT_VIBRATION__=1;var active='';" +
                    "function s(){var b=document.getElementById('memberForegroundAlert');if(!b)return;var visible=!b.classList.contains('hidden');" +
                    "var t=document.getElementById('memberForegroundAlertTitle');var mid=(t&&t.textContent)||'';" +
                    "try{if(visible&&mid!==active&&window.NativeUserApp&&typeof NativeUserApp.startAdminMessageVibration==='function'){active=mid||String(Date.now());NativeUserApp.startAdminMessageVibration('wait_court_'+active);}" +
                    "else if(!visible&&active&&window.NativeUserApp&&typeof NativeUserApp.stopAdminMessageVibration==='function'){active='';NativeUserApp.stopAdminMessageVibration();}}catch(e){}}" +
                    "function w(){var b=document.getElementById('memberForegroundAlert');if(!b){setTimeout(w,300);return;}new MutationObserver(s).observe(b,{attributes:true,attributeFilter:['class']});s();}" +
                    "if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',w,{once:true});}else{w();}" +
                    "window.addEventListener('pagehide',function(){try{active='';NativeUserApp.stopAdminMessageVibration();}catch(e){}});})();",
                    null
                );
''' + anchor

source = source.replace(anchor, insertion, 1)

required = (
    '__JM_NATIVE_WAIT_COURT_ALERT_VIBRATION__',
    "getElementById('memberForegroundAlert')",
    "getElementById('memberForegroundAlertTitle')",
    "NativeUserApp.startAdminMessageVibration('wait_court_'+active)",
)
for marker in required:
    if marker not in source:
        raise SystemExit('foreground-alert-vibration patch failed: ' + marker)

path.write_text(source, encoding='utf-8')
print('FOREGROUND_ALERT_VIBRATION_V1_OK')
