#!/usr/bin/env bash
set -euo pipefail

: "${MAIN_DEPLOYMENT_ID:?MAIN_DEPLOYMENT_ID is required}"

JAVA_FILE="app/src/main/java/com/jayuminton/admin/MainActivity.java"
GRADLE_FILE="app/build.gradle"
STRINGS_FILE="app/src/main/res/values/strings.xml"
MANIFEST_FILE="app/src/main/AndroidManifest.xml"
SOURCE_B64="app/src/main/res/drawable/icon_from_library.b64"
TARGET_ICON="app/src/main/res/drawable/icon.png"
OUT_APK="releases/jayuminton-user-v1.0.0.apk"
STATUS="deployment/status/user-apk-v1.0.0.txt"
USER_URL="https://script.google.com/macros/s/${MAIN_DEPLOYMENT_ID}/exec?mode=user&userAppVersion=1.0.0&apkUser=1"

mkdir -p releases deployment/status

test -s "$JAVA_FILE"
test -s "$GRADLE_FILE"
test -s "$STRINGS_FILE"
test -s "$MANIFEST_FILE"
test -s "$SOURCE_B64"
test -s signing/jayuminton-release.keystore.b64

cat > "$JAVA_FILE" <<JAVA
package com.jayuminton.admin;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
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
    private static final String USER_APP_VERSION = "1.0.0";
    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.WHITE);
        getWindow().setNavigationBarColor(Color.WHITE);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            int flags = View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                flags |= View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
            }
            getWindow().getDecorView().setSystemUiVisibility(flags);
        }
        setContentView(R.layout.activity_main);
        configureWebView();
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
        settings.setUserAgentString(settings.getUserAgentString() + " JayumintonUserNative/1.0.0");

        // Keep DOM/localStorage so member login and the selected member survive relaunches.
        // Only the ordinary HTTP cache/history is refreshed.
        webView.clearCache(true);
        webView.clearHistory();

        webView.addJavascriptInterface(new UserAppBridge(), "NativeUserApp");
        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String scheme = request.getUrl().getScheme();
                return !("http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme));
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                view.evaluateJavascript(
                    "window.__JAYUMINTON_USER_APK__=true;" +
                    "window.__JAYUMINTON_USER_APK_VERSION__='1.0.0';" +
                    "document.documentElement.setAttribute('data-user-apk','1');",
                    null
                );
            }
        });

        Map<String, String> headers = new HashMap<>();
        headers.put("Cache-Control", "no-cache, no-store, must-revalidate");
        headers.put("Pragma", "no-cache");
        headers.put("Expires", "0");
        webView.loadUrl(USER_URL + "&ts=" + System.currentTimeMillis(), headers);
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.removeJavascriptInterface("NativeUserApp");
            webView.destroy();
        }
        super.onDestroy();
    }

    public final class UserAppBridge {
        @JavascriptInterface
        public boolean isInstalled() {
            return true;
        }

        @JavascriptInterface
        public String getVersion() {
            return USER_APP_VERSION;
        }
    }
}
JAVA

cat > "$STRINGS_FILE" <<'XML'
<resources>
    <string name="app_name">자유민턴 사용자</string>
</resources>
XML

python3 - "$GRADLE_FILE" <<'PY'
from pathlib import Path
import re, sys
p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')
s = re.sub(r"applicationId\s+['\"][^'\"]+['\"]", "applicationId 'com.jayuminton.user'", s, count=1)
s = re.sub(r'versionCode\s+\d+', 'versionCode 100', s, count=1)
s = re.sub(r"versionName\s+['\"][^'\"]+['\"]", "versionName '1.0.0'", s, count=1)
p.write_text(s, encoding='utf-8')
PY

python3 - "$SOURCE_B64" "$TARGET_ICON" <<'PY'
import base64, re, sys
from pathlib import Path
src = Path(sys.argv[1]).read_text(encoding='utf-8').strip()
clean = re.sub(r'\s+', '', src)
raw = base64.b64decode(clean, validate=True)
if raw[:8] != b'\x89PNG\r\n\x1a\n':
    raise SystemExit('source dog icon is not PNG')
Path(sys.argv[2]).write_bytes(raw)
PY

cat > "$RUNNER_TEMP/CropUserDogIcon.java" <<'JAVAICON'
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.File;
import javax.imageio.ImageIO;

public final class CropUserDogIcon {
  public static void main(String[] args) throws Exception {
    File file = new File(args[0]);
    BufferedImage source = ImageIO.read(file);
    if (source == null) throw new RuntimeException("dog icon decode failed");
    if (source.getWidth() != 128 || source.getHeight() != 152)
      throw new RuntimeException("unexpected dog source size: " + source.getWidth() + "x" + source.getHeight());
    BufferedImage crop = source.getSubimage(16, 56, 96, 96);
    BufferedImage square = new BufferedImage(128, 128, BufferedImage.TYPE_INT_ARGB);
    Graphics2D g = square.createGraphics();
    g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
    g.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
    g.drawImage(crop, 0, 0, 128, 128, null);
    g.dispose();
    if (!ImageIO.write(square, "png", file)) throw new RuntimeException("dog icon write failed");
  }
}
JAVAICON
javac "$RUNNER_TEMP/CropUserDogIcon.java"
java -cp "$RUNNER_TEMP" CropUserDogIcon "$TARGET_ICON"
cp "$TARGET_ICON" "$RUNNER_TEMP/user-dog-reference.png"
rm -f "$SOURCE_B64"

# User APK does not need the admin audio-control permission.
python3 - "$MANIFEST_FILE" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')
s = s.replace('    <uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />\n', '')
p.write_text(s, encoding='utf-8')
PY

grep -F "applicationId 'com.jayuminton.user'" "$GRADLE_FILE" >/dev/null
grep -F 'versionCode 100' "$GRADLE_FILE" >/dev/null
grep -F "versionName '1.0.0'" "$GRADLE_FILE" >/dev/null
grep -F '자유민턴 사용자' "$STRINGS_FILE" >/dev/null
grep -F 'JayumintonUserNative/1.0.0' "$JAVA_FILE" >/dev/null
grep -F "$MAIN_DEPLOYMENT_ID" "$JAVA_FILE" >/dev/null
grep -F 'NativeUserApp' "$JAVA_FILE" >/dev/null
if grep -F '?mode=admin' "$JAVA_FILE" >/dev/null; then
  echo 'admin mode URL leaked into user APK source' >&2
  exit 1
fi

# Restore the same verified release-signing key used by the admin APK.
mkdir -p signing
base64 --decode signing/jayuminton-release.keystore.b64 > signing/jayuminton-release.jks
test -s signing/jayuminton-release.jks

gradle --no-daemon clean assembleRelease

APK="app/build/outputs/apk/release/app-release.apk"
test -s "$APK"
BUILD_TOOLS="$(find "$ANDROID_HOME/build-tools" -mindepth 1 -maxdepth 1 -type d | sort -V | tail -1)"
AAPT="$BUILD_TOOLS/aapt"
APKSIGNER="$BUILD_TOOLS/apksigner"
test -x "$AAPT"
test -x "$APKSIGNER"

"$APKSIGNER" verify --verbose --print-certs "$APK" > "$RUNNER_TEMP/user-apksigner.txt"
"$AAPT" dump badging "$APK" > "$RUNNER_TEMP/user-badging.txt"

grep -F "package: name='com.jayuminton.user' versionCode='100' versionName='1.0.0'" "$RUNNER_TEMP/user-badging.txt" >/dev/null
grep -F "application-label:'자유민턴 사용자'" "$RUNNER_TEMP/user-badging.txt" >/dev/null

unzip -p "$APK" classes.dex > "$RUNNER_TEMP/user-classes.dex"
strings "$RUNNER_TEMP/user-classes.dex" > "$RUNNER_TEMP/user-classes.txt"
grep -F "$MAIN_DEPLOYMENT_ID" "$RUNNER_TEMP/user-classes.txt" >/dev/null
grep -F 'JayumintonUserNative/1.0.0' "$RUNNER_TEMP/user-classes.txt" >/dev/null
grep -F 'NativeUserApp' "$RUNNER_TEMP/user-classes.txt" >/dev/null
if grep -F '?mode=admin' "$RUNNER_TEMP/user-classes.txt" >/dev/null; then
  echo 'admin mode URL leaked into packaged user APK' >&2
  exit 1
fi

ICON_PATH="$(sed -n "s/^application-icon-160:'\([^']*\)'.*/\1/p" "$RUNNER_TEMP/user-badging.txt" | head -1)"
if [ -z "$ICON_PATH" ]; then
  ICON_PATH="$(sed -n "s/^application:.* icon='\([^']*\)'.*/\1/p" "$RUNNER_TEMP/user-badging.txt" | head -1)"
fi
test -n "$ICON_PATH"
unzip -p "$APK" "$ICON_PATH" > "$RUNNER_TEMP/user-final-icon.png"

cat > "$RUNNER_TEMP/CompareUserDogIcon.java" <<'JAVAICON'
import java.awt.image.BufferedImage;
import java.io.File;
import javax.imageio.ImageIO;
public final class CompareUserDogIcon {
  public static void main(String[] args) throws Exception {
    BufferedImage a = ImageIO.read(new File(args[0]));
    BufferedImage b = ImageIO.read(new File(args[1]));
    if (a == null || b == null) throw new RuntimeException("icon decode failed");
    if (a.getWidth()!=128 || a.getHeight()!=128 || b.getWidth()!=128 || b.getHeight()!=128)
      throw new RuntimeException("user icon must be 128x128");
    for (int y=0; y<128; y++) for (int x=0; x<128; x++)
      if (a.getRGB(x,y) != b.getRGB(x,y)) throw new RuntimeException("packaged user icon pixel mismatch");
  }
}
JAVAICON
javac "$RUNNER_TEMP/CompareUserDogIcon.java"
java -cp "$RUNNER_TEMP" CompareUserDogIcon "$RUNNER_TEMP/user-dog-reference.png" "$RUNNER_TEMP/user-final-icon.png"

mkdir -p "$(dirname "$OUT_APK")"
cp "$APK" "$OUT_APK"
APK_SHA="$(sha256sum "$OUT_APK" | awk '{print $1}')"
SIGNER_SHA="$(sed -n -E 's/^.*certificate SHA-256 digest: ([0-9A-Fa-f:]+).*$/\1/p' "$RUNNER_TEMP/user-apksigner.txt" | head -1 | tr -d ':' | tr '[:lower:]' '[:upper:]')"
test -n "$SIGNER_SHA"

cat > "$STATUS" <<EOF
workflow=Build Jayuminton user APK
status=success
version=1.0.0
version_code=100
application_id=com.jayuminton.user
user_deployment_id=$MAIN_DEPLOYMENT_ID
user_agent=JayumintonUserNative/1.0.0
native_install_signal=NativeUserApp
web_storage=preserved_on_launch
cache_mode=LOAD_NO_CACHE
launcher_label=자유민턴 사용자
launcher_icon_layout=dog-full-square-128x128
apk_sha256=$APK_SHA
signer_sha256=$SIGNER_SHA
updated_at=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
EOF

cat "$STATUS"
