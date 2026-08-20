#!/usr/bin/env bash
set -euo pipefail

BASE="deployment/scripts/build_user_lite_fresh_v140.sh"
TMP="${RUNNER_TEMP:-/tmp}/build_user_v143_known_gas_entry.sh"
KNOWN_USER_URL="https://script.google.com/macros/s/AKfycbwVgdQG-DXbgxCgd8L11WA57-DCVaOwF4Sc_lktAZZ0yPJSCIosOOKkmKe3oU8a5pfJ7Q/exec?mode=user&apkUser=1&freshInstall=1&userAppVersion=1.4.3"
SIGNING_B64="signing/jayuminton-release.keystore.b64"
SIGNING_JKS="signing/jayuminton-release.jks"

test -s "$BASE"
test -s "$SIGNING_B64"
mkdir -p signing
base64 -d "$SIGNING_B64" > "$SIGNING_JKS"
test -s "$SIGNING_JKS"
cp "$BASE" "$TMP"

python3 - "$TMP" "$KNOWN_USER_URL" <<'PY'
from pathlib import Path
import re,sys
p=Path(sys.argv[1]); user_url=sys.argv[2]
s=p.read_text(encoding='utf-8')
repls={
 'jayuminton-courtstatus-v1.4.0-lite-fresh.apk':'jayuminton-courtstatus-v1.4.3-known-gas-fresh.apk',
 'user-lite-v1.4.0.txt':'user-lite-v1.4.3-known-gas-fresh.txt',
 'VERSION="1.4.0"':'VERSION="1.4.3"',
 'VERSION_CODE="140"':'VERSION_CODE="143"',
 'PACKAGE="com.jayuminton.user"':'PACKAGE="com.jayuminton.courtstatus.fresh143"',
 "applicationId 'com.jayuminton.user'":"applicationId 'com.jayuminton.courtstatus.fresh143'",
 'versionCode 140':'versionCode 143',
 "versionName '1.4.0'":"versionName '1.4.3'",
 "package: name='com.jayuminton.user' versionCode='140' versionName='1.4.0'":"package: name='com.jayuminton.courtstatus.fresh143' versionCode='143' versionName='1.4.3'",
}
for old,new in repls.items():
    if old not in s: raise SystemExit(f'missing anchor: {old}')
    s=s.replace(old,new)
s=re.sub(r'^USER_URL=.*$', 'USER_URL="'+user_url+'"', s, count=1, flags=re.M)
s=s.replace('install_mode=uninstall-old-then-fresh-install','install_mode=true-new-package-fresh-install\nlegacy_application_id=com.jayuminton.user\nprevious_fresh_application_id=com.jayuminton.courtstatus.fresh\npackage_collision=impossible-by-application-id')
s=s.replace('architecture=webview-plus-minimal-native-vibration-alarm','architecture=known-gas-user-webview-plus-minimal-native-vibration-alarm\nlaunch_url='+user_url+'\nlaunch_contract=known-working-gas-user-route')
p.write_text(s,encoding='utf-8')
PY

bash "$TMP"
APK="releases/jayuminton-courtstatus-v1.4.3-known-gas-fresh.apk"
STATUS="deployment/status/user-lite-v1.4.3-known-gas-fresh.txt"
test -s "$APK"
test -s "$STATUS"
grep -F 'status=success' "$STATUS" >/dev/null
grep -F 'application_id=com.jayuminton.courtstatus.fresh143' "$STATUS" >/dev/null
grep -F 'package_collision=impossible-by-application-id' "$STATUS" >/dev/null
grep -F 'launch_contract=known-working-gas-user-route' "$STATUS" >/dev/null
grep -F '?mode=user' "$STATUS" >/dev/null
if grep -F '?mode=admin' "$STATUS" >/dev/null; then echo 'admin route leaked' >&2; exit 1; fi
