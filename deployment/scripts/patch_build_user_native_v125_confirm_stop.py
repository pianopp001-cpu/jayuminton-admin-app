#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

for old, new in (
    ("v1.2.4-confirmed-overlay.apk", "v1.2.5-confirm-stop.apk"),
    ("user-native-push-v1.2.4.txt", "user-native-push-v1.2.5.txt"),
    ('VERSION="1.2.4"', 'VERSION="1.2.5"'),
    ('VERSION_CODE="124"', 'VERSION_CODE="125"'),
    ("versionCode 124", "versionCode 125"),
    ("versionCode='124'", "versionCode='125'"),
    ("versionName '1.2.4'", "versionName '1.2.5'"),
    ("versionName='1.2.4'", "versionName='1.2.5'"),
    ('USER_APP_VERSION = "1.2.4"', 'USER_APP_VERSION = "1.2.5"'),
    ("JayumintonUserNative/1.2.3", "JayumintonUserNative/1.2.5"),
    ("JayumintonNativeAndroid/1.2.3", "JayumintonNativeAndroid/1.2.5"),
    ('APP_VERSION = "1.2.4"', 'APP_VERSION = "1.2.5"'),
    ("version=1.2.4", "version=1.2.5"),
    ("version_code=124", "version_code=125"),
    ("jayuminton_wait1_native_v124", "jayuminton_wait1_native_v125"),
    ("jayuminton_court_native_v124", "jayuminton_court_native_v125"),
):
    s = s.replace(old, new)

# Android associates each vibration request with the Vibrator client that started it.
# Retain that exact client so the centre confirmation button cancels the repeating
# waveform, instead of creating a second client and attempting to cancel through it.
class_anchor = "public final class JayumintonFirebaseMessagingService extends FirebaseMessagingService {\n"
if s.count(class_anchor) != 1:
    raise SystemExit("FCM service class anchor missing")
s = s.replace(class_anchor, class_anchor + "    private static volatile Vibrator activeAlertVibrator;\n\n", 1)

start_anchor = "        if (vibrator == null || !vibrator.hasVibrator()) return;\n\n        List<Long> timingsList"
if s.count(start_anchor) != 1:
    raise SystemExit("vibration start anchor missing")
s = s.replace(start_anchor,
    "        if (vibrator == null || !vibrator.hasVibrator()) return;\n"
    "        activeAlertVibrator = vibrator;\n\n        List<Long> timingsList", 1)

method_anchor = "    private void vibrateStrong(int groups, boolean repeatUntilConfirmed) {"
if s.count(method_anchor) != 1:
    raise SystemExit("vibrateStrong anchor missing")
stop_method = '''    public static void stopActiveAlertVibration() {
        Vibrator active = activeAlertVibrator;
        activeAlertVibrator = null;
        if (active != null) active.cancel();
    }

'''
s = s.replace(method_anchor, stop_method + method_anchor, 1)

# Both the centre overlay button and notification receiver now cancel the exact
# repeating waveform instance. Existing notification cleanup remains unchanged.
generic_cancel = "        if (vibrator != null) vibrator.cancel();"
if s.count(generic_cancel) < 2:
    raise SystemExit("expected overlay/receiver cancel routes missing")
s = s.replace(generic_cancel,
              generic_cancel + "\n        JayumintonFirebaseMessagingService.stopActiveAlertVibration();")

for marker in (
    'VERSION="1.2.5"', 'VERSION_CODE="125"',
    'private static volatile Vibrator activeAlertVibrator',
    'activeAlertVibrator = vibrator',
    'public static void stopActiveAlertVibration()',
    'JayumintonFirebaseMessagingService.stopActiveAlertVibration();',
    'confirm.setOnClickListener(view -> stopEverything(app, notificationId))',
):
    if marker not in s:
        raise SystemExit("missing v1.2.5 marker: " + marker)

path.write_text(s, encoding="utf-8")
print("Prepared v1.2.5: centre confirmation cancels the exact active vibrator client.")
