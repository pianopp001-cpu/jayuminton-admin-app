#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding='utf-8')

# Play Store AAB build patch for the already verified v1.3.0/code130 user app.
# Keep the app/UI/FCM/vibration logic unchanged. Only:
#   1) target API 35 for current Google Play submission requirements,
#   2) use AGP 8.6.1 (API 35 supported; Gradle 8.7 compatible),
#   3) use a separate private Play upload key supplied via GitHub Secrets,
#   4) build a signed Android App Bundle instead of an APK.

if 'VERSION="1.3.0"' not in s or 'VERSION_CODE="130"' not in s:
    raise SystemExit('expected v1.3.0/code130 baseline missing')
if 'private static final int MAX_GROUPS = 8;' not in s:
    raise SystemExit('expected v1.3.0 cap8 vibration baseline missing')

old_agp = "    id 'com.android.application' version '8.5.2' apply false\n"
new_agp = "    id 'com.android.application' version '8.6.1' apply false\n"
if s.count(old_agp) != 1:
    raise SystemExit('AGP 8.5.2 anchor missing or duplicated')
s = s.replace(old_agp, new_agp, 1)

old_target = '        targetSdk 34\n'
new_target = '        targetSdk 35\n'
if s.count(old_target) != 1:
    raise SystemExit('targetSdk 34 anchor missing or duplicated')
s = s.replace(old_target, new_target, 1)

old_signing = '''    signingConfigs {
        release {
            storeFile file('../signing/jayuminton-release.jks')
            storePassword 'JayuMinton14!'
            keyAlias 'jayuminton'
            keyPassword 'JayuMinton14!'
        }
    }
'''
new_signing = '''    signingConfigs {
        release {
            storeFile file(System.getenv('PLAY_UPLOAD_KEYSTORE_PATH'))
            storePassword System.getenv('PLAY_UPLOAD_KEY_PASSWORD')
            keyAlias System.getenv('PLAY_UPLOAD_KEY_ALIAS')
            keyPassword System.getenv('PLAY_UPLOAD_KEY_PASSWORD')
        }
    }
'''
if s.count(old_signing) != 1:
    raise SystemExit('legacy release signing block missing or duplicated')
s = s.replace(old_signing, new_signing, 1)

old_key_test = 'test -s signing/jayuminton-release.keystore.b64\n'
new_key_test = ''': "${PLAY_UPLOAD_KEYSTORE_B64:?PLAY_UPLOAD_KEYSTORE_B64 required}"
: "${PLAY_UPLOAD_KEY_PASSWORD:?PLAY_UPLOAD_KEY_PASSWORD required}"
: "${PLAY_UPLOAD_KEY_ALIAS:?PLAY_UPLOAD_KEY_ALIAS required}"
export PLAY_UPLOAD_KEYSTORE_PATH="$RUNNER_TEMP/jayuminton-play-upload.jks"
'''
if s.count(old_key_test) != 1:
    raise SystemExit('legacy keystore test anchor missing or duplicated')
s = s.replace(old_key_test, new_key_test, 1)

old_decode = '''base64 --decode signing/jayuminton-release.keystore.b64 > signing/jayuminton-release.jks
test -s signing/jayuminton-release.jks
'''
new_decode = '''printf '%s' "$PLAY_UPLOAD_KEYSTORE_B64" | base64 --decode > "$PLAY_UPLOAD_KEYSTORE_PATH"
test -s "$PLAY_UPLOAD_KEYSTORE_PATH"
keytool -list -keystore "$PLAY_UPLOAD_KEYSTORE_PATH" -storepass "$PLAY_UPLOAD_KEY_PASSWORD" -alias "$PLAY_UPLOAD_KEY_ALIAS" >/dev/null
'''
if s.count(old_decode) != 1:
    raise SystemExit('legacy keystore decode anchor missing or duplicated')
s = s.replace(old_decode, new_decode, 1)

anchor = 'gradle --no-daemon clean assembleRelease\n'
pos = s.find(anchor)
if pos < 0:
    raise SystemExit('assembleRelease tail anchor missing')

play_tail = r'''gradle --no-daemon clean bundleRelease
AAB="app/build/outputs/bundle/release/app-release.aab"
PLAY_OUT="releases/jayuminton-user-play-v1.3.0-code130.aab"
PLAY_STATUS="deployment/status/user-play-aab-v1.3.0.txt"
test -s "$AAB"

echo '[AAB verify] checking bundle structure'
unzip -l "$AAB" > "$RUNNER_TEMP/aab-list.txt"
grep -F 'base/manifest/AndroidManifest.xml' "$RUNNER_TEMP/aab-list.txt" >/dev/null
grep -F 'BundleConfig.pb' "$RUNNER_TEMP/aab-list.txt" >/dev/null

echo '[AAB verify] checking release signature'
jarsigner -verify "$AAB" > "$RUNNER_TEMP/aab-jarsigner.txt" 2>&1

echo '[AAB verify] checking generated app identity/version'
grep -F "applicationId 'com.jayuminton.user'" app/build.gradle >/dev/null
grep -F 'targetSdk 35' app/build.gradle >/dev/null
grep -F 'versionCode 130' app/build.gradle >/dev/null
grep -F "versionName '1.3.0'" app/build.gradle >/dev/null
grep -F "id 'com.android.application' version '8.6.1' apply false" build.gradle >/dev/null

# Read the signer fingerprint from the exact upload key used by Gradle. This is
# more reliable than parsing jarsigner/keytool output from the bundle itself.
keytool -list -v -keystore "$PLAY_UPLOAD_KEYSTORE_PATH" -storepass "$PLAY_UPLOAD_KEY_PASSWORD" -alias "$PLAY_UPLOAD_KEY_ALIAS" > "$RUNNER_TEMP/play-upload-cert.txt"
SIGNER_SHA="$(sed -n -E 's/^.*SHA256: ([0-9A-Fa-f:]+).*$/\1/p' "$RUNNER_TEMP/play-upload-cert.txt" | head -1 | tr -d ':' | tr '[:lower:]' '[:upper:]')"
test -n "$SIGNER_SHA"

mkdir -p releases deployment/status
cp "$AAB" "$PLAY_OUT"
AAB_SHA="$(sha256sum "$PLAY_OUT" | awk '{print $1}')"
cat > "$PLAY_STATUS" <<EOF
workflow=Build Jayuminton Google Play AAB
status=success
version=1.3.0
version_code=130
application_id=com.jayuminton.user
android_gradle_plugin=8.6.1
compile_sdk=35
target_sdk=35
min_sdk=24
bundle_format=aab
play_upload_key=yes
play_upload_alias=$PLAY_UPLOAD_KEY_ALIAS
play_upload_signer_sha256=$SIGNER_SHA
wait1_vibration=controller-finite-3-pulse-groups-max8-or-until-confirmed
court_vibration=controller-finite-3-pulse-groups-max8-or-until-confirmed
vibration_max_groups=8
pulse_ms=650
intra_pulse_gap_ms=220
group_gap_ms=1100
aab_sha256=$AAB_SHA
updated_at=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
EOF
cat "$PLAY_STATUS"
'''

s = s[:pos] + play_tail

for required in (
    "version '8.6.1' apply false",
    'targetSdk 35',
    "System.getenv('PLAY_UPLOAD_KEYSTORE_PATH')",
    "System.getenv('PLAY_UPLOAD_KEY_PASSWORD')",
    "System.getenv('PLAY_UPLOAD_KEY_ALIAS')",
    'gradle --no-daemon clean bundleRelease',
    'jayuminton-user-play-v1.3.0-code130.aab',
    'vibration_max_groups=8',
):
    if required not in s:
        raise SystemExit('Play AAB patch verification marker missing: ' + required)

for forbidden in (
    "version '8.5.2' apply false",
    "storePassword 'JayuMinton14!'",
    "keyPassword 'JayuMinton14!'",
    "storeFile file('../signing/jayuminton-release.jks')",
    'gradle --no-daemon clean assembleRelease',
):
    if forbidden in s:
        raise SystemExit('legacy APK signing/build marker remains: ' + forbidden)

path.write_text(s, encoding='utf-8')
print('Prepared v1.3.0/code130 Play AAB build with robust post-build verification; app behavior unchanged.')
