#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_user_native_v135_clean_user_shell.py <build-script>')

p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')

# Bump identity.
for old, new in (
    ('VERSION="1.3.4"', 'VERSION="1.3.5"'),
    ('VERSION_CODE="134"', 'VERSION_CODE="135"'),
    ('versionCode 134', 'versionCode 135'),
    ("versionName '1.3.4'", "versionName '1.3.5'"),
    ('USER_APP_VERSION = "1.3.4"', 'USER_APP_VERSION = "1.3.5"'),
    ('JayumintonUserNative/1.3.4', 'JayumintonUserNative/1.3.5'),
    ('JayumintonNativeAndroid/1.3.4', 'JayumintonNativeAndroid/1.3.5'),
    ("versionCode='134' versionName='1.3.4'", "versionCode='135' versionName='1.3.5'"),
):
    s = s.replace(old, new)
s = re.sub(r'^OUT=.*$', 'OUT="releases/jayuminton-user-v1.3.5-clean-shell.apk"', s, count=1, flags=re.M)

# The old repository app layout/theme belonged to the admin app. Replace them
# completely before Gradle runs so the user APK has no inherited admin loading UI.
anchor = 'mkdir -p "$JAVA_DIR" releases deployment/status signing'
if anchor not in s:
    raise SystemExit('mkdir anchor not found')
replacement = anchor + r'''
mkdir -p app/src/main/res/layout app/src/main/res/values
cat > app/src/main/res/layout/activity_main.xml <<'XML'
<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="#FFFFFF">
    <WebView
        android:id="@+id/webView"
        android:layout_width="match_parent"
        android:layout_height="match_parent" />
</FrameLayout>
XML
cat > app/src/main/res/values/styles.xml <<'XML'
<resources>
    <style name="Theme.JayumintonAdmin" parent="android:style/Theme.Material.Light.NoActionBar">
        <item name="android:windowActionModeOverlay">true</item>
        <item name="android:windowNoTitle">true</item>
        <item name="android:fontFamily">sans</item>
        <item name="android:colorAccent">#222222</item>
        <item name="android:windowLightStatusBar">true</item>
        <item name="android:navigationBarColor">#FFFFFF</item>
        <item name="android:statusBarColor">#FFFFFF</item>
    </style>
</resources>
XML
'''
s = s.replace(anchor, replacement, 1)

# Force the first navigation to the verified Cloudflare user page. No fallback
# to admin/main deployment is allowed in the user shell.
s = re.sub(r'private static final String USER_URL = "[^"]+";',
           'private static final String USER_URL = "https://jayuminton-user-web.pianopp001.workers.dev/?app=user&mode=user&native=1";',
           s, count=1)

# Add a visible user-only marker immediately after page load. This is not a loading
# screen; it is only a DOM attribute used by runtime diagnostics.
s = s.replace("document.documentElement.setAttribute('data-user-apk','1');",
              "document.documentElement.setAttribute('data-user-apk','1');document.documentElement.setAttribute('data-user-shell','clean-v135');")

required = [
    'app/src/main/res/layout/activity_main.xml',
    '<WebView',
    'clean-v135',
    'https://jayuminton-user-web.pianopp001.workers.dev/?app=user&mode=user&native=1',
    "versionCode='135' versionName='1.3.5'",
]
for x in required:
    if x not in s:
        raise SystemExit('missing clean-shell marker: ' + x)

for bad in ('관리자 화면을 불러오는 중입니다', '관리자 화면을 여는 중', '?mode=admin'):
    if bad in s:
        raise SystemExit('admin loading marker survived: ' + bad)

p.write_text(s, encoding='utf-8')
print('Prepared v1.3.5 clean user shell: WebView-only layout, Cloudflare user URL only, native push preserved.')
