#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding='utf-8')

for old, new in (
    ('v1.1.3-fresh-install.apk', 'v1.1.4-fresh-install.apk'),
    ('user-native-push-v1.1.3.txt', 'user-native-push-v1.1.4.txt'),
    ('VERSION="1.1.3"', 'VERSION="1.1.4"'),
    ('VERSION_CODE="113"', 'VERSION_CODE="114"'),
    ('versionCode 113', 'versionCode 114'),
    ("versionCode='113'", "versionCode='114'"),
    ("versionName '1.1.3'", "versionName '1.1.4'"),
    ("versionName='1.1.3'", "versionName='1.1.4'"),
    ('USER_APP_VERSION = "1.1.3"', 'USER_APP_VERSION = "1.1.4"'),
    ('JayumintonUserNative/1.1.3', 'JayumintonUserNative/1.1.4'),
    ("__JAYUMINTON_USER_APK_VERSION__='1.1.3'", "__JAYUMINTON_USER_APK_VERSION__='1.1.4'"),
    ('jayuminton_native_push_v113', 'jayuminton_native_push_v114'),
    ('JayumintonNativeAndroid/1.1.3', 'JayumintonNativeAndroid/1.1.4'),
    ('jayuminton_wait1_native_v113', 'jayuminton_wait1_native_v114'),
    ('jayuminton_court_native_v113', 'jayuminton_court_native_v114'),
    ('jayuminton_ready_test_v113', 'jayuminton_ready_test_v114'),
    ('version=1.1.3', 'version=1.1.4'),
    ('version_code=113', 'version_code=114'),
    ('__JAYUMINTON_NATIVE_DIRECT_V113__', '__JAYUMINTON_NATIVE_DIRECT_V114__'),
):
    s = s.replace(old, new)

if 'CHANNELS_JAVA=' not in s:
    s = s.replace(
        'PROBE_JAVA="$JAVA_DIR/NativeAlertProbe.java"',
        'PROBE_JAVA="$JAVA_DIR/NativeAlertProbe.java"\nCHANNELS_JAVA="$JAVA_DIR/NativeSystemChannels.java"',
        1,
    )

# Channels must exist before a background notification arrives because Android,
# not the app process, renders notification messages in the background.
old = '''        requestNotificationPermissionIfNeeded();
        NativePushRegistrar.ensureToken(this);'''
new = '''        NativeSystemChannels.ensure(this);
        requestNotificationPermissionIfNeeded();
        NativePushRegistrar.ensureToken(this);'''
if 'NativeSystemChannels.ensure(this);' not in s:
    if old not in s:
        raise SystemExit('system channel startup insertion point missing')
    s = s.replace(old, new, 1)

# Default channel is a safe fallback if an older sender omits the event channel.
old = '''        android:usesCleartextTraffic="false">'''
new = '''        android:usesCleartextTraffic="false">

        <meta-data
            android:name="com.google.firebase.messaging.default_notification_channel_id"
            android:value="jayuminton_wait1_system_v114" />'''
if 'default_notification_channel_id' not in s:
    if old not in s:
        raise SystemExit('default FCM channel insertion point missing')
    s = s.replace(old, new, 1)

anchor = 'cat > "$PROBE_JAVA" <<\'JAVA\'\n'
channels = r'''cat > "$CHANNELS_JAVA" <<'JAVA'
package com.jayuminton.admin;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.Context;
import android.media.AudioAttributes;
import android.media.RingtoneManager;
import android.net.Uri;
import android.os.Build;

public final class NativeSystemChannels {
    public static final String WAIT = "jayuminton_wait1_system_v114";
    public static final String COURT = "jayuminton_court_system_v114";
    private NativeSystemChannels() {}

    public static void ensure(Context source) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return;
        Context context = source.getApplicationContext();
        NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null) return;
        manager.createNotificationChannel(channel(WAIT, "대기1 알림", waitPattern()));
        manager.createNotificationChannel(channel(COURT, "코트 입장 알림", courtPattern()));
    }

    private static NotificationChannel channel(String id, String name, long[] vibration) {
        NotificationChannel channel = new NotificationChannel(id, name, NotificationManager.IMPORTANCE_HIGH);
        channel.setDescription("다른 앱 사용 중에도 표시되는 자유민턴 배정 알림");
        channel.enableLights(true);
        channel.enableVibration(true);
        channel.setVibrationPattern(vibration);
        Uri sound = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);
        AudioAttributes attrs = new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_NOTIFICATION_EVENT).build();
        channel.setSound(sound, attrs);
        channel.setLockscreenVisibility(android.app.Notification.VISIBILITY_PUBLIC);
        return channel;
    }

    private static long[] waitPattern() {
        return new long[]{0,900,220,900,220,900,1100,900,220,900,220,900,1100,900,220,900,220,900};
    }

    private static long[] courtPattern() {
        return new long[]{0,900,220,900,220,900,1100,900,220,900,220,900,1100,900,220,900,220,900,1100,900,220,900,220,900,1100,900,220,900,220,900};
    }
}
JAVA

'''
if 'class NativeSystemChannels' not in s:
    if anchor not in s:
        raise SystemExit('system channels source insertion point missing')
    s = s.replace(anchor, channels + anchor, 1)

required = (
    'v1.1.4-fresh-install.apk', 'VERSION="1.1.4"', 'VERSION_CODE="114"',
    'NativeSystemChannels.ensure(this)', 'default_notification_channel_id',
    'class NativeSystemChannels', 'jayuminton_wait1_system_v114',
    'jayuminton_court_system_v114',
)
for marker in required:
    if marker not in s:
        raise SystemExit('missing native v1.1.4 marker: ' + marker)

path.write_text(s, encoding='utf-8')
print('Prepared native v1.1.4 with pre-created Android system notification channels.')
