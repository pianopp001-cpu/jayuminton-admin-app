#!/usr/bin/env python3
from pathlib import Path
import sys


path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")

replacements = (
    ("jayuminton-courtstatus-v1.1.0-fresh-install.apk", "jayuminton-courtstatus-v1.1.1-fresh-install.apk"),
    ("user-native-push-v1.1.0.txt", "user-native-push-v1.1.1.txt"),
    ('VERSION="1.1.0"', 'VERSION="1.1.1"'),
    ('VERSION_CODE="110"', 'VERSION_CODE="111"'),
    ("versionCode 110", "versionCode 111"),
    ("versionCode='110'", "versionCode='111'"),
    ("versionName '1.1.0'", "versionName '1.1.1'"),
    ("versionName='1.1.0'", "versionName='1.1.1'"),
    ('private static final String USER_APP_VERSION = "1.1.0";', 'private static final String USER_APP_VERSION = "1.1.1";'),
    ("JayumintonUserNative/1.1.0", "JayumintonUserNative/1.1.1"),
    ("__JAYUMINTON_USER_APK_VERSION__='1.1.0'", "__JAYUMINTON_USER_APK_VERSION__='1.1.1'"),
    ("jayuminton_native_push_v110", "jayuminton_native_push_v111"),
    ("JayumintonNativeAndroid/1.1.0", "JayumintonNativeAndroid/1.1.1"),
    ("jayuminton_wait1_native_v110", "jayuminton_wait1_native_v111"),
    ("jayuminton_court_native_v110", "jayuminton_court_native_v111"),
    ("version=1.1.0", "version=1.1.1"),
    ("version_code=110", "version_code=111"),
    ('grep -F "$MAIN_DEPLOYMENT_ID" "$RUNNER_TEMP/classes.txt" >/dev/null', 'grep -F "jayuminton-push.web.app" "$RUNNER_TEMP/classes.txt" >/dev/null'),
)
for old, new in replacements:
    source = source.replace(old, new)

old_url = 'USER_URL="https://script.google.com/macros/s/${MAIN_DEPLOYMENT_ID}/exec?mode=user&userAppVersion=${VERSION}&apkUser=1&freshInstall=1"'
new_url = 'USER_URL="https://jayuminton-push.web.app/?mode=user&app=user&nativeApk=1&userAppVersion=${VERSION}"'
if old_url not in source and new_url not in source:
    raise SystemExit("user app URL insertion point missing")
source = source.replace(old_url, new_url, 1)

token_anchor = """        Context app = context.getApplicationContext();
        FirebaseMessaging.getInstance().getToken().addOnCompleteListener(task -> {
"""
token_replacement = """        Context app = context.getApplicationContext();
        FirebaseMessaging.getInstance().setAutoInitEnabled(true);
        FirebaseMessaging.getInstance().getToken().addOnCompleteListener(task -> {
"""
if "setAutoInitEnabled(true)" not in source:
    if token_anchor not in source:
        raise SystemExit("Firebase auto-init insertion point missing")
    source = source.replace(token_anchor, token_replacement, 1)

channel_anchor = """            channel.enableVibration(false);
"""
channel_replacement = """            channel.enableVibration(true);
            channel.setVibrationPattern(new long[]{0, 650, 220, 650, 220, 650});
"""
if "channel.setVibrationPattern" not in source:
    if channel_anchor not in source:
        raise SystemExit("notification channel vibration insertion point missing")
    source = source.replace(channel_anchor, channel_replacement, 1)

required = (
    "jayuminton-courtstatus-v1.1.1-fresh-install.apk",
    'VERSION="1.1.1"',
    'VERSION_CODE="111"',
    "https://jayuminton-push.web.app/?mode=user&app=user&nativeApk=1",
    "setAutoInitEnabled(true)",
    "jayuminton_wait1_native_v111",
    "channel.enableVibration(true)",
    "channel.setVibrationPattern",
)
for marker in required:
    if marker not in source:
        raise SystemExit("missing native v1.1.1 build marker: " + marker)

path.write_text(source, encoding="utf-8")
print("Prepared native background push APK build v1.1.1.")
