#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_user_native_v136_push_resync.py <build-script>')

p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')

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

# Existing patch chain already provides onResume in some builds. Reuse it instead
# of creating a duplicate Java lifecycle method.
if 'NativePushRegistrar.registerCurrentNow(this);' not in s:
    m = re.search(r'protected\s+void\s+onResume\s*\(\s*\)\s*\{', s)
    if m:
        brace = s.find('{', m.start())
        insert = '\n        NativePushRegistrar.ensureToken(this);\n        NativePushRegistrar.registerCurrentNow(this);\n        if (webView != null) {\n            webView.evaluateJavascript("if(typeof syncNativeUserPushBridge===\\\'function\\\'){syncNativeUserPushBridge();}", null);\n        }'
        s = s[:brace+1] + insert + s[brace+1:]
    else:
        anchor = '    @Override\n    public void onBackPressed() {'
        if anchor not in s:
            raise SystemExit('MainActivity lifecycle anchor missing')
        resume = '''    @Override\n    protected void onResume() {\n        super.onResume();\n        NativePushRegistrar.ensureToken(this);\n        NativePushRegistrar.registerCurrentNow(this);\n        if (webView != null) {\n            webView.evaluateJavascript("if(typeof syncNativeUserPushBridge==='function'){syncNativeUserPushBridge();}", null);\n        }\n    }\n\n'''
        s = s.replace(anchor, resume + anchor, 1)

anchor2 = '    private static void registerCurrent(Context context) {'
if 'public static void registerCurrentNow(Context context)' not in s:
    if anchor2 not in s:
        raise SystemExit('registerCurrent anchor missing')
    wrapper = '''    public static void registerCurrentNow(Context context) {\n        Context app = context.getApplicationContext();\n        if (!pushEnabled(app)) return;\n        SharedPreferences p = prefs(app);\n        String token = p.getString(KEY_TOKEN, "");\n        if (token.isEmpty()) {\n            ensureToken(app);\n            return;\n        }\n        registerCurrent(app);\n    }\n\n'''
    s = s.replace(anchor2, wrapper + anchor2, 1)

# Keep the proven relay submit implementation from the existing patch chain.
# Foreground re-registration is sufficient to recover a lost/stale member-token
# binding without introducing duplicate submit implementations.
required = (
    "versionCode='136' versionName='1.3.6'",
    'clean-v136',
    'protected void onResume()',
    'NativePushRegistrar.registerCurrentNow(this);',
    'public static void registerCurrentNow(Context context)',
    'syncNativeUserPushBridge',
)
for marker in required:
    if marker not in s:
        raise SystemExit('missing v1.3.6 push-resync marker: ' + marker)

p.write_text(s, encoding='utf-8')
print('Prepared v1.3.6: foreground current-member/token resync using existing relay submit path.')
