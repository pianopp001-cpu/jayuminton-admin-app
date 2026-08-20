#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding='utf-8')

repls = (
    ('v1.3.2-current-member-only.apk', 'v1.3.3-install-safe.apk'),
    ('user-native-push-v1.3.2.txt', 'user-native-push-v1.3.3.txt'),
    ('VERSION="1.3.2"', 'VERSION="1.3.3"'),
    ('VERSION_CODE="132"', 'VERSION_CODE="2000133"'),
    ('versionCode 132', 'versionCode 2000133'),
    ("versionCode='132'", "versionCode='2000133'"),
    ("versionName '1.3.2'", "versionName '1.3.3'"),
    ("versionName='1.3.2'", "versionName='1.3.3'"),
    ('USER_APP_VERSION = "1.3.2"', 'USER_APP_VERSION = "1.3.3"'),
    ('JayumintonUserNative/1.3.2', 'JayumintonUserNative/1.3.3'),
    ('JayumintonNativeAndroid/1.3.2', 'JayumintonNativeAndroid/1.3.3'),
    ('APP_VERSION = "1.3.2"', 'APP_VERSION = "1.3.3"'),
    ('version=1.3.2', 'version=1.3.3'),
    ('version_code=132', 'version_code=2000133'),
)
for old, new in repls:
    if old not in s:
        raise SystemExit('v133 install-safe anchor missing: ' + old)
    s = s.replace(old, new)

for required in (
    'VERSION="1.3.3"',
    'VERSION_CODE="2000133"',
    'versionCode 2000133',
    "versionName '1.3.3'",
    'boolean selectedMemberMatches = hasTargetMemberId &&',
    'assignmentType && (!hasTargetMemberId || !selectedMemberMatches)',
    'private static final int MAX_GROUPS = 8;',
):
    if required not in s:
        raise SystemExit('v133 required marker missing: ' + required)

s = s.replace(
    'assignment_types=wait1_ready,court_assignment',
    'assignment_types=wait1_ready,court_assignment\ninstall_compat=high-version-code-same-package-same-release-signer',
)

path.write_text(s, encoding='utf-8')
print('Prepared v1.3.3 install-safe build with versionCode 2000133 and preserved current-member alert contract.')
