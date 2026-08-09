#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys


path = Path(sys.argv[1])
# Reuse the already asserted telemetry instrumentation layer, then give this
# one-time APK a diagnostic-only identity that cannot collide with candidate
# release numbering happening in parallel.
instrumentation = Path(__file__).with_name("patch_build_user_native_v124_diagnostic.py")
subprocess.run([sys.executable, str(instrumentation), str(path)], check=True)

s = path.read_text(encoding="utf-8")
for old, new in (
    ("v1.2.4-diagnostic.apk", "native-path-diagnostic.apk"),
    ("user-native-push-v1.2.4-diagnostic.txt", "user-native-path-diagnostic.txt"),
    ('VERSION="1.2.4"', 'VERSION="1.2.3-diag"'),
    ('VERSION_CODE="124"', 'VERSION_CODE="900123"'),
    ("versionCode 124", "versionCode 900123"),
    ("versionCode='124'", "versionCode='900123'"),
    ("versionName '1.2.4'", "versionName '1.2.3-diag'"),
    ("versionName='1.2.4'", "versionName='1.2.3-diag'"),
    ('USER_APP_VERSION = "1.2.4"', 'USER_APP_VERSION = "1.2.3-diag"'),
    ("JayumintonUserNative/1.2.4", "JayumintonUserNative/1.2.3-diag"),
    ("JayumintonNativeAndroid/1.2.4", "JayumintonNativeAndroid/1.2.3-diag"),
    ('APP_VERSION = "1.2.4"', 'APP_VERSION = "1.2.3-diag"'),
    ("version=1.2.4", "version=1.2.3-diag"),
    ("version_code=124", "version_code=900123"),
    ("jayuminton_wait1_native_v124_diag", "jayuminton_wait1_native_path_diag"),
    ("jayuminton_court_native_v124_diag", "jayuminton_court_native_path_diag"),
):
    s = s.replace(old, new)

for marker in (
    'VERSION="1.2.3-diag"',
    'VERSION_CODE="900123"',
    "versionCode 900123",
    "versionName '1.2.3-diag'",
    'APP_VERSION = "1.2.3-diag"',
    'native-path-diagnostic.apk',
    'user-native-path-diagnostic.txt',
    'reportPath("fcm_received"',
    'reportPath("notification_posted"',
    'reportPath("confirm_action"',
    'reportPath("vibration_cancelled"',
    'AtomicBoolean(false)',
):
    if marker not in s:
        raise SystemExit("missing collision-proof native diagnostic marker: " + marker)

path.write_text(s, encoding="utf-8")
print("Prepared collision-proof one-time native receive-path diagnostic identity.")
