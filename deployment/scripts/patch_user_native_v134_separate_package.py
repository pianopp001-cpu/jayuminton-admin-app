#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_user_native_v134_separate_package.py <build-script>')

p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')

# The browser-verified Cloudflare user web. Never point the user APK back to
# Firebase hosting or an Apps Script page.
USER_WEB = 'https://jayuminton-user-web.pianopp001.workers.dev/'
s, n = re.subn(r'^USER_URL=.*$', f'USER_URL="{USER_WEB}"', s, count=1, flags=re.M)
if n != 1:
    raise SystemExit('USER_URL assignment not found exactly once')

# Move generated Android sources out of the admin namespace entirely.
s = s.replace('JAVA_DIR="app/src/main/java/com/jayuminton/admin"',
              'JAVA_DIR="app/src/main/java/com/jayuminton/user"')
s = s.replace("namespace 'com.jayuminton.admin'", "namespace 'com.jayuminton.user'")
s = s.replace('package com.jayuminton.admin;', 'package com.jayuminton.user;')

# The repository itself contains administrator Android sources. A user APK build
# must remove them before javac runs so the two apps cannot be mixed.
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
    ("versionCode='133' versionName='1.3.3'", "versionCode='134' versionName='1.3.4'"),
    ('version=1.3.3', 'version=1.3.4'),
    ('version_code=133', 'version_code=134'),
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
    USER_WEB,
    'NativeUserApp',
    'NativePushRegistrar.isCurrentMember(this, targetMemberId)',
    'private static final int MAX_GROUPS = 8;',
    "versionCode='134' versionName='1.3.4'",
)
for marker in required:
    if marker not in s:
        raise SystemExit('missing v1.3.4 user-only marker: ' + marker)

for forbidden in (
    'JAVA_DIR="app/src/main/java/com/jayuminton/admin"',
    "namespace 'com.jayuminton.admin'",
    'package com.jayuminton.admin;',
    'https://jayuminton-push.web.app/',
    'script.google.com/macros/s/',
    "versionCode='133' versionName='1.3.3'",
):
    if forbidden in s:
        raise SystemExit('stale/admin user-web marker survived: ' + forbidden)

p.write_text(s, encoding='utf-8')
print('Prepared v1.3.4 user-only APK against the verified Cloudflare user web, with admin sources removed and native push/vibration preserved.')
