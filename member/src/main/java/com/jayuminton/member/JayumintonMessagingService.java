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
    static final String CHANNEL_ID = "court_assignment";
    private static final long[] VIBRATION_PATTERN = {0, 600, 220, 600};

    @Override
    public void onNewToken(String token) {
        super.onNewToken(token);
        String memberId = MemberStore.getSelectedMemberId(this);
        if (!memberId.isEmpty()) {
            FirebaseMessaging.getInstance()
                    .subscribeToTopic(MemberStore.topicForMemberId(memberId));
        }
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
                assignmentId,
                "코트 입장 안내",
                memberName,
                courtText + "로 들어가 주세요."
        );
    }

    static void ensureNotificationChannel(Context context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return;
        NotificationManager manager =
                (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null || manager.getNotificationChannel(CHANNEL_ID) != null) return;

        NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "대기·코트 배정 알림",
                NotificationManager.IMPORTANCE_HIGH
        );
        channel.setDescription("대기1 승급과 코트 입장 시 진동과 알림을 표시합니다.");
        channel.enableVibration(true);
        channel.setVibrationPattern(VIBRATION_PATTERN);
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

    private void showAssignmentNotification(
            String assignmentId,
            String title,
            String memberName,
            String instruction
    ) {
        ensureNotificationChannel(this);

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
                ? new Notification.Builder(this, CHANNEL_ID)
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
            builder.setPriority(Notification.PRIORITY_HIGH)
                    .setDefaults(Notification.DEFAULT_SOUND | Notification.DEFAULT_LIGHTS)
                    .setVibrate(VIBRATION_PATTERN);
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
