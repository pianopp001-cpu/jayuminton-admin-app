#!/usr/bin/env python3
from pathlib import Path
import sys


path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

for old, new in (
    ("v1.1.7-fresh-install.apk", "v1.1.8-fresh-install.apk"),
    ("user-native-push-v1.1.7.txt", "user-native-push-v1.1.8.txt"),
    ('VERSION="1.1.7"', 'VERSION="1.1.8"'),
    ('VERSION_CODE="117"', 'VERSION_CODE="118"'),
    ("versionCode 117", "versionCode 118"),
    ("versionCode='117'", "versionCode='118'"),
    ("versionName '1.1.7'", "versionName '1.1.8'"),
    ("versionName='1.1.7'", "versionName='1.1.8'"),
    ('USER_APP_VERSION = "1.1.7"', 'USER_APP_VERSION = "1.1.8"'),
    ("JayumintonUserNative/1.1.7", "JayumintonUserNative/1.1.8"),
    ("JayumintonNativeAndroid/1.1.7", "JayumintonNativeAndroid/1.1.8"),
    ("version=1.1.7", "version=1.1.8"),
    ("version_code=117", "version_code=118"),
    ("jayuminton_wait1_native_v117", "jayuminton_wait1_native_v118"),
    ("jayuminton_court_native_v117", "jayuminton_court_native_v118"),
    ("jayuminton_wait1_system_v117", "jayuminton_wait1_system_v118"),
    ("jayuminton_court_system_v117", "jayuminton_court_system_v118"),
):
    s = s.replace(old, new)

old = '''        String title = value(data, "title", court ? "코트 입장 안내" : "대기1 안내");
        String body = value(data, "body", court ? "코트에 배정되었습니다." : "대기1에 들어왔습니다.");
        String assignmentId = value(data, "assignmentId", String.valueOf(System.currentTimeMillis()));
        // Post a non-vibrating persistent/full-screen notification first.'''
new = '''        String targetMemberId = value(data, "memberId", "");
        if (!targetMemberId.isEmpty() && !NativePushRegistrar.isCurrentMember(this, targetMemberId)) return;
        String courtNo = value(data, "courtNo", "");
        String title = court ? "코트 입장 안내" : "대기 1순위 안내";
        String body = court
                ? (courtNo.isEmpty() ? "코트로 들어가세요." : courtNo + "번 코트로 들어가세요.")
                : "대기 1순위입니다. 라켓 들고 준비하세요.";
        String assignmentId = value(data, "assignmentId", String.valueOf(System.currentTimeMillis()));
        // Post a non-vibrating persistent/full-screen notification first.'''
if s.count(old) != 1:
    raise SystemExit("v118 assignment wording insertion point missing")
s = s.replace(old, new, 1)

anchor = '''    public static boolean vibrationEnabled(Context context) {
        return prefs(context).getBoolean(KEY_VIBRATION, true);
    }
'''
replacement = anchor + '''
    public static boolean isCurrentMember(Context context, String memberId) {
        String current = prefs(context.getApplicationContext()).getString(KEY_MEMBER_ID, "");
        return !current.isEmpty() && current.equals(String.valueOf(memberId == null ? "" : memberId).trim());
    }
'''
if s.count(anchor) != 1:
    raise SystemExit("v118 current member guard insertion point missing")
s = s.replace(anchor, replacement, 1)

# Repeat the complete strong waveform until the user opens the alert and taps
# "확인하고 닫기". AssignmentAlertActivity.dismissAlert() calls vibrator.cancel().
s = s.replace(
    'VibrationEffect.createWaveform(timings, amplitudes, -1),\n                    vibrationAttributes',
    'VibrationEffect.createWaveform(timings, amplitudes, 0),\n                    vibrationAttributes',
    1,
)
s = s.replace('vibrator.vibrate(timings, -1);', 'vibrator.vibrate(timings, 0);', 1)

for marker in (
    'VERSION="1.1.8"', 'VERSION_CODE="118"',
    'JayumintonNativeAndroid/1.1.8',
    '"대기 1순위입니다. 라켓 들고 준비하세요."',
    'courtNo + "번 코트로 들어가세요."',
    'NativePushRegistrar.isCurrentMember(this, targetMemberId)',
    'VibrationEffect.createWaveform(timings, amplitudes, 0)',
    'vibrator.vibrate(timings, 0)',
    '.setFullScreenIntent(pending, true)',
    '.setOngoing(true)',
):
    if marker not in s:
        raise SystemExit("missing native v1.1.8 marker: " + marker)

path.write_text(s, encoding="utf-8")
print("Prepared v1.1.8 with correct wait1 wording, stale-member guard and until-dismissed vibration.")
