#!/usr/bin/env bash
set -euo pipefail

: "${MAIN_DEPLOYMENT_ID:?MAIN_DEPLOYMENT_ID required}"
: "${PUSH_URL:?PUSH_URL required}"
: "${FIREBASE_PROJECT_ID:?FIREBASE_PROJECT_ID required}"

JAVA_DIR="app/src/main/java/com/jayuminton/admin"
MAIN_JAVA="$JAVA_DIR/MainActivity.java"
SERVICE_JAVA="$JAVA_DIR/JayumintonFirebaseMessagingService.java"
REGISTRAR_JAVA="$JAVA_DIR/NativePushRegistrar.java"
ROOT_GRADLE="build.gradle"
APP_GRADLE="app/build.gradle"
STRINGS="app/src/main/res/values/strings.xml"
MANIFEST="app/src/main/AndroidManifest.xml"
SOURCE_B64="app/src/main/res/drawable/icon_from_library.b64"
TARGET_ICON="app/src/main/res/drawable/icon.png"
OUT="releases/jayuminton-courtstatus-v1.1.0-fresh-install.apk"
STATUS="deployment/status/user-native-push-v1.1.0.txt"
PACKAGE="com.jayuminton.user"
VERSION="1.1.0"
VERSION_CODE="110"
USER_URL="https://script.google.com/macros/s/${MAIN_DEPLOYMENT_ID}/exec?mode=user&userAppVersion=${VERSION}&apkUser=1&freshInstall=1"

mkdir -p "$JAVA_DIR" releases deployment/status signing

test -s "$SOURCE_B64"
test -s app/google-services.json
test -s signing/jayuminton-release.keystore.b64

cat > "$ROOT_GRADLE" <<'GRADLE'
plugins {
    id 'com.android.application' version '8.5.2' apply false
    id 'com.google.gms.google-services' version '4.5.0' apply false
}
GRADLE

cat > "$APP_GRADLE" <<'GRADLE'
plugins {
    id 'com.android.application'
    id 'com.google.gms.google-services'
}

android {
    namespace 'com.jayuminton.admin'
    compileSdk 35

    defaultConfig {
        applicationId 'com.jayuminton.user'
        minSdk 24
        targetSdk 34
        versionCode 110
        versionName '1.1.0'
    }

    signingConfigs {
        release {
            storeFile file('../signing/jayuminton-release.jks')
            storePassword 'JayuMinton14!'
            keyAlias 'jayuminton'
            keyPassword 'JayuMinton14!'
        }
    }

    buildTypes {
        release {
            minifyEnabled false
            shrinkResources false
            signingConfig signingConfigs.release
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }
}

dependencies {
    implementation platform('com.google.firebase:firebase-bom:34.16.0')
    implementation 'com.google.firebase:firebase-messaging'
}
GRADLE

cat > "$STRINGS" <<'XML'
<resources>
    <string name="app_name">자유민턴 코트현황</string>
</resources>
XML

cat > "$MANIFEST" <<'XML'
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.VIBRATE" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />

    <application
        android:allowBackup="false"
        android:icon="@drawable/icon"
        android:roundIcon="@drawable/icon"
        android:label="자유민턴 코트현황"
        android:supportsRtl="true"
        android:theme="@style/Theme.JayumintonAdmin"
        android:usesCleartextTraffic="false">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:screenOrientation="portrait">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <service
            android:name=".JayumintonFirebaseMessagingService"
            android:exported="false">
            <intent-filter>
                <action android:name="com.google.firebase.MESSAGING_EVENT" />
            </intent-filter>
        </service>
    </application>
</manifest>
XML

cat > "$MAIN_JAVA" <<JAVA
package com.jayuminton.admin;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.pm.PackageManager;
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
    private static final String USER_APP_VERSION = "1.1.0";
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
        requestNotificationPermissionIfNeeded();
        NativePushRegistrar.ensureToken(this);
        configureWebView();
    }

    private void requestNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 1101);
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
        settings.setUserAgentString(settings.getUserAgentString() + " JayumintonUserNative/1.1.0 FreshInstall NativeFCM");
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
                    "window.__JAYUMINTON_USER_APK_VERSION__='1.1.0';" +
                    "window.__JAYUMINTON_NATIVE_FCM__=true;" +
                    "document.documentElement.setAttribute('data-user-apk','1');" +
                    "document.documentElement.setAttribute('data-native-fcm','1');" +
                    "if(typeof syncNativeUserPushBridge==='function'){syncNativeUserPushBridge();}",
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
        if (webView != null && webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
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
        @JavascriptInterface public boolean isInstalled() { return true; }
        @JavascriptInterface public String getVersion() { return USER_APP_VERSION; }
        @JavascriptInterface public boolean hasNativeFcm() { return true; }
        @JavascriptInterface public void setMember(String memberId, String memberName) {
            NativePushRegistrar.setMember(MainActivity.this, memberId, memberName);
        }
        @JavascriptInterface public void clearMember() {
            NativePushRegistrar.clearMember(MainActivity.this);
        }
        @JavascriptInterface public void setPushEnabled(boolean enabled) {
            NativePushRegistrar.setPushEnabled(MainActivity.this, enabled);
        }
        @JavascriptInterface public void setVibrationEnabled(boolean enabled) {
            NativePushRegistrar.setVibrationEnabled(MainActivity.this, enabled);
        }
    }
}
JAVA

cat > "$REGISTRAR_JAVA" <<JAVA
package com.jayuminton.admin;

import android.content.Context;
import android.content.SharedPreferences;
import android.net.Uri;

import com.google.firebase.messaging.FirebaseMessaging;

import org.json.JSONObject;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class NativePushRegistrar {
    private static final String PREFS = "jayuminton_native_push_v110";
    private static final String KEY_MEMBER_ID = "member_id";
    private static final String KEY_MEMBER_NAME = "member_name";
    private static final String KEY_TOKEN = "fcm_token";
    private static final String KEY_PUSH = "push_enabled";
    private static final String KEY_VIBRATION = "vibration_enabled";
    private static final String RELAY_URL = "${PUSH_URL}";
    private static final ExecutorService EXECUTOR = Executors.newSingleThreadExecutor();

    private NativePushRegistrar() {}

    private static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static boolean pushEnabled(Context context) {
        return prefs(context).getBoolean(KEY_PUSH, true);
    }

    public static boolean vibrationEnabled(Context context) {
        return prefs(context).getBoolean(KEY_VIBRATION, true);
    }

    public static void ensureToken(Context context) {
        Context app = context.getApplicationContext();
        FirebaseMessaging.getInstance().getToken().addOnCompleteListener(task -> {
            if (!task.isSuccessful() || task.getResult() == null || task.getResult().isEmpty()) return;
            onNewToken(app, task.getResult());
        });
    }

    public static void onNewToken(Context context, String token) {
        Context app = context.getApplicationContext();
        prefs(app).edit().putString(KEY_TOKEN, token == null ? "" : token).apply();
        if (pushEnabled(app)) registerCurrent(app);
    }

    public static void setMember(Context context, String memberId, String memberName) {
        Context app = context.getApplicationContext();
        SharedPreferences p = prefs(app);
        String oldId = p.getString(KEY_MEMBER_ID, "");
        String oldName = p.getString(KEY_MEMBER_NAME, "");
        String token = p.getString(KEY_TOKEN, "");
        String newId = memberId == null ? "" : memberId.trim();
        String newName = memberName == null ? "" : memberName.trim();
        if (!oldId.isEmpty() && !token.isEmpty() && (!oldId.equals(newId) || !oldName.equals(newName))) {
            submitAsync("unregister_web_token", oldId, oldName, token);
        }
        p.edit().putString(KEY_MEMBER_ID, newId).putString(KEY_MEMBER_NAME, newName).apply();
        if (pushEnabled(app)) {
            if (token.isEmpty()) ensureToken(app);
            else registerCurrent(app);
        }
    }

    public static void clearMember(Context context) {
        Context app = context.getApplicationContext();
        SharedPreferences p = prefs(app);
        String id = p.getString(KEY_MEMBER_ID, "");
        String name = p.getString(KEY_MEMBER_NAME, "");
        String token = p.getString(KEY_TOKEN, "");
        if (!id.isEmpty() && !token.isEmpty()) submitAsync("unregister_web_token", id, name, token);
        p.edit().remove(KEY_MEMBER_ID).remove(KEY_MEMBER_NAME).apply();
    }

    public static void setPushEnabled(Context context, boolean enabled) {
        Context app = context.getApplicationContext();
        SharedPreferences p = prefs(app);
        boolean previous = p.getBoolean(KEY_PUSH, true);
        p.edit().putBoolean(KEY_PUSH, enabled).apply();
        if (enabled) {
            ensureToken(app);
        } else if (previous) {
            String id = p.getString(KEY_MEMBER_ID, "");
            String name = p.getString(KEY_MEMBER_NAME, "");
            String token = p.getString(KEY_TOKEN, "");
            if (!id.isEmpty() && !token.isEmpty()) submitAsync("unregister_web_token", id, name, token);
        }
    }

    public static void setVibrationEnabled(Context context, boolean enabled) {
        prefs(context.getApplicationContext()).edit().putBoolean(KEY_VIBRATION, enabled).apply();
    }

    private static void registerCurrent(Context context) {
        SharedPreferences p = prefs(context);
        String id = p.getString(KEY_MEMBER_ID, "");
        String name = p.getString(KEY_MEMBER_NAME, "");
        String token = p.getString(KEY_TOKEN, "");
        if (id.isEmpty() || token.isEmpty()) return;
        submitAsync("register_web_token", id, name, token);
    }

    private static void submitAsync(String action, String memberId, String memberName, String token) {
        EXECUTOR.execute(() -> submit(action, memberId, memberName, token));
    }

    private static void submit(String action, String memberId, String memberName, String token) {
        HttpURLConnection connection = null;
        try {
            JSONObject payload = new JSONObject();
            payload.put("action", action);
            payload.put("memberId", memberId == null ? "" : memberId);
            payload.put("memberName", memberName == null ? "" : memberName);
            payload.put("token", token == null ? "" : token);
            payload.put("userAgent", "JayumintonNativeAndroid/1.1.0 FreshInstall NativeFCM");
            String body = "payload=" + Uri.encode(payload.toString());
            URL url = new URL(RELAY_URL);
            connection = (HttpURLConnection) url.openConnection();
            connection.setConnectTimeout(12000);
            connection.setReadTimeout(12000);
            connection.setRequestMethod("POST");
            connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded;charset=UTF-8");
            byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
            connection.setFixedLengthStreamingMode(bytes.length);
            try (OutputStream output = connection.getOutputStream()) { output.write(bytes); }
            int code = connection.getResponseCode();
            if (code >= 200 && code < 400) {
                try { if (connection.getInputStream() != null) connection.getInputStream().close(); } catch (Exception ignored) {}
            } else {
                try { if (connection.getErrorStream() != null) connection.getErrorStream().close(); } catch (Exception ignored) {}
            }
        } catch (Exception ignored) {
        } finally {
            if (connection != null) connection.disconnect();
        }
    }
}
JAVA

cat > "$SERVICE_JAVA" <<'JAVA'
package com.jayuminton.admin;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.media.AudioAttributes;
import android.media.RingtoneManager;
import android.net.Uri;
import android.os.Build;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.os.VibratorManager;

import com.google.firebase.messaging.FirebaseMessagingService;
import com.google.firebase.messaging.RemoteMessage;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public final class JayumintonFirebaseMessagingService extends FirebaseMessagingService {
    private static final String WAIT_CHANNEL = "jayuminton_wait1_native_v110";
    private static final String COURT_CHANNEL = "jayuminton_court_native_v110";

    @Override
    public void onNewToken(String token) {
        super.onNewToken(token);
        NativePushRegistrar.onNewToken(this, token);
    }

    @Override
    public void onMessageReceived(RemoteMessage remoteMessage) {
        super.onMessageReceived(remoteMessage);
        if (!NativePushRegistrar.pushEnabled(this)) return;
        Map<String, String> data = remoteMessage.getData();
        String type = value(data, "type", "wait1_ready");
        boolean court = "court_assignment".equals(type);
        String title = value(data, "title", court ? "코트 입장 안내" : "대기1 안내");
        String body = value(data, "body", court ? "코트에 배정되었습니다." : "대기1에 들어왔습니다.");
        String assignmentId = value(data, "assignmentId", String.valueOf(System.currentTimeMillis()));
        showNotification(court, title, body, assignmentId);
        if (NativePushRegistrar.vibrationEnabled(this)) vibrateStrong(court ? 5 : 3);
    }

    private static String value(Map<String, String> data, String key, String fallback) {
        if (data == null) return fallback;
        String value = data.get(key);
        return value == null || value.trim().isEmpty() ? fallback : value;
    }

    private void showNotification(boolean court, String title, String body, String assignmentId) {
        NotificationManager manager = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null) return;
        String channelId = court ? COURT_CHANNEL : WAIT_CHANNEL;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    channelId,
                    court ? "코트 입장 알림" : "대기1 알림",
                    NotificationManager.IMPORTANCE_HIGH
            );
            channel.setDescription(court ? "코트에 배정될 때 표시되는 자유민턴 알림" : "대기1에 진입할 때 표시되는 자유민턴 알림");
            channel.enableLights(true);
            channel.enableVibration(false);
            Uri sound = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);
            AudioAttributes attrs = new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_NOTIFICATION_EVENT).build();
            channel.setSound(sound, attrs);
            manager.createNotificationChannel(channel);
        }

        Intent intent = new Intent(this, MainActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent pending = PendingIntent.getActivity(
                this,
                assignmentId.hashCode(),
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        Notification.Builder builder = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? new Notification.Builder(this, channelId)
                : new Notification.Builder(this);
        builder.setSmallIcon(R.drawable.icon)
                .setContentTitle((court ? "🚨 " : "🏸 ") + title)
                .setContentText(body)
                .setStyle(new Notification.BigTextStyle().bigText(body))
                .setContentIntent(pending)
                .setAutoCancel(true)
                .setCategory(court ? Notification.CATEGORY_EVENT : Notification.CATEGORY_STATUS)
                .setVisibility(Notification.VISIBILITY_PUBLIC)
                .setWhen(System.currentTimeMillis());
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            builder.setPriority(Notification.PRIORITY_MAX);
            builder.setDefaults(Notification.DEFAULT_SOUND | Notification.DEFAULT_LIGHTS);
        }
        manager.notify(assignmentId.hashCode(), builder.build());
    }

    private void vibrateStrong(int groups) {
        Vibrator vibrator;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            VibratorManager vm = (VibratorManager) getSystemService(Context.VIBRATOR_MANAGER_SERVICE);
            vibrator = vm == null ? null : vm.getDefaultVibrator();
        } else {
            vibrator = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
        }
        if (vibrator == null || !vibrator.hasVibrator()) return;

        List<Long> timingsList = new ArrayList<>();
        List<Integer> amplitudesList = new ArrayList<>();
        timingsList.add(0L); amplitudesList.add(0);
        for (int group = 0; group < groups; group++) {
            for (int pulse = 0; pulse < 3; pulse++) {
                timingsList.add(650L); amplitudesList.add(255);
                if (pulse < 2) { timingsList.add(220L); amplitudesList.add(0); }
            }
            if (group < groups - 1) { timingsList.add(1100L); amplitudesList.add(0); }
        }
        long[] timings = new long[timingsList.size()];
        int[] amplitudes = new int[amplitudesList.size()];
        for (int i = 0; i < timings.length; i++) {
            timings[i] = timingsList.get(i);
            amplitudes[i] = amplitudesList.get(i);
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createWaveform(timings, amplitudes, -1));
        } else {
            vibrator.vibrate(timings, -1);
        }
    }
}
JAVA

python3 - "$SOURCE_B64" "$TARGET_ICON" <<'PY'
import base64,re,sys
from pathlib import Path
raw=base64.b64decode(re.sub(r'\s+','',Path(sys.argv[1]).read_text(encoding='utf-8').strip()),validate=True)
if raw[:8] != b'\x89PNG\r\n\x1a\n': raise SystemExit('dog source is not PNG')
Path(sys.argv[2]).write_bytes(raw)
PY
cat > "$RUNNER_TEMP/CropDog.java" <<'JAVAICON'
import java.awt.*; import java.awt.image.*; import java.io.*; import javax.imageio.*;
public final class CropDog { public static void main(String[] a)throws Exception{BufferedImage s=ImageIO.read(new File(a[0]));if(s==null||s.getWidth()!=128||s.getHeight()!=152)throw new RuntimeException("dog source size");BufferedImage c=s.getSubimage(16,56,96,96),o=new BufferedImage(128,128,BufferedImage.TYPE_INT_ARGB);Graphics2D g=o.createGraphics();g.setRenderingHint(RenderingHints.KEY_INTERPOLATION,RenderingHints.VALUE_INTERPOLATION_BICUBIC);g.drawImage(c,0,0,128,128,null);g.dispose();ImageIO.write(o,"png",new File(a[0]));}}
JAVAICON
javac "$RUNNER_TEMP/CropDog.java"
java -cp "$RUNNER_TEMP" CropDog "$TARGET_ICON"
cp "$TARGET_ICON" "$RUNNER_TEMP/dog-ref.png"
rm -f "$SOURCE_B64"

base64 --decode signing/jayuminton-release.keystore.b64 > signing/jayuminton-release.jks
test -s signing/jayuminton-release.jks

gradle --no-daemon clean assembleRelease
APK="app/build/outputs/apk/release/app-release.apk"
test -s "$APK"
BUILD_TOOLS="$(find "$ANDROID_HOME/build-tools" -mindepth 1 -maxdepth 1 -type d | sort -V | tail -1)"
AAPT="$BUILD_TOOLS/aapt"; APKSIGNER="$BUILD_TOOLS/apksigner"
"$APKSIGNER" verify --verbose --print-certs "$APK" > "$RUNNER_TEMP/apksigner.txt"
"$AAPT" dump badging "$APK" > "$RUNNER_TEMP/badging.txt"
"$AAPT" dump xmltree "$APK" AndroidManifest.xml > "$RUNNER_TEMP/manifest-tree.txt"

grep -F "package: name='com.jayuminton.user' versionCode='110' versionName='1.1.0'" "$RUNNER_TEMP/badging.txt" >/dev/null
grep -F "application-label:'자유민턴 코트현황'" "$RUNNER_TEMP/badging.txt" >/dev/null
grep -F 'android.permission.POST_NOTIFICATIONS' "$RUNNER_TEMP/manifest-tree.txt" >/dev/null
grep -F 'android.permission.VIBRATE' "$RUNNER_TEMP/manifest-tree.txt" >/dev/null
grep -F 'com.google.firebase.MESSAGING_EVENT' "$RUNNER_TEMP/manifest-tree.txt" >/dev/null

unzip -p "$APK" classes.dex > "$RUNNER_TEMP/classes.dex"
strings "$RUNNER_TEMP/classes.dex" > "$RUNNER_TEMP/classes.txt"
grep -F "$MAIN_DEPLOYMENT_ID" "$RUNNER_TEMP/classes.txt" >/dev/null
grep -F "$PUSH_URL" "$RUNNER_TEMP/classes.txt" >/dev/null
grep -F 'JayumintonUserNative/1.1.0 FreshInstall NativeFCM' "$RUNNER_TEMP/classes.txt" >/dev/null
grep -F 'JayumintonFirebaseMessagingService' "$RUNNER_TEMP/classes.txt" >/dev/null
grep -F 'register_web_token' "$RUNNER_TEMP/classes.txt" >/dev/null
grep -F '650' "$RUNNER_TEMP/classes.txt" >/dev/null
grep -F '255' "$RUNNER_TEMP/classes.txt" >/dev/null
if grep -F '?mode=admin' "$RUNNER_TEMP/classes.txt" >/dev/null; then echo 'admin URL leaked' >&2; exit 1; fi

ICON_PATH="$(sed -n "s/^application-icon-160:'\([^']*\)'.*/\1/p" "$RUNNER_TEMP/badging.txt" | head -1)"
[ -n "$ICON_PATH" ] || ICON_PATH="$(sed -n "s/^application:.* icon='\([^']*\)'.*/\1/p" "$RUNNER_TEMP/badging.txt" | head -1)"
unzip -p "$APK" "$ICON_PATH" > "$RUNNER_TEMP/final-icon.png"
cat > "$RUNNER_TEMP/CompareDog.java" <<'JAVAICON'
import java.awt.image.*;import java.io.*;import javax.imageio.*;public final class CompareDog{public static void main(String[]a)throws Exception{BufferedImage x=ImageIO.read(new File(a[0])),y=ImageIO.read(new File(a[1]));if(x==null||y==null||x.getWidth()!=128||x.getHeight()!=128||y.getWidth()!=128||y.getHeight()!=128)throw new RuntimeException("icon size");for(int j=0;j<128;j++)for(int i=0;i<128;i++)if(x.getRGB(i,j)!=y.getRGB(i,j))throw new RuntimeException("icon mismatch");}}
JAVAICON
javac "$RUNNER_TEMP/CompareDog.java"
java -cp "$RUNNER_TEMP" CompareDog "$RUNNER_TEMP/dog-ref.png" "$RUNNER_TEMP/final-icon.png"

cp "$APK" "$OUT"
APK_SHA="$(sha256sum "$OUT" | awk '{print $1}')"
SIGNER_SHA="$(sed -n -E 's/^.*certificate SHA-256 digest: ([0-9A-Fa-f:]+).*$/\1/p' "$RUNNER_TEMP/apksigner.txt" | head -1 | tr -d ':' | tr '[:lower:]' '[:upper:]')"
test -n "$SIGNER_SHA"
cat > "$STATUS" <<EOF
workflow=Build Jayuminton court status native push fresh install
status=success
version=1.1.0
version_code=110
application_id=$PACKAGE
launcher_label=자유민턴 코트현황
install_mode=uninstall-old-then-fresh-install
native_fcm=yes
android_fcm_priority=high
notification_channel_importance=high
wait1_vibration=3-long-pulses-x3-groups
court_vibration=3-long-pulses-x5-groups
native_vibration_amplitude=255-when-supported
pulse_ms=650
intra_pulse_gap_ms=220
group_gap_ms=1100
notification_permission=android-13-runtime-request
web_storage=fresh-after-uninstall
launcher_icon=dog-full-square-128x128
apk_sha256=$APK_SHA
signer_sha256=$SIGNER_SHA
updated_at=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
EOF
cat "$STATUS"
