#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_user_native_v136_push_resync.py <build-script>')

p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')

# Bump the clean user shell to v1.3.6.
for old, new in (
    ('VERSION="1.3.5"', 'VERSION="1.3.6"'),
    ('VERSION_CODE="135"', 'VERSION_CODE="136"'),
    ('versionCode 135', 'versionCode 136'),
    ("versionName '1.3.5'", "versionName '1.3.6'"),
    ('USER_APP_VERSION = "1.3.5"', 'USER_APP_VERSION = "1.3.6"'),
    ('JayumintonUserNative/1.3.5', 'JayumintonUserNative/1.3.6'),
    ('JayumintonNativeAndroid/1.3.5', 'JayumintonNativeAndroid/1.3.6'),
    ("versionCode='135' versionName='1.3.5'", "versionCode='136' versionName='1.3.6'"),
    ('clean-v135', 'clean-v136'),
):
    s = s.replace(old, new)
s = re.sub(r'^OUT=.*$', 'OUT="releases/jayuminton-user-v1.3.6-push-resync.apk"', s, count=1, flags=re.M)

# Rebind the current member every time the app comes to foreground. This closes
# the gap where the WebView is correct but FCM token/member registration was lost
# or completed before member selection had been restored.
anchor = '''    @Override\n    public void onBackPressed() {'''
if anchor not in s:
    raise SystemExit('MainActivity onBackPressed anchor missing')
resume = '''    @Override\n    protected void onResume() {\n        super.onResume();\n        NativePushRegistrar.ensureToken(this);\n        NativePushRegistrar.registerCurrentNow(this);\n        if (webView != null) {\n            webView.evaluateJavascript(\n                "if(typeof syncNativeUserPushBridge==='function'){syncNativeUserPushBridge();}",\n                null\n            );\n        }\n    }\n\n'''
s = s.replace(anchor, resume + anchor, 1)

# Expose a safe foreground re-registration entrypoint without changing the
# existing internal registration semantics.
anchor2 = '''    private static void registerCurrent(Context context) {'''
if anchor2 not in s:
    raise SystemExit('registerCurrent anchor missing')
wrapper = '''    public static void registerCurrentNow(Context context) {\n        Context app = context.getApplicationContext();\n        if (!pushEnabled(app)) return;\n        SharedPreferences p = prefs(app);\n        String token = p.getString(KEY_TOKEN, "");\n        if (token.isEmpty()) {\n            ensureToken(app);\n            return;\n        }\n        registerCurrent(app);\n    }\n\n'''
s = s.replace(anchor2, wrapper + anchor2, 1)

# Retry relay registration/unregistration on transient network failures. Keep the
# same single-thread executor so member-switch ordering remains deterministic.
old = '''    private static void submitAsync(String action, String memberId, String memberName, String token) {\n        EXECUTOR.execute(() -> submit(action, memberId, memberName, token));\n    }'''
if old not in s:
    raise SystemExit('submitAsync anchor missing')
new = '''    private static void submitAsync(String action, String memberId, String memberName, String token) {\n        EXECUTOR.execute(() -> {\n            for (int attempt = 0; attempt < 4; attempt++) {\n                if (submitWithResult(action, memberId, memberName, token)) return;\n                try { Thread.sleep(700L * (attempt + 1)); }\n                catch (InterruptedException e) { Thread.currentThread().interrupt(); return; }\n            }\n        });\n    }'''
s = s.replace(old, new, 1)

# Convert the old fire-and-forget submit body to a boolean result while preserving
# its payload/HTTP contract. This makes retries meaningful instead of silently
# swallowing a failed token registration.
s = s.replace('    private static void submit(String action, String memberId, String memberName, String token) {',
              '    private static boolean submitWithResult(String action, String memberId, String memberName, String token) {', 1)
s = s.replace('''            if (code >= 200 && code < 400) {\n                try { if (connection.getInputStream() != null) connection.getInputStream().close(); } catch (Exception ignored) {}\n            } else {\n                try { if (connection.getErrorStream() != null) connection.getErrorStream().close(); } catch (Exception ignored) {}\n            }\n        } catch (Exception ignored) {\n        } finally {\n            if (connection != null) connection.disconnect();\n        }\n    }''', '''            if (code >= 200 && code < 300) {\n                try { if (connection.getInputStream() != null) connection.getInputStream().close(); } catch (Exception ignored) {}\n                return true;\n            }\n            try { if (connection.getErrorStream() != null) connection.getErrorStream().close(); } catch (Exception ignored) {}\n            return false;\n        } catch (Exception ignored) {\n            return false;\n        } finally {\n            if (connection != null) connection.disconnect();\n        }\n    }''', 1)

required = (
    "versionCode='136' versionName='1.3.6'",
    'clean-v136',
    'protected void onResume()',
    'NativePushRegistrar.registerCurrentNow(this);',
    'public static void registerCurrentNow(Context context)',
    'submitWithResult(action, memberId, memberName, token)',
    'attempt < 4',
    'syncNativeUserPushBridge',
)
for marker in required:
    if marker not in s:
        raise SystemExit('missing v1.3.6 push-resync marker: ' + marker)

p.write_text(s, encoding='utf-8')
print('Prepared v1.3.6: foreground member/token resync + bounded push relay retries.')
