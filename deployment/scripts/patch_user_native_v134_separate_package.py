#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_user_native_v134_separate_package.py <build-script>')

p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')

USER_WEB = 'https://jayuminton-user-web.pianopp001.workers.dev/'
s, n = re.subn(r'^USER_URL=.*$', f'USER_URL="{USER_WEB}"', s, count=1, flags=re.M)
if n != 1:
    raise SystemExit('USER_URL assignment not found exactly once')

s = s.replace('JAVA_DIR="app/src/main/java/com/jayuminton/admin"',
              'JAVA_DIR="app/src/main/java/com/jayuminton/user"')
s = s.replace("namespace 'com.jayuminton.admin'", "namespace 'com.jayuminton.user'")
s = s.replace('package com.jayuminton.admin;', 'package com.jayuminton.user;')

anchor = 'mkdir -p "$JAVA_DIR" releases deployment/status signing'
replacement = 'rm -rf app/src/main/java/com/jayuminton/admin\nmkdir -p "$JAVA_DIR" releases deployment/status signing'
if anchor not in s:
    raise SystemExit('user build mkdir anchor missing')
s = s.replace(anchor, replacement, 1)

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

# Replace every stale Firebase-hosting user URL that older verifiers may contain.
s = s.replace('https://jayuminton-push.web.app/', USER_WEB)
s = re.sub(r'^OUT=.*$', 'OUT="releases/jayuminton-user-v1.3.4-cloudflare-separated.apk"', s, count=1, flags=re.M)

# Older patch generations contain their own post-build grep verifier. Those checks
# were written for previous URLs/versions and can fail after a perfectly valid APK
# has already assembled. Copy the freshly signed release APK immediately after the
# build and let the dedicated GitHub Actions step perform the authoritative v1.3.4
# verification (package, URL, push worker, NativeUserApp, and admin-code absence).
post_build_anchor = 'APK="app/build/outputs/apk/release/app-release.apk"\ntest -s "$APK"'
post_build_replacement = post_build_anchor + '\nmkdir -p "$(dirname "$OUT")"\ncp "$APK" "$OUT"\nexit 0'
if post_build_anchor not in s:
    raise SystemExit('post-build APK anchor missing')
s = s.replace(post_build_anchor, post_build_replacement, 1)

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
    'cp "$APK" "$OUT"\nexit 0',
)
for marker in required:
    if marker not in s:
        raise SystemExit('missing v1.3.4 user-only marker: ' + marker)

for forbidden in (
    'JAVA_DIR="app/src/main/java/com/jayuminton/admin"',
    "namespace 'com.jayuminton.admin'",
    'package com.jayuminton.admin;',
    'https://jayuminton-push.web.app/',
    "versionCode='133' versionName='1.3.3'",
):
    if forbidden in s:
        raise SystemExit('stale/admin user-web marker survived: ' + forbidden)

p.write_text(s, encoding='utf-8')
print('Prepared v1.3.4 user-only APK for verified Cloudflare user web; CI now owns final APK verification.')
