#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding='utf-8')

for old, new in (
    ('v1.2.8-repeat-switch.apk', 'v1.3.0-md4-8groups.apk'),
    ('user-native-push-v1.2.8.txt', 'user-native-push-v1.3.0.txt'),
    ('VERSION="1.2.8"', 'VERSION="1.3.0"'),
    ('VERSION_CODE="128"', 'VERSION_CODE="130"'),
    ('versionCode 128', 'versionCode 130'),
    ("versionCode='128'", "versionCode='130'"),
    ("versionName '1.2.8'", "versionName '1.3.0'"),
    ("versionName='1.2.8'", "versionName='1.3.0'"),
    ('USER_APP_VERSION = "1.2.8"', 'USER_APP_VERSION = "1.3.0"'),
    ('JayumintonUserNative/1.2.8', 'JayumintonUserNative/1.3.0'),
    ('JayumintonNativeAndroid/1.2.8', 'JayumintonNativeAndroid/1.3.0'),
    ('APP_VERSION = "1.2.8"', 'APP_VERSION = "1.3.0"'),
    ('version=1.2.8', 'version=1.3.0'),
    ('version_code=128', 'version_code=130'),
    ('jayuminton_wait1_native_v128', 'jayuminton_wait1_native_v130'),
    ('jayuminton_court_native_v128', 'jayuminton_court_native_v130'),
    ('repeat-switch-v128-current-member-only', 'md4-8groups-v130-current-member-only'),
):
    s = s.replace(old, new)

field_anchor = '''    private static boolean active;\n    private static int generation;\n    private static Runnable activeRunnable;'''
field_replacement = '''    private static final int MAX_GROUPS = 8;\n    private static boolean active;\n    private static int generation;\n    private static int groupsPlayed;\n    private static Runnable activeRunnable;'''
if s.count(field_anchor) != 1:
    raise SystemExit('v130 vibration controller field anchor missing')
s = s.replace(field_anchor, field_replacement, 1)

start_anchor = '''            generation++;\n            myGeneration = generation;\n            active = true;'''
start_replacement = '''            generation++;\n            myGeneration = generation;\n            active = true;\n            groupsPlayed = 0;'''
if s.count(start_anchor) != 1:
    raise SystemExit('v130 vibration start anchor missing')
s = s.replace(start_anchor, start_replacement, 1)

schedule_anchor = '''                        vibrateFiniteGroup(vibrator);\n                    }\n                    synchronized (LOCK) {\n                        if (!active || generation != myGeneration || activeRunnable != this) return;\n                        HANDLER.postDelayed(this, GROUP_REPEAT_MS);\n                    }'''
schedule_replacement = '''                        vibrateFiniteGroup(vibrator);\n                    }\n                    synchronized (LOCK) {\n                        if (!active || generation != myGeneration || activeRunnable != this) return;\n                        groupsPlayed++;\n                        if (groupsPlayed >= MAX_GROUPS) {\n                            active = false;\n                            activeRunnable = null;\n                            return;\n                        }\n                        HANDLER.postDelayed(this, GROUP_REPEAT_MS);\n                    }'''
if s.count(schedule_anchor) != 1:
    raise SystemExit('v130 vibration repeat anchor missing')
s = s.replace(schedule_anchor, schedule_replacement, 1)

for marker in (
    'VERSION="1.3.0"',
    'VERSION_CODE="130"',
    'APP_VERSION = "1.3.0"',
    'private static final int MAX_GROUPS = 8;',
    'groupsPlayed = 0;',
    'groupsPlayed++;',
    'if (groupsPlayed >= MAX_GROUPS)',
    'AlertVibrationController.stop(this)',
    'AlertVibrationController.stop(context)',
    'stopPreviousMemberAlert(app);',
    'NativePushRegistrar.isCurrentMember(this, targetMemberId)',
    'JAYUMINTON_V126_START_STOP_RACE_GUARD',
):
    if marker not in s:
        raise SystemExit('missing v1.3.0 MD4 vibration marker: ' + marker)

s = s.replace('vibration_max_groups=10', 'vibration_max_groups=8')
s = s.replace(
    'wait1_vibration=controller-finite-3-pulse-groups-max10-or-until-confirmed-md4-8groups-v130-current-member-only',
    'wait1_vibration=3-pulses-x8-max-confirm-stops-current-member-only',
)
s = s.replace(
    'court_vibration=controller-finite-3-pulse-groups-max10-or-until-confirmed-md4-8groups-v130-current-member-only',
    'court_vibration=3-pulses-x8-max-confirm-stops-current-member-only',
)

path.write_text(s, encoding='utf-8')
print('Prepared v1.3.0: MD(4) finite 3-pulse x 8-group maximum.')
