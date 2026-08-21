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

# Robustly replace the shell-level USER_URL regardless of extra query parameters
# added by earlier patches. This is safer than depending on one exact historical URL.
s, n = re.subn(
    r'(?m)^USER_URL="https://script\.google\.com/macros/s/[^\"]+"\s*$',
    f'USER_URL="{USER_WEB}"',
    s,
    count=1,
)
if n != 1:
    # Fallback for variants where only the generated Java constant remains.
    s, n2 = re.subn(
        r'private static final String USER_URL = "https://script\.google\.com/macros/s/[^\"]+";',
        f'private static final String USER_URL = "{USER_WEB}";',
        s,
        count=1,
    )
    if n2 != 1:
        raise SystemExit('Apps Script USER_URL anchor not found')

# Cloudflare/Firebase standalone URL has no query string. Base builder appends &ts=,
# so make that generated WebView load expression separator-safe.
s = s.replace(
    'webView.loadUrl(USER_URL + "&ts=" + System.currentTimeMillis(), headers);',
    'webView.loadUrl(USER_URL + (USER_URL.contains("?") ? "&ts=" : "?ts=") + System.currentTimeMillis(), headers);'
)

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
if re.search(r'(?m)^USER_URL="https://script\.google\.com/macros/s/', s):
    raise SystemExit('Apps Script USER_URL survived v1.3.3')

p.write_text(s, encoding='utf-8')
print('Prepared v1.3.3: Cloudflare user web + strict selected-member push + max8 vibration.')
