#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys


path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

# The current chain has the v1.1.3 atomic member-state write and the v1.1.5
# verified token-registration flow. The shared telemetry layer was authored
# against older textual anchors, so temporarily provide those anchors while
# patching, then restore the current behavior exactly.
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

# v1.1.5 requires a non-empty member name and performs one verified JSONObject
# registration request. Add the older two-line anchor only as a temporary patch
# target; it is removed again before compilation.
register_original = '''        if (id.isEmpty() || name.isEmpty() || token.isEmpty()) return;
        p.edit().putBoolean(KEY_REGISTERED, false).putString(KEY_STATUS, "registering").apply();'''
register_compat = '''        if (id.isEmpty() || name.isEmpty() || token.isEmpty()) return;
        if (id.isEmpty() || token.isEmpty()) return;
        submitAsync("register_web_token", id, name, token);
        // JAYUMINTON_NATIVE_DIAG_TEMP_REGISTER_ANCHOR
        p.edit().putBoolean(KEY_REGISTERED, false).putString(KEY_STATUS, "registering").apply();'''
if s.count(register_original) != 1:
    raise SystemExit("native diagnostic v115-register anchor missing")
s = s.replace(register_original, register_compat, 1)

# The shared layer also patches the old void submit() response branch. v1.1.5
# already has a JSONObject-returning submit(), so provide an inert block-comment
# copy of that old branch only to let the shared patch run. It is removed later.
http_anchor = '''            int code = connection.getResponseCode();
            if (code >= 200 && code < 400) {
                try { if (connection.getInputStream() != null) connection.getInputStream().close(); } catch (Exception ignored) {}
            } else {
                try { if (connection.getErrorStream() != null) connection.getErrorStream().close(); } catch (Exception ignored) {}
            }
        } catch (Exception ignored) {
        } finally {'''
http_dummy = '''
/* JAYUMINTON_NATIVE_DIAG_HTTP_DUMMY_BEGIN
''' + http_anchor + '''
JAYUMINTON_NATIVE_DIAG_HTTP_DUMMY_END */
'''
registrar_end = s.find('\n}\nJAVA\n\ncat > "$SERVICE_JAVA"')
if registrar_end < 0:
    raise SystemExit("native diagnostic registrar end missing")
s = s[:registrar_end] + http_dummy + s[registrar_end:]
path.write_text(s, encoding="utf-8")

# Reuse the asserted receive/notification/overlay telemetry layer.
instrumentation = Path(__file__).with_name("patch_build_user_native_v124_diagnostic.py")
subprocess.run([sys.executable, str(instrumentation), str(path)], check=True)
s = path.read_text(encoding="utf-8")

# Restore the atomic member-state write, retaining only the new member_changed
# telemetry immediately after the state actually changes.
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

# Remove the temporary submitAsync call. The real v1.1.5 JSONObject registration
# remains the sole registration request, preceded by request telemetry.
register_instrumented = '''        if (id.isEmpty() || name.isEmpty() || token.isEmpty()) return;
        NativeDeliveryReporter.reportPath("token_register_requested", "", "", id, id,
                true, false, false, false, false, false,
                "native_registrar", "");
        submitAsync("register_web_token", id, name, token);
        // JAYUMINTON_NATIVE_DIAG_TEMP_REGISTER_ANCHOR
        p.edit().putBoolean(KEY_REGISTERED, false).putString(KEY_STATUS, "registering").apply();'''
register_restored = '''        if (id.isEmpty() || name.isEmpty() || token.isEmpty()) return;
        NativeDeliveryReporter.reportPath("token_register_requested", "", "", id, id,
                true, false, false, false, false, false,
                "native_registrar", "");
        p.edit().putBoolean(KEY_REGISTERED, false).putString(KEY_STATUS, "registering").apply();'''
if s.count(register_instrumented) != 1:
    raise SystemExit("native diagnostic v115-register restore anchor missing")
s = s.replace(register_instrumented, register_restored, 1)

# Remove the inert old-submit compatibility block in full.
dummy_start = s.find('/* JAYUMINTON_NATIVE_DIAG_HTTP_DUMMY_BEGIN')
dummy_end = s.find('JAYUMINTON_NATIVE_DIAG_HTTP_DUMMY_END */', dummy_start)
if dummy_start < 0 or dummy_end < 0:
    raise SystemExit("native diagnostic HTTP dummy restore anchor missing")
dummy_end += len('JAYUMINTON_NATIVE_DIAG_HTTP_DUMMY_END */')
s = s[:dummy_start] + s[dummy_end:]

# Record the outcome of the real v1.1.5 JSONObject registration response. This
# gives request -> HTTP/application outcome without changing retry or token logic.
registration_result = '''            JSONObject registered = submit("register_web_token", id, name, token);
            boolean registrationOk = registered.optBoolean("ok", false);'''
registration_result_logged = '''            JSONObject registered = submit("register_web_token", id, name, token);
            boolean registrationOk = registered.optBoolean("ok", false);
            NativeDeliveryReporter.reportPath(
                    registrationOk ? "token_register_http_ok" : "token_register_http_failed",
                    "", "", id, id, true, false, false, false,
                    false, false, "native_registrar_http", "");'''
if s.count(registration_result) != 1:
    raise SystemExit("native diagnostic registration result anchor missing")
s = s.replace(registration_result, registration_result_logged, 1)

# Give this one-time APK a diagnostic-only identity that cannot collide with
# release candidate numbering being produced in parallel.
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
    '"token_register_http_ok"',
    '"token_register_http_failed"',
    'reportPath("fcm_received"',
    'reportPath("notification_posted"',
    'reportPath("confirm_action"',
    'reportPath("vibration_cancelled"',
    'AtomicBoolean(false)',
    '.putBoolean(KEY_REGISTERED, false)',
    'JSONObject registered = submit("register_web_token"',
):
    if marker not in s:
        raise SystemExit("missing collision-proof native diagnostic marker: " + marker)
for forbidden in (
    'JAYUMINTON_NATIVE_DIAG_TEMP_REGISTER_ANCHOR',
    'JAYUMINTON_NATIVE_DIAG_HTTP_DUMMY_BEGIN',
    'JAYUMINTON_NATIVE_DIAG_HTTP_DUMMY_END',
):
    if forbidden in s:
        raise SystemExit("temporary native diagnostic anchor leaked: " + forbidden)

path.write_text(s, encoding="utf-8")
print("Prepared collision-proof one-time native receive-path diagnostic on current verified token flow.")
