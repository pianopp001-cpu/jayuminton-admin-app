package com.jayuminton.member;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONArray;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

final class MemberStore {
    private static final String PREFS = "jayuminton_member_notification";
    private static final String KEY_MEMBER_ID = "selected_member_id";
    private static final String KEY_MEMBER_NAME = "selected_member_name";
    private static final String KEY_SEEN_ASSIGNMENTS = "seen_assignments";
    private static final int MAX_SEEN_ASSIGNMENTS = 50;
    private static final Object SEEN_LOCK = new Object();

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

    static String topicForMemberId(String memberId) {
        String normalized = memberId == null ? "" : memberId.trim();
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(normalized.getBytes(StandardCharsets.UTF_8));
            StringBuilder hex = new StringBuilder(hash.length * 2);
            for (byte value : hash) {
                hex.append(String.format(java.util.Locale.ROOT, "%02x", value & 0xff));
            }
            return "jm_" + hex;
        } catch (Exception error) {
            throw new IllegalStateException("멤버 알림 주제를 만들 수 없습니다.", error);
        }
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
}
