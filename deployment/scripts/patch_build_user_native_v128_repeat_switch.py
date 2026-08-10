#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding='utf-8')

for old, new in (
    ('v1.2.7-member-switch.apk', 'v1.2.8-repeat-switch.apk'),
    ('user-native-push-v1.2.7.txt', 'user-native-push-v1.2.8.txt'),
    ('VERSION="1.2.7"', 'VERSION="1.2.8"'),
    ('VERSION_CODE="127"', 'VERSION_CODE="128"'),
    ('versionCode 127', 'versionCode 128'),
    ("versionCode='127'", "versionCode='128'"),
    ("versionName '1.2.7'", "versionName '1.2.8'"),
    ("versionName='1.2.7'", "versionName='1.2.8'"),
    ('USER_APP_VERSION = "1.2.7"', 'USER_APP_VERSION = "1.2.8"'),
    ('JayumintonUserNative/1.2.7', 'JayumintonUserNative/1.2.8'),
    ('JayumintonNativeAndroid/1.2.7', 'JayumintonNativeAndroid/1.2.8'),
    ('APP_VERSION = "1.2.7"', 'APP_VERSION = "1.2.8"'),
    ('version=1.2.7', 'version=1.2.8'),
    ('version_code=127', 'version_code=128'),
    ('jayuminton_wait1_native_v127', 'jayuminton_wait1_native_v128'),
    ('jayuminton_court_native_v127', 'jayuminton_court_native_v128'),
    ('member-switch-v127', 'repeat-switch-v128'),
):
    s = s.replace(old, new)

registrar_start = s.find('cat > "$REGISTRAR_JAVA" <<JAVA\n')
registrar_end = s.find('\nJAVA\n\ncat > "$REPORTER_JAVA"', registrar_start)
if registrar_start < 0 or registrar_end < 0:
    raise SystemExit('v128 registrar segment missing')
r = s[registrar_start:registrar_end]

# Actual member changes invalidate every alert owned by the previous member.
# This prevents A's vibration/overlay from surviving after A -> B -> C... while
# preserving v1.2.7's token generation guard and same-member no-op behavior.
import_anchor = 'import android.content.Context;\n'
if import_anchor not in r:
    raise SystemExit('v128 registrar Context import missing')
r = r.replace(import_anchor, 'import android.app.NotificationManager;\n' + import_anchor, 1)

change_anchor = '''        long generation = REGISTRATION_GENERATION.incrementAndGet();
        p.edit()
                .putString(KEY_MEMBER_ID, newId)'''
change_replacement = '''        long generation = REGISTRATION_GENERATION.incrementAndGet();
        stopPreviousMemberAlert(app);
        p.edit()
                .putString(KEY_MEMBER_ID, newId)'''
if r.count(change_anchor) != 1:
    raise SystemExit('v128 actual member-change anchor missing')
r = r.replace(change_anchor, change_replacement, 1)

# Clearing the selected user or turning push off is also an ownership boundary.
clear_anchor = '''    public static void clearMember(Context context) {
        Context app = context.getApplicationContext();
        REGISTRATION_GENERATION.incrementAndGet();'''
clear_replacement = '''    public static void clearMember(Context context) {
        Context app = context.getApplicationContext();
        REGISTRATION_GENERATION.incrementAndGet();
        stopPreviousMemberAlert(app);'''
if r.count(clear_anchor) != 1:
    raise SystemExit('v128 clearMember anchor missing')
r = r.replace(clear_anchor, clear_replacement, 1)

disable_anchor = '''        } else if (previous) {
            REGISTRATION_GENERATION.incrementAndGet();
            String id = p.getString(KEY_MEMBER_ID, "");'''
disable_replacement = '''        } else if (previous) {
            REGISTRATION_GENERATION.incrementAndGet();
            stopPreviousMemberAlert(app);
            String id = p.getString(KEY_MEMBER_ID, "");'''
if r.count(disable_anchor) != 1:
    raise SystemExit('v128 push-disable anchor missing')
r = r.replace(disable_anchor, disable_replacement, 1)

helper_anchor = '''    private static boolean registrationStillCurrent(Context context, long generation,
                                                     String memberId, String token) {
        if (generation != REGISTRATION_GENERATION.get()) return false;
        SharedPreferences current = prefs(context.getApplicationContext());
        return memberId.equals(current.getString(KEY_MEMBER_ID, "")) &&
                token.equals(current.getString(KEY_TOKEN, "")) &&
                current.getBoolean(KEY_PUSH, true);
    }

'''
if r.count(helper_anchor) != 1:
    raise SystemExit('v128 registrationStillCurrent helper missing')
helper = helper_anchor + '''    private static void stopPreviousMemberAlert(Context context) {
        Context app = context.getApplicationContext();
        // One controller owns all active assignment vibration. Stopping here
        // invalidates pending finite vibration groups and guarded OEM retries.
        AlertVibrationController.stop(app);
        AssignmentOverlay.dismissOnly();
        try {
            NotificationManager notifications =
                    (NotificationManager) app.getSystemService(Context.NOTIFICATION_SERVICE);
            if (notifications != null) notifications.cancelAll();
        } catch (Exception ignored) {}
    }

'''
r = r.replace(helper_anchor, helper, 1)

# Repeated same-member WebView sync must not stop a currently valid alert.
set_start = r.find('    public static void setMember(Context context, String memberId, String memberName) {')
set_end = r.find('    public static void clearMember(', set_start)
set_block = r[set_start:set_end]
if set_block.find('if (!changed) {') < 0:
    raise SystemExit('v128 same-member no-op missing')
if set_block.find('if (!changed) {') > set_block.find('stopPreviousMemberAlert(app)'):
    raise SystemExit('v128 same-member sync would stop current vibration')

for required in (
    'REGISTER_EXECUTOR = Executors.newSingleThreadExecutor()',
    'REGISTRATION_GENERATION = new AtomicLong(0L)',
    'registrationStillCurrent(app, expectedGeneration, id, token)',
    'stopPreviousMemberAlert(app);',
    'AlertVibrationController.stop(app);',
    'AssignmentOverlay.dismissOnly();',
    'notifications.cancelAll();',
):
    if required not in r:
        raise SystemExit('missing v128 repeated-switch registrar marker: ' + required)

s = s[:registrar_start] + r + s[registrar_end:]

# The v1.2.6 controller already handles arbitrarily many starts safely: every
# start increments its own generation, removes the old Runnable and cancels the
# previous hardware object before starting the current assignment.
for required in (
    'VERSION="1.2.8"',
    'VERSION_CODE="128"',
    'APP_VERSION = "1.2.8"',
    'class AlertVibrationController',
    'generation++;',
    'if (activeRunnable != null) HANDLER.removeCallbacks(activeRunnable);',
    'cancelHardware(app, activeVibrator);',
    'AlertVibrationController.start(this, assignmentId)',
    'JAYUMINTON_V126_START_STOP_RACE_GUARD',
    'NativePushRegistrar.isCurrentMember(this, targetMemberId)',
    'confirm.setText("확인하고 닫기")',
    '"확인 · 진동 끄기"',
    '"대기 1순위입니다. 라켓 들고 준비하세요."',
    'courtNo + "번 코트로 들어가세요."',
):
    if required not in s:
        raise SystemExit('missing v1.2.8 repeated-switch marker: ' + required)

# Build evidence text: explicitly state the behavior under repeated switches.
s = s.replace(
    'wait1_vibration=controller-finite-3-pulse-groups-repeat-until-confirmed-repeat-switch-v128',
    'wait1_vibration=controller-finite-3-pulse-groups-repeat-until-confirmed-repeat-switch-v128-current-member-only',
)
s = s.replace(
    'court_vibration=controller-finite-3-pulse-groups-repeat-until-confirmed-repeat-switch-v128',
    'court_vibration=controller-finite-3-pulse-groups-repeat-until-confirmed-repeat-switch-v128-current-member-only',
)

path.write_text(s, encoding='utf-8')
print('Prepared v1.2.8: repeated A->B->C member changes stop stale alerts immediately; current-member FCM starts the same proven vibration controller.')
