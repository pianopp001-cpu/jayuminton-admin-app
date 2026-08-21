#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_user_native_v133_cloudflare_web.py <build-script>')
p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')

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

# The generated build script always has exactly one shell USER_URL assignment.
# Replace that assignment by variable name instead of depending on its exact URL text,
# because earlier native patches can alter the query string before this patch runs.
s,n = re.subn(r'^USER_URL=.*$', f'USER_URL="{USER_WEB}"', s, count=1, flags=re.M)
if n != 1:
    raise SystemExit('USER_URL assignment not found exactly once')

# Cloudflare/Firebase web root has no existing query string, so timestamp must start with ?.
s = s.replace('webView.loadUrl(USER_URL + "&ts=" + System.currentTimeMillis(), headers);',
              'webView.loadUrl(USER_URL + (USER_URL.contains("?") ? "&ts=" : "?ts=") + System.currentTimeMillis(), headers);')

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
if 'script.google.com/macros/s/' in re.search(r'^USER_URL=.*$', s, flags=re.M).group(0):
    raise SystemExit('Apps Script USER_URL survived v1.3.3')

p.write_text(s, encoding='utf-8')
print('Prepared v1.3.3: Cloudflare/Firebase user web + strict current-member push + max8 vibration.')
