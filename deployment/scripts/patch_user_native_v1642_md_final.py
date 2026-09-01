#!/usr/bin/env python3
from pathlib import Path
import sys
import re

# 2026-09-01 Play hotfix: force the user route and isolate the user APK layout
# from the admin-only loading overlay. This patches only the temporary user
# build script; the permanent admin Activity/layout stays untouched.
path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')

pairs = (
    ('v1.3.4-cloudflare-complete.apk', 'v1.6.42-md-final.apk'),
    ('user-native-push-v1.3.4.txt', 'user-native-push-v1.6.42.txt'),
    ('VERSION="1.3.4"', 'VERSION="1.6.42"'),
    ('VERSION_CODE="2000134"', 'VERSION_CODE="2001642"'),
    ('versionCode 2000134', 'versionCode 2001642'),
    ("versionName '1.3.4'", "versionName '1.6.42'"),
    ('version=1.3.4', 'version=1.6.42'),
    ('version_code=2000134', 'version_code=2001642'),
    ("versionCode='2000134'", "versionCode='2001642'"),
    ("versionName='1.3.4'", "versionName='1.6.42'"),
    ('USER_APP_VERSION = "1.3.4"', 'USER_APP_VERSION = "1.6.42"'),
    ('JayumintonUserNative/1.3.4', 'JayumintonUserNative/1.6.42'),
    ('JayumintonNativeAndroid/1.3.4', 'JayumintonNativeAndroid/1.6.42'),
    ('APP_VERSION = "1.3.4"', 'APP_VERSION = "1.6.42"'),
)
for old, new in pairs:
    source = source.replace(old, new)

ROUTE_MARKER = '20260901b-user-layout-isolation'
USER_ROUTE = f'https://jayuminton-push.web.app/?mode=user&apkUser=1&userAppVersion=1.6.42&memberRoute={ROUTE_MARKER}'
source = re.sub(
    r'USER_URL="https://jayuminton-push\.web\.app/[^"\n]*"',
    f'USER_URL="{USER_ROUTE}"',
    source,
    count=1,
)

old = '''            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String scheme = request.getUrl().getScheme();
                return !("http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme));
            }'''
new = '''            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String requested = request.getUrl().toString();
                if (requested.contains("mode=admin") || requested.contains("/admin")) {
                    view.stopLoading();
                    view.clearHistory();
                    view.loadUrl(USER_URL + "&routeGuard=1&ts=" + System.currentTimeMillis());
                    return true;
                }
                String scheme = request.getUrl().getScheme();
                return !("http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme));
            }'''
if old not in source:
    raise SystemExit('user route guard anchor missing')
source = source.replace(old, new, 1)

bridge_anchor = '''        @JavascriptInterface public void setVibrationEnabled(boolean enabled) {
            NativePushRegistrar.setVibrationEnabled(MainActivity.this, enabled);
        }
'''
bridge_replacement = '''        @JavascriptInterface public void setVibrationEnabled(boolean enabled) {
            NativePushRegistrar.setVibrationEnabled(MainActivity.this, enabled);
        }
        @JavascriptInterface public void startAdminMessageVibration(String messageId) {
            if (!NativePushRegistrar.vibrationEnabled(MainActivity.this)) return;
            AlertVibrationController.start(MainActivity.this,
                    "admin_message_" + (messageId == null ? System.currentTimeMillis() : messageId));
        }
        @JavascriptInterface public void stopAdminMessageVibration() {
            AlertVibrationController.stop(MainActivity.this);
        }
'''
if bridge_anchor not in source:
    raise SystemExit('native message vibration bridge anchor missing')
source = source.replace(bridge_anchor, bridge_replacement, 1)

page_start_anchor = '''            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
'''
observer_block = '''            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                view.evaluateJavascript(
                    "(function(){if(window.__JM_NATIVE_ADMIN_MSG_VIBRATION__)return;window.__JM_NATIVE_ADMIN_MSG_VIBRATION__=1;var active='';" +
                    "function s(){var b=document.getElementById('jmDirectMessageAlert');if(!b)return;var visible=!b.classList.contains('hidden');" +
                    "var mid=(b.dataset&&b.dataset.messageId)||'';var body=document.getElementById('jmDirectMessageBody');if(!mid)mid=(body&&body.textContent)||'';" +
                    "try{if(visible&&mid!==active&&window.NativeUserApp&&typeof NativeUserApp.startAdminMessageVibration==='function'){active=mid||String(Date.now());NativeUserApp.startAdminMessageVibration(active);}" +
                    "else if(!visible&&active&&window.NativeUserApp&&typeof NativeUserApp.stopAdminMessageVibration==='function'){active='';NativeUserApp.stopAdminMessageVibration();}}catch(e){}}" +
                    "function w(){var b=document.getElementById('jmDirectMessageAlert');if(!b){setTimeout(w,300);return;}new MutationObserver(s).observe(b,{attributes:true,attributeFilter:['class','data-message-id']});s();}" +
                    "if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',w,{once:true});}else{w();}" +
                    "window.addEventListener('pagehide',function(){try{active='';NativeUserApp.stopAdminMessageVibration();}catch(e){}});})();",
                    null
                );
'''
if page_start_anchor not in source:
    raise SystemExit('native admin-message onPageFinished start anchor missing')
source = source.replace(page_start_anchor, observer_block, 1)

layout_anchor = 'mkdir -p "$JAVA_DIR" releases deployment/status signing\n'
layout_block = '''mkdir -p "$JAVA_DIR" releases deployment/status signing

# USER_ONLY_LAYOUT_V2001648: user APK must never inherit the admin loading overlay.
mkdir -p app/src/main/res/layout
cat > app/src/main/res/layout/activity_main.xml <<'XML'
<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:fitsSystemWindows="true">

    <WebView
        android:id="@+id/webView"
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:overScrollMode="never" />
</FrameLayout>
XML

grep -F '@+id/webView' app/src/main/res/layout/activity_main.xml >/dev/null
if grep -F 'adminLoadPanel' app/src/main/res/layout/activity_main.xml >/dev/null || grep -F '관리자 화면을 불러오는 중입니다.' app/src/main/res/layout/activity_main.xml >/dev/null; then
    echo 'USER_LAYOUT_ADMIN_OVERLAY_DETECTED' >&2
    exit 1
fi
'''
if layout_anchor not in source:
    raise SystemExit('user layout isolation anchor missing')
source = source.replace(layout_anchor, layout_block, 1)

required = (
    'VERSION="1.6.42"',
    'VERSION_CODE="2001642"',
    'private static final int MAX_GROUPS = 8;',
    'NativePushRegistrar.isCurrentMember(this, targetMemberId)',
    'AlertVibrationController.stop(',
    'stopPreviousMemberAlert(app);',
    f'USER_URL="{USER_ROUTE}"',
    'com.jayuminton.user',
    'requested.contains("mode=admin")',
    'routeGuard=1',
    'USER_ONLY_LAYOUT_V2001648',
    'android:id="@+id/webView"',
    'USER_LAYOUT_ADMIN_OVERLAY_DETECTED',
    'startAdminMessageVibration',
    'stopAdminMessageVibration',
    '__JM_NATIVE_ADMIN_MSG_VIBRATION__',
    "!b.classList.contains('hidden')",
    'jmDirectMessageAlert',
)
for marker in required:
    if marker not in source:
        raise SystemExit('v1642 MD final contract missing: ' + marker)
if 'script.google.com' in source or 'MAIN_DEPLOYMENT_ID' in source:
    raise SystemExit('v1642 must remain Cloudflare/Firebase-only')
if re.search(r'USER_URL="[^"\n]*[?&]mode=admin(?:[&#"\n]|$)', source):
    raise SystemExit('v1642 user APK must never contain admin mode routing')
if 'mode=user' not in source or ROUTE_MARKER not in source:
    raise SystemExit('v1642 fresh member route guard missing')

path.write_text(source, encoding='utf-8')
print('Prepared v1.6.42 MD-final user APK with native admin-message vibration, isolated user layout and fresh member route.')
