#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys


path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

# v1.1.3 made member preference updates atomic and replaced the original
# registerCurrent() body with a verified retry loop.  The telemetry layer was
# authored against the earlier textual anchors, so normalize those anchors only
# while patching, then restore the exact verified behavior afterward.
member_original = '''        p.edit()
                .putString(KEY_MEMBER_ID, newId)
                .putString(KEY_MEMBER_NAME, newName)
                .putBoolean(KEY_REGISTERED, false)
                .putString(KEY_STATUS, "registering")
                .apply();
        if (pushEnabled(app)) {'''
member_compat = '''        p.edit().putBoolean(KEY_REGISTERED, false).putString(KEY_STATUS, "registering").apply();
        p.edit().putString(KEY_MEMBER_ID, newId).putString(KEY_MEMBER_NAME, newName).apply();
        if (pushEnabled(app)) {'''
if s.count(member_original) != 1:
    raise SystemExit("native diagnostic verified-member anchor missing")
s = s.replace(member_original, member_compat, 1)

register_original = '''        if (id.isEmpty() || token.isEmpty()) return;
        p.edit().putBoolean(KEY_REGISTERED, false).putString(KEY_STATUS, "registering").apply();'''
register_compat = '''        if (id.isEmpty() || token.isEmpty()) return;
        submitAsync("register_web_token", id, name, token);
        // JAYUMINTON_NATIVE_DIAG_TEMP_REGISTER_ANCHOR
        p.edit().putBoolean(KEY_REGISTERED, false).putString(KEY_STATUS, "registering").apply();'''
if s.count(register_original) != 1:
    raise SystemExit("native diagnostic verified-register anchor missing")
s = s.replace(register_original, register_compat, 1)
path.write_text(s, encoding="utf-8")

# Reuse the asserted telemetry instrumentation layer.
instrumentation = Path(__file__).with_name("patch_build_user_native_v124_diagnostic.py")
subprocess.run([sys.executable, str(instrumentation), str(path)], check=True)
s = path.read_text(encoding="utf-8")

# Restore v1.1.3's atomic member-state write with telemetry immediately after it.
member_instrumented = '''        p.edit().putBoolean(KEY_REGISTERED, false).putString(KEY_STATUS, "registering").apply();
        p.edit().putString(KEY_MEMBER_ID, newId).putString(KEY_MEMBER_NAME, newName).apply();
        NativeDeliveryReporter.reportPath("member_changed", "", "", newId, newId,
                !newId.isEmpty(), false, false, false, false, false,
                "native_member_selection", "");
        if (pushEnabled(app)) {'''
member_restored = '''        p.edit()
                .putString(KEY_MEMBER_ID, newId)
                .putString(KEY_MEMBER_NAME, newName)
                .putBoolean(KEY_REGISTERED, false)
                .putString(KEY_STATUS, "registering")
                .apply();
        NativeDeliveryReporter.reportPath("member_changed", "", "", newId, newId,
                !newId.isEmpty(), false, false, false, false, false,
                "native_member_selection", "");
        if (pushEnabled(app)) {'''
if s.count(member_instrumented) != 1:
    raise SystemExit("native diagnostic instrumented-member restore anchor missing")
s = s.replace(member_instrumented, member_restored, 1)

# Remove the temporary extra POST. The existing verified retry loop remains
# untouched; only token_register_requested telemetry stays before it.
register_instrumented = '''        NativeDeliveryReporter.reportPath("token_register_requested", "", "", id, id,
                true, false, false, false, false, false,
                "native_registrar", "");
        submitAsync("register_web_token", id, name, token);
        // JAYUMINTON_NATIVE_DIAG_TEMP_REGISTER_ANCHOR
        p.edit().putBoolean(KEY_REGISTERED, false).putString(KEY_STATUS, "registering").apply();'''
register_restored = '''        NativeDeliveryReporter.reportPath("token_register_requested", "", "", id, id,
                true, false, false, false, false, false,
                "native_registrar", "");
        p.edit().putBoolean(KEY_REGISTERED, false).putString(KEY_STATUS, "registering").apply();'''
if s.count(register_instrumented) != 1:
    raise SystemExit("native diagnostic verified-register restore anchor missing")
s = s.replace(register_instrumented, register_restored, 1)

# Give this one-time APK a diagnostic-only identity that cannot collide with
# candidate release numbering happening in parallel.
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
    'reportPath("member_changed"',
    'reportPath("token_register_requested"',
    'reportPath("fcm_received"',
    'reportPath("notification_posted"',
    'reportPath("confirm_action"',
    'reportPath("vibration_cancelled"',
    'AtomicBoolean(false)',
    '.putBoolean(KEY_REGISTERED, false)',
    'verifyRegistered(id, token)',
):
    if marker not in s:
        raise SystemExit("missing collision-proof native diagnostic marker: " + marker)
if "JAYUMINTON_NATIVE_DIAG_TEMP_REGISTER_ANCHOR" in s:
    raise SystemExit("temporary native diagnostic registration anchor leaked")

path.write_text(s, encoding="utf-8")
print("Prepared collision-proof one-time native receive-path diagnostic identity on verified registration behavior.")
