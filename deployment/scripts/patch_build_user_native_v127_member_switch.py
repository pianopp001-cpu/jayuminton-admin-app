#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding='utf-8')

for old, new in (
    ('v1.2.6-stop-controller.apk', 'v1.2.7-member-switch.apk'),
    ('user-native-push-v1.2.6.txt', 'user-native-push-v1.2.7.txt'),
    ('VERSION="1.2.6"', 'VERSION="1.2.7"'),
    ('VERSION_CODE="126"', 'VERSION_CODE="127"'),
    ('versionCode 126', 'versionCode 127'),
    ("versionCode='126'", "versionCode='127'"),
    ("versionName '1.2.6'", "versionName '1.2.7'"),
    ("versionName='1.2.6'", "versionName='1.2.7'"),
    ('USER_APP_VERSION = "1.2.6"', 'USER_APP_VERSION = "1.2.7"'),
    ('JayumintonUserNative/1.2.6', 'JayumintonUserNative/1.2.7'),
    ('JayumintonNativeAndroid/1.2.6', 'JayumintonNativeAndroid/1.2.7'),
    ('APP_VERSION = "1.2.6"', 'APP_VERSION = "1.2.7"'),
    ('version=1.2.6', 'version=1.2.7'),
    ('version_code=126', 'version_code=127'),
    ('jayuminton_wait1_native_v126', 'jayuminton_wait1_native_v127'),
    ('jayuminton_court_native_v126', 'jayuminton_court_native_v127'),
):
    s = s.replace(old, new)

registrar_start = s.find('cat > "$REGISTRAR_JAVA" <<JAVA\n')
registrar_end = s.find('\nJAVA\n\ncat > "$REPORTER_JAVA"', registrar_start)
if registrar_start < 0 or registrar_end < 0:
    raise SystemExit('v127 registrar segment missing')
r = s[registrar_start:registrar_end]

# One executor remains for ordinary unregister calls. A separate registration
# executor prevents a member switch from sitting behind unrelated unregister
# work, while a generation guard invalidates stale queued registrations.
import_anchor = 'import java.util.concurrent.Executors;\n'
if import_anchor not in r:
    raise SystemExit('v127 registrar executor import missing')
r = r.replace(import_anchor, import_anchor + 'import java.util.concurrent.atomic.AtomicLong;\n', 1)

field_anchor = '    private static final ExecutorService EXECUTOR = Executors.newSingleThreadExecutor();\n'
if r.count(field_anchor) != 1:
    raise SystemExit('v127 registrar executor field missing')
r = r.replace(
    field_anchor,
    field_anchor +
    '    private static final ExecutorService REGISTER_EXECUTOR = Executors.newSingleThreadExecutor();\n' +
    '    private static final AtomicLong REGISTRATION_GENERATION = new AtomicLong(0L);\n',
    1,
)

# Refreshing the same FCM token must not create an endless queue on every resume.
on_token_start = r.find('    public static void onNewToken(Context context, String token) {')
on_token_end = r.find('    public static void setMember(', on_token_start)
if on_token_start < 0 or on_token_end < 0:
    raise SystemExit('v127 onNewToken block missing')
on_token = '''    public static void onNewToken(Context context, String token) {
        Context app = context.getApplicationContext();
        SharedPreferences p = prefs(app);
        String safeToken = token == null ? "" : token.trim();
        String previousToken = p.getString(KEY_TOKEN, "");
        boolean tokenChanged = !previousToken.equals(safeToken);
        p.edit().putString(KEY_TOKEN, safeToken).apply();
        if (!pushEnabled(app)) return;
        boolean registered = p.getBoolean(KEY_REGISTERED, false);
        String status = p.getString(KEY_STATUS, "");
        if (!tokenChanged && registered) return;
        if (!tokenChanged && "registering".equals(status)) return;
        long generation = REGISTRATION_GENERATION.incrementAndGet();
        registerCurrent(app, generation);
    }

'''
r = r[:on_token_start] + on_token + r[on_token_end:]

# Core fix: repeated 2-second WebView synchronisation for the SAME member is a
# no-op. An ACTUAL member change updates native state immediately and registers
# the existing token to the new member. Do not unregister the old member first:
# registerWebToken_ atomically removes the same token from its previous record
# and reassigns it, while the server now also ignores delayed old-member
# unregisters after reassignment.
set_start = r.find('    public static void setMember(Context context, String memberId, String memberName) {')
set_end = r.find('    public static void clearMember(', set_start)
if set_start < 0 or set_end < 0:
    raise SystemExit('v127 setMember block missing')
set_member = '''    public static void setMember(Context context, String memberId, String memberName) {
        Context app = context.getApplicationContext();
        SharedPreferences p = prefs(app);
        String oldId = p.getString(KEY_MEMBER_ID, "");
        String oldName = p.getString(KEY_MEMBER_NAME, "");
        String token = p.getString(KEY_TOKEN, "");
        String newId = memberId == null ? "" : memberId.trim();
        String newName = memberName == null ? "" : memberName.trim();
        boolean changed = !oldId.equals(newId) || !oldName.equals(newName);

        if (!changed) {
            if (pushEnabled(app)) {
                if (token.isEmpty()) {
                    ensureToken(app);
                } else {
                    boolean registered = p.getBoolean(KEY_REGISTERED, false);
                    String status = p.getString(KEY_STATUS, "");
                    if (!registered && !"registering".equals(status)) registerCurrent(app);
                }
            }
            return;
        }

        long generation = REGISTRATION_GENERATION.incrementAndGet();
        p.edit()
                .putString(KEY_MEMBER_ID, newId)
                .putString(KEY_MEMBER_NAME, newName)
                .putBoolean(KEY_REGISTERED, false)
                .putString(KEY_STATUS, "registering")
                .apply();
        NativeDeliveryReporter.report("member_changed", "", !newId.isEmpty(),
                true, false, false, false);

        if (pushEnabled(app)) {
            if (token.isEmpty()) ensureToken(app);
            else registerCurrent(app, generation);
        }
    }

'''
r = r[:set_start] + set_member + r[set_end:]

# Clearing/disabling invalidates any registration task captured before it.
clear_anchor = '''    public static void clearMember(Context context) {
        Context app = context.getApplicationContext();'''
if clear_anchor not in r:
    raise SystemExit('v127 clearMember anchor missing')
r = r.replace(clear_anchor, clear_anchor + '\n        REGISTRATION_GENERATION.incrementAndGet();', 1)

disable_anchor = '''        } else if (previous) {
            String id = p.getString(KEY_MEMBER_ID, "");'''
if disable_anchor not in r:
    raise SystemExit('v127 push disable anchor missing')
r = r.replace(disable_anchor, '''        } else if (previous) {
            REGISTRATION_GENERATION.incrementAndGet();
            String id = p.getString(KEY_MEMBER_ID, "");''', 1)

# Replace v1.1.5 registration queueing with generation-aware registration.
reg_start = r.find('    private static void registerCurrent(Context context) {')
reg_end = r.find('    public static String registrationStatus(Context context) {', reg_start)
if reg_start < 0 or reg_end < 0:
    raise SystemExit('v127 registerCurrent block missing')
register_current = '''    private static void registerCurrent(Context context) {
        registerCurrent(context, REGISTRATION_GENERATION.get());
    }

    private static void registerCurrent(Context context, long expectedGeneration) {
        Context app = context.getApplicationContext();
        SharedPreferences p = prefs(app);
        final String id = p.getString(KEY_MEMBER_ID, "");
        final String name = p.getString(KEY_MEMBER_NAME, "");
        final String token = p.getString(KEY_TOKEN, "");
        if (id.isEmpty() || name.isEmpty() || token.isEmpty()) return;
        p.edit().putBoolean(KEY_REGISTERED, false).putString(KEY_STATUS, "registering").apply();
        NativeDeliveryReporter.report("token_register_requested", "", true,
                true, false, false, false);

        REGISTER_EXECUTOR.execute(() -> {
            if (!registrationStillCurrent(app, expectedGeneration, id, token)) return;
            JSONObject registered = submit("register_web_token", id, name, token);
            if (!registrationStillCurrent(app, expectedGeneration, id, token)) return;
            boolean registrationOk = registered.optBoolean("ok", false);
            NativeDeliveryReporter.report(
                    registrationOk ? "token_register_http_ok" : "token_register_http_failed",
                    "", true, true, false, false, false);
            if (!registrationOk) {
                prefs(app).edit().putBoolean(KEY_REGISTERED, false)
                        .putString(KEY_STATUS, "registration_failed")
                        .apply();
                return;
            }

            prefs(app).edit()
                    .putBoolean(KEY_REGISTERED, true)
                    .putString(KEY_STATUS, "token_registered")
                    .putString(KEY_TESTED_KEY, "")
                    .apply();
        });
    }

    private static boolean registrationStillCurrent(Context context, long generation,
                                                     String memberId, String token) {
        if (generation != REGISTRATION_GENERATION.get()) return false;
        SharedPreferences current = prefs(context.getApplicationContext());
        return memberId.equals(current.getString(KEY_MEMBER_ID, "")) &&
                token.equals(current.getString(KEY_TOKEN, "")) &&
                current.getBoolean(KEY_PUSH, true);
    }

'''
r = r[:reg_start] + register_current + r[reg_end:]

# There must be no member-switch unregister in setMember anymore. Unregister is
# still intentionally present in clearMember/push-disable paths.
set_check_start = r.find('    public static void setMember(')
set_check_end = r.find('    public static void clearMember(', set_check_start)
if 'unregister_web_token' in r[set_check_start:set_check_end]:
    raise SystemExit('v127 stale member-switch unregister still present')

for required in (
    'REGISTER_EXECUTOR = Executors.newSingleThreadExecutor()',
    'REGISTRATION_GENERATION = new AtomicLong(0L)',
    'boolean changed = !oldId.equals(newId) || !oldName.equals(newName)',
    'if (!changed) {',
    'registerCurrent(app, generation)',
    'registrationStillCurrent(app, expectedGeneration, id, token)',
    'NativeDeliveryReporter.report("member_changed"',
    'NativeDeliveryReporter.report("token_register_requested"',
    '"token_register_http_ok" : "token_register_http_failed"',
):
    if required not in r:
        raise SystemExit('missing v127 registrar marker: ' + required)

s = s[:registrar_start] + r + s[registrar_end:]

# Preserve the verified v1.2.6 vibration controller and race guard unchanged.
for required in (
    'VERSION="1.2.7"',
    'VERSION_CODE="127"',
    'APP_VERSION = "1.2.7"',
    'class AlertVibrationController',
    'JAYUMINTON_V126_START_STOP_RACE_GUARD',
    'AlertVibrationController.start(this, assignmentId)',
    'AlertVibrationController.stop(this)',
    'confirm.setText("확인하고 닫기")',
    '"확인 · 진동 끄기"',
    'NativePushRegistrar.isCurrentMember(this, targetMemberId)',
    '"대기 1순위입니다. 라켓 들고 준비하세요."',
    'courtNo + "번 코트로 들어가세요."',
):
    if required not in s:
        raise SystemExit('missing v1.2.7 member-switch marker: ' + required)

s = s.replace(
    'wait1_vibration=controller-finite-3-pulse-groups-repeat-until-confirmed',
    'wait1_vibration=controller-finite-3-pulse-groups-repeat-until-confirmed-member-switch-v127',
)
s = s.replace(
    'court_vibration=controller-finite-3-pulse-groups-repeat-until-confirmed',
    'court_vibration=controller-finite-3-pulse-groups-repeat-until-confirmed-member-switch-v127',
)

path.write_text(s, encoding='utf-8')
print('Prepared v1.2.7: idempotent member sync, immediate token reassignment, stale registration generation guard, v1.2.6 vibration controller preserved.')
