#!/usr/bin/env python3
from pathlib import Path
import sys


path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

for old, new in (
    ("v1.1.6-fresh-install.apk", "v1.1.7-fresh-install.apk"),
    ("user-native-push-v1.1.6.txt", "user-native-push-v1.1.7.txt"),
    ('VERSION="1.1.6"', 'VERSION="1.1.7"'),
    ('VERSION_CODE="116"', 'VERSION_CODE="117"'),
    ("versionCode 116", "versionCode 117"),
    ("versionCode='116'", "versionCode='117'"),
    ("versionName '1.1.6'", "versionName '1.1.7'"),
    ("versionName='1.1.6'", "versionName='1.1.7'"),
    ('USER_APP_VERSION = "1.1.6"', 'USER_APP_VERSION = "1.1.7"'),
    ("JayumintonUserNative/1.1.6", "JayumintonUserNative/1.1.7"),
    ("JayumintonNativeAndroid/1.1.6", "JayumintonNativeAndroid/1.1.7"),
    ("version=1.1.6", "version=1.1.7"),
    ("version_code=116", "version_code=117"),
    ("jayuminton_wait1_native_v114", "jayuminton_wait1_native_v117"),
    ("jayuminton_court_native_v114", "jayuminton_court_native_v117"),
    ("jayuminton_wait1_system_v116", "jayuminton_wait1_system_v117"),
    ("jayuminton_court_system_v116", "jayuminton_court_system_v117"),
):
    s = s.replace(old, new)

s = s.replace(
    'SERVICE_JAVA="$JAVA_DIR/JayumintonFirebaseMessagingService.java"',
    'SERVICE_JAVA="$JAVA_DIR/JayumintonFirebaseMessagingService.java"\n'
    'ALERT_JAVA="$JAVA_DIR/AssignmentAlertActivity.java"',
    1,
)

old = '    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />'
new = old + '\n    <uses-permission android:name="android.permission.USE_FULL_SCREEN_INTENT" />'
if s.count(old) != 1:
    raise SystemExit("full-screen permission insertion point missing")
s = s.replace(old, new, 1)

anchor = '''        <service
            android:name=".JayumintonFirebaseMessagingService"'''
activity = '''        <activity
            android:name=".AssignmentAlertActivity"
            android:exported="false"
            android:excludeFromRecents="true"
            android:showWhenLocked="true"
            android:turnScreenOn="true"
            android:taskAffinity=""
            android:theme="@android:style/Theme.Material.Light.Dialog.Alert" />

        <service
            android:name=".JayumintonFirebaseMessagingService"'''
if s.count(anchor) != 1:
    raise SystemExit("alert activity manifest insertion point missing")
s = s.replace(anchor, activity, 1)

service_anchor = 'cat > "$SERVICE_JAVA" <<\'JAVA\'\n'
alert_java = r'''cat > "$ALERT_JAVA" <<'JAVA'
package com.jayuminton.admin;

import android.app.Activity;
import android.app.NotificationManager;
import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Build;
import android.os.Bundle;
import android.os.Vibrator;
import android.os.VibratorManager;
import android.view.Gravity;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public final class AssignmentAlertActivity extends Activity {
    public static final String EXTRA_TITLE = "assignment_title";
    public static final String EXTRA_BODY = "assignment_body";
    public static final String EXTRA_NOTIFICATION_ID = "assignment_notification_id";
    private int notificationId;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().addFlags(
                WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON |
                WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED |
                WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON
        );
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true);
            setTurnScreenOn(true);
        }
        notificationId = getIntent().getIntExtra(EXTRA_NOTIFICATION_ID, 0);
        String title = getIntent().getStringExtra(EXTRA_TITLE);
        String body = getIntent().getStringExtra(EXTRA_BODY);

        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setGravity(Gravity.CENTER);
        panel.setPadding(56, 52, 56, 40);
        panel.setBackgroundColor(Color.WHITE);

        TextView heading = new TextView(this);
        heading.setText(title == null ? "자유민턴 순서 알림" : title);
        heading.setTextSize(25);
        heading.setTextColor(Color.rgb(15, 50, 120));
        heading.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        heading.setGravity(Gravity.CENTER);
        panel.addView(heading, new LinearLayout.LayoutParams(-1, -2));

        TextView message = new TextView(this);
        message.setText(body == null ? "순서를 확인해 주세요." : body);
        message.setTextSize(20);
        message.setTextColor(Color.BLACK);
        message.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams messageParams = new LinearLayout.LayoutParams(-1, -2);
        messageParams.setMargins(0, 34, 0, 38);
        panel.addView(message, messageParams);

        Button confirm = new Button(this);
        confirm.setText("확인하고 닫기");
        confirm.setTextSize(18);
        confirm.setOnClickListener(view -> dismissAlert());
        panel.addView(confirm, new LinearLayout.LayoutParams(-1, -2));
        setContentView(panel);
    }

    private void dismissAlert() {
        NotificationManager manager = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager != null && notificationId != 0) manager.cancel(notificationId);
        Vibrator vibrator;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            VibratorManager vm = (VibratorManager) getSystemService(Context.VIBRATOR_MANAGER_SERVICE);
            vibrator = vm == null ? null : vm.getDefaultVibrator();
        } else {
            vibrator = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
        }
        if (vibrator != null) vibrator.cancel();
        finishAndRemoveTask();
    }

    @Override public void onBackPressed() { dismissAlert(); }
}
JAVA

'''
if s.count(service_anchor) != 1:
    raise SystemExit("alert activity source insertion point missing")
s = s.replace(service_anchor, alert_java + service_anchor, 1)

old = '''        // Sound/TTS and vibration are deliberately independent.  Start the
        // device vibrator first and never suppress a real assignment vibration
        // because a stale WebView preference failed to synchronize.
        vibrateStrong(court ? 5 : 3);
        showNotification(court, title, body, assignmentId);'''
new = '''        // Post a non-vibrating persistent/full-screen notification first.
        // Then start one explicit waveform so the notification subsystem cannot
        // replace the intended 3-group/5-group vibration with a short pattern.
        showNotification(court, title, body, assignmentId);
        vibrateStrong(court ? 5 : 3);'''
if s.count(old) != 1:
    raise SystemExit("notification/vibration ordering point missing")
s = s.replace(old, new, 1)

old = '''            channel.enableVibration(true);
            channel.setVibrationPattern(new long[]{0, 650, 220, 650, 220, 650});'''
new = '''            // Vibration is executed explicitly after notify(); disabling the
            // channel waveform prevents Android from cancelling the long one.
            channel.enableVibration(false);
            channel.setVibrationPattern(null);'''
if s.count(old) != 1:
    raise SystemExit("channel vibration cancellation point missing")
s = s.replace(old, new, 1)

old = '''        Intent intent = new Intent(this, MainActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent pending = PendingIntent.getActivity(
                this,
                assignmentId.hashCode(),
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );'''
new = '''        int notificationId = assignmentId.hashCode();
        Intent alertIntent = new Intent(this, AssignmentAlertActivity.class);
        alertIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        alertIntent.putExtra(AssignmentAlertActivity.EXTRA_TITLE,
                (court ? "코트 입장 안내" : "대기 1순위 안내"));
        alertIntent.putExtra(AssignmentAlertActivity.EXTRA_BODY, body);
        alertIntent.putExtra(AssignmentAlertActivity.EXTRA_NOTIFICATION_ID, notificationId);
        PendingIntent pending = PendingIntent.getActivity(
                this,
                notificationId,
                alertIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );'''
if s.count(old) != 1:
    raise SystemExit("persistent alert pending intent point missing")
s = s.replace(old, new, 1)

old = '''                .setContentIntent(pending)
                .setAutoCancel(true)
                .setCategory(court ? Notification.CATEGORY_EVENT : Notification.CATEGORY_STATUS)'''
new = '''                .setContentIntent(pending)
                .setFullScreenIntent(pending, true)
                .setAutoCancel(false)
                .setOngoing(true)
                .setCategory(Notification.CATEGORY_ALARM)'''
if s.count(old) != 1:
    raise SystemExit("persistent full-screen notification builder point missing")
s = s.replace(old, new, 1)
s = s.replace('manager.notify(assignmentId.hashCode(), builder.build());',
              'manager.notify(notificationId, builder.build());', 1)

for marker in (
    'VERSION="1.1.7"', 'VERSION_CODE="117"',
    'android.permission.USE_FULL_SCREEN_INTENT',
    'class AssignmentAlertActivity',
    '.setFullScreenIntent(pending, true)',
    '.setOngoing(true)',
    'channel.enableVibration(false)',
    'showNotification(court, title, body, assignmentId);\n        vibrateStrong(court ? 5 : 3);',
    'AudioAttributes.USAGE_ALARM',
):
    if marker not in s:
        raise SystemExit("missing native v1.1.7 marker: " + marker)

path.write_text(s, encoding="utf-8")
print("Prepared v1.1.7 persistent alert with uncancelled explicit vibration.")
