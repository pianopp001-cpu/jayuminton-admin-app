#!/usr/bin/env bash
set -euo pipefail

: "${JAYUMINTON_DEPLOY_CONFIG_JSON:?JAYUMINTON_DEPLOY_CONFIG_JSON is required}"
: "${ANDROID_HOME:?ANDROID_HOME is required}"

OLD_APK_CERT_SHA256="1C54FD8A5912E6E6F3A04D80DEAF904CC1FE78CF089A3048105CC5652F4973C9"
STATUS_FILE="deployment/status/apk-v1996.txt"
APK_OUT="releases/jayuminton-v199.6-verified.apk"
mkdir -p deployment/status releases

# Never build an APK on top of an unverified live web state.
grep -F 'status=success' deployment/status/stable-admin-interactions.txt >/dev/null
grep -F 'verification=deployed-project-pull-and-js-syntax' deployment/status/stable-admin-interactions.txt >/dev/null
grep -F 'admin_push_button=removed' deployment/status/stable-admin-interactions.txt >/dev/null
grep -F 'excluded_double_tap=active' deployment/status/stable-admin-interactions.txt >/dev/null
grep -F 'status=success' deployment/status/verified-push-live.txt >/dev/null
grep -F 'hosting_verification=live-bytes-checked' deployment/status/verified-push-live.txt >/dev/null
grep -F 'pwa_install=chrome-native-prompt-only' deployment/status/verified-push-live.txt >/dev/null
grep -F 'legacy_handoff=intent-drive-resolver-absent' deployment/status/verified-push-live.txt >/dev/null
grep -F 'token_registration=server-verified-before-on' deployment/status/verified-push-live.txt >/dev/null
grep -F 'wait1_vibration=3-pulse-x2' deployment/status/verified-push-live.txt >/dev/null
grep -F 'court_vibration=3-pulse-x4' deployment/status/verified-push-live.txt >/dev/null

CONFIG="$RUNNER_TEMP/deploy.json"
printf '%s' "$JAYUMINTON_DEPLOY_CONFIG_JSON" > "$CONFIG"
jq -e '.mainDeploymentId' "$CONFIG" >/dev/null
ADMIN_DEPLOYMENT_ID="$(jq -r '.mainDeploymentId' "$CONFIG")"
test -n "$ADMIN_DEPLOYMENT_ID"
export ADMIN_DEPLOYMENT_ID

# Restore the pinned dog/badminton launcher icon that was saved from the user-provided source.
SOURCE_B64="app/src/main/res/drawable/icon_from_library.b64"
TARGET_ICON="app/src/main/res/drawable/icon.png"
test -s "$SOURCE_B64"
base64 --decode "$SOURCE_B64" > "$TARGET_ICON"
test -s "$TARGET_ICON"
file "$TARGET_ICON" | grep -F 'PNG image data' >/dev/null
python3 - <<'PY'
from pathlib import Path
import struct
p = Path('app/src/main/res/drawable/icon.png')
data = p.read_bytes()
if data[:8] != b'\x89PNG\r\n\x1a\n':
    raise SystemExit('launcher icon is not PNG')
w, h = struct.unpack('>II', data[16:24])
if w != h or w < 128:
    raise SystemExit(f'launcher icon must be square and >=128px, got {w}x{h}')
print(f'Pinned launcher icon: {w}x{h}, {len(data)} bytes')
PY

# Patch only the temporary checked-out build tree. The live Apps Script source is not modified here.
python3 - <<'PY'
from pathlib import Path
import os, re

deployment_id = os.environ['ADMIN_DEPLOYMENT_ID'].strip()
java_path = Path('app/src/main/java/com/jayuminton/admin/MainActivity.java')
text = java_path.read_text(encoding='utf-8')
admin_url = (
    'https://script.google.com/macros/s/' + deployment_id +
    '/exec?mode=admin&appVersion=199.6&freshAdmin=1'
)
text, count = re.subn(
    r'https://script\.google\.com/macros/s/[^"\\]+/exec\?mode=admin[^"\\]*',
    admin_url,
    text,
    count=1,
)
if count != 1:
    raise SystemExit('ADMIN_URL replacement failed')
text = re.sub(
    r'JayumintonNative/[0-9A-Za-z.\-]+(?: FreshAdmin/[0-9A-Za-z.\-]+)?',
    'JayumintonNative/199.6 FreshAdmin/1996',
    text,
)
text = re.sub(
    r'private static final String APK_WEB_BUILD = "[^"]+";',
    'private static final String APK_WEB_BUILD = "1996-verified-admin";',
    text,
    count=1,
)
java_path.write_text(text, encoding='utf-8')

gradle_path = Path('app/build.gradle')
gradle = gradle_path.read_text(encoding='utf-8')
gradle = re.sub(
    r"applicationId\s+['\"][^'\"]+['\"]",
    "applicationId 'com.jayuminton.admin199'",
    gradle,
    count=1,
)
gradle = re.sub(r'versionCode\s+\d+', 'versionCode 1996', gradle, count=1)
gradle = re.sub(
    r"versionName\s+['\"][^'\"]+['\"]",
    "versionName '199.6'",
    gradle,
    count=1,
)
gradle_path.write_text(gradle, encoding='utf-8')
PY

JAVA_FILE="app/src/main/java/com/jayuminton/admin/MainActivity.java"
grep -F "applicationId 'com.jayuminton.admin199'" app/build.gradle >/dev/null
grep -F 'versionCode 1996' app/build.gradle >/dev/null
grep -F "versionName '199.6'" app/build.gradle >/dev/null
grep -F "$ADMIN_DEPLOYMENT_ID" "$JAVA_FILE" >/dev/null
grep -F 'JayumintonNative/199.6 FreshAdmin/1996' "$JAVA_FILE" >/dev/null
grep -F 'APK_WEB_BUILD = "1996-verified-admin"' "$JAVA_FILE" >/dev/null
grep -F 'WebSettings.LOAD_NO_CACHE' "$JAVA_FILE" >/dev/null
grep -F 'WebStorage.getInstance().deleteAllData();' "$JAVA_FILE" >/dev/null
grep -F 'webView.clearCache(true);' "$JAVA_FILE" >/dev/null
grep -F 'webView.clearHistory();' "$JAVA_FILE" >/dev/null
grep -F 'removeSessionCookies' "$JAVA_FILE" >/dev/null
grep -F 'private static final int VOICE_VOLUME_STEP = 6;' "$JAVA_FILE" >/dev/null
grep -F 'setStreamVolume(AudioManager.STREAM_MUSIC, minimumMusic, 0);' "$JAVA_FILE" >/dev/null
grep -F 'setStreamVolume(AudioManager.STREAM_ALARM, voiceStep, 0);' "$JAVA_FILE" >/dev/null
grep -F 'android.permission.MODIFY_AUDIO_SETTINGS' app/src/main/AndroidManifest.xml >/dev/null
grep -F 'android:icon="@drawable/icon"' app/src/main/AndroidManifest.xml >/dev/null
grep -F '<string name="app_name">자유민턴 관리자</string>' app/src/main/res/values/strings.xml >/dev/null

# Stale deployment IDs that caused the earlier APK regressions are forbidden.
for stale in \
  'AKfycbzaExnvUwO1FWcLhXQxUUJyHLXgC7mZHM0Z2T33Z4EvNap3lqHPryOV-FlQ09NJKt48Ww' \
  'AKfycbwVgdQG-DXbgxCgd8L11WA57-DCVaOwF4Sc_lktAZZ0yPJSCIosOOKkmKe3oU8a5pfJ7Q'; do
  if grep -F "$stale" "$JAVA_FILE" >/dev/null; then
    echo "Stale admin deployment remains in MainActivity: $stale" >&2
    exit 1
  fi
done

mkdir -p signing
base64 --decode signing/jayuminton-release.keystore.b64 > signing/jayuminton-release.jks
test -s signing/jayuminton-release.jks

gradle --no-daemon :app:assembleRelease

APK="app/build/outputs/apk/release/app-release.apk"
test -s "$APK"
unzip -t "$APK" >/dev/null
APKSIGNER="$(find "$ANDROID_HOME/build-tools" -name apksigner -type f | sort -V | tail -1)"
AAPT="$(find "$ANDROID_HOME/build-tools" -name aapt -type f | sort -V | tail -1)"
test -x "$APKSIGNER"
test -x "$AAPT"

"$APKSIGNER" verify --verbose --print-certs "$APK" | tee "$RUNNER_TEMP/apksigner.txt"
"$AAPT" dump badging "$APK" | tee "$RUNNER_TEMP/badging.txt"
"$AAPT" dump permissions "$APK" | tee "$RUNNER_TEMP/permissions.txt"

grep -F "package: name='com.jayuminton.admin199' versionCode='1996' versionName='199.6'" "$RUNNER_TEMP/badging.txt" >/dev/null
grep -F "application-label:'자유민턴 관리자'" "$RUNNER_TEMP/badging.txt" >/dev/null
grep -F "android.permission.INTERNET" "$RUNNER_TEMP/permissions.txt" >/dev/null
grep -F "android.permission.MODIFY_AUDIO_SETTINGS" "$RUNNER_TEMP/permissions.txt" >/dev/null

unzip -p "$APK" classes.dex > "$RUNNER_TEMP/classes.dex"
strings "$RUNNER_TEMP/classes.dex" > "$RUNNER_TEMP/classes.strings"
grep -F "$ADMIN_DEPLOYMENT_ID" "$RUNNER_TEMP/classes.strings" >/dev/null
grep -F 'JayumintonNative/199.6 FreshAdmin/1996' "$RUNNER_TEMP/classes.strings" >/dev/null
grep -F '1996-verified-admin' "$RUNNER_TEMP/classes.strings" >/dev/null
for stale in \
  'AKfycbzaExnvUwO1FWcLhXQxUUJyHLXgC7mZHM0Z2T33Z4EvNap3lqHPryOV-FlQ09NJKt48Ww' \
  'AKfycbwVgdQG-DXbgxCgd8L11WA57-DCVaOwF4Sc_lktAZZ0yPJSCIosOOKkmKe3oU8a5pfJ7Q'; do
  if grep -F "$stale" "$RUNNER_TEMP/classes.strings" >/dev/null; then
    echo "Stale admin deployment found in final classes.dex: $stale" >&2
    exit 1
  fi
done

unzip -p "$APK" res/drawable/icon.png > "$RUNNER_TEMP/final-icon.png"
test -s "$RUNNER_TEMP/final-icon.png"
cat > "$RUNNER_TEMP/VerifyIcon.java" <<'JAVA'
import java.awt.image.BufferedImage;
import java.io.File;
import javax.imageio.ImageIO;
public final class VerifyIcon {
  public static void main(String[] args) throws Exception {
    BufferedImage source = ImageIO.read(new File(args[0]));
    BufferedImage built = ImageIO.read(new File(args[1]));
    if (source == null || built == null) throw new RuntimeException("PNG decode failed");
    if (source.getWidth() != built.getWidth() || source.getHeight() != built.getHeight()) throw new RuntimeException("launcher icon dimensions changed");
    for (int y = 0; y < source.getHeight(); y++) {
      for (int x = 0; x < source.getWidth(); x++) {
        if (source.getRGB(x, y) != built.getRGB(x, y)) throw new RuntimeException("launcher icon pixels changed at " + x + "," + y);
      }
    }
    System.out.println("Launcher icon pixels verified: " + source.getWidth() + "x" + source.getHeight());
  }
}
JAVA
javac "$RUNNER_TEMP/VerifyIcon.java"
java -cp "$RUNNER_TEMP" VerifyIcon "$TARGET_ICON" "$RUNNER_TEMP/final-icon.png"

SIGNER_SHA="$(awk -F': ' '/Signer #1 certificate SHA-256 digest:/ {gsub(":", "", $2); print toupper($2); exit}' "$RUNNER_TEMP/apksigner.txt")"
test -n "$SIGNER_SHA"
if [ "$SIGNER_SHA" = "$OLD_APK_CERT_SHA256" ]; then
  UPGRADE_COMPATIBLE=yes
else
  UPGRADE_COMPATIBLE=no
fi

cp "$APK" "$APK_OUT"
APK_SHA="$(sha256sum "$APK_OUT" | awk '{print $1}')"
ICON_SHA="$(sha256sum "$TARGET_ICON" | awk '{print $1}')"

cat > "$STATUS_FILE" <<EOF
workflow=Build verified Jayuminton v199.6 APK
status=success
version=199.6
version_code=1996
application_id=com.jayuminton.admin199
admin_deployment_id=$ADMIN_DEPLOYMENT_ID
cache_mode=LOAD_NO_CACHE
web_storage=cleared_on_launch
session_cookies=cleared_on_launch
voice_volume_step=6
media_ducking=minimum-then-restored
audio_permission=verified
launcher_label=자유민턴 관리자
launcher_icon_sha256=$ICON_SHA
apk_sha256=$APK_SHA
signer_sha256=$SIGNER_SHA
old_apk_upgrade_compatible=$UPGRADE_COMPATIBLE
updated_at=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
EOF

cat "$STATUS_FILE"
ls -lh "$APK_OUT"
