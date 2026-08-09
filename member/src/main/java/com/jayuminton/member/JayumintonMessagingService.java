package com.jayuminton.member;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.media.AudioAttributes;
import android.os.Build;

import com.google.firebase.messaging.FirebaseMessaging;
import com.google.firebase.messaging.FirebaseMessagingService;
import com.google.firebase.messaging.RemoteMessage;

import java.util.Map;

public final class JayumintonMessagingService extends FirebaseMessagingService {
    static final String CHANNEL_WAIT1 = "jayuminton_wait1_v1";
    static final String CHANNEL_COURT = "jayuminton_court_v1";
    private static final int WAIT1_GROUPS = 3;
    private static final int COURT_GROUPS = 5;
    private static final long PULSE_MS = 650L;
    private static final long INTRA_PULSE_GAP_MS = 220L;
    private static final long GROUP_GAP_MS = 1100L;

    @Override
    public void onNewToken(String token) {
        super.onNewToken(token);
        MemberStore.registerTokenIfMemberSelected(this, token);
    }

    @Override
    public void onMessageReceived(RemoteMessage remoteMessage) {
        super.onMessageReceived(remoteMessage);
        Map<String, String> data = remoteMessage.getData();
        String type = value(data, "type");
        String assignmentId = value(data, "assignmentId");
        String memberId = value(data, "memberId");
        String memberName = value(data, "memberName");

        String selectedMemberId = MemberStore.getSelectedMemberId(this);
        if (selectedMemberId.isEmpty() || !selectedMemberId.equals(memberId)) {
            return;
        }
        if (!MemberStore.markAssignmentSeen(this, assignmentId)) {
            return;
        }

        if (memberName.isEmpty()) {
            memberName = MemberStore.getSelectedMemberName(this);
        }

        if ("wait1_ready".equals(type)) {
            String expectedCourtNo = value(data, "expectedCourtNo");
            String expectedCourtText = expectedCourtNo.isEmpty()
                    ? "경기 시간이 가장 많이 지난 코트가"
                    : expectedCourtNo + "번 코트가";
            showAssignmentNotification(
                    CHANNEL_WAIT1,
                    assignmentId,
                    "대기 1순위 안내",
                    memberName,
                    "대기 1순위입니다. " + expectedCourtText +
                            " 다음으로 나올 예정이니 준비해 주세요."
            );
            return;
        }

        String courtNo = value(data, "courtNo");
        String courtText = courtNo.isEmpty()
                ? "배정된 코트"
                : courtNo + "번 코트";
        showAssignmentNotification(
                CHANNEL_COURT,
                assignmentId,
                "코트 입장 안내",
                memberName,
                courtText + "로 들어가 주세요."
        );
    }

    static void ensureNotificationChannels(Context context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return;
        NotificationManager manager =
                (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null) return;

        ensureChannel(
                manager,
                CHANNEL_WAIT1,
                "대기 1순위 알림",
                "대기1로 올라올 때 긴 진동 3회 x 3그룹으로 알려드립니다.",
                buildVibrationPattern(WAIT1_GROUPS)
        );
        ensureChannel(
                manager,
                CHANNEL_COURT,
                "코트 입장 알림",
                "코트에 배정될 때 긴 진동 3회 x 5그룹으로 알려드립니다.",
                buildVibrationPattern(COURT_GROUPS)
        );
    }

    private static void ensureChannel(
            NotificationManager manager,
            String channelId,
            String name,
            String description,
            long[] vibrationPattern
    ) {
        if (manager.getNotificationChannel(channelId) != null) return;

        NotificationChannel channel = new NotificationChannel(
                channelId,
                name,
                NotificationManager.IMPORTANCE_HIGH
        );
        channel.setDescription(description);
        channel.enableVibration(true);
        channel.setVibrationPattern(vibrationPattern);
        channel.enableLights(true);
        channel.setLightColor(Color.BLUE);
        channel.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);
        channel.setSound(
                android.provider.Settings.System.DEFAULT_NOTIFICATION_URI,
                new AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_NOTIFICATION)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                        .build()
        );
        manager.createNotificationChannel(channel);
    }

    /**
     * One group is 3 long pulses. Android channel vibration patterns alternate
     * off/on starting with an initial (possibly zero) delay, so a single FCM
     * message can still ring out the full multi-group pattern locally.
     */
    private static long[] buildVibrationPattern(int groups) {
        int pulsesPerGroup = 3;
        int segments = 1 + groups * (pulsesPerGroup * 2 - 1) + (groups - 1);
        long[] pattern = new long[segments];
        pattern[0] = 0L;
        int index = 1;
        for (int group = 0; group < groups; group++) {
            for (int pulse = 0; pulse < pulsesPerGroup; pulse++) {
                pattern[index++] = PULSE_MS;
                if (pulse < pulsesPerGroup - 1) {
                    pattern[index++] = INTRA_PULSE_GAP_MS;
                }
            }
            if (group < groups - 1) {
                pattern[index++] = GROUP_GAP_MS;
            }
        }
        return pattern;
    }

    private void showAssignmentNotification(
            String channelId,
            String assignmentId,
            String title,
            String memberName,
            String instruction
    ) {
        ensureNotificationChannels(this);

        Intent launchIntent = new Intent(this, MainActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent pendingIntent = PendingIntent.getActivity(
                this,
                assignmentId.hashCode(),
                launchIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        String body = (memberName.isEmpty() ? "회원" : memberName + "님") + ", " + instruction;

        Notification.Builder builder = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? new Notification.Builder(this, channelId)
                : new Notification.Builder(this);
        builder.setSmallIcon(R.drawable.ic_notification)
                .setContentTitle(title)
                .setContentText(body)
                .setStyle(new Notification.BigTextStyle().bigText(body))
                .setContentIntent(pendingIntent)
                .setAutoCancel(true)
                .setOnlyAlertOnce(true)
                .setCategory(Notification.CATEGORY_REMINDER)
                .setVisibility(Notification.VISIBILITY_PUBLIC);

        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            int groups = CHANNEL_WAIT1.equals(channelId) ? WAIT1_GROUPS : COURT_GROUPS;
            builder.setPriority(Notification.PRIORITY_HIGH)
                    .setDefaults(Notification.DEFAULT_SOUND | Notification.DEFAULT_LIGHTS)
                    .setVibrate(buildVibrationPattern(groups));
        }

        NotificationManager manager =
                (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null) return;
        try {
            manager.notify(assignmentId.hashCode(), builder.build());
        } catch (SecurityException ignored) {
            // Android 13+에서 사용자가 알림 권한을 거부한 경우 조용히 종료합니다.
        }
    }

    private static String value(Map<String, String> data, String key) {
        String value = data == null ? null : data.get(key);
        return value == null ? "" : value.trim();
    }
}
