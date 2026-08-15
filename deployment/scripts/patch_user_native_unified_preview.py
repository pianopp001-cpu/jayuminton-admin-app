#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding='utf-8')

# Apply only after the proven v1.3.0/cap8 patch chain.
# Keep FCM registration, background notification, vibration controller,
# member switching and native bridge intact. Only give the test build a
# distinct version/output and make its WebView open the SAME Firebase
# member preview URL used by non-installed web users.

replacements = (
    ('v1.3.0-cap8.apk', 'v1.3.2-unified-preview.apk'),
    ('user-native-push-v1.3.0.txt', 'user-native-push-v1.3.2-unified-preview.txt'),
    ('VERSION="1.3.0"', 'VERSION="1.3.2"'),
    ('VERSION_CODE="130"', 'VERSION_CODE="132"'),
    ('versionCode 130', 'versionCode 132'),
    ("versionName '1.3.0'", "versionName '1.3.2'"),
    ('USER_APP_VERSION = "1.3.0"', 'USER_APP_VERSION = "1.3.2"'),
    ('JayumintonUserNative/1.3.0', 'JayumintonUserNative/1.3.2'),
    ('JayumintonNativeAndroid/1.3.0', 'JayumintonNativeAndroid/1.3.2'),
    ('APP_VERSION = "1.3.0"', 'APP_VERSION = "1.3.2"'),
    ('version=1.3.0', 'version=1.3.2'),
    ('version_code=130', 'version_code=132'),
)
for old, new in replacements:
    if old not in s:
        raise SystemExit('unified preview version anchor missing: ' + old)
    s = s.replace(old, new)

lines = s.splitlines()
url_indexes = [i for i, line in enumerate(lines) if line.startswith('USER_URL=')]
if len(url_indexes) != 1:
    raise SystemExit('expected exactly one USER_URL assignment')
i = url_indexes[0]
lines[i:i+1] = [
    ': "${UNIFIED_MEMBER_URL:?UNIFIED_MEMBER_URL required}"',
    'USER_URL="${UNIFIED_MEMBER_URL%/}/?apkUser=1&unifiedMember=1&userAppVersion=${VERSION}"',
]
s = '\n'.join(lines) + '\n'

for required in (
    'VERSION="1.3.2"',
    'VERSION_CODE="132"',
    'versionCode 132',
    "versionName '1.3.2'",
    'USER_APP_VERSION = "1.3.2"',
    'JayumintonUserNative/1.3.2',
    'NativeUserApp',
    'NativePushRegistrar.ensureToken(this);',
    'setMember(String memberId, String memberName)',
    'setPushEnabled(boolean enabled)',
    'setVibrationEnabled(boolean enabled)',
    'private static final int MAX_GROUPS = 8;',
    'JAYUMINTON_V126_START_STOP_RACE_GUARD',
    'UNIFIED_MEMBER_URL required',
    'unifiedMember=1',
):
    if required not in s:
        raise SystemExit('unified preview required marker missing: ' + required)

for forbidden in (
    'VERSION="1.3.0"',
    'VERSION_CODE="130"',
    'script.google.com/macros/s/${MAIN_DEPLOYMENT_ID}/exec?mode=user',
):
    if forbidden in s:
        raise SystemExit('unified preview stale marker remained: ' + forbidden)

path.write_text(s, encoding='utf-8')
print('Prepared v1.3.2 unified-preview APK: native FCM/vibration preserved; WebView uses UNIFIED_MEMBER_URL.')
