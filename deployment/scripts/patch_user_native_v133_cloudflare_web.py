#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_user_native_v133_cloudflare_web.py <build-script>')
p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')

# v1.3.3: keep v1.3.2 strict native FCM/vibration but stop loading the old Apps Script UI.
# Use the established standalone member web entry; PUSH_URL remains supplied by the
# isolated Cloudflare worker deployment at build time.
USER_WEB = 'https://jayuminton-push.web.app/'

repls = (
    ('VERSION="1.3.2"', 'VERSION="1.3.3"'),
    ('VERSION_CODE="132"', 'VERSION_CODE="133"'),
    ('versionCode 132', 'versionCode 133'),
    ("versionName '1.3.2'", "versionName '1.3.3'"),
    ('USER_APP_VERSION = "1.3.2"', 'USER_APP_VERSION = "1.3.3"'),
    ('JayumintonUserNative/1.3.2', 'JayumintonUserNative/1.3.3'),
    ('JayumintonNativeAndroid/1.3.2', 'JayumintonNativeAndroid/1.3.3'),
    ('APP_VERSION = "1.3.2"', 'APP_VERSION = "1.3.3"'),
    ('v1.3.2-current-member-only.apk', 'v1.3.3-cloudflare-user-web.apk'),
    ('user-native-push-v1.3.2.txt', 'user-native-push-v1.3.3.txt'),
)
for old,new in repls:
    s=s.replace(old,new)

# Replace any generated Apps Script USER_URL assignment exactly once.
pat = r'USER_URL="https://script\.google\.com/macros/s/\$\{MAIN_DEPLOYMENT_ID\}/exec\?mode=user[^\"]*"'
s,n = re.subn(pat, f'USER_URL="{USER_WEB}"', s, count=1)
if n != 1:
    # Some patched build versions have the Java constant already materialized.
    pat2 = r'private static final String USER_URL = "https://script\.google\.com/macros/s/[^\"]+";'
    s,n2 = re.subn(pat2, f'private static final String USER_URL = "{USER_WEB}";', s, count=1)
    if n2 != 1:
        raise SystemExit('old Apps Script USER_URL anchor not found exactly once')

# The WebView must still expose the native member bridge so selecting "me" can bind
# memberId to the FCM token. The strict FCM service must remain intact.
required = (
    USER_WEB,
    'NativeUserApp',
    'setMember(String memberId, String memberName)',
    'NativePushRegistrar.ensureToken(this)',
    'NativePushRegistrar.isCurrentMember(this, targetMemberId)',
    'private static final int MAX_GROUPS = 8;',
    'VERSION="1.3.3"',
    'VERSION_CODE="133"',
)
for marker in required:
    if marker not in s:
        raise SystemExit('missing v1.3.3 marker: ' + marker)
if 'USER_URL="https://script.google.com/macros/s/' in s:
    raise SystemExit('Apps Script USER_URL survived v1.3.3')

p.write_text(s, encoding='utf-8')
print('Prepared v1.3.3: standalone user web entry + strict current-member Cloudflare push + max8 vibration.')
