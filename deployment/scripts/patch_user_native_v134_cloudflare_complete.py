#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')

replacements = (
    ('v1.3.3-install-safe.apk', 'v1.3.4-cloudflare-complete.apk'),
    ('user-native-push-v1.3.3.txt', 'user-native-push-v1.3.4.txt'),
    ('VERSION="1.3.3"', 'VERSION="1.3.4"'),
    ('VERSION_CODE="2000133"', 'VERSION_CODE="2000134"'),
    ('versionCode 2000133', 'versionCode 2000134'),
    ("versionName '1.3.3'", "versionName '1.3.4'"),
    ('version=1.3.3', 'version=1.3.4'),
    ('version_code=2000133', 'version_code=2000134'),
)
for old, new in replacements:
    if old not in source:
        raise SystemExit('v134 version anchor missing: ' + old)
    source = source.replace(old, new)

for old, new in (
    ("versionCode='2000133'", "versionCode='2000134'"),
    ("versionName='1.3.3'", "versionName='1.3.4'"),
    ('USER_APP_VERSION = "1.3.3"', 'USER_APP_VERSION = "1.3.4"'),
    ('JayumintonUserNative/1.3.3', 'JayumintonUserNative/1.3.4'),
    ('JayumintonNativeAndroid/1.3.3', 'JayumintonNativeAndroid/1.3.4'),
    ('APP_VERSION = "1.3.3"', 'APP_VERSION = "1.3.4"'),
):
    source = source.replace(old, new)

status_anchor = 'install_compat=high-version-code-same-package-same-release-signer'
if status_anchor in source and 'push_backend=cloudflare-durable-object' not in source:
    source = source.replace(
        status_anchor,
        status_anchor + '\npush_backend=cloudflare-durable-object\nalert_pattern=3-pulses-x8-groups-until-confirmed',
    )

required = (
    'VERSION="1.3.4"',
    'VERSION_CODE="2000134"',
    'private static final int MAX_GROUPS = 8;',
    'NativePushRegistrar.isCurrentMember(this, targetMemberId)',
    'AssignmentOverlay',
    'AlertVibrationController.stop(',
    'stopPreviousMemberAlert(app);',
)
for marker in required:
    if marker not in source:
        raise SystemExit('v134 alert contract missing: ' + marker)

path.write_text(source, encoding='utf-8')
print('Prepared v1.3.4 Cloudflare native user APK with current-member-only 3x8 vibration and confirm stop.')
