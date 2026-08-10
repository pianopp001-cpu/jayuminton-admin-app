#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding='utf-8')

for old, new in (
    ('v1.2.8-repeat-switch.apk', 'v1.2.9-background-registration.apk'),
    ('user-native-push-v1.2.8.txt', 'user-native-push-v1.2.9.txt'),
    ('VERSION="1.2.8"', 'VERSION="1.2.9"'),
    ('VERSION_CODE="128"', 'VERSION_CODE="129"'),
    ('versionCode 128', 'versionCode 129'),
    ("versionCode='128'", "versionCode='129'"),
    ("versionName '1.2.8'", "versionName '1.2.9'"),
    ("versionName='1.2.8'", "versionName='1.2.9'"),
    ('USER_APP_VERSION = "1.2.8"', 'USER_APP_VERSION = "1.2.9"'),
    ('JayumintonUserNative/1.2.8', 'JayumintonUserNative/1.2.9'),
    ('JayumintonNativeAndroid/1.2.8', 'JayumintonNativeAndroid/1.2.9'),
    ('APP_VERSION = "1.2.8"', 'APP_VERSION = "1.2.9"'),
    ('version=1.2.8', 'version=1.2.9'),
    ('version_code=128', 'version_code=129'),
    ('jayuminton_wait1_native_v128', 'jayuminton_wait1_native_v129'),
    ('jayuminton_court_native_v128', 'jayuminton_court_native_v129'),
):
    s = s.replace(old, new)

# Build-only user app source. Nothing in the admin runtime is changed or published.
var_anchor = 'REGISTRAR_JAVA="$JAVA_DIR/NativePushRegistrar.java"\n'
if var_anchor not in s:
    raise SystemExit('v129 registrar variable anchor missing')
s = s.replace(var_anchor, var_anchor + 'REG_JOB_JAVA="$JAVA_DIR/NativeRegistrationJobService.java"\n', 1)

manifest_anchor = '''        <service
            android:name=".JayumintonFirebaseMessagingService"
            android:exported="false">
            <intent-filter>
                <action android:name="com.google.firebase.MESSAGING_EVENT" />
            </intent-filter>
        </service>
'''
manifest_replacement = manifest_anchor + '''
        <service
            android:name=".NativeRegistrationJobService"
            android:permission="android.permission.BIND_JOB_SERVICE"
            android:exported="false" />
'''
if manifest_anchor not in s:
    raise SystemExit('v129 manifest service anchor missing')
s = s.replace(manifest_anchor, manifest_replacement, 1)

registrar_start = s.find('cat > "$REGISTRAR_JAVA" <<JAVA\n')
registrar_end = s.find('\nJAVA\n\ncat > "$REPORTER_JAVA"', registrar_start)
if registrar_start < 0 or registrar_end < 0:
    raise SystemExit('v129 registrar segment missing')
r = s[registrar_start:registrar_end]

import_anchor = 'import android.app.NotificationManager;\n'
if import_anchor not in r:
    raise SystemExit('v129 notification manager import missing')
r = r.replace(
    import_anchor,
    'import android.app.NotificationManager;\n'
    'import android.app.job.JobInfo;\n'
    'import android.app.job.JobScheduler;\n'
    'import android.content.ComponentName;\n',
    1,
)

# Add a persistent timestamp for stale in-process registration detection.
status_idx = r.find('    private static final String KEY_STATUS = ')
if status_idx < 0:
    raise SystemExit('v129 KEY_STATUS marker missing')
status_line_end = r.find('\n', status_idx)
r = r[:status_line_end + 1] + '    private static final String KEY_REGISTER_JOB_AT = "register_job_at";\n' + r[status_line_end + 1:]

field_anchor = '    private static final AtomicLong REGISTRATION_GENERATION = new AtomicLong(0L);\n'
if field_anchor not in r:
    raise SystemExit('v129 registration generation field missing')
r = r.replace(field_anchor, field_anchor + '    private static final int REGISTRATION_JOB_ID = 49129;\n', 1)

# Replace token callback so a stale persisted "registering" state can never block
# recovery. Immediate registration is kept; JobScheduler is a background-safe fallback.
on_token_start = r.find('    public static void onNewToken(Context context, String token) {')
on_token_end = r.find('    public static void setMember(', on_token_start)
if on_token_start < 0 or on_token_end < 0:
    raise SystemExit('v129 onNewToken block missing')
on_token = '''    public static void onNewToken(Context context, String token) {
        Context app = context.getApplicationContext();
        SharedPreferences p = prefs(app);
        String safeToken = token == null ? "" : token.trim();
        String previousToken = p.getString(KEY_TOKEN, "");
        boolean tokenChanged = !previousToken.equals(safeToken);
        p.edit().putString(KEY_TOKEN, safeToken).apply();
        if (!pushEnabled(app) || safeToken.isEmpty()) return;

        boolean registered = p.getBoolean(KEY_REGISTERED, false);
        String status = p.getString(KEY_STATUS, "");
        long lastAttempt = p.getLong(KEY_REGISTER_JOB_AT, 0L);
        boolean staleAttempt = !"registering".equals(status) ||
                System.currentTimeMillis() - lastAttempt > 5000L;
        if (!registered && (tokenChanged || staleAttempt)) {
            long generation = REGISTRATION_GENERATION.incrementAndGet();
            registerCurrent(app, generation);
        }
        if (!registered) scheduleRegistrationJob(app);
    }

'''
r = r[:on_token_start] + on_token + r[on_token_end:]

# Same-member WebView sync should retry a stale interrupted registration instead of
# trusting the persisted word "registering" forever.
set_start = r.find('    public static void setMember(Context context, String memberId, String memberName) {')
set_end = r.find('    public static void clearMember(', set_start)
if set_start < 0 or set_end < 0:
    raise SystemExit('v129 setMember block missing')
set_block = r[set_start:set_end]
old_same = '''                    boolean registered = p.getBoolean(KEY_REGISTERED, false);
                    String status = p.getString(KEY_STATUS, "");
                    if (!registered && !"registering".equals(status)) registerCurrent(app);'''
new_same = '''                    boolean registered = p.getBoolean(KEY_REGISTERED, false);
                    String status = p.getString(KEY_STATUS, "");
                    long lastAttempt = p.getLong(KEY_REGISTER_JOB_AT, 0L);
                    boolean staleAttempt = !"registering".equals(status) ||
                            System.currentTimeMillis() - lastAttempt > 5000L;
                    if (!registered && staleAttempt) {
                        long retryGeneration = REGISTRATION_GENERATION.incrementAndGet();
                        registerCurrent(app, retryGeneration);
                    }
                    if (!registered) scheduleRegistrationJob(app);'''
if old_same not in set_block:
    raise SystemExit('v129 same-member retry anchor missing')
set_block = set_block.replace(old_same, new_same, 1)
old_changed = '''        if (pushEnabled(app)) {
            if (token.isEmpty()) ensureToken(app);
            else registerCurrent(app, generation);
        }
'''
new_changed = '''        if (pushEnabled(app)) {
            if (token.isEmpty()) ensureToken(app);
            else {
                registerCurrent(app, generation);
                scheduleRegistrationJob(app);
            }
        }
'''
if old_changed not in set_block:
    raise SystemExit('v129 changed-member registration anchor missing')
set_block = set_block.replace(old_changed, new_changed, 1)
r = r[:set_start] + set_block + r[set_end:]

# Mark the beginning of an immediate registration attempt. This gives same-member
# sync a short lease rather than a permanent stale lock.
reg_start = r.find('    private static void registerCurrent(Context context, long expectedGeneration) {')
reg_end = r.find('    private static boolean registrationStillCurrent(', reg_start)
if reg_start < 0 or reg_end < 0:
    raise SystemExit('v129 registerCurrent block missing')
reg_block = r[reg_start:reg_end]
status_write = 'p.edit().putBoolean(KEY_REGISTERED, false).putString(KEY_STATUS, "registering").apply();'
if status_write not in reg_block:
    raise SystemExit('v129 registration status write missing')
reg_block = reg_block.replace(
    status_write,
    'p.edit().putBoolean(KEY_REGISTERED, false).putString(KEY_STATUS, "registering")\n'
    '                .putLong(KEY_REGISTER_JOB_AT, System.currentTimeMillis()).apply();',
    1,
)
reg_block = reg_block.replace(
    '.putString(KEY_STATUS, "registration_failed")\n                        .apply();',
    '.putString(KEY_STATUS, "registration_failed")\n                        .putLong(KEY_REGISTER_JOB_AT, 0L)\n                        .apply();',
    1,
)
reg_block = reg_block.replace(
    '.putString(KEY_TESTED_KEY, "")\n                    .apply();',
    '.putString(KEY_TESTED_KEY, "")\n                    .putLong(KEY_REGISTER_JOB_AT, 0L)\n                    .apply();',
    1,
)
r = r[:reg_start] + reg_block + r[reg_end:]

# OS-managed background registration. JobScheduler can relaunch the user APK process
# after the user leaves the app, so server token ownership is not dependent on the
# WebView/activity remaining foreground.
helper_anchor = '    private static void stopPreviousMemberAlert(Context context) {'
helper_pos = r.find(helper_anchor)
if helper_pos < 0:
    raise SystemExit('v129 helper insertion anchor missing')
helpers = '''    public static boolean hasCompleteRegistrationInputs(Context context) {
        Context app = context.getApplicationContext();
        SharedPreferences p = prefs(app);
        return p.getBoolean(KEY_PUSH, true) &&
                !p.getString(KEY_MEMBER_ID, "").isEmpty() &&
                !p.getString(KEY_MEMBER_NAME, "").isEmpty() &&
                !p.getString(KEY_TOKEN, "").isEmpty();
    }

    public static void scheduleRegistrationJob(Context context) {
        Context app = context.getApplicationContext();
        if (!hasCompleteRegistrationInputs(app)) return;
        try {
            JobScheduler scheduler = (JobScheduler) app.getSystemService(Context.JOB_SCHEDULER_SERVICE);
            if (scheduler == null) return;
            ComponentName component = new ComponentName(app, NativeRegistrationJobService.class);
            JobInfo info = new JobInfo.Builder(REGISTRATION_JOB_ID, component)
                    .setRequiredNetworkType(JobInfo.NETWORK_TYPE_ANY)
                    .setMinimumLatency(1200L)
                    .setOverrideDeadline(5000L)
                    .setBackoffCriteria(30000L, JobInfo.BACKOFF_POLICY_EXPONENTIAL)
                    .build();
            scheduler.schedule(info);
        } catch (Exception ignored) {}
    }

    public static void cancelRegistrationJob(Context context) {
        try {
            JobScheduler scheduler = (JobScheduler) context.getApplicationContext()
                    .getSystemService(Context.JOB_SCHEDULER_SERVICE);
            if (scheduler != null) scheduler.cancel(REGISTRATION_JOB_ID);
        } catch (Exception ignored) {}
    }

    public static boolean registerCurrentBlocking(Context context) {
        Context app = context.getApplicationContext();
        SharedPreferences p = prefs(app);
        if (!p.getBoolean(KEY_PUSH, true)) return true;
        if (p.getBoolean(KEY_REGISTERED, false)) return true;
        final String id = p.getString(KEY_MEMBER_ID, "");
        final String name = p.getString(KEY_MEMBER_NAME, "");
        final String token = p.getString(KEY_TOKEN, "");
        if (id.isEmpty() || name.isEmpty() || token.isEmpty()) return true;

        p.edit().putBoolean(KEY_REGISTERED, false)
                .putString(KEY_STATUS, "registering")
                .putLong(KEY_REGISTER_JOB_AT, System.currentTimeMillis())
                .apply();
        NativeDeliveryReporter.report("token_register_job_started", "", true,
                true, false, false, false);
        JSONObject registered = submit("register_web_token", id, name, token);

        SharedPreferences current = prefs(app);
        boolean stillCurrent = id.equals(current.getString(KEY_MEMBER_ID, "")) &&
                token.equals(current.getString(KEY_TOKEN, "")) &&
                current.getBoolean(KEY_PUSH, true);
        if (!stillCurrent) {
            NativeDeliveryReporter.report("token_register_job_stale", "", false,
                    true, false, false, false);
            scheduleRegistrationJob(app);
            return false;
        }

        boolean ok = registered.optBoolean("ok", false);
        NativeDeliveryReporter.report(
                ok ? "token_register_job_http_ok" : "token_register_job_http_failed",
                "", true, true, false, false, false);
        current.edit()
                .putBoolean(KEY_REGISTERED, ok)
                .putString(KEY_STATUS, ok ? "token_registered" : "registration_failed")
                .putLong(KEY_REGISTER_JOB_AT, 0L)
                .apply();
        if (ok) cancelRegistrationJob(app);
        return ok;
    }

'''
r = r[:helper_pos] + helpers + r[helper_pos:]

# Clearing/disabling is intentionally explicit in diagnostics and cancels any queued job.
clear_start = r.find('    public static void clearMember(Context context) {')
clear_end = r.find('    public static void setPushEnabled(', clear_start)
clear_block = r[clear_start:clear_end]
clear_anchor = '        stopPreviousMemberAlert(app);\n'
if clear_anchor not in clear_block:
    raise SystemExit('v129 clear member alert anchor missing')
clear_block = clear_block.replace(
    clear_anchor,
    clear_anchor + '        cancelRegistrationJob(app);\n        NativeDeliveryReporter.report("member_cleared", "", false, true, false, false, false);\n',
    1,
)
r = r[:clear_start] + clear_block + r[clear_end:]

push_start = r.find('    public static void setPushEnabled(Context context, boolean enabled) {')
push_end = r.find('    public static void setVibrationEnabled(', push_start)
push_block = r[push_start:push_end]
if push_start < 0 or push_end < 0:
    raise SystemExit('v129 push block missing')
push_block = push_block.replace(
    '        if (enabled) {\n            ensureToken(app);',
    '        if (enabled) {\n            ensureToken(app);\n            scheduleRegistrationJob(app);',
    1,
)
push_block = push_block.replace(
    '            stopPreviousMemberAlert(app);\n',
    '            stopPreviousMemberAlert(app);\n            cancelRegistrationJob(app);\n            NativeDeliveryReporter.report("push_disabled", "", false, true, false, false, false);\n',
    1,
)
r = r[:push_start] + push_block + r[push_end:]

s = s[:registrar_start] + r + s[registrar_end:]

job_marker = '\nJAVA\n\ncat > "$REPORTER_JAVA"'
job_idx = s.find(job_marker, registrar_start)
if job_idx < 0:
    raise SystemExit('v129 reporter insertion marker missing')
job_java = r'''
JAVA

cat > "$REG_JOB_JAVA" <<'JAVA'
package com.jayuminton.admin;

import android.app.job.JobParameters;
import android.app.job.JobService;

public final class NativeRegistrationJobService extends JobService {
    @Override
    public boolean onStartJob(JobParameters params) {
        new Thread(() -> {
            boolean ok = NativePushRegistrar.registerCurrentBlocking(this);
            boolean retry = !ok && NativePushRegistrar.hasCompleteRegistrationInputs(this);
            jobFinished(params, retry);
        }, "jayuminton-registration-job").start();
        return true;
    }

    @Override
    public boolean onStopJob(JobParameters params) {
        return NativePushRegistrar.hasCompleteRegistrationInputs(this);
    }
}
JAVA

cat > "$REPORTER_JAVA"'''
s = s[:job_idx] + job_java + s[job_idx + len(job_marker):]

for required in (
    'VERSION="1.2.9"',
    'VERSION_CODE="129"',
    'APP_VERSION = "1.2.9"',
    'class NativeRegistrationJobService',
    'registerCurrentBlocking(Context context)',
    'scheduleRegistrationJob(Context context)',
    'token_register_job_http_ok',
    'token_register_job_http_failed',
    'member_cleared',
    'push_disabled',
    'jayuminton_wait1_native_v129',
    'jayuminton_court_native_v129',
    'AlertVibrationController.start(this, assignmentId)',
    'NativePushRegistrar.isCurrentMember(this, targetMemberId)',
):
    if required not in s:
        raise SystemExit('missing v1.2.9 background registration marker: ' + required)

path.write_text(s, encoding='utf-8')
print('Prepared v1.2.9 diagnostic candidate: immediate + JobScheduler background token registration, stale-registering recovery, v1.2.8 alert behavior preserved.')
