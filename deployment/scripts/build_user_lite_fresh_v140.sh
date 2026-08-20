#!/usr/bin/env bash
set -euo pipefail

: "${MAIN_DEPLOYMENT_ID:?MAIN_DEPLOYMENT_ID required}"

JAVA_FILE="app/src/main/java/com/jayuminton/admin/MainActivity.java"
GRADLE_FILE="app/build.gradle"
STRINGS_FILE="app/src/main/res/values/strings.xml"
MANIFEST_FILE="app/src/main/AndroidManifest.xml"
SOURCE_B64="app/src/main/res/drawable/icon_from_library.b64"
TARGET_ICON="app/src/main/res/drawable/icon.png"
OUT="releases/jayuminton-courtstatus-v1.4.0-lite-fresh.apk"
STATUS="deployment/status/user-lite-v1.4.0.txt"
VERSION="1.4.0"
VERSION_CODE="140"
PACKAGE="com.jayuminton.user"
USER_URL="https://script.google.com/macros/s/${MAIN_DEPLOYMENT_ID}/exec?mode=user&app=user&userAppVersion=${VERSION}&apkUser=1&freshInstall=1"

mkdir -p releases deployment/status

test -s "$JAVA_FILE"
test -s "$GRADLE_FILE"
test -s "$STRINGS_FILE"
test -s "$MANIFEST_FILE"
test -s "$SOURCE_B64"

cat > "$JAVA_FILE" <<JAVA
package com.jayuminton.admin;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Context;
import android.graphics.Color;
import android.media.Ringtone;
import android.media.RingtoneManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.os.VibratorManager;
import android.view.View;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.util.HashMap;
import java.util.Map;

public final class MainActivity extends Activity {
    private static final String USER_URL = "${USER_URL}";
    private static final String USER_APP_VERSION = "${VERSION}";
    private WebView webView;
    private Vibrator vibrator;
    private Ringtone alarmTone;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.WHITE);
        getWindow().setNavigationBarColor(Color.WHITE);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            int flags = View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) flags |= View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
            getWindow().getDecorView().setSystemUiVisibility(flags);
        }
        setContentView(R.layout.activity_main);
        configureVibrator();
        configureWebView();
    }

    private void configureVibrator() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            VibratorManager vm = (VibratorManager) getSystemService(Context.VIBRATOR_MANAGER_SERVICE);
            vibrator = vm == null ? null : vm.getDefaultVibrator();
        } else {
            vibrator = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
        }
    }

    @SuppressLint({"SetJavaScriptEnabled", "AddJavascriptInterface"})
    private void configureWebView() {
        webView = findViewById(R.id.webView);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setTextZoom(100);
        settings.setLoadWithOverviewMode(false);
        settings.setUseWideViewPort(false);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setCacheMode(WebSettings.LOAD_NO_CACHE);
        settings.setUserAgentString(settings.getUserAgentString() + " JayumintonUserLite/${VERSION} FreshInstall");
        webView.clearCache(true);
        webView.clearHistory();
        webView.addJavascriptInterface(new UserAppBridge(), "NativeUserApp");
        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String scheme = request.getUrl().getScheme();
                return !("http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme));
            }
            @Override public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                view.evaluateJavascript(
                    "window.__JAYUMINTON_USER_APK__=true;" +
                    "window.__JAYUMINTON_USER_APK_VERSION__='${VERSION}';" +
                    "document.documentElement.setAttribute('data-user-apk','1');" +
                    "document.documentElement.setAttribute('data-user-lite','1');" +
                    "(function(){try{var nv=navigator.vibrate&&navigator.vibrate.bind(navigator);" +
                    "navigator.vibrate=function(p){try{NativeUserApp.vibrate(String(JSON.stringify(p)));return true;}catch(e){return nv?nv(p):false;}};}catch(e){}})();",
                    null
                );
            }
        });
        Map<String,String> headers = new HashMap<>();
        headers.put("Cache-Control", "no-cache, no-store, must-revalidate");
        headers.put("Pragma", "no-cache");
        headers.put("Expires", "0");
        webView.loadUrl(USER_URL + "&ts=" + System.currentTimeMillis(), headers);
    }

    private void startStrongAlert() {
        stopStrongAlert();
        if (vibrator != null && vibrator.hasVibrator()) {
            long[] pattern = new long[1 + 8 * 6];
            int idx = 0;
            pattern[idx++] = 0L;
            for (int group = 0; group < 8; group++) {
                pattern[idx++] = 650L; pattern[idx++] = 220L;
                pattern[idx++] = 650L; pattern[idx++] = 220L;
                pattern[idx++] = 650L; pattern[idx++] = group == 7 ? 0L : 1100L;
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) vibrator.vibrate(VibrationEffect.createWaveform(pattern, -1));
            else vibrator.vibrate(pattern, -1);
        }
        try {
            Uri toneUri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM);
            if (toneUri == null) toneUri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);
            alarmTone = RingtoneManager.getRingtone(this, toneUri);
            if (alarmTone != null) {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) alarmTone.setLooping(true);
                alarmTone.play();
            }
        } catch (Exception ignored) {}
    }

    private void stopStrongAlert() {
        try { if (vibrator != null) vibrator.cancel(); } catch (Exception ignored) {}
        try { if (alarmTone != null && alarmTone.isPlaying()) alarmTone.stop(); } catch (Exception ignored) {}
        alarmTone = null;
    }

    @Override public void onBackPressed() {
        if (webView != null && webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }

    @Override protected void onDestroy() {
        stopStrongAlert();
        if (webView != null) {
            webView.removeJavascriptInterface("NativeUserApp");
            webView.destroy();
        }
        super.onDestroy();
    }

    public final class UserAppBridge {
        @JavascriptInterface public boolean isInstalled() { return true; }
        @JavascriptInterface public String getVersion() { return USER_APP_VERSION; }
        @JavascriptInterface public boolean hasNativeFcm() { return false; }
        @JavascriptInterface public void vibrate(String jsonPattern) {
            runOnUiThread(() -> {
                String p = jsonPattern == null ? "" : jsonPattern.trim();
                if (p.equals("0") || p.equals("[]") || p.equals("null") || p.equals("false")) stopStrongAlert();
                else startStrongAlert();
            });
        }
        @JavascriptInterface public void stopAlert() { runOnUiThread(() -> stopStrongAlert()); }
    }
}
JAVA

python3 - "$GRADLE_FILE" <<'PY'
from pathlib import Path
import re,sys
p=Path(sys.argv[1]); s=p.read_text(encoding='utf-8')
s=re.sub(r"applicationId\s+['\"][^'\"]+['\"]", "applicationId 'com.jayuminton.user'", s, count=1)
s=re.sub(r'versionCode\s+\d+', 'versionCode 140', s, count=1)
s=re.sub(r"versionName\s+['\"][^'\"]+['\"]", "versionName '1.4.0'", s, count=1)
s=re.sub(r"\n?\s*id ['\"]com\.google\.gms\.google-services['\"]", '', s)
s=re.sub(r"\n?\s*implementation\s+platform\([^\n]+firebase[^\n]+\)", '', s, flags=re.I)
s=re.sub(r"\n?\s*implementation\s+['\"][^'\"]*firebase[^'\"]*['\"]", '', s, flags=re.I)
p.write_text(s,encoding='utf-8')
PY

cat > "$STRINGS_FILE" <<'XML'
<resources><string name="app_name">자유민턴 코트현황</string></resources>
XML

python3 - "$MANIFEST_FILE" <<'PY'
from pathlib import Path
import re,sys
p=Path(sys.argv[1]); s=p.read_text(encoding='utf-8')
for perm in ['MODIFY_AUDIO_SETTINGS','POST_NOTIFICATIONS','WAKE_LOCK']:
    s=re.sub(r'\s*<uses-permission android:name="android\.permission\.'+perm+r'"\s*/>\s*','\n',s)
if 'android.permission.VIBRATE' not in s:
    s=s.replace('<manifest xmlns:android="http://schemas.android.com/apk/res/android">','<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n    <uses-permission android:name="android.permission.VIBRATE" />')
s=re.sub(r'\s*<service[^>]*JayumintonFirebaseMessagingService[\s\S]*?</service>\s*','\n',s)
p.write_text(s,encoding='utf-8')
PY

python3 - "$SOURCE_B64" "$TARGET_ICON" <<'PY'
import base64,re,sys
from pathlib import Path
raw=base64.b64decode(re.sub(r'\s+','',Path(sys.argv[1]).read_text(encoding='utf-8').strip()),validate=True)
if raw[:8] != b'\x89PNG\r\n\x1a\n': raise SystemExit('icon source is not PNG')
Path(sys.argv[2]).write_bytes(raw)
PY
rm -f "$SOURCE_B64"

gradle --no-daemon clean assembleRelease
APK="app/build/outputs/apk/release/app-release.apk"
test -s "$APK"
BUILD_TOOLS="$(find "$ANDROID_HOME/build-tools" -mindepth 1 -maxdepth 1 -type d | sort -V | tail -1)"
AAPT="$BUILD_TOOLS/aapt"; APKSIGNER="$BUILD_TOOLS/apksigner"
"$AAPT" dump badging "$APK" > "$RUNNER_TEMP/user-lite-badging.txt"
"$APKSIGNER" verify --verbose --print-certs "$APK" > "$RUNNER_TEMP/user-lite-signing.txt"
grep -F "package: name='com.jayuminton.user' versionCode='140' versionName='1.4.0'" "$RUNNER_TEMP/user-lite-badging.txt" >/dev/null
if unzip -l "$APK" | grep -Ei 'firebase|google-services' >/dev/null; then
  echo 'Firebase payload leaked into lite APK' >&2; exit 1
fi
SIZE="$(stat -c%s "$APK")"
[ "$SIZE" -lt 500000 ] || { echo "Lite APK unexpectedly large: $SIZE" >&2; exit 1; }
mkdir -p releases deployment/status
cp "$APK" "$OUT"
SHA="$(sha256sum "$OUT" | awk '{print $1}')"
SIGNER="$(sed -n -E 's/^.*certificate SHA-256 digest: ([0-9A-Fa-f:]+).*$/\1/p' "$RUNNER_TEMP/user-lite-signing.txt" | head -1 | tr -d ':' | tr '[:lower:]' '[:upper:]')"
cat > "$STATUS" <<EOF
workflow=Build lightweight Jayuminton user APK
status=success
version=$VERSION
version_code=$VERSION_CODE
application_id=$PACKAGE
install_mode=uninstall-old-then-fresh-install
architecture=webview-plus-minimal-native-vibration-alarm
firebase_messaging=removed
background_fcm=removed
screen_alert_source=existing-web-member-alert-contract
current_member_filter=existing-gas-isSelfMember
native_vibration_bridge=3-pulses-x-8-groups-stop-on-vibrate-zero
apk_size_bytes=$SIZE
apk_sha256=$SHA
signer_sha256=$SIGNER
updated_at=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
EOF
cat "$STATUS"
