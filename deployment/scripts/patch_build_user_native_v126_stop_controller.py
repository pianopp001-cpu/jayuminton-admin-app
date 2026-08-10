#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

# v1.2.6 is built on the verified v1.2.4 overlay base, not on the rejected
# v1.2.5 cancellation implementation.  The real-device trace showed that the
# confirm route executed but the Android repeating waveform continued.  Avoid a
# platform-level infinite waveform entirely: repeat finite strong groups from an
# app-owned controller and cancel both the controller and VibratorManager.
for old, new in (
    ("v1.2.4-confirmed-overlay.apk", "v1.2.6-stop-controller.apk"),
    ("user-native-push-v1.2.4.txt", "user-native-push-v1.2.6.txt"),
    ('VERSION="1.2.4"', 'VERSION="1.2.6"'),
    ('VERSION_CODE="124"', 'VERSION_CODE="126"'),
    ("versionCode 124", "versionCode 126"),
    ("versionCode='124'", "versionCode='126'"),
    ("versionName '1.2.4'", "versionName '1.2.6'"),
    ("versionName='1.2.4'", "versionName='1.2.6'"),
    ('USER_APP_VERSION = "1.2.4"', 'USER_APP_VERSION = "1.2.6"'),
    ("JayumintonUserNative/1.2.4", "JayumintonUserNative/1.2.6"),
    ("JayumintonNativeAndroid/1.2.4", "JayumintonNativeAndroid/1.2.6"),
    ('APP_VERSION = "1.2.4"', 'APP_VERSION = "1.2.6"'),
    ("version=1.2.4", "version=1.2.6"),
    ("version_code=124", "version_code=126"),
    ("jayuminton_wait1_native_v124", "jayuminton_wait1_native_v126"),
    ("jayuminton_court_native_v124", "jayuminton_court_native_v126"),
):
    s = s.replace(old, new)

# Add one dedicated source file for vibration ownership.
var_anchor = 'OVERLAY_JAVA="$JAVA_DIR/AssignmentOverlay.java"'
if s.count(var_anchor) != 1:
    raise SystemExit("v126 overlay source variable anchor missing")
s = s.replace(var_anchor, var_anchor + '\nVIBRATION_JAVA="$JAVA_DIR/AlertVibrationController.java"', 1)

service_anchor = "cat > \"$SERVICE_JAVA\" <<'JAVA'\n"
if s.count(service_anchor) != 1:
    raise SystemExit("v126 FCM service heredoc anchor missing")

controller_java = r'''cat > "$VIBRATION_JAVA" <<'JAVA'
package com.jayuminton.admin;

import android.content.Context;
import android.media.AudioAttributes;
import android.os.Build;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.VibrationAttributes;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.os.VibratorManager;

/**
 * Owns every assignment vibration for the process.
 *
 * Important: never use VibrationEffect repeatIndex >= 0 here.  Some real devices
 * acknowledged Vibrator.cancel() while keeping that platform repeating waveform
 * alive.  This controller emits one finite strong 3-pulse group at a time and
 * schedules the next group itself.  Confirmation removes future groups and then
 * cancels through both VibratorManager and Vibrator, with guarded retry cancels.
 */
public final class AlertVibrationController {
    private static final Object LOCK = new Object();
    private static final HandlerThread THREAD = new HandlerThread("JayumintonAlertVibration");
    private static final Handler HANDLER;
    private static final long[] GROUP_TIMINGS = new long[]{0, 650, 220, 650, 220, 650};
    private static final int[] GROUP_AMPLITUDES = new int[]{0, 255, 0, 255, 0, 255};
    private static final long GROUP_REPEAT_MS = 3490L; // finite group + 1.1 s group gap

    private static boolean active;
    private static int generation;
    private static Runnable activeRunnable;
    private static Vibrator activeVibrator;

    static {
        THREAD.start();
        HANDLER = new Handler(THREAD.getLooper());
    }

    private AlertVibrationController() {}

    public static void start(Context context, String assignmentId) {
        final Context app = context.getApplicationContext();
        final int myGeneration;
        final Runnable[] holder = new Runnable[1];
        synchronized (LOCK) {
            generation++;
            myGeneration = generation;
            active = true;
            if (activeRunnable != null) HANDLER.removeCallbacks(activeRunnable);
            cancelHardware(app, activeVibrator);
            activeVibrator = null;

            holder[0] = new Runnable() {
                @Override public void run() {
                    synchronized (LOCK) {
                        if (!active || generation != myGeneration || activeRunnable != this) return;
                    }
                    Vibrator vibrator = defaultVibrator(app);
                    if (vibrator != null && vibrator.hasVibrator()) {
                        synchronized (LOCK) {
                            if (!active || generation != myGeneration || activeRunnable != this) return;
                            activeVibrator = vibrator;
                        }
                        vibrateFiniteGroup(vibrator);
                    }
                    synchronized (LOCK) {
                        if (!active || generation != myGeneration || activeRunnable != this) return;
                        HANDLER.postDelayed(this, GROUP_REPEAT_MS);
                    }
                }
            };
            activeRunnable = holder[0];
            HANDLER.post(activeRunnable);
        }
    }

    public static void stop(Context context) {
        final Context app = context.getApplicationContext();
        final int stoppedGeneration;
        final Vibrator captured;
        synchronized (LOCK) {
            active = false;
            generation++;
            stoppedGeneration = generation;
            if (activeRunnable != null) HANDLER.removeCallbacks(activeRunnable);
            activeRunnable = null;
            captured = activeVibrator;
            activeVibrator = null;
        }

        // First cancellation is synchronous so the button press is acted on now.
        cancelHardware(app, captured);

        // OEM safety retries.  They are generation-guarded so a later assignment
        // can never be cancelled by an old confirmation retry.
        scheduleGuardedCancel(app, stoppedGeneration, 80L);
        scheduleGuardedCancel(app, stoppedGeneration, 250L);
        scheduleGuardedCancel(app, stoppedGeneration, 700L);
    }

    private static void scheduleGuardedCancel(Context app, int stoppedGeneration, long delayMs) {
        HANDLER.postDelayed(() -> {
            synchronized (LOCK) {
                if (active || generation != stoppedGeneration) return;
            }
            cancelHardware(app, null);
        }, delayMs);
    }

    private static Vibrator defaultVibrator(Context context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            VibratorManager manager =
                    (VibratorManager) context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE);
            return manager == null ? null : manager.getDefaultVibrator();
        }
        return (Vibrator) context.getSystemService(Context.VIBRATOR_SERVICE);
    }

    private static void cancelHardware(Context context, Vibrator captured) {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                VibratorManager manager =
                        (VibratorManager) context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE);
                if (manager != null) {
                    try { manager.cancel(); } catch (Exception ignored) {}
                    try {
                        Vibrator current = manager.getDefaultVibrator();
                        if (current != null) current.cancel();
                    } catch (Exception ignored) {}
                }
            } else {
                Vibrator current = (Vibrator) context.getSystemService(Context.VIBRATOR_SERVICE);
                if (current != null) current.cancel();
            }
        } catch (Exception ignored) {}
        if (captured != null) {
            try { captured.cancel(); } catch (Exception ignored) {}
        }
    }

    private static void vibrateFiniteGroup(Vibrator vibrator) {
        if (Build.VERSION.SDK_INT >= 33) {
            VibrationAttributes attrs = new VibrationAttributes.Builder()
                    .setUsage(VibrationAttributes.USAGE_ALARM)
                    .build();
            vibrator.vibrate(
                    VibrationEffect.createWaveform(GROUP_TIMINGS, GROUP_AMPLITUDES, -1),
                    attrs
            );
        } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            AudioAttributes attrs = new AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .build();
            vibrator.vibrate(
                    VibrationEffect.createWaveform(GROUP_TIMINGS, GROUP_AMPLITUDES, -1),
                    attrs
            );
        } else {
            vibrator.vibrate(GROUP_TIMINGS, -1);
        }
    }
}
JAVA

'''
s = s.replace(service_anchor, controller_java + service_anchor, 1)

# Every visible/user-accessible stop route must stop the same controller.
def patch_segment(source, start_marker, end_marker, old, new, label):
    start = source.find(start_marker)
    end = source.find(end_marker, start)
    if start < 0 or end < 0:
        raise SystemExit(f"v126 {label} segment missing")
    segment = source[start:end]
    if old not in segment:
        raise SystemExit(f"v126 {label} stop anchor missing")
    segment = segment.replace(old, new, 1)
    return source[:start] + segment + source[end:]

s = patch_segment(
    s,
    'cat > "$ALERT_JAVA" <<\'JAVA\'\n',
    '\nJAVA\n\n',
    '    private void dismissAlert() {\n',
    '    private void dismissAlert() {\n        AlertVibrationController.stop(this);\n',
    'alert activity',
)

s = patch_segment(
    s,
    'cat > "$DISMISS_JAVA" <<\'JAVA\'\n',
    '\nJAVA\n\n',
    '    @Override public void onReceive(Context context, Intent intent) {\n',
    '    @Override public void onReceive(Context context, Intent intent) {\n        AlertVibrationController.stop(context);\n',
    'notification receiver',
)

s = patch_segment(
    s,
    'cat > "$OVERLAY_JAVA" <<\'JAVA\'\n',
    '\nJAVA\n\n',
    '    public static void stopEverything(Context context, int notificationId) {\n',
    '    public static void stopEverything(Context context, int notificationId) {\n        AlertVibrationController.stop(context);\n',
    'overlay',
)

# Start controller-owned repetition before any center/full-screen UI can become
# clickable. This removes the old race where a very fast confirmation could run
# before the repeating waveform had been started.
flow_anchor = '''        int notificationId = assignmentId.hashCode();
        boolean overlayShown = AssignmentOverlay.show(this, title, body, notificationId);'''
flow_replacement = '''        int notificationId = assignmentId.hashCode();
        AlertVibrationController.start(this, assignmentId);
        NativeDeliveryReporter.report("vibration_started", type, hasTargetMemberId,
                true, false, false, false);
        boolean overlayShown = AssignmentOverlay.show(this, title, body, notificationId);'''
if s.count(flow_anchor) != 1:
    raise SystemExit("v126 controller start flow anchor missing")
s = s.replace(flow_anchor, flow_replacement, 1)

old_call = '        vibrateStrong(court ? 5 : 3, overlayShown);'
if s.count(old_call) != 1:
    raise SystemExit("v126 legacy repeating vibration call missing")
s = s.replace(old_call, '        // Repetition is owned by AlertVibrationController; no platform repeat waveform here.', 1)

# Update generated status text so build evidence reflects the new actual path.
s = s.replace('wait1_vibration=3-long-pulses-x3-groups',
              'wait1_vibration=controller-finite-3-pulse-groups-repeat-until-confirmed')
s = s.replace('court_vibration=3-long-pulses-x5-groups',
              'court_vibration=controller-finite-3-pulse-groups-repeat-until-confirmed')

for marker in (
    'VERSION="1.2.6"',
    'VERSION_CODE="126"',
    'APP_VERSION = "1.2.6"',
    'class AlertVibrationController',
    'VibratorManager manager',
    'manager.cancel()',
    'GROUP_REPEAT_MS = 3490L',
    'createWaveform(GROUP_TIMINGS, GROUP_AMPLITUDES, -1)',
    'AlertVibrationController.start(this, assignmentId)',
    'AlertVibrationController.stop(this)',
    'AlertVibrationController.stop(context)',
    'NativeDeliveryReporter.report("vibration_started"',
    'confirm.setOnClickListener(view -> stopEverything(app, notificationId))',
    '"확인 · 진동 끄기"',
    '.setDeleteIntent(dismissPending)',
    '"대기 1순위입니다. 라켓 들고 준비하세요."',
    'courtNo + "번 코트로 들어가세요."',
):
    if marker not in s:
        raise SystemExit("missing v1.2.6 stop-controller marker: " + marker)

# Hard release gates: there must be no active call site using the old Android
# infinite waveform path. The old method may remain compiled but unused.
if '        vibrateStrong(court ? 5 : 3, overlayShown);' in s:
    raise SystemExit("legacy repeat call still active in v1.2.6")

path.write_text(s, encoding="utf-8")
print("Prepared v1.2.6 candidate: finite-group controller + manager-wide cancel + guarded cancel retries.")
