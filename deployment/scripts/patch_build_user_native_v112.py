#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding='utf-8')

for old, new in (
    ('v1.1.1-fresh-install.apk', 'v1.1.2-fresh-install.apk'),
    ('user-native-push-v1.1.1.txt', 'user-native-push-v1.1.2.txt'),
    ('VERSION="1.1.1"', 'VERSION="1.1.2"'),
    ('VERSION_CODE="111"', 'VERSION_CODE="112"'),
    ('versionCode 111', 'versionCode 112'),
    ("versionCode='111'", "versionCode='112'"),
    ("versionName '1.1.1'", "versionName '1.1.2'"),
    ("versionName='1.1.1'", "versionName='1.1.2'"),
    ('USER_APP_VERSION = "1.1.1"', 'USER_APP_VERSION = "1.1.2"'),
    ('JayumintonUserNative/1.1.1', 'JayumintonUserNative/1.1.2'),
    ("__JAYUMINTON_USER_APK_VERSION__='1.1.1'", "__JAYUMINTON_USER_APK_VERSION__='1.1.2'"),
    ('jayuminton_native_push_v111', 'jayuminton_native_push_v112'),
    ('JayumintonNativeAndroid/1.1.1', 'JayumintonNativeAndroid/1.1.2'),
    ('jayuminton_wait1_native_v111', 'jayuminton_wait1_native_v112'),
    ('jayuminton_court_native_v111', 'jayuminton_court_native_v112'),
    ('version=1.1.1', 'version=1.1.2'),
    ('version_code=111', 'version_code=112'),
):
    s = s.replace(old, new)

# The top Hosting page owns the JavaScript interface. Listen directly for every
# member-frame message so native registration does not depend on Hosting glue code.
old = '''                    "if(typeof syncNativeUserPushBridge==='function'){syncNativeUserPushBridge();}",
                    null
                );'''
new = '''                    "if(!window.__JAYUMINTON_NATIVE_DIRECT_V112__){" +
                    "window.__JAYUMINTON_NATIVE_DIRECT_V112__=true;" +
                    "window.addEventListener('message',function(e){try{" +
                    "var d=e&&e.data||{};var m=d.member||null;" +
                    "if((d.type==='JAYUMINTON_MEMBER_SELECTED'||d.type==='JAYUMINTON_MEMBER_BRIDGE_READY'||d.type==='JAYUMINTON_PUSH_SETUP_REQUEST')&&m&&m.id){" +
                    "window.NativeUserApp.setPushEnabled(true);window.NativeUserApp.setVibrationEnabled(true);" +
                    "window.NativeUserApp.setMember(String(m.id),String(m.name||''));}" +
                    "if(d.type==='JAYUMINTON_MEMBER_ALERT_PREFERENCE'){window.NativeUserApp.setPushEnabled(!!d.enabled);}" +
                    "if(d.type==='JAYUMINTON_MEMBER_VIBRATION_PREFERENCE'){window.NativeUserApp.setVibrationEnabled(!!d.enabled);}" +
                    "}catch(x){}});}" +
                    "if(typeof syncNativeUserPushBridge==='function'){syncNativeUserPushBridge();}",
                    null
                );'''
if '__JAYUMINTON_NATIVE_DIRECT_V112__' not in s:
    if old not in s:
        raise SystemExit('direct native listener insertion point missing')
    s = s.replace(old, new, 1)

# Explicit selection always enables the two native preferences before registering.
old = '''        @JavascriptInterface public void setMember(String memberId, String memberName) {
            NativePushRegistrar.setMember(MainActivity.this, memberId, memberName);
        }'''
new = '''        @JavascriptInterface public void setMember(String memberId, String memberName) {
            NativePushRegistrar.setPushEnabled(MainActivity.this, true);
            NativePushRegistrar.setVibrationEnabled(MainActivity.this, true);
            NativePushRegistrar.setMember(MainActivity.this, memberId, memberName);
        }'''
if 'setPushEnabled(MainActivity.this, true);' not in s:
    if old not in s:
        raise SystemExit('native setMember insertion point missing')
    s = s.replace(old, new, 1)

# Re-register whenever the app returns to the foreground and immediately after the
# Android notification permission dialog is accepted.
anchor = '''    @Override
    public void onBackPressed() {'''
methods = '''    @Override
    protected void onResume() {
        super.onResume();
        NativePushRegistrar.ensureToken(this);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == 1101 && grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            NativePushRegistrar.ensureToken(this);
        }
    }

'''
if 'protected void onResume()' not in s:
    if anchor not in s:
        raise SystemExit('activity resume insertion point missing')
    s = s.replace(anchor, methods + anchor, 1)

# A changed member or refreshed token is registered more than once to survive a
# transient Apps Script/network failure. Calls are idempotent for the same token.
old = '''    private static void registerCurrent(Context context) {
        SharedPreferences p = prefs(context);
        String id = p.getString(KEY_MEMBER_ID, "");
        String name = p.getString(KEY_MEMBER_NAME, "");
        String token = p.getString(KEY_TOKEN, "");
        if (id.isEmpty() || token.isEmpty()) return;
        submitAsync("register_web_token", id, name, token);
    }'''
new = '''    private static void registerCurrent(Context context) {
        SharedPreferences p = prefs(context);
        String id = p.getString(KEY_MEMBER_ID, "");
        String name = p.getString(KEY_MEMBER_NAME, "");
        String token = p.getString(KEY_TOKEN, "");
        if (id.isEmpty() || token.isEmpty()) return;
        submitAsync("register_web_token", id, name, token);
        EXECUTOR.execute(() -> {
            try { Thread.sleep(2500L); } catch (InterruptedException ignored) { Thread.currentThread().interrupt(); }
            submit("register_web_token", id, name, token);
            try { Thread.sleep(7500L); } catch (InterruptedException ignored) { Thread.currentThread().interrupt(); }
            submit("register_web_token", id, name, token);
        });
    }'''
if 'Thread.sleep(2500L)' not in s:
    if old not in s:
        raise SystemExit('native registration retry insertion point missing')
    s = s.replace(old, new, 1)

required = (
    'v1.1.2-fresh-install.apk', 'VERSION="1.1.2"', 'VERSION_CODE="112"',
    '__JAYUMINTON_NATIVE_DIRECT_V112__', 'protected void onResume()',
    'Thread.sleep(2500L)', 'jayuminton_wait1_native_v112',
    'jayuminton_court_native_v112',
)
for marker in required:
    if marker not in s:
        raise SystemExit('missing native v1.1.2 marker: ' + marker)

path.write_text(s, encoding='utf-8')
print('Prepared native v1.1.2 with direct member bridge and registration retries.')
