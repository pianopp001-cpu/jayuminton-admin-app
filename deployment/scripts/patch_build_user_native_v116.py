#!/usr/bin/env python3
from pathlib import Path
import sys


path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

for old, new in (
    ("v1.1.5-fresh-install.apk", "v1.1.6-fresh-install.apk"),
    ("user-native-push-v1.1.5.txt", "user-native-push-v1.1.6.txt"),
    ('VERSION="1.1.5"', 'VERSION="1.1.6"'),
    ('VERSION_CODE="115"', 'VERSION_CODE="116"'),
    ("versionCode 115", "versionCode 116"),
    ("versionCode='115'", "versionCode='116'"),
    ("versionName '1.1.5'", "versionName '1.1.6'"),
    ("versionName='1.1.5'", "versionName='1.1.6'"),
    ('USER_APP_VERSION = "1.1.5"', 'USER_APP_VERSION = "1.1.6"'),
    ("JayumintonUserNative/1.1.5", "JayumintonUserNative/1.1.6"),
    ("JayumintonNativeAndroid/1.1.5", "JayumintonNativeAndroid/1.1.6"),
    ("version=1.1.5", "version=1.1.6"),
    ("version_code=115", "version_code=116"),
    ("jayuminton_wait1_system_v114", "jayuminton_wait1_system_v116"),
    ("jayuminton_court_system_v114", "jayuminton_court_system_v116"),
):
    s = s.replace(old, new)

old = '''        showNotification(court, title, body, assignmentId);
        if (NativePushRegistrar.vibrationEnabled(this)) vibrateStrong(court ? 5 : 3);'''
new = '''        // Sound/TTS and vibration are deliberately independent.  Start the
        // device vibrator first and never suppress a real assignment vibration
        // because a stale WebView preference failed to synchronize.
        vibrateStrong(court ? 5 : 3);
        showNotification(court, title, body, assignmentId);'''
if s.count(old) != 1:
    raise SystemExit("native vibration gate insertion point missing")
s = s.replace(old, new, 1)

old = '''        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createWaveform(timings, amplitudes, -1));
        } else {
            vibrator.vibrate(timings, -1);
        }'''
new = '''        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            AudioAttributes vibrationAttributes = new AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .build();
            vibrator.vibrate(
                    VibrationEffect.createWaveform(timings, amplitudes, -1),
                    vibrationAttributes
            );
        } else {
            vibrator.vibrate(timings, -1);
        }'''
if s.count(old) != 1:
    raise SystemExit("native alarm vibration insertion point missing")
s = s.replace(old, new, 1)

for marker in (
    'VERSION="1.1.6"', 'VERSION_CODE="116"',
    'vibrateStrong(court ? 5 : 3);',
    'AudioAttributes.USAGE_ALARM',
    'jayuminton_wait1_system_v116',
    'jayuminton_court_system_v116',
    'JayumintonFirebaseMessagingService',
):
    if marker not in s:
        raise SystemExit("missing native v1.1.6 marker: " + marker)

if 'if (NativePushRegistrar.vibrationEnabled(this)) vibrateStrong' in s:
    raise SystemExit("stale native vibration preference gate remains")

path.write_text(s, encoding="utf-8")
print("Prepared native v1.1.6 with unconditional alarm-usage assignment vibration.")
