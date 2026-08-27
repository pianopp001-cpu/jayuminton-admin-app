#!/usr/bin/env python3
from pathlib import Path
import sys

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

# The final user APK must always enter the Firebase member page explicitly.
# A cache-busting memberRoute marker prevents a stale WebView/admin document from
# being restored after an APK update while keeping the user's saved auth storage.
USER_ROUTE = 'https://jayuminton-push.web.app/?mode=user&apkUser=1&userAppVersion=1.6.42&memberRoute=20260827b'
source = source.replace(
    'USER_URL="https://jayuminton-push.web.app/"',
    f'USER_URL="{USER_ROUTE}"',
)
source = source.replace(
    'USER_URL="https://jayuminton-push.web.app/;',
    f'USER_URL="{USER_ROUTE}";',
)

# Normalize every older Firebase user URL, including already-parameterized ones.
import re
source = re.sub(
    r'USER_URL="https://jayuminton-push\.web\.app/[^"\n]*"',
    f'USER_URL="{USER_ROUTE}"',
    source,
    count=1,
)

required = (
    'VERSION="1.6.42"',
    'VERSION_CODE="2001642"',
    'private static final int MAX_GROUPS = 8;',
    'NativePushRegistrar.isCurrentMember(this, targetMemberId)',
    'AlertVibrationController.stop(',
    'stopPreviousMemberAlert(app);',
    f'USER_URL="{USER_ROUTE}"',
    'com.jayuminton.user',
)
for marker in required:
    if marker not in source:
        raise SystemExit('v1642 MD final contract missing: ' + marker)
if 'script.google.com' in source or 'MAIN_DEPLOYMENT_ID' in source:
    raise SystemExit('v1642 must remain Cloudflare/Firebase-only')
if 'mode=admin' in source:
    raise SystemExit('v1642 user APK must never contain admin mode routing')
if 'mode=user' not in source or 'memberRoute=20260827b' not in source:
    raise SystemExit('v1642 fresh member route guard missing')

path.write_text(source, encoding='utf-8')
print('Prepared v1.6.42 MD-final native user APK with fresh Firebase member route guard.')
