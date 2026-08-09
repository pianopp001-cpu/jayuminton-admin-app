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
                        .apply();
                return;
            }

            SharedPreferences latest = prefs(app);
            latest.edit()
                    .putBoolean(KEY_REGISTERED, true)
                    .putString(KEY_STATUS, "token_registered")
                    .putString(KEY_TESTED_KEY, "")
                    .apply();
        });
    }

'''
s = s[:start] + replacement + s[end:]

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
    '"token_registered"',
    'JayumintonNativeAndroid/1.1.5',
):
    if marker not in s:
        raise SystemExit("missing native v1.1.5 marker: " + marker)

path.write_text(s, encoding="utf-8")
print("Prepared native v1.1.5 with token registration and no automatic test push.")
