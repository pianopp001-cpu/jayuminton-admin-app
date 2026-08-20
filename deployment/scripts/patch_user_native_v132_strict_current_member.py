#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding='utf-8')

for old, new in (
    ('v1.3.0-cap8.apk', 'v1.3.2-current-member-only.apk'),
    ('user-native-push-v1.3.0.txt', 'user-native-push-v1.3.2.txt'),
    ('VERSION="1.3.0"', 'VERSION="1.3.2"'),
    ('VERSION_CODE="130"', 'VERSION_CODE="132"'),
    ('versionCode 130', 'versionCode 132'),
    ("versionCode='130'", "versionCode='132'"),
    ("versionName '1.3.0'", "versionName '1.3.2'"),
    ("versionName='1.3.0'", "versionName='1.3.2'"),
    ('USER_APP_VERSION = "1.3.0"', 'USER_APP_VERSION = "1.3.2"'),
    ('JayumintonUserNative/1.3.0', 'JayumintonUserNative/1.3.2'),
    ('JayumintonNativeAndroid/1.3.0', 'JayumintonNativeAndroid/1.3.2'),
    ('APP_VERSION = "1.3.0"', 'APP_VERSION = "1.3.2"'),
    ('version=1.3.0', 'version=1.3.2'),
    ('version_code=130', 'version_code=132'),
):
    s = s.replace(old, new)

old = '''        boolean hasTargetMemberId = !targetMemberId.isEmpty();
        boolean selectedMemberMatches = !hasTargetMemberId || NativePushRegistrar.isCurrentMember(this, targetMemberId);
        NativeDeliveryReporter.report("fcm_received", type, hasTargetMemberId,
                selectedMemberMatches, false, false, false);
        if (!selectedMemberMatches) {
            NativeDeliveryReporter.report("member_rejected", type, true, false, false, false, false);
            return;
        }
        NativeDeliveryReporter.report("member_accepted", type, hasTargetMemberId,
                true, false, false, false);'''
new = '''        boolean hasTargetMemberId = !targetMemberId.isEmpty();
        boolean assignmentType = "wait1_ready".equals(type) || "court_assignment".equals(type) ||
                "WAIT_ONE".equals(type) || "COURT".equals(type) ||
                "WAIT_ONE_PROMOTED".equals(type) || "COURT_PROMOTED".equals(type);
        boolean selectedMemberMatches = hasTargetMemberId &&
                NativePushRegistrar.isCurrentMember(this, targetMemberId);
        NativeDeliveryReporter.report("fcm_received", type, hasTargetMemberId,
                selectedMemberMatches, false, false, false);
        if (assignmentType && (!hasTargetMemberId || !selectedMemberMatches)) {
            AlertVibrationController.stop(this);
            AssignmentOverlay.dismissOnly();
            NativeDeliveryReporter.report(
                    hasTargetMemberId ? "member_rejected" : "missing_target_rejected",
                    type, hasTargetMemberId, false, false, false, true);
            return;
        }
        if (!assignmentType && hasTargetMemberId && !selectedMemberMatches) {
            NativeDeliveryReporter.report("member_rejected", type, true, false, false, false, false);
            return;
        }
        NativeDeliveryReporter.report("member_accepted", type, hasTargetMemberId,
                selectedMemberMatches, false, false, false);'''
if s.count(old) != 1:
    raise SystemExit('v132 strict member-gate anchor missing')
s = s.replace(old, new, 1)

for required in (
    'VERSION="1.3.2"',
    'VERSION_CODE="132"',
    'private static final int MAX_GROUPS = 8;',
    'NativePushRegistrar.isCurrentMember(this, targetMemberId)',
    'boolean selectedMemberMatches = hasTargetMemberId &&',
    '"wait1_ready".equals(type)',
    '"court_assignment".equals(type)',
    'assignmentType && (!hasTargetMemberId || !selectedMemberMatches)',
    '"missing_target_rejected"',
    'AlertVibrationController.stop(this);',
    'AssignmentOverlay.dismissOnly();',
    'stopPreviousMemberAlert(app);',
    'jayuminton_web_push_selected_member_v1',
    '"대기 1순위입니다. 라켓 들고 준비하세요."',
    'courtNo + "번 코트로 들어가세요."',
):
    if required not in s:
        raise SystemExit('missing v1.3.2 strict-member marker: ' + required)

if 'selectedMemberMatches = !hasTargetMemberId || NativePushRegistrar.isCurrentMember' in s:
    raise SystemExit('generic missing-target acceptance survived v132')

s = s.replace(
    'vibration_max_groups=8',
    'vibration_max_groups=8\nassignment_alert_scope=current-selected-member-only\nmissing_target_assignment=reject-before-popup-sound-vibration\nassignment_types=wait1_ready,court_assignment',
)

path.write_text(s, encoding='utf-8')
print('Prepared v1.3.2 strict current-member-only assignment alerts for real FCM types.')
