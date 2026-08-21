#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_user_native_v134_separate_package.py <build-script>')

p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')

# Move generated Android sources out of the admin namespace entirely.
s = s.replace('JAVA_DIR="app/src/main/java/com/jayuminton/admin"',
              'JAVA_DIR="app/src/main/java/com/jayuminton/user"')
s = s.replace("namespace 'com.jayuminton.admin'", "namespace 'com.jayuminton.user'")
s = s.replace('package com.jayuminton.admin;', 'package com.jayuminton.user;')

# The repository itself contains the administrator Android sources. A user APK build
# must remove those checked-in sources before javac runs, otherwise Gradle compiles
# both the user package and the old administrator MainActivity.
anchor = 'mkdir -p "$JAVA_DIR" releases deployment/status signing'
replacement = 'rm -rf app/src/main/java/com/jayuminton/admin\nmkdir -p "$JAVA_DIR" releases deployment/status signing'
if anchor not in s:
    raise SystemExit('user build mkdir anchor missing')
s = s.replace(anchor, replacement, 1)

# v1.3.4 identity.
repls = (
    ('VERSION="1.3.3"', 'VERSION="1.3.4"'),
    ('VERSION_CODE="133"', 'VERSION_CODE="134"'),
    ('versionCode 133', 'versionCode 134'),
    ("versionName '1.3.3'", "versionName '1.3.4'"),
    ('USER_APP_VERSION = "1.3.3"', 'USER_APP_VERSION = "1.3.4"'),
    ('JayumintonUserNative/1.3.3', 'JayumintonUserNative/1.3.4'),
    ('JayumintonNativeAndroid/1.3.3', 'JayumintonNativeAndroid/1.3.4'),
    ('APP_VERSION = "1.3.3"', 'APP_VERSION = "1.3.4"'),
)
for old,new in repls:
    s = s.replace(old,new)

s = re.sub(r'^OUT=.*$', 'OUT="releases/jayuminton-user-v1.3.4-cloudflare-separated.apk"', s, count=1, flags=re.M)

required = (
    'JAVA_DIR="app/src/main/java/com/jayuminton/user"',
    "namespace 'com.jayuminton.user'",
    "applicationId 'com.jayuminton.user'",
    'package com.jayuminton.user;',
    'rm -rf app/src/main/java/com/jayuminton/admin',
    'https://jayuminton-push.web.app/',
    'NativeUserApp',
    'NativePushRegistrar.isCurrentMember(this, targetMemberId)',
    'private static final int MAX_GROUPS = 8;',
)
for marker in required:
    if marker not in s:
        raise SystemExit('missing v1.3.4 user-only marker: ' + marker)

for forbidden in (
    'JAVA_DIR="app/src/main/java/com/jayuminton/admin"',
    "namespace 'com.jayuminton.admin'",
    'package com.jayuminton.admin;',
):
    if forbidden in s:
        raise SystemExit('admin Android namespace survived: ' + forbidden)

p.write_text(s, encoding='utf-8')
print('Prepared v1.3.4 user-only Android namespace, removed checked-in admin Java sources, and preserved Cloudflare user push/vibration contract.')
