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

required = (
    'VERSION="1.6.42"',
    'VERSION_CODE="2001642"',
    'private static final int MAX_GROUPS = 8;',
    'NativePushRegistrar.isCurrentMember(this, targetMemberId)',
    'AlertVibrationController.stop(',
    'stopPreviousMemberAlert(app);',
    'USER_URL="https://jayuminton-push.web.app/',
    'com.jayuminton.user',
)
for marker in required:
    if marker not in source:
        raise SystemExit('v1642 MD final contract missing: ' + marker)
if 'script.google.com' in source or 'MAIN_DEPLOYMENT_ID' in source:
    raise SystemExit('v1642 must remain Cloudflare/Firebase-only')

path.write_text(source, encoding='utf-8')
print('Prepared v1.6.42 MD-final native user APK contract.')
