#!/usr/bin/env python3
from pathlib import Path
import sys


path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

for old, new in (
    ("v1.1.4-fresh-install.apk", "v1.1.5-fresh-install.apk"),
    ("user-native-push-v1.1.4.txt", "user-native-push-v1.1.5.txt"),
    ('VERSION="1.1.4"', 'VERSION="1.1.5"'),
    ('VERSION_CODE="114"', 'VERSION_CODE="115"'),
    ("versionCode 114", "versionCode 115"),
    ("versionCode='114'", "versionCode='115'"),
    ("versionName '1.1.4'", "versionName '1.1.5'"),
    ("versionName='1.1.4'", "versionName='1.1.5'"),
    ('USER_APP_VERSION = "1.1.4"', 'USER_APP_VERSION = "1.1.5"'),
    ("JayumintonUserNative/1.1.4", "JayumintonUserNative/1.1.5"),
    ("__JAYUMINTON_USER_APK_VERSION__='1.1.4'", "__JAYUMINTON_USER_APK_VERSION__='1.1.5'"),
    ("jayuminton_native_push_v114", "jayuminton_native_push_v115"),
    ("JayumintonNativeAndroid/1.1.4", "JayumintonNativeAndroid/1.1.5"),
    ("version=1.1.4", "version=1.1.5"),
    ("version_code=114", "version_code=115"),
    ("__JAYUMINTON_NATIVE_DIRECT_V114__", "__JAYUMINTON_NATIVE_DIRECT_V115__"),
):
    s = s.replace(old, new)

# Native diagnostics report real Android permission/channel state instead of
# inferring readiness from the existence of Java code.
old = '''import android.content.Context;
import android.content.SharedPreferences;
import android.net.Uri;'''
new = '''import android.Manifest;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;'''
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit("v115 Android diagnostic imports insertion point missing")

old = '''    private static final String KEY_TESTED_KEY = "tested_registration_key";
    private static final String RELAY_URL = "${PUSH_URL}";'''
new = '''    private static final String KEY_TESTED_KEY = "tested_registration_key";
    private static final String KEY_FCM_MESSAGE_ID = "fcm_test_message_id";
    private static final String KEY_FCM_ERROR = "fcm_test_error";
    private static final String RELAY_URL = "${PUSH_URL}";'''
if "KEY_FCM_MESSAGE_ID" not in s:
    if old not in s:
        raise SystemExit("v115 preference insertion point missing")
    s = s.replace(old, new, 1)

start = s.find("    private static void registerCurrent(Context context) {")
end = s.find("    public static String registrationStatus(Context context) {", start)
if start < 0 or end < 0:
    raise SystemExit("v115 registerCurrent block missing")
replacement = '''    private static void registerCurrent(Context context) {
        Context app = context.getApplicationContext();
        SharedPreferences p = prefs(app);
        final String id = p.getString(KEY_MEMBER_ID, "");
        final String name = p.getString(KEY_MEMBER_NAME, "");
        final String token = p.getString(KEY_TOKEN, "");
        if (id.isEmpty() || name.isEmpty() || token.isEmpty()) return;
        p.edit().putBoolean(KEY_REGISTERED, false).putString(KEY_STATUS, "registering").apply();
        EXECUTOR.execute(() -> {
            JSONObject registered = submit("register_web_token", id, name, token);
            boolean registrationOk = registered.optBoolean("ok", false);
            if (!registrationOk) {
                prefs(app).edit().putBoolean(KEY_REGISTERED, false)
                        .putString(KEY_STATUS, "registration_failed")
                        .putString(KEY_FCM_ERROR, registered.optString("error", "registration_failed"))
                        .apply();
                return;
            }

            String testedKey = id + ":" + sha256(token);
            SharedPreferences latest = prefs(app);
            boolean alreadyTested = testedKey.equals(latest.getString(KEY_TESTED_KEY, ""));
            JSONObject tested = alreadyTested ? null : submit("test_native_push", id, name, token);
            boolean deliveryAccepted = alreadyTested || (tested != null
                    && tested.optBoolean("ok", false)
                    && !tested.optString("messageId", "").isEmpty());
            latest.edit()
                    .putBoolean(KEY_REGISTERED, deliveryAccepted)
                    .putString(KEY_STATUS, deliveryAccepted ? "fcm_accepted" : "fcm_test_failed")
                    .putString(KEY_TESTED_KEY, deliveryAccepted ? testedKey : "")
                    .putString(KEY_FCM_MESSAGE_ID, tested == null ? latest.getString(KEY_FCM_MESSAGE_ID, "") : tested.optString("messageId", ""))
                    .putString(KEY_FCM_ERROR, tested == null ? "" : tested.optString("error", ""))
                    .apply();
        });
    }

'''
s = s[:start] + replacement + s[end:]

old = '''        @JavascriptInterface public void testNativeAlert() {
            NativeAlertProbe.show(MainActivity.this, "자유민턴 테스트", "팝업·강한 진동이 정상 작동합니다.", "manual-test");
        }
    }'''
new = '''        @JavascriptInterface public void testNativeAlert() {
            NativeAlertProbe.show(MainActivity.this, "자유민턴 테스트", "팝업·강한 진동이 정상 작동합니다.", "manual-test");
        }
        @JavascriptInterface public void retryServerPushTest() {
            NativePushRegistrar.retryCurrent(MainActivity.this);
        }
    }'''
if 'retryServerPushTest()' not in s:
    if old not in s:
        raise SystemExit("v115 diagnostic bridge insertion point missing")
    s = s.replace(old, new, 1)

old = '''                    null
                );
            }
        });'''
new = '''                    null
                );
                view.evaluateJavascript(
                    "(function(){if(window.__JAYUMINTON_NATIVE_STATUS_UI__)return;window.__JAYUMINTON_NATIVE_STATUS_UI__=1;" +
                    "var box=document.createElement('div');box.id='jayuminton-native-status';" +
                    "box.style.cssText='position:fixed;left:8px;right:8px;bottom:76px;z-index:2147483646;background:#102a43;color:white;padding:9px 10px;border-radius:10px;font:12px sans-serif;box-shadow:0 3px 12px #0005';" +
                    "var label=document.createElement('div');label.textContent='알림 연결 확인 중…';box.appendChild(label);" +
                    "var local=document.createElement('button');local.textContent='휴대폰 자체 테스트';local.style.cssText='margin-top:7px;margin-right:6px;padding:5px 8px';local.onclick=function(){NativeUserApp.testNativeAlert();};box.appendChild(local);" +
                    "var server=document.createElement('button');server.textContent='서버 실제발송 재확인';server.style.cssText='margin-top:7px;padding:5px 8px';server.onclick=function(){NativeUserApp.retryServerPushTest();label.textContent='서버 실제발송 확인 중…';};box.appendChild(server);" +
                    "document.body.appendChild(box);function refresh(){try{var s=JSON.parse(NativeUserApp.getPushRegistrationStatus());" +
                    "var ok=s.status==='fcm_accepted'&&s.notificationPermission&&s.waitChannelImportance>=4&&s.courtChannelImportance>=4;" +
                    "label.textContent=(ok?'✅ ':'⚠️ ')+s.status+' · 권한 '+(s.notificationPermission?'허용':'거부')+' · 채널 '+s.waitChannelImportance+'/'+s.courtChannelImportance+(s.fcmError?' · '+s.fcmError:'');" +
                    "box.style.background=ok?'#146c43':'#8a3b12';}catch(e){label.textContent='⚠️ 상태 읽기 실패';}}refresh();setInterval(refresh,1500);})();",
                    null
                );
            }
        });'''
if 'jayuminton-native-status' not in s:
    if s.count(old) != 1:
        raise SystemExit("v115 diagnostic UI insertion point missing")
    s = s.replace(old, new, 1)

anchor = '''    public static String registrationStatus(Context context) {'''
retry = '''    public static void retryCurrent(Context context) {
        Context app = context.getApplicationContext();
        prefs(app).edit().putString(KEY_TESTED_KEY, "").putString(KEY_STATUS, "retrying").apply();
        registerCurrent(app);
    }

'''
if 'public static void retryCurrent(Context context)' not in s:
    if s.count(anchor) != 1:
        raise SystemExit("v115 retry insertion point missing")
    s = s.replace(anchor, retry + anchor, 1)

old = '''            result.put("vibrationEnabled", p.getBoolean(KEY_VIBRATION, true));
            return result.toString();'''
new = '''            result.put("vibrationEnabled", p.getBoolean(KEY_VIBRATION, true));
            result.put("fcmMessageId", p.getString(KEY_FCM_MESSAGE_ID, ""));
            result.put("fcmError", p.getString(KEY_FCM_ERROR, ""));
            boolean permissionGranted = Build.VERSION.SDK_INT < 33 ||
                    context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED;
            result.put("notificationPermission", permissionGranted);
            NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
            int waitImportance = -1;
            int courtImportance = -1;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && manager != null) {
                NotificationChannel wait = manager.getNotificationChannel(NativeSystemChannels.WAIT);
                NotificationChannel court = manager.getNotificationChannel(NativeSystemChannels.COURT);
                waitImportance = wait == null ? -1 : wait.getImportance();
                courtImportance = court == null ? -1 : court.getImportance();
            }
            result.put("waitChannelImportance", waitImportance);
            result.put("courtChannelImportance", courtImportance);
            return result.toString();'''
if 'result.put("fcmMessageId"' not in s:
    if old not in s:
        raise SystemExit("v115 status insertion point missing")
    s = s.replace(old, new, 1)

start = s.find("    private static void submit(String action,")
end = s.find("\n    }\n}\nJAVA", start)
if start < 0 or end < 0:
    raise SystemExit("v115 submit method missing")
end += len("\n    }")
submit = '''    private static JSONObject submit(String action, String memberId, String memberName, String token) {
        HttpURLConnection connection = null;
        try {
            JSONObject payload = new JSONObject();
            payload.put("action", action);
            payload.put("memberId", memberId == null ? "" : memberId);
            payload.put("memberName", memberName == null ? "" : memberName);
            payload.put("token", token == null ? "" : token);
            payload.put("userAgent", "JayumintonNativeAndroid/1.1.5 FreshInstall NativeFCM");
            String body = "payload=" + Uri.encode(payload.toString());
            connection = (HttpURLConnection) new URL(RELAY_URL).openConnection();
            connection.setConnectTimeout(15000);
            connection.setReadTimeout(20000);
            connection.setRequestMethod("POST");
            connection.setInstanceFollowRedirects(false);
            connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded;charset=UTF-8");
            byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
            connection.setFixedLengthStreamingMode(bytes.length);
            try (OutputStream output = connection.getOutputStream()) { output.write(bytes); }
            int code = connection.getResponseCode();
            String redirect = connection.getHeaderField("Location");
            if (code >= 300 && code < 400 && redirect != null && !redirect.isEmpty()) {
                connection.disconnect();
                connection = (HttpURLConnection) new URL(redirect).openConnection();
                connection.setConnectTimeout(15000);
                connection.setReadTimeout(20000);
                connection.setRequestMethod("GET");
                code = connection.getResponseCode();
            }
            InputStream input = code >= 200 && code < 300 ? connection.getInputStream() : connection.getErrorStream();
            StringBuilder responseBody = new StringBuilder();
            if (input != null) {
                BufferedReader reader = new BufferedReader(new InputStreamReader(input, StandardCharsets.UTF_8));
                String line;
                while ((line = reader.readLine()) != null) responseBody.append(line);
                reader.close();
            }
            JSONObject result = responseBody.length() == 0 ? new JSONObject() : new JSONObject(responseBody.toString());
            if (code < 200 || code >= 400) result.put("ok", false).put("httpStatus", code);
            return result;
        } catch (Exception error) {
            try { return new JSONObject().put("ok", false).put("error", error.getClass().getSimpleName() + ": " + error.getMessage()); }
            catch (Exception ignored) { return new JSONObject(); }
        } finally {
            if (connection != null) connection.disconnect();
        }
    }'''
s = s[:start] + submit + s[end:]

for marker in (
    'VERSION="1.1.5"', 'VERSION_CODE="115"',
    'action, String memberId, String memberName, String token)',
    'submit("test_native_push", id, name, token)',
    '"fcm_accepted"', 'result.put("fcmMessageId"',
    'JayumintonNativeAndroid/1.1.5',
    'retryServerPushTest()', 'notificationPermission',
    'waitChannelImportance', 'jayuminton-native-status',
):
    if marker not in s:
        raise SystemExit("missing native v1.1.5 marker: " + marker)

path.write_text(s, encoding="utf-8")
print("Prepared native v1.1.5 with server-confirmed FCM delivery acceptance.")
