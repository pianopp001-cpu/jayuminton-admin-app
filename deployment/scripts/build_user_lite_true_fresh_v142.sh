#!/usr/bin/env bash
set -euo pipefail

: "${MAIN_DEPLOYMENT_ID:?MAIN_DEPLOYMENT_ID required}"

BASE="deployment/scripts/build_user_lite_true_fresh_v141.sh"
TMP="${RUNNER_TEMP:-/tmp}/build_user_lite_true_fresh_v142.sh"
test -s "$BASE"
cp "$BASE" "$TMP"

python3 - "$TMP" <<'PY'
from pathlib import Path
import re,sys
p=Path(sys.argv[1])
s=p.read_text(encoding='utf-8')
repls={
 'v1.4.1-true-fresh':'v1.4.2-live-entry-fresh',
 'user-lite-v1.4.1-true-fresh':'user-lite-v1.4.2-live-entry-fresh',
 'VERSION="1.4.1"':'VERSION="1.4.2"',
 'VERSION_CODE="141"':'VERSION_CODE="142"',
 "versionCode 141":"versionCode 142",
 "versionName '1.4.1'":"versionName '1.4.2'",
 "versionCode='141' versionName='1.4.1'":"versionCode='142' versionName='1.4.2'",
}
for old,new in repls.items():
    if old not in s:
        raise SystemExit(f'missing v141 anchor: {old}')
    s=s.replace(old,new)
# Do not open the Apps Script deployment directly. Current production user shell is Firebase Hosting.
s=re.sub(r'^USER_URL=.*$', 'USER_URL="https://jayuminton-push.web.app/?source=apk&app=user&mode=user&freshInstall=1&userAppVersion=${VERSION}"', s, count=1, flags=re.M)
s=s.replace('architecture=webview-plus-minimal-native-vibration-alarm', 'architecture=webview-live-user-shell-plus-minimal-native-vibration-alarm\nlaunch_url=https://jayuminton-push.web.app/\nlaunch_contract=production-unified-member-app')
p.write_text(s,encoding='utf-8')
PY

bash "$TMP"

APK="releases/jayuminton-courtstatus-v1.4.2-live-entry-fresh.apk"
STATUS="deployment/status/user-lite-v1.4.2-live-entry-fresh.txt"
test -s "$APK"
test -s "$STATUS"
grep -F 'status=success' "$STATUS" >/dev/null
grep -F 'application_id=com.jayuminton.courtstatus.fresh' "$STATUS" >/dev/null
grep -F 'launch_url=https://jayuminton-push.web.app/' "$STATUS" >/dev/null
grep -F 'launch_contract=production-unified-member-app' "$STATUS" >/dev/null
grep -F 'firebase_messaging=removed' "$STATUS" >/dev/null
