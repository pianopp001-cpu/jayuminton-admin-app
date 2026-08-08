#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding='utf-8')

for old, new in (
    ('v1.1.2-fresh-install.apk', 'v1.1.3-fresh-install.apk'),
    ('user-native-push-v1.1.2.txt', 'user-native-push-v1.1.3.txt'),
    ('VERSION="1.1.2"', 'VERSION="1.1.3"'),
    ('VERSION_CODE="112"', 'VERSION_CODE="113"'),
    ('versionCode 112', 'versionCode 113'),
    ("versionCode='112'", "versionCode='113'"),
    ("versionName '1.1.2'", "versionName '1.1.3'"),
    ("versionName='1.1.2'", "versionName='1.1.3'"),
    ('USER_APP_VERSION = "1.1.2"', 'USER_APP_VERSION = "1.1.3"'),
    ('JayumintonUserNative/1.1.2', 'JayumintonUserNative/1.1.3'),
    ("__JAYUMINTON_USER_APK_VERSION__='1.1.2'", "__JAYUMINTON_USER_APK_VERSION__='1.1.3'"),
    ('jayuminton_native_push_v112', 'jayuminton_native_push_v113'),
    ('JayumintonNativeAndroid/1.1.2', 'JayumintonNativeAndroid/1.1.3'),
    ('jayuminton_wait1_native_v112', 'jayuminton_wait1_native_v113'),
    ('jayuminton_court_native_v112', 'jayuminton_court_native_v113'),
    ('version=1.1.2', 'version=1.1.3'),
    ('version_code=112', 'version_code=113'),
    ('__JAYUMINTON_NATIVE_DIRECT_V112__', '__JAYUMINTON_NATIVE_DIRECT_V113__'),
):
    s = s.replace(old, new)

if 'PROBE_JAVA=' not in s:
    s = s.replace(
        'REGISTRAR_JAVA="$JAVA_DIR/NativePushRegistrar.java"',
        'REGISTRAR_JAVA="$JAVA_DIR/NativePushRegistrar.java"\nPROBE_JAVA="$JAVA_DIR/NativeAlertProbe.java"',
        1,
    )

# Expose verified native state and an explicit local alert test to the WebView.
old = '''        @JavascriptInterface public void setVibrationEnabled(boolean enabled) {
            NativePushRegistrar.setVibrationEnabled(MainActivity.this, enabled);
        }
    }'''
new = '''        @JavascriptInterface public void setVibrationEnabled(boolean enabled) {
            NativePushRegistrar.setVibrationEnabled(MainActivity.this, enabled);
        }
        @JavascriptInterface public String getPushRegistrationStatus() {
            return NativePushRegistrar.registrationStatus(MainActivity.this);
        }
        @JavascriptInterface public void testNativeAlert() {
            NativeAlertProbe.show(MainActivity.this, "자유민턴 테스트", "팝업·강한 진동이 정상 작동합니다.", "manual-test");
        }
    }'''
if 'getPushRegistrationStatus()' not in s:
    if old not in s:
        raise SystemExit('native bridge status insertion point missing')
    s = s.replace(old, new, 1)

# Registration verification needs a few standard-library imports only.
old = '''import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;'''
new = '''import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;'''
if 'java.security.MessageDigest' not in s:
    if old not in s:
        raise SystemExit('registrar import insertion point missing')
    s = s.replace(old, new, 1)

old = '''    private static final String KEY_VIBRATION = "vibration_enabled";
    private static final String RELAY_URL = "${PUSH_URL}";'''
new = '''    private static final String KEY_VIBRATION = "vibration_enabled";
    private static final String KEY_REGISTERED = "server_registered";
    private static final String KEY_STATUS = "registration_status";
    private static final String KEY_TESTED_KEY = "tested_registration_key";
    private static final String RELAY_URL = "${PUSH_URL}";'''
if 'KEY_REGISTERED' not in s:
    if old not in s:
        raise SystemExit('registration preference insertion point missing')
    s = s.replace(old, new, 1)

# Any token/member change immediately becomes pending, never a misleading ON state.
old = '''        p.edit().putString(KEY_MEMBER_ID, newId).putString(KEY_MEMBER_NAME, newName).apply();
        if (pushEnabled(app)) {'''
new = '''        p.edit()
                .putString(KEY_MEMBER_ID, newId)
                .putString(KEY_MEMBER_NAME, newName)
                .putBoolean(KEY_REGISTERED, false)
                .putString(KEY_STATUS, "registering")
                .apply();
        if (pushEnabled(app)) {'''
if '.putString(KEY_STATUS, "registering")' not in s:
    if old not in s:
        raise SystemExit('pending registration insertion point missing')
    s = s.replace(old, new, 1)

# Replace blind retries with POST + server token_status verification.
start = s.find('    private static void registerCurrent(Context context) {')
end = s.find('    private static void submitAsync(', start)
if start < 0 or end < 0:
    raise SystemExit('registerCurrent block missing')
replacement = '''    private static void registerCurrent(Context context) {
        Context app = context.getApplicationContext();
        SharedPreferences p = prefs(app);
        final String id = p.getString(KEY_MEMBER_ID, "");
        final String name = p.getString(KEY_MEMBER_NAME, "");
        final String token = p.getString(KEY_TOKEN, "");
        if (id.isEmpty() || token.isEmpty()) return;
        p.edit().putBoolean(KEY_REGISTERED, false).putString(KEY_STATUS, "registering").apply();
        EXECUTOR.execute(() -> {
            boolean verified = false;
            long[] waits = new long[]{0L, 1200L, 3000L, 7000L};
            for (long wait : waits) {
                if (wait > 0L) {
                    try { Thread.sleep(wait); }
                    catch (InterruptedException ignored) { Thread.currentThread().interrupt(); break; }
                }
                submit("register_web_token", id, name, token);
                try { Thread.sleep(500L); }
                catch (InterruptedException ignored) { Thread.currentThread().interrupt(); break; }
                if (verifyRegistered(id, token)) { verified = true; break; }
            }
            SharedPreferences latest = prefs(app);
            latest.edit()
                    .putBoolean(KEY_REGISTERED, verified)
                    .putString(KEY_STATUS, verified ? "connected" : "registration_failed")
                    .apply();
            if (verified) {
                String testedKey = id + ":" + sha256(token);
                if (!testedKey.equals(latest.getString(KEY_TESTED_KEY, ""))) {
                    latest.edit().putString(KEY_TESTED_KEY, testedKey).apply();
                    NativeAlertProbe.show(app, "알림 서버 연결 완료", "다른 앱 사용 중에도 배정 알림을 받을 준비가 됐습니다.", "registration-ready");
                }
            }
        });
    }

    public static String registrationStatus(Context context) {
        SharedPreferences p = prefs(context.getApplicationContext());
        try {
            JSONObject result = new JSONObject();
            result.put("memberId", p.getString(KEY_MEMBER_ID, ""));
            result.put("hasToken", !p.getString(KEY_TOKEN, "").isEmpty());
            result.put("registered", p.getBoolean(KEY_REGISTERED, false));
            result.put("status", p.getString(KEY_STATUS, "not_started"));
            result.put("pushEnabled", p.getBoolean(KEY_PUSH, true));
            result.put("vibrationEnabled", p.getBoolean(KEY_VIBRATION, true));
            return result.toString();
        } catch (Exception error) {
            return "{\\"status\\":\\"error\\"}";
        }
    }

    private static boolean verifyRegistered(String memberId, String token) {
        HttpURLConnection connection = null;
        try {
            String callback = "nativeStatus";
            String target = RELAY_URL + (RELAY_URL.contains("?") ? "&" : "?")
                    + "action=token_status&memberId=" + URLEncoder.encode(memberId, "UTF-8")
                    + "&tokenHash=" + URLEncoder.encode(sha256(token), "UTF-8")
                    + "&callback=" + callback;
            connection = (HttpURLConnection) new URL(target).openConnection();
            connection.setConnectTimeout(12000);
            connection.setReadTimeout(12000);
            connection.setRequestMethod("GET");
            int code = connection.getResponseCode();
            if (code < 200 || code >= 400) return false;
            InputStream input = connection.getInputStream();
            BufferedReader reader = new BufferedReader(new InputStreamReader(input, StandardCharsets.UTF_8));
            StringBuilder body = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) body.append(line);
            reader.close();
            String value = body.toString().replace(" ", "").replace("\\n", "").replace("\\r", "");
            return value.contains("\\\"registered\\\":true") || value.contains("registered:true");
        } catch (Exception ignored) {
            return false;
        } finally {
            if (connection != null) connection.disconnect();
        }
    }

    private static String sha256(String value) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] bytes = digest.digest(String.valueOf(value).getBytes(StandardCharsets.UTF_8));
            StringBuilder hex = new StringBuilder();
            for (byte item : bytes) hex.append(String.format("%02x", item & 0xff));
            return hex.toString();
        } catch (Exception ignored) {
            return "";
        }
    }

'''
s = s[:start] + replacement + s[end:]

# Add a native local test notification/vibrator. It is called only after the
# server confirms the member/token registration, and is also callable manually.
probe_anchor = 'cat > "$SERVICE_JAVA" <<\'JAVA\'\n'
probe = r'''cat > "$PROBE_JAVA" <<'JAVA'
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

public final class NativeAlertProbe {
    private static final String CHANNEL = "jayuminton_ready_test_v113";
    private NativeAlertProbe() {}

    public static void show(Context source, String title, String body, String key) {
        Context context = source.getApplicationContext();
        NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager != null) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                NotificationChannel channel = new NotificationChannel(CHANNEL, "알림 연결 확인", NotificationManager.IMPORTANCE_HIGH);
                channel.enableVibration(true);
                channel.setVibrationPattern(new long[]{0, 900, 250, 900, 250, 900});
                Uri sound = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);
                AudioAttributes attrs = new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_NOTIFICATION_EVENT).build();
                channel.setSound(sound, attrs);
                manager.createNotificationChannel(channel);
            }
            Intent intent = new Intent(context, MainActivity.class);
            intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
            PendingIntent pending = PendingIntent.getActivity(context, key.hashCode(), intent,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            Notification.Builder builder = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                    ? new Notification.Builder(context, CHANNEL) : new Notification.Builder(context);
            builder.setSmallIcon(R.drawable.icon).setContentTitle(title).setContentText(body)
                    .setStyle(new Notification.BigTextStyle().bigText(body)).setContentIntent(pending)
                    .setAutoCancel(true).setCategory(Notification.CATEGORY_STATUS)
                    .setVisibility(Notification.VISIBILITY_PUBLIC).setWhen(System.currentTimeMillis());
            if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) builder.setPriority(Notification.PRIORITY_MAX);
            manager.notify(key.hashCode(), builder.build());
        }
        Vibrator vibrator;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            VibratorManager vm = (VibratorManager) context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE);
            vibrator = vm == null ? null : vm.getDefaultVibrator();
        } else vibrator = (Vibrator) context.getSystemService(Context.VIBRATOR_SERVICE);
        if (vibrator != null && vibrator.hasVibrator()) {
            long[] timing = new long[]{0, 900, 250, 900, 250, 900};
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator.vibrate(VibrationEffect.createWaveform(timing, new int[]{0,255,0,255,0,255}, -1));
            } else vibrator.vibrate(timing, -1);
        }
    }
}
JAVA

'''
if 'class NativeAlertProbe' not in s:
    if probe_anchor not in s:
        raise SystemExit('native probe insertion point missing')
    s = s.replace(probe_anchor, probe + probe_anchor, 1)

required = (
    'v1.1.3-fresh-install.apk', 'VERSION="1.1.3"', 'VERSION_CODE="113"',
    'getPushRegistrationStatus()', 'verifyRegistered(String memberId, String token)',
    'class NativeAlertProbe', 'registration-ready', 'jayuminton_wait1_native_v113',
    'jayuminton_court_native_v113',
)
for marker in required:
    if marker not in s:
        raise SystemExit('missing native v1.1.3 marker: ' + marker)

path.write_text(s, encoding='utf-8')
print('Prepared native v1.1.3 with verified registration and local alert probe.')
