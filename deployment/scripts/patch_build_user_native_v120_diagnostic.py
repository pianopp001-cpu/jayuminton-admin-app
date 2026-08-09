#!/usr/bin/env python3
from pathlib import Path
import sys


path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

for old, new in (
    ("v1.1.9-fresh-install.apk", "v1.2.0-diagnostic.apk"),
    ("user-native-push-v1.1.9.txt", "user-native-push-v1.2.0-diagnostic.txt"),
    ('VERSION="1.1.9"', 'VERSION="1.2.0"'),
    ('VERSION_CODE="119"', 'VERSION_CODE="120"'),
    ("versionCode 119", "versionCode 120"),
    ("versionCode='119'", "versionCode='120'"),
    ("versionName '1.1.9'", "versionName '1.2.0'"),
    ("versionName='1.1.9'", "versionName='1.2.0'"),
    ('USER_APP_VERSION = "1.1.9"', 'USER_APP_VERSION = "1.2.0"'),
    ("JayumintonUserNative/1.1.9", "JayumintonUserNative/1.2.0"),
    ("JayumintonNativeAndroid/1.1.9", "JayumintonNativeAndroid/1.2.0"),
    ("version=1.1.9", "version=1.2.0"),
    ("version_code=119", "version_code=120"),
    ("jayuminton_wait1_native_v119", "jayuminton_wait1_native_v120_diag"),
    ("jayuminton_court_native_v119", "jayuminton_court_native_v120_diag"),
    ("jayuminton_wait1_system_v119", "jayuminton_wait1_system_v120_diag"),
    ("jayuminton_court_system_v119", "jayuminton_court_system_v120_diag"),
):
    s = s.replace(old, new)

s = s.replace(
    'DISMISS_JAVA="$JAVA_DIR/AlertDismissReceiver.java"',
    'DISMISS_JAVA="$JAVA_DIR/AlertDismissReceiver.java"\n'
    'REPORTER_JAVA="$JAVA_DIR/NativeDeliveryReporter.java"',
    1,
)

service_anchor = 'cat > "$SERVICE_JAVA" <<\'JAVA\'\n'
reporter_java = r'''cat > "$REPORTER_JAVA" <<JAVA
package com.jayuminton.admin;

import android.net.Uri;

import org.json.JSONObject;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class NativeDeliveryReporter {
    private static final String RELAY_URL = "${PUSH_URL}";
    private static final String APP_VERSION = "1.2.0";
    private static final ExecutorService EXECUTOR = Executors.newSingleThreadExecutor();

    private NativeDeliveryReporter() {}

    public static void report(String stage, String eventType, boolean hasTargetMemberId,
                              boolean selectedMemberMatches, boolean notificationPosted,
                              boolean fullScreenAllowed, boolean vibrationCancelled) {
        EXECUTOR.execute(() -> {
            HttpURLConnection connection = null;
            try {
                JSONObject payload = new JSONObject();
                payload.put("action", "native_delivery_ack");
                payload.put("stage", stage == null ? "" : stage);
                payload.put("appVersion", APP_VERSION);
                payload.put("eventType", eventType == null ? "" : eventType);
                payload.put("hasTargetMemberId", hasTargetMemberId);
                payload.put("selectedMemberMatches", selectedMemberMatches);
                payload.put("notificationPosted", notificationPosted);
                payload.put("fullScreenAllowed", fullScreenAllowed);
                payload.put("vibrationCancelled", vibrationCancelled);
                byte[] bytes = ("payload=" + Uri.encode(payload.toString())).getBytes(StandardCharsets.UTF_8);
                connection = (HttpURLConnection) new URL(RELAY_URL).openConnection();
                connection.setConnectTimeout(10000);
                connection.setReadTimeout(10000);
                connection.setRequestMethod("POST");
                connection.setInstanceFollowRedirects(false);
                connection.setDoOutput(true);
                connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded;charset=UTF-8");
                connection.setFixedLengthStreamingMode(bytes.length);
                try (OutputStream output = connection.getOutputStream()) { output.write(bytes); }
                connection.getResponseCode();
            } catch (Exception ignored) {
            } finally {
                if (connection != null) connection.disconnect();
            }
        });
    }
}
JAVA

'''
if s.count(service_anchor) != 1:
    raise SystemExit("v120 reporter insertion point missing")
s = s.replace(service_anchor, reporter_java + service_anchor, 1)

old = '''        String targetMemberId = value(data, "memberId", "");
        if (!targetMemberId.isEmpty() && !NativePushRegistrar.isCurrentMember(this, targetMemberId)) return;
        String courtNo = value(data, "courtNo", "");'''
new = '''        String targetMemberId = value(data, "memberId", "");
        boolean hasTargetMemberId = !targetMemberId.isEmpty();
        boolean selectedMemberMatches = !hasTargetMemberId || NativePushRegistrar.isCurrentMember(this, targetMemberId);
        NativeDeliveryReporter.report("fcm_received", type, hasTargetMemberId,
                selectedMemberMatches, false, false, false);
        if (!selectedMemberMatches) {
            NativeDeliveryReporter.report("member_rejected", type, true, false, false, false, false);
            return;
        }
        NativeDeliveryReporter.report("member_accepted", type, hasTargetMemberId,
                true, false, false, false);
        String courtNo = value(data, "courtNo", "");'''
if s.count(old) != 1:
    raise SystemExit("v120 FCM receive reporter insertion point missing")
s = s.replace(old, new, 1)

old = '''        showNotification(court, title, body, assignmentId);
        vibrateStrong(court ? 5 : 3);'''
new = '''        showNotification(court, title, body, assignmentId);
        boolean fullScreenAllowed = true;
        if (Build.VERSION.SDK_INT >= 34) {
            NotificationManager notificationManager =
                    (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
            fullScreenAllowed = notificationManager != null && notificationManager.canUseFullScreenIntent();
        }
        NativeDeliveryReporter.report("notification_posted", type, hasTargetMemberId,
                true, true, fullScreenAllowed, false);
        // Diagnostic build uses a finite waveform so a blocked button can never
        // leave the tester with an unstoppable vibration.
        vibrateStrong(court ? 5 : 3);'''
if s.count(old) != 1:
    raise SystemExit("v120 notification reporter insertion point missing")
s = s.replace(old, new, 1)

# Diagnostic build is deliberately finite. The final build restores repeating
# vibration only after a real dismiss acknowledgement has been observed.
s = s.replace(
    'VibrationEffect.createWaveform(timings, amplitudes, 0),\n                    vibrationAttributes',
    'VibrationEffect.createWaveform(timings, amplitudes, -1),\n                    vibrationAttributes',
    1,
)
s = s.replace('vibrator.vibrate(timings, 0);', 'vibrator.vibrate(timings, -1);', 1)

# Record dismissal from the notification action or swipe-delete receiver.
old = '''        if (vibrator != null) vibrator.cancel();
    }
}
JAVA'''
new = '''        if (vibrator != null) vibrator.cancel();
        NativeDeliveryReporter.report("vibration_cancelled", "", false,
                true, true, false, true);
    }
}
JAVA'''
if s.count(old) < 1:
    raise SystemExit("v120 dismiss acknowledgement insertion point missing")
# First occurrence after receiver source, not the later Activity source.
receiver_start = s.find("public final class AlertDismissReceiver")
receiver_end = s.find("\nJAVA", receiver_start)
segment = s[receiver_start:receiver_end]
if "NativeDeliveryReporter.report" not in segment:
    segment = segment.replace(
        '        if (vibrator != null) vibrator.cancel();',
        '        if (vibrator != null) vibrator.cancel();\n'
        '        NativeDeliveryReporter.report("vibration_cancelled", "", false,\n'
        '                true, true, false, true);',
        1,
    )
    s = s[:receiver_start] + segment + s[receiver_end:]

for marker in (
    'VERSION="1.2.0"', 'VERSION_CODE="120"',
    'class NativeDeliveryReporter',
    '"action", "native_delivery_ack"',
    'NativeDeliveryReporter.report("fcm_received"',
    'NativeDeliveryReporter.report("notification_posted"',
    'notificationManager.canUseFullScreenIntent()',
    'NativeDeliveryReporter.report("vibration_cancelled"',
    'VibrationEffect.createWaveform(timings, amplitudes, -1)',
    '"확인 · 진동 끄기"',
):
    if marker not in s:
        raise SystemExit("missing native v1.2.0 diagnostic marker: " + marker)

path.write_text(s, encoding="utf-8")
print("Prepared safe v1.2.0 native delivery diagnostic APK.")
