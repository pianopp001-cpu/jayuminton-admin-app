#!/usr/bin/env bash
set -euo pipefail

: "${JAYUMINTON_DEPLOY_CONFIG_JSON:?JAYUMINTON_DEPLOY_CONFIG_JSON is required}"
: "${ANDROID_HOME:?ANDROID_HOME is required}"

STATUS_FILE="deployment/status/apk-v1997.txt"
APK_OUT="releases/jayuminton-v199.7-verified.apk"
V1996_SIGNER_SHA256="D47ADB93363FF397601E63667E79F27F99AE499AADC1FD0013861809950FC787"
ICON_SHA256="a64eaa06107cd20478fe49ab7c10b5b2afd2347533b95c383a439f8705d4a58e"
mkdir -p deployment/status releases

# Never build over an unverified web state.
grep -F 'status=success' deployment/status/stable-admin-interactions.txt >/dev/null
grep -F 'verification=deployed-project-pull-and-js-syntax' deployment/status/stable-admin-interactions.txt >/dev/null
grep -F 'admin_push_button=removed' deployment/status/stable-admin-interactions.txt >/dev/null
grep -F 'status=success' deployment/status/verified-push-live.txt >/dev/null
grep -F 'hosting_verification=live-bytes-checked' deployment/status/verified-push-live.txt >/dev/null
grep -F 'pwa_install=chrome-native-prompt-only' deployment/status/verified-push-live.txt >/dev/null
grep -F 'token_registration=server-verified-before-on' deployment/status/verified-push-live.txt >/dev/null
grep -F 'wait1_vibration=3-pulse-x2' deployment/status/verified-push-live.txt >/dev/null
grep -F 'court_vibration=3-pulse-x4' deployment/status/verified-push-live.txt >/dev/null

# Verify the newly deployed admin behavior before packaging the WebView shell.
grep -F 'id="updateMemberButton"' source-snapshot/current-main/Admin.html >/dev/null
grep -F 'onclick="selectAllMembers()"' source-snapshot/current-main/Admin.html >/dev/null
if grep -F 'id="memberEditModal"' source-snapshot/current-main/Admin.html >/dev/null; then
  echo 'Old member edit modal still exists in live snapshot.' >&2
  exit 1
fi
if grep -F '📱 푸시앱' source-snapshot/current-main/Admin.html >/dev/null; then
  echo 'Admin push-app button returned.' >&2
  exit 1
fi
grep -F "document.getElementById('updateMemberButton')" source-snapshot/current-main/Script.html >/dev/null
grep -F "server('updateMemberProfile'" source-snapshot/current-main/Script.html >/dev/null
grep -F 'function selectAllMembers()' source-snapshot/current-main/Script.html >/dev/null
grep -F "runAction('setMemberStatus', [ADMIN_PIN_VALUE, [memberId], 'active'])" source-snapshot/current-main/Script.html >/dev/null
grep -F "localStorage.setItem(" source-snapshot/current-main/Script.html >/dev/null
grep -F 'ADMIN_AUTH_KEY' source-snapshot/current-main/Script.html >/dev/null
grep -F "resumeAdminSession" source-snapshot/current-main/Script.html >/dev/null
grep -F 'members[index].name = name;' source-snapshot/current-main/Code.js >/dev/null

CONFIG="$RUNNER_TEMP/deploy.json"
printf '%s' "$JAYUMINTON_DEPLOY_CONFIG_JSON" > "$CONFIG"
jq -e '.mainDeploymentId' "$CONFIG" >/dev/null
ADMIN_DEPLOYMENT_ID="$(jq -r '.mainDeploymentId' "$CONFIG")"
test -n "$ADMIN_DEPLOYMENT_ID"
export ADMIN_DEPLOYMENT_ID

# Restore and strictly validate the pinned dog/badminton launcher icon.
SOURCE_B64="app/src/main/res/drawable/icon_from_library.b64"
TARGET_ICON="app/src/main/res/drawable/icon.png"
python3 - "$SOURCE_B64" "$TARGET_ICON" "$ICON_SHA256" <<'PYICON'
import base64, hashlib, re, struct, sys, zlib
from pathlib import Path
source, target, expected = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
raw = re.sub(r'\s+', '', source.read_text(encoding='utf-8'))
png = base64.b64decode(raw, validate=True)
if not png.startswith(b'\x89PNG\r\n\x1a\n'):
    raise SystemExit('launcher icon is not PNG')
pos = 8
width = height = None
saw_iend = False
while pos < len(png):
    if pos + 12 > len(png): raise SystemExit('launcher PNG truncated')
    length = struct.unpack('>I', png[pos:pos+4])[0]
    typ = png[pos+4:pos+8]
    ds = pos + 8
    de = ds + length
    ce = de + 4
    if ce > len(png): raise SystemExit('launcher PNG chunk truncated')
    expected_crc = struct.unpack('>I', png[de:ce])[0]
    actual_crc = zlib.crc32(png[ds:de], zlib.crc32(typ)) & 0xffffffff
    if expected_crc != actual_crc: raise SystemExit('launcher PNG CRC mismatch')
    if typ == b'IHDR': width, height = struct.unpack('>II', png[ds:ds+8])
    if typ == b'IEND':
        saw_iend = True
        pos = ce
        break
    pos = ce
if not saw_iend or pos != len(png): raise SystemExit('launcher PNG incomplete')
if (width, height) != (128, 152): raise SystemExit(f'launcher dimensions changed: {width}x{height}')
sha = hashlib.sha256(png).hexdigest()
if sha != expected: raise SystemExit(f'launcher SHA mismatch: {sha}')
target.write_bytes(png)
print(f'Pinned launcher icon verified: {width}x{height} sha256={sha}')
PYICON
rm -f "$SOURCE_B64"

# Patch only the temporary runner checkout.
python3 - <<'PY'
from pathlib import Path
import os, re

deployment_id = os.environ['ADMIN_DEPLOYMENT_ID'].strip()
java_path = Path('app/src/main/java/com/jayuminton/admin/MainActivity.java')
text = java_path.read_text(encoding='utf-8')

admin_url = 'https://script.google.com/macros/s/' + deployment_id + '/exec?mode=admin&appVersion=199.7&freshAdmin=1'
text, count = re.subn(
    r'https://script\.google\.com/macros/s/[^"\\]+/exec\?mode=admin[^"\\]*',
    admin_url,
    text,
    count=1,
)
if count != 1: raise SystemExit('ADMIN_URL replacement failed')

text = re.sub(
    r'private static final String APK_WEB_BUILD = "[^"]+";',
    'private static final String APK_WEB_BUILD = "1997-persistent-admin";',
    text,
    count=1,
)
text = re.sub(
    r'JayumintonNative/[0-9A-Za-z.\-]+(?: FreshAdmin/[0-9A-Za-z.\-]+)?',
    'JayumintonNative/199.7 FreshAdmin/1997',
    text,
)

# Keep localStorage/WebStorage so the server-validated admin session survives relaunches.
text = text.replace('import android.webkit.WebStorage;\n', '')
text = text.replace('        WebStorage.getInstance().deleteAllData();\n', '')

# Music remains audible at level 6 while TTS/ALARM is also explicitly level 6.
if 'private static final int MEDIA_DUCK_VOLUME_STEP = 6;' not in text:
    text = text.replace(
        '    private static final int VOICE_VOLUME_STEP = 6;\n',
        '    private static final int VOICE_VOLUME_STEP = 6;\n'
        '    private static final int MEDIA_DUCK_VOLUME_STEP = 6;\n',
        1,
    )
old = '''                int maxMedia = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC);
                int minimumMusic = maxMedia > 0 ? 1 : 0;
                audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, minimumMusic, 0);'''
new = '''                int maxMedia = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC);
                int mediaStep = Math.max(0, Math.min(MEDIA_DUCK_VOLUME_STEP, maxMedia));
                audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, mediaStep, 0);'''
if old not in text:
    raise SystemExit('legacy media duck block missing')
text = text.replace(old, new, 1)
java_path.write_text(text, encoding='utf-8')

gradle_path = Path('app/build.gradle')
gradle = gradle_path.read_text(encoding='utf-8')
gradle = re.sub(r"applicationId\s+['\"][^'\"]+['\"]", "applicationId 'com.jayuminton.admin199'", gradle, count=1)
gradle = re.sub(r'versionCode\s+\d+', 'versionCode 1997', gradle, count=1)
gradle = re.sub(r"versionName\s+['\"][^'\"]+['\"]", "versionName '199.7'", gradle, count=1)
gradle_path.write_text(gradle, encoding='utf-8')
PY

JAVA_FILE="app/src/main/java/com/jayuminton/admin/MainActivity.java"
grep -F "applicationId 'com.jayuminton.admin199'" app/build.gradle >/dev/null
grep -F 'versionCode 1997' app/build.gradle >/dev/null
grep -F "versionName '199.7'" app/build.gradle >/dev/null
grep -F "$ADMIN_DEPLOYMENT_ID" "$JAVA_FILE" >/dev/null
grep -F 'JayumintonNative/199.7 FreshAdmin/1997' "$JAVA_FILE" >/dev/null
grep -F 'APK_WEB_BUILD = "1997-persistent-admin"' "$JAVA_FILE" >/dev/null
grep -F 'WebSettings.LOAD_NO_CACHE' "$JAVA_FILE" >/dev/null
grep -F 'webView.clearCache(true);' "$JAVA_FILE" >/dev/null
grep -F 'webView.clearHistory();' "$JAVA_FILE" >/dev/null
grep -F 'removeSessionCookies' "$JAVA_FILE" >/dev/null
if grep -F 'WebStorage.getInstance().deleteAllData();' "$JAVA_FILE" >/dev/null; then
  echo 'WebStorage is still deleted on APK launch.' >&2
  exit 1
fi
grep -F 'private static final int VOICE_VOLUME_STEP = 6;' "$JAVA_FILE" >/dev/null
grep -F 'private static final int MEDIA_DUCK_VOLUME_STEP = 6;' "$JAVA_FILE" >/dev/null
grep -F 'int mediaStep = Math.max(0, Math.min(MEDIA_DUCK_VOLUME_STEP, maxMedia));' "$JAVA_FILE" >/dev/null
grep -F 'setStreamVolume(AudioManager.STREAM_MUSIC, mediaStep, 0);' "$JAVA_FILE" >/dev/null
grep -F 'setStreamVolume(AudioManager.STREAM_ALARM, voiceStep, 0);' "$JAVA_FILE" >/dev/null
grep -F 'setStreamVolume(AudioManager.STREAM_MUSIC, originalMediaVolume, 0);' "$JAVA_FILE" >/dev/null
grep -F 'android.permission.MODIFY_AUDIO_SETTINGS' app/src/main/AndroidManifest.xml >/dev/null
grep -F '<string name="app_name">자유민턴 관리자</string>' app/src/main/res/values/strings.xml >/dev/null

# Old deployments that caused regressions are forbidden in the APK class source.
for stale in \
  'AKfycbzaExnvUwO1FWcLhXQxUUJyHLXgC7mZHM0Z2T33Z4EvNap3lqHPryOV-FlQ09NJKt48Ww' \
  'AKfycbwVgdQG-DXbgxCgd8L11WA57-DCVaOwF4Sc_lktAZZ0yPJSCIosOOKkmKe3oU8a5pfJ7Q'; do
  if grep -F "$stale" "$JAVA_FILE" >/dev/null; then
    echo "Stale admin deployment remains: $stale" >&2
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
test -x "$APKSIGNER"; test -x "$AAPT"

"$APKSIGNER" verify --verbose --print-certs "$APK" | tee "$RUNNER_TEMP/apksigner.txt"
"$AAPT" dump badging "$APK" | tee "$RUNNER_TEMP/badging.txt"
"$AAPT" dump permissions "$APK" | tee "$RUNNER_TEMP/permissions.txt"

grep -F "package: name='com.jayuminton.admin199' versionCode='1997' versionName='199.7'" "$RUNNER_TEMP/badging.txt" >/dev/null
grep -F "application-label:'자유민턴 관리자'" "$RUNNER_TEMP/badging.txt" >/dev/null
grep -F 'android.permission.INTERNET' "$RUNNER_TEMP/permissions.txt" >/dev/null
grep -F 'android.permission.MODIFY_AUDIO_SETTINGS' "$RUNNER_TEMP/permissions.txt" >/dev/null

unzip -p "$APK" classes.dex > "$RUNNER_TEMP/classes.dex"
strings "$RUNNER_TEMP/classes.dex" > "$RUNNER_TEMP/classes.strings"
grep -F "$ADMIN_DEPLOYMENT_ID" "$RUNNER_TEMP/classes.strings" >/dev/null
grep -F 'JayumintonNative/199.7 FreshAdmin/1997' "$RUNNER_TEMP/classes.strings" >/dev/null
grep -F '1997-persistent-admin' "$RUNNER_TEMP/classes.strings" >/dev/null
grep -F 'MEDIA_DUCK_VOLUME_STEP' "$JAVA_FILE" >/dev/null
for stale in \
  'AKfycbzaExnvUwO1FWcLhXQxUUJyHLXgC7mZHM0Z2T33Z4EvNap3lqHPryOV-FlQ09NJKt48Ww' \
  'AKfycbwVgdQG-DXbgxCgd8L11WA57-DCVaOwF4Sc_lktAZZ0yPJSCIosOOKkmKe3oU8a5pfJ7Q'; do
  if grep -F "$stale" "$RUNNER_TEMP/classes.strings" >/dev/null; then
    echo "Stale deployment found in final APK: $stale" >&2
    exit 1
  fi
done

# Resolve optimized icon filename and compare pixels to the pinned source.
ICON_PATH="$(sed -n "s/^application-icon-160:'\([^']*\)'.*/\1/p" "$RUNNER_TEMP/badging.txt" | head -1)"
if [ -z "$ICON_PATH" ]; then
  ICON_PATH="$(sed -n "s/^application:.* icon='\([^']*\)'.*/\1/p" "$RUNNER_TEMP/badging.txt" | head -1)"
fi
test -n "$ICON_PATH"
unzip -p "$APK" "$ICON_PATH" > "$RUNNER_TEMP/final-icon.png"
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
    for (int y = 0; y < source.getHeight(); y++) for (int x = 0; x < source.getWidth(); x++)
      if (source.getRGB(x,y) != built.getRGB(x,y)) throw new RuntimeException("launcher icon pixels changed");
    System.out.println("Launcher icon pixels verified: " + source.getWidth() + "x" + source.getHeight());
  }
}
JAVA
javac "$RUNNER_TEMP/VerifyIcon.java"
java -cp "$RUNNER_TEMP" VerifyIcon "$TARGET_ICON" "$RUNNER_TEMP/final-icon.png"

SIGNER_SHA="$(sed -n -E 's/^.*certificate SHA-256 digest: ([0-9A-Fa-f:]+).*$/\1/p' "$RUNNER_TEMP/apksigner.txt" | head -1 | tr -d ':' | tr '[:lower:]' '[:upper:]')"
test -n "$SIGNER_SHA"
if [ "$SIGNER_SHA" != "$V1996_SIGNER_SHA256" ]; then
  echo "v199.7 signer differs from v199.6 signer." >&2
  exit 1
fi

cp "$APK" "$APK_OUT"
APK_SHA="$(sha256sum "$APK_OUT" | awk '{print $1}')"
BUILT_ICON_SHA="$(sha256sum "$TARGET_ICON" | awk '{print $1}')"
cat > "$STATUS_FILE" <<EOF
workflow=Build verified Jayuminton v199.7 APK
status=success
version=199.7
version_code=1997
application_id=com.jayuminton.admin199
admin_deployment_id=$ADMIN_DEPLOYMENT_ID
admin_session=server-validated-localstorage-persistent
web_storage=preserved_on_launch
cache_mode=LOAD_NO_CACHE
voice_volume_step=6
media_duck_volume_step=6
media_restore=original-value
audio_permission=verified
launcher_label=자유민턴 관리자
launcher_icon_sha256=$BUILT_ICON_SHA
apk_sha256=$APK_SHA
signer_sha256=$SIGNER_SHA
upgrade_from_v1996=yes
updated_at=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
EOF
cat "$STATUS_FILE"
ls -lh "$APK_OUT"
