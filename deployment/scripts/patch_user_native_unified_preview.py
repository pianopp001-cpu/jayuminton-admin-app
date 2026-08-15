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
    ("versionCode='130'", "versionCode='132'"),
    ("versionName '1.3.0'", "versionName '1.3.2'"),
    ("versionName='1.3.0'", "versionName='1.3.2'"),
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

# Historical native builds proved their WebView target in classes.dex. v1.1.1
# changed that proof from MAIN_DEPLOYMENT_ID to the production Hosting hostname.
# Unified preview must remove either legacy form and prove the exact preview URL.
filtered = []
removed_legacy_url_proofs = 0
for line in lines:
    is_classes_grep = 'classes.txt' in line and 'grep' in line
    is_legacy_target_proof = (
        'MAIN_DEPLOYMENT_ID' in line or
        'script.google.com/macros/s/' in line or
        'jayuminton-push.web.app' in line
    )
    if is_classes_grep and is_legacy_target_proof:
        removed_legacy_url_proofs += 1
        continue
    filtered.append(line)
lines = filtered
if removed_legacy_url_proofs < 1:
    raise SystemExit('no legacy WebView URL proof found to replace')

classes_anchor = 'strings "$RUNNER_TEMP/classes.dex" > "$RUNNER_TEMP/classes.txt"'
classes_indexes = [i for i, line in enumerate(lines) if line.strip() == classes_anchor]
if len(classes_indexes) != 1:
    raise SystemExit('expected exactly one classes.txt extraction anchor')
ci = classes_indexes[0]
proof_line = 'grep -F "${UNIFIED_MEMBER_URL%/}" "$RUNNER_TEMP/classes.txt" >/dev/null'
lines.insert(ci + 1, proof_line)

# Make any remaining set -e post-build validation self-identifying in Actions.
set_indexes = [i for i, line in enumerate(lines) if line.strip() == 'set -euo pipefail']
if len(set_indexes) != 1:
    raise SystemExit('expected exactly one strict-shell anchor')
lines.insert(
    set_indexes[0] + 1,
    "trap 'rc=$?; echo \"NATIVE_BUILD_FAILED line=$LINENO command=$BASH_COMMAND rc=$rc\" >&2; exit $rc' ERR",
)

s = '\n'.join(lines) + '\n'

for required in (
    'VERSION="1.3.2"',
    'VERSION_CODE="132"',
    'versionCode 132',
    "versionCode='132'",
    "versionName '1.3.2'",
    "versionName='1.3.2'",
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
    proof_line,
    'NATIVE_BUILD_FAILED line=',
):
    if required not in s:
        raise SystemExit('unified preview required marker missing: ' + required)

for forbidden in (
    'VERSION="1.3.0"',
    'VERSION_CODE="130"',
    "versionCode='130'",
    "versionName='1.3.0'",
    'script.google.com/macros/s/${MAIN_DEPLOYMENT_ID}/exec?mode=user',
    'grep -F "jayuminton-push.web.app" "$RUNNER_TEMP/classes.txt"',
):
    if forbidden in s:
        raise SystemExit('unified preview stale marker remained: ' + forbidden)

path.write_text(s, encoding='utf-8')
print(
    'Prepared v1.3.2 unified-preview APK: native FCM/vibration preserved; '
    'WebView and classes.dex proof use UNIFIED_MEMBER_URL; '
    f'legacy URL proofs removed={removed_legacy_url_proofs}.'
)
