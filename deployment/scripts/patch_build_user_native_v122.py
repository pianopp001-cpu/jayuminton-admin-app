#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

for old, new in (
    ("v1.2.1-fresh-install.apk", "v1.2.2-overlay.apk"),
    ("user-native-push-v1.2.1.txt", "user-native-push-v1.2.2.txt"),
    ('VERSION="1.2.1"', 'VERSION="1.2.2"'),
    ('VERSION_CODE="121"', 'VERSION_CODE="122"'),
    ("versionCode 121", "versionCode 122"),
    ("versionCode='121'", "versionCode='122'"),
    ("versionName '1.2.1'", "versionName '1.2.2'"),
    ("versionName='1.2.1'", "versionName='1.2.2'"),
    ('USER_APP_VERSION = "1.2.1"', 'USER_APP_VERSION = "1.2.2"'),
    ("JayumintonUserNative/1.2.1", "JayumintonUserNative/1.2.2"),
    ("JayumintonNativeAndroid/1.2.1", "JayumintonNativeAndroid/1.2.2"),
    ('APP_VERSION = "1.2.1"', 'APP_VERSION = "1.2.2"'),
    ("version=1.2.1", "version=1.2.2"),
    ("version_code=121", "version_code=122"),
    ("jayuminton_wait1_native_v121", "jayuminton_wait1_native_v122"),
    ("jayuminton_court_native_v121", "jayuminton_court_native_v122"),
):
    s = s.replace(old, new)

# A notification full-screen intent is not guaranteed while another app is open.
# A user-approved application overlay is the reliable center-screen stop UI.
permission_anchor = '    <uses-permission android:name="android.permission.USE_FULL_SCREEN_INTENT" />'
if s.count(permission_anchor) != 1:
    raise SystemExit("v122 overlay permission anchor missing")
s = s.replace(permission_anchor, permission_anchor +
              '\n    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />', 1)

s = s.replace(
    'ALERT_JAVA="$JAVA_DIR/AssignmentAlertActivity.java"',
    'ALERT_JAVA="$JAVA_DIR/AssignmentAlertActivity.java"\n'
    'OVERLAY_JAVA="$JAVA_DIR/AssignmentOverlay.java"',
    1,
)

# Ask for exactly the permission that makes the center popup deterministic.
old = '''        requestFullScreenAlertAccessIfNeeded();
        syncSelectedMemberFromWebStorage();'''
new = '''        requestOverlayAlertAccessIfNeeded();
        syncSelectedMemberFromWebStorage();'''
if s.count(old) != 1:
    raise SystemExit("v122 resume permission call anchor missing")
s = s.replace(old, new, 1)

method_anchor = '    private void requestFullScreenAlertAccessIfNeeded() {'
overlay_method = '''    private void requestOverlayAlertAccessIfNeeded() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.M || Settings.canDrawOverlays(this) || fullScreenPromptShown) return;
        fullScreenPromptShown = true;
        new AlertDialog.Builder(this)
                .setTitle("중앙 알림 표시 권한")
                .setMessage("다른 앱을 사용 중이어도 화면 중앙에 '확인하고 닫기' 버튼을 띄우려면 다음 화면에서 '다른 앱 위에 표시'를 허용해 주세요.")
                .setCancelable(false)
                .setPositiveButton("권한 설정 열기", (dialog, which) -> {
                    Intent intent = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                            Uri.parse("package:" + getPackageName()));
                    startActivity(intent);
                })
                .setNegativeButton("나중에", null)
                .show();
    }

'''
if s.count(method_anchor) != 1:
    raise SystemExit("v122 overlay request insertion anchor missing")
s = s.replace(method_anchor, overlay_method + method_anchor, 1)

service_anchor = "cat > \"$SERVICE_JAVA\" <<'JAVA'\n"
overlay_java = r'''cat > "$OVERLAY_JAVA" <<'JAVA'
package com.jayuminton.admin;

import android.app.NotificationManager;
import android.content.Context;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.Typeface;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.os.Vibrator;
import android.os.VibratorManager;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public final class AssignmentOverlay {
    private static final Handler MAIN = new Handler(Looper.getMainLooper());
    private static WindowManager windowManager;
    private static View activeView;

    private AssignmentOverlay() {}

    public static boolean canShow(Context context) {
        return Build.VERSION.SDK_INT < Build.VERSION_CODES.M || Settings.canDrawOverlays(context);
    }

    public static boolean show(Context context, String title, String body, int notificationId) {
        Context app = context.getApplicationContext();
        if (!canShow(app)) return false;
        MAIN.post(() -> {
            dismissOnly();
            windowManager = (WindowManager) app.getSystemService(Context.WINDOW_SERVICE);
            if (windowManager == null) return;

            LinearLayout panel = new LinearLayout(app);
            panel.setOrientation(LinearLayout.VERTICAL);
            panel.setGravity(Gravity.CENTER);
            panel.setPadding(56, 50, 56, 42);
            panel.setBackgroundColor(Color.WHITE);

            TextView heading = new TextView(app);
            heading.setText(title);
            heading.setTextSize(25);
            heading.setTextColor(Color.rgb(12, 49, 126));
            heading.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
            heading.setGravity(Gravity.CENTER);
            panel.addView(heading, new LinearLayout.LayoutParams(-1, -2));

            TextView message = new TextView(app);
            message.setText(body);
            message.setTextSize(21);
            message.setTextColor(Color.BLACK);
            message.setGravity(Gravity.CENTER);
            LinearLayout.LayoutParams messageParams = new LinearLayout.LayoutParams(-1, -2);
            messageParams.setMargins(0, 32, 0, 38);
            panel.addView(message, messageParams);

            Button confirm = new Button(app);
            confirm.setText("확인하고 닫기");
            confirm.setTextSize(19);
            confirm.setOnClickListener(view -> stopEverything(app, notificationId));
            panel.addView(confirm, new LinearLayout.LayoutParams(-1, -2));

            int type = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                    ? WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                    : WindowManager.LayoutParams.TYPE_PHONE;
            WindowManager.LayoutParams params = new WindowManager.LayoutParams(
                    -1, -2, type,
                    WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON |
                            WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED,
                    PixelFormat.TRANSLUCENT);
            params.gravity = Gravity.CENTER;
            activeView = panel;
            try { windowManager.addView(panel, params); }
            catch (Exception ignored) { activeView = null; }
        });
        return true;
    }

    public static void stopEverything(Context context, int notificationId) {
        dismissOnly();
        NotificationManager notifications =
                (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (notifications != null) {
            if (notificationId != 0) notifications.cancel(notificationId);
            else notifications.cancelAll();
        }
        Vibrator vibrator;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            VibratorManager vm = (VibratorManager) context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE);
            vibrator = vm == null ? null : vm.getDefaultVibrator();
        } else {
            vibrator = (Vibrator) context.getSystemService(Context.VIBRATOR_SERVICE);
        }
        if (vibrator != null) vibrator.cancel();
        NativeDeliveryReporter.report("vibration_cancelled", "", false,
                true, true, true, true);
    }

    public static void dismissOnly() {
        MAIN.post(() -> {
            if (windowManager != null && activeView != null) {
                try { windowManager.removeView(activeView); } catch (Exception ignored) {}
            }
            activeView = null;
        });
    }
}
JAVA

'''
if s.count(service_anchor) != 1:
    raise SystemExit("v122 overlay source insertion anchor missing")
s = s.replace(service_anchor, overlay_java + service_anchor, 1)

# The receiver also removes a currently visible overlay.
receiver_cancel = '        if (vibrator != null) vibrator.cancel();\n        NativeDeliveryReporter.report("vibration_cancelled"'
receiver_replacement = '        if (vibrator != null) vibrator.cancel();\n        AssignmentOverlay.dismissOnly();\n        NativeDeliveryReporter.report("vibration_cancelled"'
if s.count(receiver_cancel) < 1:
    raise SystemExit("v122 receiver overlay dismissal anchor missing")
s = s.replace(receiver_cancel, receiver_replacement, 1)

# Keep announcement/alarm volume at maximum and music at level 6. No audio-focus
# request is made, so existing music is not paused by this native component.
service_import = 'import android.media.AudioAttributes;\n'
if s.count(service_import) < 1:
    raise SystemExit("v122 service audio import anchor missing")
# The last AudioAttributes import belongs to the FCM service; replacing all is harmless.
s = s.replace(service_import, service_import + 'import android.media.AudioManager;\n')

old = '''        showNotification(court, title, body, assignmentId);
        boolean fullScreenAllowed = true;'''
new = '''        configureAlertVolumes();
        int notificationId = assignmentId.hashCode();
        boolean overlayShown = AssignmentOverlay.show(this, title, body, notificationId);
        showNotification(court, title, body, assignmentId);
        boolean fullScreenAllowed = true;'''
if s.count(old) != 1:
    raise SystemExit("v122 overlay show anchor missing")
s = s.replace(old, new, 1)

s = s.replace('        vibrateStrong(court ? 5 : 3);',
              '        vibrateStrong(court ? 5 : 3, overlayShown);', 1)
s = s.replace('    private void vibrateStrong(int groups) {',
              '''    private void configureAlertVolumes() {
        AudioManager audio = (AudioManager) getSystemService(Context.AUDIO_SERVICE);
        if (audio == null) return;
        audio.setStreamVolume(AudioManager.STREAM_ALARM,
                audio.getStreamMaxVolume(AudioManager.STREAM_ALARM), 0);
        audio.setStreamVolume(AudioManager.STREAM_MUSIC,
                Math.min(6, audio.getStreamMaxVolume(AudioManager.STREAM_MUSIC)), 0);
    }

    private void vibrateStrong(int groups, boolean repeatUntilConfirmed) {''', 1)
s = s.replace('VibrationEffect.createWaveform(timings, amplitudes, 0),',
              'VibrationEffect.createWaveform(timings, amplitudes, repeatUntilConfirmed ? 0 : -1),', 1)
s = s.replace('vibrator.vibrate(timings, 0);',
              'vibrator.vibrate(timings, repeatUntilConfirmed ? 0 : -1);', 1)

for marker in (
    'VERSION="1.2.2"', 'VERSION_CODE="122"',
    'android.permission.SYSTEM_ALERT_WINDOW',
    'Settings.ACTION_MANAGE_OVERLAY_PERMISSION',
    'class AssignmentOverlay',
    'TYPE_APPLICATION_OVERLAY',
    'AssignmentOverlay.show(this, title, body, notificationId)',
    'confirm.setText("확인하고 닫기")',
    'repeatUntilConfirmed ? 0 : -1',
    'AudioManager.STREAM_ALARM',
    'AudioManager.STREAM_MUSIC',
    'Math.min(6, audio.getStreamMaxVolume',
    '"대기 1순위입니다. 라켓 들고 준비하세요."',
    'courtNo + "번 코트로 들어가세요."',
):
    if marker not in s:
        raise SystemExit("missing native v1.2.2 marker: " + marker)

path.write_text(s, encoding="utf-8")
print("Prepared v1.2.2 deterministic overlay stop UI and safe vibration fallback.")
