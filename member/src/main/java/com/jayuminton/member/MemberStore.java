package com.jayuminton.member;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;

import com.google.firebase.messaging.FirebaseMessaging;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

final class MemberStore {
    private static final String TAG = "JayumintonPush";
    private static final String PREFS = "jayuminton_member_notification";
    private static final String KEY_MEMBER_ID = "selected_member_id";
    private static final String KEY_MEMBER_NAME = "selected_member_name";
    private static final String KEY_SEEN_ASSIGNMENTS = "seen_assignments";
    private static final int MAX_SEEN_ASSIGNMENTS = 50;
    private static final Object SEEN_LOCK = new Object();

    /**
     * Free Apps Script FCM relay. register_web_token/unregister_web_token are
     * public actions (no shared secret) — see apps-script-push/Code.gs.
     */
    private static final String RELAY_URL =
            "https://script.google.com/macros/s/AKfycbyVPlL35pwN9QXvyzUG_TRaE4zC9QiEBB3z4jg3PjJwcuUmX-MI_hKuFX6FO757WaRHIg/exec";
    private static final ExecutorService NETWORK_EXECUTOR = Executors.newSingleThreadExecutor();

    private MemberStore() {
    }

    static String getSelectedMemberId(Context context) {
        return preferences(context).getString(KEY_MEMBER_ID, "").trim();
    }

    static String getSelectedMemberName(Context context) {
        return preferences(context).getString(KEY_MEMBER_NAME, "").trim();
    }

    static void saveSelection(Context context, String memberId, String memberName) {
        preferences(context).edit()
                .putString(KEY_MEMBER_ID, memberId == null ? "" : memberId.trim())
                .putString(KEY_MEMBER_NAME, memberName == null ? "" : memberName.trim())
                .apply();
    }

    static void clearSelection(Context context) {
        preferences(context).edit()
                .remove(KEY_MEMBER_ID)
                .remove(KEY_MEMBER_NAME)
                .remove(KEY_SEEN_ASSIGNMENTS)
                .apply();
    }

    static boolean markAssignmentSeen(Context context, String assignmentId) {
        String normalized = assignmentId == null ? "" : assignmentId.trim();
        if (normalized.isEmpty()) return false;

        synchronized (SEEN_LOCK) {
            SharedPreferences preferences = preferences(context);
            JSONArray previous;
            try {
                previous = new JSONArray(
                        preferences.getString(KEY_SEEN_ASSIGNMENTS, "[]")
                );
            } catch (Exception ignored) {
                previous = new JSONArray();
            }

            for (int index = 0; index < previous.length(); index++) {
                if (normalized.equals(previous.optString(index))) {
                    return false;
                }
            }

            JSONArray next = new JSONArray();
            int start = Math.max(0, previous.length() - (MAX_SEEN_ASSIGNMENTS - 1));
            for (int index = start; index < previous.length(); index++) {
                String value = previous.optString(index, "");
                if (!value.isEmpty()) next.put(value);
            }
            next.put(normalized);
            preferences.edit()
                    .putString(KEY_SEEN_ASSIGNMENTS, next.toString())
                    .apply();
            return true;
        }
    }

    private static SharedPreferences preferences(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    interface RelayCallback {
        void onResult(boolean success);
    }

    /**
     * Registers the device's current FCM token under the given member with the
     * push relay so server-side assignment events can reach this device. The
     * relay de-duplicates by token, so re-registering the same token under a
     * new memberId naturally moves it away from whichever member it was
     * previously tied to. Runs fire-and-forget (no UI feedback needed).
     */
    static void registerCurrentToken(Context appContext, String memberId, String memberName) {
        registerToken(appContext, memberId, memberName, null);
    }

    /** Same as {@link #registerCurrentToken}, but reports success/failure for interactive UI. */
    static void registerToken(
            Context appContext, String memberId, String memberName, RelayCallback callback
    ) {
        if (memberId == null || memberId.trim().isEmpty()) {
            if (callback != null) callback.onResult(false);
            return;
        }
        FirebaseMessaging.getInstance().getToken().addOnCompleteListener(task -> {
            if (!task.isSuccessful() || task.getResult() == null) {
                Log.w(TAG, "FCM token fetch failed", task.getException());
                if (callback != null) callback.onResult(false);
                return;
            }
            postRelayAction("register_web_token", memberId, memberName, task.getResult(), callback);
        });
    }

    /** Called from FirebaseMessagingService#onNewToken so a rotated token stays registered. */
    static void registerTokenIfMemberSelected(Context appContext, String newToken) {
        String memberId = getSelectedMemberId(appContext);
        if (memberId.isEmpty()) return;
        String memberName = getSelectedMemberName(appContext);
        postRelayAction("register_web_token", memberId, memberName, newToken, null);
    }

    static void unregisterCurrentToken(Context appContext) {
        FirebaseMessaging.getInstance().getToken().addOnCompleteListener(task -> {
            if (!task.isSuccessful() || task.getResult() == null) return;
            postRelayAction("unregister_web_token", "", "", task.getResult(), null);
        });
    }

    private static void postRelayAction(
            String action,
            String memberId,
            String memberName,
            String token,
            RelayCallback callback
    ) {
        NETWORK_EXECUTOR.execute(() -> {
            boolean success = false;
            try {
                JSONObject payload = new JSONObject();
                payload.put("action", action);
                if (!memberId.isEmpty()) payload.put("memberId", memberId);
                if (!memberName.isEmpty()) payload.put("memberName", memberName);
                payload.put("token", token);
                payload.put("userAgent", "JayumintonMemberNative/1.5 Android");

                String responseBody = postAndFollowAppsScriptRedirect_(
                        RELAY_URL, payload.toString().getBytes(StandardCharsets.UTF_8));
                success = responseBody != null &&
                        new JSONObject(responseBody).optBoolean("ok", false);
                if (!success) {
                    Log.w(TAG, action + " did not report ok:true — " + responseBody);
                }
            } catch (Exception error) {
                Log.w(TAG, action + " failed", error);
            }
            if (callback != null) callback.onResult(success);
        });
    }

    /**
     * Apps Script's /exec endpoint answers a POST with a 302 whose Location
     * points at a script.googleusercontent.com "echo" URL holding the actual
     * response body — the server already executed doPost() by this point.
     * Automatically-followed redirects (Java's default, curl -L) resend the
     * original method/body to that Location and get a broken 4xx back, so the
     * Location must be re-fetched with a fresh, bodyless GET instead.
     */
    private static String postAndFollowAppsScriptRedirect_(String targetUrl, byte[] body)
            throws Exception {
        HttpURLConnection connection = null;
        try {
            URL url = new URL(targetUrl);
            connection = (HttpURLConnection) url.openConnection();
            connection.setConnectTimeout(8000);
            connection.setReadTimeout(12000);
            connection.setRequestMethod("POST");
            connection.setInstanceFollowRedirects(false);
            connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
            connection.setFixedLengthStreamingMode(body.length);
            try (OutputStream output = connection.getOutputStream()) {
                output.write(body);
            }

            int status = connection.getResponseCode();
            if (status >= 300 && status < 400) {
                String location = connection.getHeaderField("Location");
                connection.disconnect();
                if (location == null || location.isEmpty()) return null;
                return httpGet_(location);
            }
            if (status < 200 || status >= 300) return null;
            return readStream_(connection.getInputStream());
        } finally {
            if (connection != null) connection.disconnect();
        }
    }

    private static String httpGet_(String targetUrl) throws Exception {
        HttpURLConnection connection = null;
        try {
            URL url = new URL(targetUrl);
            connection = (HttpURLConnection) url.openConnection();
            connection.setConnectTimeout(8000);
            connection.setReadTimeout(12000);
            connection.setRequestMethod("GET");
            connection.setInstanceFollowRedirects(true);
            int status = connection.getResponseCode();
            if (status < 200 || status >= 300) return null;
            return readStream_(connection.getInputStream());
        } finally {
            if (connection != null) connection.disconnect();
        }
    }

    private static String readStream_(java.io.InputStream input) throws Exception {
        java.io.ByteArrayOutputStream buffer = new java.io.ByteArrayOutputStream();
        byte[] chunk = new byte[1024];
        int read;
        while ((read = input.read(chunk)) != -1) {
            buffer.write(chunk, 0, read);
        }
        return buffer.toString("UTF-8");
    }
}
