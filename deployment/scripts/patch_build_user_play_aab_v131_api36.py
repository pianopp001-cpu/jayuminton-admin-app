#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding='utf-8')

# Google Play API 36 build patch. This runs AFTER the verified v1.3.0/code130
# Play AAB patch, and changes build/version metadata only. App UI, FCM,
# member switching, vibration behavior, and web-app logic remain unchanged.

required_baseline = (
    'VERSION="1.3.0"',
    'VERSION_CODE="130"',
    "version '8.6.1' apply false",
    'compileSdk 35',
    'targetSdk 35',
    'versionCode 130',
    "versionName '1.3.0'",
    'gradle --no-daemon clean bundleRelease',
    'private static final int MAX_GROUPS = 8;',
)
for marker in required_baseline:
    if marker not in s:
        raise SystemExit('expected v1.3.0/code130 Play baseline missing: ' + marker)

replacements = (
    ('VERSION="1.3.0"', 'VERSION="1.3.1"'),
    ('VERSION_CODE="130"', 'VERSION_CODE="131"'),
    ("version '8.6.1' apply false", "version '8.9.1' apply false"),
    ('compileSdk 35', 'compileSdk 36'),
    ('targetSdk 35', 'targetSdk 36'),
    ('versionCode 130', 'versionCode 131'),
    ("versionName '1.3.0'", "versionName '1.3.1'"),
    ('JayumintonUserNative/1.3.0', 'JayumintonUserNative/1.3.1'),
    ('JayumintonNativeAndroid/1.3.0', 'JayumintonNativeAndroid/1.3.1'),
    ('jayuminton-user-play-v1.3.0-code130.aab', 'jayuminton-user-play-v1.3.1-code131.aab'),
    ('user-play-aab-v1.3.0.txt', 'user-play-aab-v1.3.1.txt'),
    ('version=1.3.0', 'version=1.3.1'),
    ('version_code=130', 'version_code=131'),
    ('android_gradle_plugin=8.6.1', 'android_gradle_plugin=8.9.1'),
    ('compile_sdk=35', 'compile_sdk=36'),
    ('target_sdk=35', 'target_sdk=36'),
)

for old, new in replacements:
    if old in s:
        s = s.replace(old, new)

# AGP 8.9.x requires Gradle 8.11.1 or newer. The workflow supplies Gradle
# 8.11.1 explicitly; keep this verification marker in the generated script.
verification = r'''

echo '[API36 verify] checking Play target/version metadata'
grep -F "id 'com.android.application' version '8.9.1' apply false" build.gradle >/dev/null
grep -F 'compileSdk 36' app/build.gradle >/dev/null
grep -F 'targetSdk 36' app/build.gradle >/dev/null
grep -F 'versionCode 131' app/build.gradle >/dev/null
grep -F "versionName '1.3.1'" app/build.gradle >/dev/null
'''

if "echo '[API36 verify] checking Play target/version metadata'" not in s:
    s += verification

for marker in (
    'VERSION="1.3.1"',
    'VERSION_CODE="131"',
    "version '8.9.1' apply false",
    'compileSdk 36',
    'targetSdk 36',
    'versionCode 131',
    "versionName '1.3.1'",
    'gradle --no-daemon clean bundleRelease',
    'private static final int MAX_GROUPS = 8;',
):
    if marker not in s:
        raise SystemExit('API 36 verification marker missing: ' + marker)

path.write_text(s, encoding='utf-8')
print('Prepared Play v1.3.1/code131 for Android API 36; app behavior unchanged.')
