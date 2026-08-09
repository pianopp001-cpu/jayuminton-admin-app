#!/usr/bin/env python3
from pathlib import Path
import sys


path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

for old, new in (
    ("v1.1.8-fresh-install.apk", "v1.1.9-fresh-install.apk"),
    ("user-native-push-v1.1.8.txt", "user-native-push-v1.1.9.txt"),
    ('VERSION="1.1.8"', 'VERSION="1.1.9"'),
    ('VERSION_CODE="118"', 'VERSION_CODE="119"'),
    ("versionCode 118", "versionCode 119"),
    ("versionCode='118'", "versionCode='119'"),
    ("versionName '1.1.8'", "versionName '1.1.9'"),
    ("versionName='1.1.8'", "versionName='1.1.9'"),
    ('USER_APP_VERSION = "1.1.8"', 'USER_APP_VERSION = "1.1.9"'),
    ("JayumintonUserNative/1.1.8", "JayumintonUserNative/1.1.9"),
    ("JayumintonNativeAndroid/1.1.8", "JayumintonNativeAndroid/1.1.9"),
    ("version=1.1.8", "version=1.1.9"),
    ("version_code=118", "version_code=119"),
    ("jayuminton_wait1_native_v118", "jayuminton_wait1_native_v119"),
    ("jayuminton_court_native_v118", "jayuminton_court_native_v119"),
    ("jayuminton_wait1_system_v118", "jayuminton_wait1_system_v119"),
    ("jayuminton_court_system_v118", "jayuminton_court_system_v119"),
):
    s = s.replace(old, new)

s = s.replace(
    'ALERT_JAVA="$JAVA_DIR/AssignmentAlertActivity.java"',
    'ALERT_JAVA="$JAVA_DIR/AssignmentAlertActivity.java"\n'
    'DISMISS_JAVA="$JAVA_DIR/AlertDismissReceiver.java"',
    1,
)

manifest_anchor = '''        <activity
            android:name=".AssignmentAlertActivity"'''
manifest_replacement = '''        <receiver
            android:name=".AlertDismissReceiver"
            android:exported="false" />

        <activity
            android:name=".AssignmentAlertActivity"'''
if s.count(manifest_anchor) != 1:
    raise SystemExit("v119 dismiss receiver manifest insertion point missing")
s = s.replace(manifest_anchor, manifest_replacement, 1)

service_anchor = 'cat > "$SERVICE_JAVA" <<\'JAVA\'\n'
receiver_java = r'''cat > "$DISMISS_JAVA" <<'JAVA'
package com.jayuminton.admin;

import android.app.NotificationManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.Vibrator;
import android.os.VibratorManager;

public final class AlertDismissReceiver extends BroadcastReceiver {
    public static final String EXTRA_NOTIFICATION_ID = "dismiss_notification_id";
    public static final String ACTION_DISMISS = "com.jayuminton.user.DISMISS_ASSIGNMENT_ALERT";

    @Override public void onReceive(Context context, Intent intent) {
        NotificationManager notifications =
                (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        int notificationId = intent == null ? 0 : intent.getIntExtra(EXTRA_NOTIFICATION_ID, 0);
        if (notifications != null) {
            if (notificationId != 0) notifications.cancel(notificationId);
            else notifications.cancelAll();
        }

        Vibrator vibrator;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            VibratorManager manager =
                    (VibratorManager) context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE);
            vibrator = manager == null ? null : manager.getDefaultVibrator();
        } else {
            vibrator = (Vibrator) context.getSystemService(Context.VIBRATOR_SERVICE);
        }
        if (vibrator != null) vibrator.cancel();
    }
}
JAVA

'''
if s.count(service_anchor) != 1:
    raise SystemExit("v119 dismiss receiver source insertion point missing")
s = s.replace(service_anchor, receiver_java + service_anchor, 1)

pending_anchor = '''        PendingIntent pending = PendingIntent.getActivity(
                this,
                notificationId,
                alertIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );'''
pending_replacement = pending_anchor + '''
        Intent dismissIntent = new Intent(this, AlertDismissReceiver.class);
        dismissIntent.setAction(AlertDismissReceiver.ACTION_DISMISS + "." + assignmentId);
        dismissIntent.putExtra(AlertDismissReceiver.EXTRA_NOTIFICATION_ID, notificationId);
        PendingIntent dismissPending = PendingIntent.getBroadcast(
                this,
                notificationId,
                dismissIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );'''
if s.count(pending_anchor) != 1:
    raise SystemExit("v119 notification dismiss action insertion point missing")
s = s.replace(pending_anchor, pending_replacement, 1)

builder_anchor = '''                .setContentIntent(pending)
                .setFullScreenIntent(pending, true)
                .setAutoCancel(false)'''
builder_replacement = '''                .setContentIntent(pending)
                .setFullScreenIntent(pending, true)
                .setDeleteIntent(dismissPending)
                .addAction(new Notification.Action.Builder(
                        android.R.drawable.ic_menu_close_clear_cancel,
                        "확인 · 진동 끄기",
                        dismissPending
                ).build())
                .setAutoCancel(false)'''
if s.count(builder_anchor) != 1:
    raise SystemExit("v119 notification builder action insertion point missing")
s = s.replace(builder_anchor, builder_replacement, 1)

for marker in (
    'VERSION="1.1.9"', 'VERSION_CODE="119"',
    'JayumintonNativeAndroid/1.1.9',
    'class AlertDismissReceiver extends BroadcastReceiver',
    'android:name=".AlertDismissReceiver"',
    '"확인 · 진동 끄기"',
    '.setDeleteIntent(dismissPending)',
    'PendingIntent.getBroadcast(',
    'if (vibrator != null) vibrator.cancel();',
    '"대기 1순위입니다. 라켓 들고 준비하세요."',
    'VibrationEffect.createWaveform(timings, amplitudes, 0)',
):
    if marker not in s:
        raise SystemExit("missing native v1.1.9 marker: " + marker)

path.write_text(s, encoding="utf-8")
print("Prepared v1.1.9 with always-available notification stop action.")
