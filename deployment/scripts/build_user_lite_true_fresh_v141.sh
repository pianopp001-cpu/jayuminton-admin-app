#!/usr/bin/env bash
set -euo pipefail

: "${MAIN_DEPLOYMENT_ID:?MAIN_DEPLOYMENT_ID required}"

BASE="deployment/scripts/build_user_lite_fresh_v140.sh"
TMP="${RUNNER_TEMP:-/tmp}/build_user_lite_true_fresh_v141.sh"
test -s "$BASE"
cp "$BASE" "$TMP"

python3 - "$TMP" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')
repls = {
    'jayuminton-courtstatus-v1.4.0-lite-fresh.apk': 'jayuminton-courtstatus-v1.4.1-true-fresh.apk',
    'user-lite-v1.4.0.txt': 'user-lite-v1.4.1-true-fresh.txt',
    'VERSION="1.4.0"': 'VERSION="1.4.1"',
    'VERSION_CODE="140"': 'VERSION_CODE="141"',
    'PACKAGE="com.jayuminton.user"': 'PACKAGE="com.jayuminton.courtstatus.fresh"',
    "applicationId 'com.jayuminton.user'": "applicationId 'com.jayuminton.courtstatus.fresh'",
    "versionCode 140": "versionCode 141",
    "versionName '1.4.0'": "versionName '1.4.1'",
    "package: name='com.jayuminton.user' versionCode='140' versionName='1.4.0'": "package: name='com.jayuminton.courtstatus.fresh' versionCode='141' versionName='1.4.1'",
}
for old, new in repls.items():
    if old not in s:
        raise SystemExit(f'missing v140 anchor: {old}')
    s = s.replace(old, new)
# Make the install contract explicit: this package must never collide with the legacy user app.
s = s.replace(
    'install_mode=uninstall-old-then-fresh-install',
    'install_mode=true-new-package-fresh-install\nlegacy_application_id=com.jayuminton.user\nlegacy_package_collision=impossible-by-application-id'
)
p.write_text(s, encoding='utf-8')
PY

bash "$TMP"

test -s releases/jayuminton-courtstatus-v1.4.1-true-fresh.apk
test -s deployment/status/user-lite-v1.4.1-true-fresh.txt
grep -F 'status=success' deployment/status/user-lite-v1.4.1-true-fresh.txt >/dev/null
grep -F 'application_id=com.jayuminton.courtstatus.fresh' deployment/status/user-lite-v1.4.1-true-fresh.txt >/dev/null
grep -F 'legacy_package_collision=impossible-by-application-id' deployment/status/user-lite-v1.4.1-true-fresh.txt >/dev/null
grep -F 'firebase_messaging=removed' deployment/status/user-lite-v1.4.1-true-fresh.txt >/dev/null
