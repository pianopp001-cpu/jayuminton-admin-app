#!/usr/bin/env bash
set -euo pipefail

: "${MAIN_DEPLOYMENT_ID:?MAIN_DEPLOYMENT_ID required}"

BASE="deployment/scripts/build_user_lite_fresh_v140.sh"
TMP="${RUNNER_TEMP:-/tmp}/build_user_lite_true_fresh_v142.generated.sh"
SIGNING_B64="signing/jayuminton-release.keystore.b64"
SIGNING_JKS="signing/jayuminton-release.jks"

test -s "$BASE"
test -s "$SIGNING_B64"
mkdir -p signing
base64 -d "$SIGNING_B64" > "$SIGNING_JKS"
test -s "$SIGNING_JKS"
cp "$BASE" "$TMP"

python3 - "$TMP" <<'PY'
from pathlib import Path
import re,sys
p=Path(sys.argv[1])
s=p.read_text(encoding='utf-8')
repls=[
 ('jayuminton-courtstatus-v1.4.0-lite-fresh.apk','jayuminton-courtstatus-v1.4.2-live-entry-fresh.apk'),
 ('user-lite-v1.4.0.txt','user-lite-v1.4.2-live-entry-fresh.txt'),
 ('VERSION="1.4.0"','VERSION="1.4.2"'),
 ('VERSION_CODE="140"','VERSION_CODE="142"'),
 ('PACKAGE="com.jayuminton.user"','PACKAGE="com.jayuminton.courtstatus.fresh"'),
 ("applicationId 'com.jayuminton.user'","applicationId 'com.jayuminton.courtstatus.fresh'"),
 ('versionCode 140','versionCode 142'),
 ("versionName '1.4.0'","versionName '1.4.2'"),
 ("package: name='com.jayuminton.user' versionCode='140' versionName='1.4.0'","package: name='com.jayuminton.courtstatus.fresh' versionCode='142' versionName='1.4.2'"),
]
for old,new in repls:
    if old not in s:
        raise SystemExit(f'missing v140 anchor: {old}')
    s=s.replace(old,new)
old_url='USER_URL="https://script.google.com/macros/s/${MAIN_DEPLOYMENT_ID}/exec?mode=user&app=user&userAppVersion=${VERSION}&apkUser=1&freshInstall=1"'
new_url='USER_URL="https://jayuminton-push.web.app/?source=apk&app=user&mode=user&freshInstall=1&userAppVersion=${VERSION}"'
if old_url not in s:
    raise SystemExit('missing direct Apps Script USER_URL anchor')
s=s.replace(old_url,new_url,1)
s=s.replace(
 'install_mode=uninstall-old-then-fresh-install',
 'install_mode=true-new-package-fresh-install\nlegacy_application_id=com.jayuminton.user\nlegacy_package_collision=impossible-by-application-id'
)
s=s.replace(
 'architecture=webview-plus-minimal-native-vibration-alarm',
 'architecture=webview-live-user-shell-plus-minimal-native-vibration-alarm\nlaunch_url=https://jayuminton-push.web.app/\nlaunch_contract=production-unified-member-app'
)
p.write_text(s,encoding='utf-8')
PY

bash "$TMP"

APK="releases/jayuminton-courtstatus-v1.4.2-live-entry-fresh.apk"
STATUS="deployment/status/user-lite-v1.4.2-live-entry-fresh.txt"
test -s "$APK"
test -s "$STATUS"
grep -F 'status=success' "$STATUS" >/dev/null
grep -F 'application_id=com.jayuminton.courtstatus.fresh' "$STATUS" >/dev/null
grep -F 'legacy_package_collision=impossible-by-application-id' "$STATUS" >/dev/null
grep -F 'launch_url=https://jayuminton-push.web.app/' "$STATUS" >/dev/null
grep -F 'launch_contract=production-unified-member-app' "$STATUS" >/dev/null
grep -F 'firebase_messaging=removed' "$STATUS" >/dev/null
