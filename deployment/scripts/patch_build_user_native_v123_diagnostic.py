#!/usr/bin/env python3
from pathlib import Path
import sys


path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

# This is a diagnostic-only build.  It deliberately preserves the v1.2.2
# notification/overlay/vibration behavior and adds path telemetry only.
for old, new in (
    ("v1.2.2-overlay.apk", "v1.2.3-diagnostic.apk"),
    ("user-native-push-v1.2.2.txt", "user-native-push-v1.2.3-diagnostic.txt"),
    ('VERSION="1.2.2"', 'VERSION="1.2.3"'),
    ('VERSION_CODE="122"', 'VERSION_CODE="123"'),
    ("versionCode 122", "versionCode 123"),
    ("versionCode='122'", "versionCode='123'"),
    ("versionName '1.2.2'", "versionName '1.2.3'"),
    ("versionName='1.2.2'", "versionName='1.2.3'"),
    ('USER_APP_VERSION = "1.2.2"', 'USER_APP_VERSION = "1.2.3"'),
    ("JayumintonUserNative/1.2.2", "JayumintonUserNative/1.2.3"),
    ("JayumintonNativeAndroid/1.2.2", "JayumintonNativeAndroid/1.2.3"),
    ('APP_VERSION = "1.2.2"', 'APP_VERSION = "1.2.3"'),
    ("version=1.2.2", "version=1.2.3"),
    ("version_code=122", "version_code=123"),
    ("jayuminton_wait1_native_v122", "jayuminton_wait1_native_v123_diag"),
    ("jayuminton_court_native_v122", "jayuminton_court_native_v123_diag"),
):
    s = s.replace(old, new)

# Replace the coarse v1.2.0 reporter with a richer reporter.  Raw member IDs,
# names, tokens and assignment IDs never leave the APK; only short SHA-256
# fingerprints are transmitted.
reporter_start = s.find('cat > "$REPORTER_JAVA" <<JAVA\n')
if reporter_start < 0:
    raise SystemExit("v123 reporter source start missing")
reporter_end = s.find('\nJAVA\n\n', reporter_start)
if reporter_end < 0:
    raise SystemExit("v123 reporter source end missing")
reporter_end += len('\nJAVA\n\n')
reporter_java = r'''cat > "$REPORTER_JAVA" <<JAVA
package com.jayuminton.admin;

import android.net.Uri;

import org.json.JSONObject;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class NativeDeliveryReporter {
    private static final String RELAY_URL = "${PUSH_URL}";
    private static final String APP_VERSION = "1.2.3";
    private static final ExecutorService EXECUTOR = Executors.newSingleThreadExecutor();

    private NativeDeliveryReporter() {}

    private static String hashValue(String value) {
        String input = value == null ? "" : value.trim();
        if (input.isEmpty()) return "";
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] bytes = digest.digest(input.getBytes(StandardCharsets.UTF_8));
            StringBuilder out = new StringBuilder();
            for (int i = 0; i < 10 && i < bytes.length; i++) {
                out.append(String.format(Locale.US, "%02x", bytes[i] & 0xff));
            }
            return out.toString();
        } catch (Exception ignored) {
            return "";
        }
    }

    // Compatibility for older instrumentation left in the generated source.
    public static void report(String stage, String eventType, boolean hasTargetMemberId,
                              boolean selectedMemberMatches, boolean notificationPosted,
                              boolean fullScreenAllowed, boolean vibrationCancelled) {
        reportPath(stage, eventType, "", "", "", selectedMemberMatches,
                notificationPosted, fullScreenAllowed, false,
                !vibrationCancelled, vibrationCancelled, "legacy", "");
    }

    public static void reportPath(String stage, String eventType, String courtNo,
                                  String targetMemberId, String selectedMemberId,
                                  boolean selectedMemberMatches, boolean notificationPosted,
                                  boolean fullScreenAllowed, boolean fullScreenAttempted,
                                  boolean vibrationActive, boolean vibrationCancelled,
                                  String source, String traceId) {
        EXECUTOR.execute(() -> {
            HttpURLConnection connection = null;
            try {
                JSONObject payload = new JSONObject();
                payload.put("action", "native_delivery_ack");
                payload.put("stage", stage == null ? "" : stage);
                payload.put("appVersion", APP_VERSION);
                payload.put("eventType", eventType == null ? "" : eventType);
                payload.put("courtNo", courtNo == null ? "" : courtNo);
                payload.put("targetMemberHash", hashValue(targetMemberId));
                payload.put("selectedMemberHash", hashValue(selectedMemberId));
                payload.put("selectedMemberMatches", selectedMemberMatches);
                payload.put("notificationPosted", notificationPosted);
                payload.put("fullScreenAllowed", fullScreenAllowed);
                payload.put("fullScreenAttempted", fullScreenAttempted);
                payload.put("vibrationActive", vibrationActive);
                payload.put("vibrationCancelled", vibrationCancelled);
                payload.put("source", source == null ? "" : source);
                payload.put("traceHash", hashValue(traceId));
                byte[] bytes = ("payload=" + Uri.encode(payload.toString()))
                        .getBytes(StandardCharsets.UTF_8);
                connection = (HttpURLConnection) new URL(RELAY_URL).openConnection();
                connection.setConnectTimeout(10000);
                connection.setReadTimeout(10000);
                connection.setRequestMethod("POST");
                connection.setInstanceFollowRedirects(false);
                connection.setDoOutput(true);
                connection.setRequestProperty(
                        "Content-Type", "application/x-www-form-urlencoded;charset=UTF-8");
                connection.setFixedLengthStreamingMode(bytes.length);
                try (OutputStream output = connection.getOutputStream()) { output.write(bytes); }
                int code = connection.getResponseCode();
                try {
                    if (code >= 200 && code < 400 && connection.getInputStream() != null) {
                        connection.getInputStream().close();
                    } else if (connection.getErrorStream() != null) {
                        connection.getErrorStream().close();
                    }
                } catch (Exception ignored) {}
            } catch (Exception ignored) {
            } finally {
                if (connection != null) connection.disconnect();
            }
        });
    }
}
JAVA

'''
s = s[:reporter_start] + reporter_java + s[reporter_end:]

# Native selected-member introspection for receive-time comparison logging.
member_anchor = '''    public static boolean isCurrentMember(Context context, String memberId) {
        String current = prefs(context.getApplicationContext()).getString(KEY_MEMBER_ID, "");
        return !current.isEmpty() && current.equals(String.valueOf(memberId == null ? "" : memberId).trim());
    }
'''
if s.count(member_anchor) != 1:
    raise SystemExit("v123 current member helper anchor missing")
member_replacement = member_anchor + '''
    public static String currentMemberId(Context context) {
        return prefs(context.getApplicationContext()).getString(KEY_MEMBER_ID, "");
    }
'''
s = s.replace(member_anchor, member_replacement, 1)

# Record the exact moment a newly selected member becomes the native target.
member_save = '''        p.edit().putString(KEY_MEMBER_ID, newId).putString(KEY_MEMBER_NAME, newName).apply();
        if (pushEnabled(app)) {'''
member_save_new = '''        p.edit().putString(KEY_MEMBER_ID, newId).putString(KEY_MEMBER_NAME, newName).apply();
        NativeDeliveryReporter.reportPath("member_changed", "", "", newId, newId,
                !newId.isEmpty(), false, false, false, false, false,
                "native_member_selection", "");
        if (pushEnabled(app)) {'''
if s.count(member_save) != 1:
    raise SystemExit("v123 member change reporter anchor missing")
s = s.replace(member_save, member_save_new, 1)

register_anchor = '''        if (id.isEmpty() || token.isEmpty()) return;
        submitAsync("register_web_token", id, name, token);'''
register_new = '''        if (id.isEmpty() || token.isEmpty()) return;
        NativeDeliveryReporter.reportPath("token_register_requested", "", "", id, id,
                true, false, false, false, false, false,
                "native_registrar", "");
        submitAsync("register_web_token", id, name, token);'''
if s.count(register_anchor) != 1:
    raise SystemExit("v123 native token registration anchor missing")
s = s.replace(register_anchor, register_new, 1)

http_anchor = '''            int code = connection.getResponseCode();
            if (code >= 200 && code < 400) {
                try { if (connection.getInputStream() != null) connection.getInputStream().close(); } catch (Exception ignored) {}
            } else {
                try { if (connection.getErrorStream() != null) connection.getErrorStream().close(); } catch (Exception ignored) {}
            }
        } catch (Exception ignored) {
        } finally {'''
http_new = '''            int code = connection.getResponseCode();
            if (code >= 200 && code < 400) {
                try { if (connection.getInputStream() != null) connection.getInputStream().close(); } catch (Exception ignored) {}
                if ("register_web_token".equals(action)) {
                    NativeDeliveryReporter.reportPath("token_register_http_ok", "", "",
                            memberId, memberId, true, false, false, false,
                            false, false, "native_registrar_http", "");
                }
            } else {
                try { if (connection.getErrorStream() != null) connection.getErrorStream().close(); } catch (Exception ignored) {}
                if ("register_web_token".equals(action)) {
                    NativeDeliveryReporter.reportPath("token_register_http_failed", "", "",
                            memberId, memberId, true, false, false, false,
                            false, false, "native_registrar_http", "");
                }
            }
        } catch (Exception ignored) {
            if ("register_web_token".equals(action)) {
                NativeDeliveryReporter.reportPath("token_register_http_failed", "", "",
                        memberId, memberId, true, false, false, false,
                        false, false, "native_registrar_exception", "");
            }
        } finally {'''
if s.count(http_anchor) != 1:
    raise SystemExit("v123 registrar HTTP reporter anchor missing")
s = s.replace(http_anchor, http_new, 1)

# Replace coarse receive logging with enough privacy-safe context to determine
# whether this installed APK really handled the FCM message and accepted it.
receive_old = '''        String targetMemberId = value(data, "memberId", "");
        boolean hasTargetMemberId = !targetMemberId.isEmpty();
        boolean selectedMemberMatches = !hasTargetMemberId || NativePushRegistrar.isCurrentMember(this, targetMemberId);
        NativeDeliveryReporter.report("fcm_received", type, hasTargetMemberId,
                selectedMemberMatches, false, false, false);
        if (!selectedMemberMatches) {
            NativeDeliveryReporter.report("member_rejected", type, true, false, false, false, false);
            return;
        }
        NativeDeliveryReporter.report("member_accepted", type, hasTargetMemberId,
                true, false, false, false);
        String courtNo = value(data, "courtNo", "");'''
receive_new = '''        String targetMemberId = value(data, "memberId", "");
        String selectedMemberId = NativePushRegistrar.currentMemberId(this);
        String courtNo = value(data, "courtNo", "");
        boolean hasTargetMemberId = !targetMemberId.isEmpty();
        boolean selectedMemberMatches = !hasTargetMemberId ||
                (!selectedMemberId.isEmpty() && selectedMemberId.equals(targetMemberId));
        NativeDeliveryReporter.reportPath("fcm_received", type, courtNo,
                targetMemberId, selectedMemberId, selectedMemberMatches,
                false, false, false, false, false,
                "native_fcm_service", assignmentIdSafe(data));
        if (!selectedMemberMatches) {
            NativeDeliveryReporter.reportPath("member_rejected", type, courtNo,
                    targetMemberId, selectedMemberId, false,
                    false, false, false, false, false,
                    "native_fcm_service", assignmentIdSafe(data));
            return;
        }
        NativeDeliveryReporter.reportPath("member_accepted", type, courtNo,
                targetMemberId, selectedMemberId, true,
                false, false, false, false, false,
                "native_fcm_service", assignmentIdSafe(data));'''
if s.count(receive_old) != 1:
    raise SystemExit("v123 detailed FCM receive anchor missing")
s = s.replace(receive_old, receive_new, 1)

# Small helper lets receive telemetry fingerprint assignmentId before the normal
# fallback assignmentId variable is created, without ever transmitting it raw.
value_anchor = '''    private static String value(Map<String, String> data, String key, String fallback) {
        if (data == null) return fallback;
        String value = data.get(key);
        return value == null || value.trim().isEmpty() ? fallback : value;
    }
'''
if s.count(value_anchor) != 1:
    raise SystemExit("v123 FCM value helper anchor missing")
value_new = value_anchor + '''
    private static String assignmentIdSafe(Map<String, String> data) {
        if (data == null) return "";
        String value = data.get("assignmentId");
        return value == null ? "" : value;
    }
'''
s = s.replace(value_anchor, value_new, 1)

# Add context extras and route-source information to the existing center
# Activity.  This changes no visible UI.
activity_start = s.find('cat > "$ALERT_JAVA" <<\'JAVA\'\n')
activity_end = s.find('\nJAVA\n\n', activity_start)
if activity_start < 0 or activity_end < 0:
    raise SystemExit("v123 alert activity segment missing")
activity_end += len('\nJAVA\n\n')
a = s[activity_start:activity_end]
a = a.replace(
    '    public static final String EXTRA_NOTIFICATION_ID = "assignment_notification_id";\n    private int notificationId;',
    '''    public static final String EXTRA_NOTIFICATION_ID = "assignment_notification_id";
    public static final String EXTRA_EVENT_TYPE = "assignment_event_type";
    public static final String EXTRA_COURT_NO = "assignment_court_no";
    public static final String EXTRA_TARGET_MEMBER_ID = "assignment_target_member_id";
    public static final String EXTRA_TRACE_ID = "assignment_trace_id";
    private int notificationId;
    private String eventType = "";
    private String courtNo = "";
    private String targetMemberId = "";
    private String traceId = "";''',
    1,
)
a = a.replace(
    '''        String body = getIntent().getStringExtra(EXTRA_BODY);

        LinearLayout panel''',
    '''        String body = getIntent().getStringExtra(EXTRA_BODY);
        eventType = String.valueOf(getIntent().getStringExtra(EXTRA_EVENT_TYPE) == null ? "" : getIntent().getStringExtra(EXTRA_EVENT_TYPE));
        courtNo = String.valueOf(getIntent().getStringExtra(EXTRA_COURT_NO) == null ? "" : getIntent().getStringExtra(EXTRA_COURT_NO));
        targetMemberId = String.valueOf(getIntent().getStringExtra(EXTRA_TARGET_MEMBER_ID) == null ? "" : getIntent().getStringExtra(EXTRA_TARGET_MEMBER_ID));
        traceId = String.valueOf(getIntent().getStringExtra(EXTRA_TRACE_ID) == null ? "" : getIntent().getStringExtra(EXTRA_TRACE_ID));
        NativeDeliveryReporter.reportPath("full_screen_attempted", eventType, courtNo,
                targetMemberId, NativePushRegistrar.currentMemberId(this),
                NativePushRegistrar.isCurrentMember(this, targetMemberId),
                true, true, true, false, false,
                "alert_activity_created", traceId);

        LinearLayout panel''',
    1,
)
a = a.replace(
    '        confirm.setOnClickListener(view -> dismissAlert());',
    '        confirm.setOnClickListener(view -> dismissAlert("center_confirm"));',
    1,
)
a = a.replace(
    '    private void dismissAlert() {\n',
    '''    private void dismissAlert(String source) {
        String selected = NativePushRegistrar.currentMemberId(this);
        NativeDeliveryReporter.reportPath(
                "center_confirm".equals(source) ? "confirm_action" : "dismiss_action",
                eventType, courtNo, targetMemberId, selected,
                NativePushRegistrar.isCurrentMember(this, targetMemberId),
                true, true, true, true, false, source, traceId);
''',
    1,
)
a = a.replace(
    '        if (vibrator != null) vibrator.cancel();\n        finishAndRemoveTask();',
    '''        if (vibrator != null) vibrator.cancel();
        NativeDeliveryReporter.reportPath("vibration_cancelled", eventType, courtNo,
                targetMemberId, selected,
                NativePushRegistrar.isCurrentMember(this, targetMemberId),
                true, true, true, false, true, source, traceId);
        finishAndRemoveTask();''',
    1,
)
a = a.replace(
    '    @Override public void onBackPressed() { dismissAlert(); }',
    '    @Override public void onBackPressed() { dismissAlert("center_back"); }',
    1,
)
for marker in ('EXTRA_EVENT_TYPE', 'alert_activity_created', 'confirm_action', 'center_confirm'):
    if marker not in a:
        raise SystemExit("v123 alert activity marker missing: " + marker)
s = s[:activity_start] + a + s[activity_end:]

# Instrument the overlay itself.  Reporting from inside addView() tells us
# whether permission existed AND whether Android actually accepted the center
# overlay, which the old boolean return value could not prove.
overlay_start = s.find('cat > "$OVERLAY_JAVA" <<\'JAVA\'\n')
overlay_end = s.find('\nJAVA\n\n', overlay_start)
if overlay_start < 0 or overlay_end < 0:
    raise SystemExit("v123 overlay segment missing")
overlay_end += len('\nJAVA\n\n')
o = s[overlay_start:overlay_end]
o = o.replace(
    '    public static boolean show(Context context, String title, String body, int notificationId) {',
    '''    public static boolean show(Context context, String title, String body, int notificationId,
                               String eventType, String courtNo, String targetMemberId,
                               String traceId) {''',
    1,
)
o = o.replace(
    '''        Context app = context.getApplicationContext();
        if (!canShow(app)) return false;
        MAIN.post(() -> {''',
    '''        Context app = context.getApplicationContext();
        String selected = NativePushRegistrar.currentMemberId(app);
        boolean allowed = canShow(app);
        NativeDeliveryReporter.reportPath("full_screen_capability", eventType, courtNo,
                targetMemberId, selected,
                NativePushRegistrar.isCurrentMember(app, targetMemberId),
                false, allowed, false, false, false,
                allowed ? "overlay_permission_allowed" : "overlay_permission_denied", traceId);
        if (!allowed) return false;
        MAIN.post(() -> {''',
    1,
)
o = o.replace(
    '            confirm.setOnClickListener(view -> stopEverything(app, notificationId));',
    '''            confirm.setOnClickListener(view -> stopEverything(app, notificationId,
                    eventType, courtNo, targetMemberId, traceId));''',
    1,
)
o = o.replace(
    '''            try { windowManager.addView(panel, params); }
            catch (Exception ignored) { activeView = null; }''',
    '''            try {
                windowManager.addView(panel, params);
                NativeDeliveryReporter.reportPath("full_screen_attempted", eventType, courtNo,
                        targetMemberId, NativePushRegistrar.currentMemberId(app),
                        NativePushRegistrar.isCurrentMember(app, targetMemberId),
                        false, true, true, false, false,
                        "overlay_added", traceId);
            } catch (Exception ignored) {
                activeView = null;
                NativeDeliveryReporter.reportPath("full_screen_attempted", eventType, courtNo,
                        targetMemberId, NativePushRegistrar.currentMemberId(app),
                        NativePushRegistrar.isCurrentMember(app, targetMemberId),
                        false, true, true, false, false,
                        "overlay_add_failed", traceId);
            }''',
    1,
)
o = o.replace(
    '    public static void stopEverything(Context context, int notificationId) {\n',
    '''    public static void stopEverything(Context context, int notificationId,
                                      String eventType, String courtNo,
                                      String targetMemberId, String traceId) {
        String selected = NativePushRegistrar.currentMemberId(context);
        NativeDeliveryReporter.reportPath("confirm_action", eventType, courtNo,
                targetMemberId, selected,
                NativePushRegistrar.isCurrentMember(context, targetMemberId),
                true, true, true, true, false,
                "overlay_confirm", traceId);
''',
    1,
)
o = o.replace(
    '''        if (vibrator != null) vibrator.cancel();
        NativeDeliveryReporter.report("vibration_cancelled", "", false,
                true, true, true, true);''',
    '''        if (vibrator != null) vibrator.cancel();
        NativeDeliveryReporter.reportPath("vibration_cancelled", eventType, courtNo,
                targetMemberId, selected,
                NativePushRegistrar.isCurrentMember(context, targetMemberId),
                true, true, true, false, true,
                "overlay_confirm", traceId);''',
    1,
)
for marker in ('overlay_permission_allowed', 'overlay_added', 'overlay_add_failed', 'overlay_confirm'):
    if marker not in o:
        raise SystemExit("v123 overlay marker missing: " + marker)
s = s[:overlay_start] + o + s[overlay_end:]

# Receiver: keep the same cancel behavior but distinguish the top action from a
# swipe-delete and record both the action and the actual vibrator cancellation.
receiver_start = s.find('cat > "$DISMISS_JAVA" <<\'JAVA\'\n')
receiver_end = s.find('\nJAVA\n\n', receiver_start)
if receiver_start < 0 or receiver_end < 0:
    raise SystemExit("v123 dismiss receiver segment missing")
receiver_end += len('\nJAVA\n\n')
r = s[receiver_start:receiver_end]
r = r.replace(
    '    public static final String ACTION_DISMISS = "com.jayuminton.user.DISMISS_ASSIGNMENT_ALERT";',
    '''    public static final String ACTION_DISMISS = "com.jayuminton.user.DISMISS_ASSIGNMENT_ALERT";
    public static final String EXTRA_SOURCE = "dismiss_source";
    public static final String EXTRA_EVENT_TYPE = "dismiss_event_type";
    public static final String EXTRA_COURT_NO = "dismiss_court_no";
    public static final String EXTRA_TARGET_MEMBER_ID = "dismiss_target_member_id";
    public static final String EXTRA_TRACE_ID = "dismiss_trace_id";''',
    1,
)
r = r.replace(
    '''        NotificationManager notifications =
                (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);''',
    '''        String source = intent == null ? "notification_action" :
                String.valueOf(intent.getStringExtra(EXTRA_SOURCE) == null ?
                        "notification_action" : intent.getStringExtra(EXTRA_SOURCE));
        String eventType = intent == null ? "" : String.valueOf(
                intent.getStringExtra(EXTRA_EVENT_TYPE) == null ? "" : intent.getStringExtra(EXTRA_EVENT_TYPE));
        String courtNo = intent == null ? "" : String.valueOf(
                intent.getStringExtra(EXTRA_COURT_NO) == null ? "" : intent.getStringExtra(EXTRA_COURT_NO));
        String targetMemberId = intent == null ? "" : String.valueOf(
                intent.getStringExtra(EXTRA_TARGET_MEMBER_ID) == null ? "" : intent.getStringExtra(EXTRA_TARGET_MEMBER_ID));
        String traceId = intent == null ? "" : String.valueOf(
                intent.getStringExtra(EXTRA_TRACE_ID) == null ? "" : intent.getStringExtra(EXTRA_TRACE_ID));
        String selected = NativePushRegistrar.currentMemberId(context);
        NativeDeliveryReporter.reportPath(
                "notification_deleted".equals(source) ? "notification_deleted" : "dismiss_action",
                eventType, courtNo, targetMemberId, selected,
                NativePushRegistrar.isCurrentMember(context, targetMemberId),
                true, true, false, true, false, source, traceId);

        NotificationManager notifications =
                (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);''',
    1,
)
r = r.replace(
    '''        if (vibrator != null) vibrator.cancel();
        AssignmentOverlay.dismissOnly();
        NativeDeliveryReporter.report("vibration_cancelled", "", false,
                true, true, false, true);''',
    '''        if (vibrator != null) vibrator.cancel();
        AssignmentOverlay.dismissOnly();
        NativeDeliveryReporter.reportPath("vibration_cancelled", eventType, courtNo,
                targetMemberId, selected,
                NativePushRegistrar.isCurrentMember(context, targetMemberId),
                true, true, false, false, true, source, traceId);''',
    1,
)
for marker in ('EXTRA_SOURCE', 'notification_deleted', 'dismiss_action'):
    if marker not in r:
        raise SystemExit("v123 receiver marker missing: " + marker)
s = s[:receiver_start] + r + s[receiver_end:]

# Notification/full-screen/overlay/vibration instrumentation in the FCM service.
service_start = s.find("cat > \"$SERVICE_JAVA\" <<'JAVA'\n")
service_end = s.find('\nJAVA\n\n', service_start)
if service_start < 0 or service_end < 0:
    raise SystemExit("v123 FCM service segment missing")
service_end += len('\nJAVA\n\n')
f = s[service_start:service_end]

# Actual notification-post success is more useful than merely reaching the call.
f = f.replace(
    '    private void showNotification(boolean court, String title, String body, String assignmentId) {',
    '''    private boolean showNotification(boolean court, String title, String body,
                                     String assignmentId, String type, String courtNo,
                                     String targetMemberId) {''',
    1,
)
f = f.replace('        if (manager == null) return;', '        if (manager == null) return false;', 1)

# Give both center Activity and stop receiver enough local context; the reporter
# hashes IDs before network transmission.
f = f.replace(
    '''        alertIntent.putExtra(AssignmentAlertActivity.EXTRA_NOTIFICATION_ID, notificationId);''',
    '''        alertIntent.putExtra(AssignmentAlertActivity.EXTRA_NOTIFICATION_ID, notificationId);
        alertIntent.putExtra(AssignmentAlertActivity.EXTRA_EVENT_TYPE, type);
        alertIntent.putExtra(AssignmentAlertActivity.EXTRA_COURT_NO, courtNo);
        alertIntent.putExtra(AssignmentAlertActivity.EXTRA_TARGET_MEMBER_ID, targetMemberId);
        alertIntent.putExtra(AssignmentAlertActivity.EXTRA_TRACE_ID, assignmentId);''',
    1,
)
f = f.replace(
    '''        dismissIntent.putExtra(AlertDismissReceiver.EXTRA_NOTIFICATION_ID, notificationId);
        PendingIntent dismissPending = PendingIntent.getBroadcast(''',
    '''        dismissIntent.putExtra(AlertDismissReceiver.EXTRA_NOTIFICATION_ID, notificationId);
        dismissIntent.putExtra(AlertDismissReceiver.EXTRA_SOURCE, "notification_action");
        dismissIntent.putExtra(AlertDismissReceiver.EXTRA_EVENT_TYPE, type);
        dismissIntent.putExtra(AlertDismissReceiver.EXTRA_COURT_NO, courtNo);
        dismissIntent.putExtra(AlertDismissReceiver.EXTRA_TARGET_MEMBER_ID, targetMemberId);
        dismissIntent.putExtra(AlertDismissReceiver.EXTRA_TRACE_ID, assignmentId);
        PendingIntent dismissPending = PendingIntent.getBroadcast(''',
    1,
)
# Insert a distinct delete PendingIntent after the existing dismiss one.
dismiss_pending_end = '''                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );'''
pos = f.find(dismiss_pending_end, f.find('PendingIntent dismissPending'))
if pos < 0:
    raise SystemExit("v123 dismiss pending end missing")
pos += len(dismiss_pending_end)
delete_block = '''
        Intent deleteIntent = new Intent(this, AlertDismissReceiver.class);
        deleteIntent.setAction(AlertDismissReceiver.ACTION_DISMISS + ".delete." + assignmentId);
        deleteIntent.putExtra(AlertDismissReceiver.EXTRA_NOTIFICATION_ID, notificationId);
        deleteIntent.putExtra(AlertDismissReceiver.EXTRA_SOURCE, "notification_deleted");
        deleteIntent.putExtra(AlertDismissReceiver.EXTRA_EVENT_TYPE, type);
        deleteIntent.putExtra(AlertDismissReceiver.EXTRA_COURT_NO, courtNo);
        deleteIntent.putExtra(AlertDismissReceiver.EXTRA_TARGET_MEMBER_ID, targetMemberId);
        deleteIntent.putExtra(AlertDismissReceiver.EXTRA_TRACE_ID, assignmentId);
        PendingIntent deletePending = PendingIntent.getBroadcast(
                this,
                notificationId ^ 0x5A5A,
                deleteIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );'''
f = f[:pos] + delete_block + f[pos:]
f = f.replace('.setDeleteIntent(dismissPending)', '.setDeleteIntent(deletePending)', 1)
f = f.replace(
    '        manager.notify(notificationId, builder.build());',
    '        manager.notify(notificationId, builder.build());\n        return true;',
    1,
)

flow_old = '''        configureAlertVolumes();
        int notificationId = assignmentId.hashCode();
        boolean overlayShown = AssignmentOverlay.show(this, title, body, notificationId);
        showNotification(court, title, body, assignmentId);
        boolean fullScreenAllowed = true;
        if (Build.VERSION.SDK_INT >= 34) {
            NotificationManager notificationManager =
                    (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
            fullScreenAllowed = notificationManager != null && notificationManager.canUseFullScreenIntent();
        }
        NativeDeliveryReporter.report("notification_posted", type, hasTargetMemberId,
                true, true, fullScreenAllowed, false);
        // Diagnostic build uses a finite waveform so a blocked button can never
        // leave the tester with an unstoppable vibration.
        vibrateStrong(court ? 5 : 3, overlayShown);'''
flow_new = '''        configureAlertVolumes();
        int notificationId = assignmentId.hashCode();
        boolean systemFullScreenAllowed = true;
        if (Build.VERSION.SDK_INT >= 34) {
            NotificationManager notificationManager =
                    (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
            systemFullScreenAllowed = notificationManager != null &&
                    notificationManager.canUseFullScreenIntent();
        }
        NativeDeliveryReporter.reportPath("full_screen_capability", type, courtNo,
                targetMemberId, selectedMemberId, true,
                false, systemFullScreenAllowed, false, false, false,
                "notification_fullscreen", assignmentId);
        boolean overlayShown = AssignmentOverlay.show(this, title, body, notificationId,
                type, courtNo, targetMemberId, assignmentId);
        boolean notificationPosted = showNotification(court, title, body, assignmentId,
                type, courtNo, targetMemberId);
        NativeDeliveryReporter.reportPath("notification_posted", type, courtNo,
                targetMemberId, selectedMemberId, true,
                notificationPosted, systemFullScreenAllowed, false, false, false,
                "native_notification_manager", assignmentId);
        boolean vibrationActive = vibrateStrong(court ? 5 : 3, overlayShown);
        NativeDeliveryReporter.reportPath("vibration_started", type, courtNo,
                targetMemberId, selectedMemberId, true,
                notificationPosted, systemFullScreenAllowed, false,
                vibrationActive, false, "native_vibrator", assignmentId);'''
if f.count(flow_old) != 1:
    raise SystemExit("v123 FCM alert flow anchor missing")
f = f.replace(flow_old, flow_new, 1)

f = f.replace(
    '    private void vibrateStrong(int groups, boolean repeatUntilConfirmed) {',
    '    private boolean vibrateStrong(int groups, boolean repeatUntilConfirmed) {',
    1,
)
f = f.replace(
    '        if (vibrator == null || !vibrator.hasVibrator()) return;',
    '        if (vibrator == null || !vibrator.hasVibrator()) return false;',
    1,
)
# Add a true return after the legacy/modern vibrate branch, immediately before method close.
vibrate_tail = '''        } else {
            vibrator.vibrate(timings, repeatUntilConfirmed ? 0 : -1);
        }
    }
}'''
vibrate_tail_new = '''        } else {
            vibrator.vibrate(timings, repeatUntilConfirmed ? 0 : -1);
        }
        return true;
    }
}'''
if f.count(vibrate_tail) != 1:
    raise SystemExit("v123 vibrator return anchor missing")
f = f.replace(vibrate_tail, vibrate_tail_new, 1)

for marker in (
    'boolean notificationPosted = showNotification',
    'notification_fullscreen',
    'native_notification_manager',
    'vibration_started',
    'return true;',
    'deletePending',
    'AssignmentOverlay.show(this, title, body, notificationId,',
):
    if marker not in f:
        raise SystemExit("v123 FCM service marker missing: " + marker)
s = s[:service_start] + f + s[service_end:]

# Build-time assertions: diagnostics must be present while all user-facing
# required behavior from v1.2.2 remains intact.
for marker in (
    'VERSION="1.2.3"',
    'VERSION_CODE="123"',
    'class NativeDeliveryReporter',
    'reportPath("fcm_received"',
    'reportPath("member_rejected"',
    'reportPath("member_accepted"',
    'reportPath("notification_posted"',
    'reportPath("full_screen_capability"',
    'reportPath("full_screen_attempted"',
    'reportPath("confirm_action"',
    'reportPath("vibration_cancelled"',
    '"token_register_requested"',
    '"token_register_http_ok"',
    '"token_register_http_failed"',
    '"notification_deleted"',
    '"확인 · 진동 끄기"',
    'confirm.setText("확인하고 닫기")',
    '"대기 1순위입니다. 라켓 들고 준비하세요."',
    'courtNo + "번 코트로 들어가세요."',
    '.setDeleteIntent(deletePending)',
    'android.permission.SYSTEM_ALERT_WINDOW',
    'NativePushRegistrar.currentMemberId',
):
    if marker not in s:
        raise SystemExit("missing native v1.2.3 diagnostic marker: " + marker)

path.write_text(s, encoding="utf-8")
print("Prepared one-time v1.2.3 native receive-path diagnostic APK without changing live install routing.")
