#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding='utf-8')

# v1.3.0 / code130: vibration-only behavior change from the verified v1.2.9 build.
# Keep every existing user-app feature, FCM path, member switching, overlay, text,
# registration flow, WebView/UI, and vibration strength/timing unchanged.
# Only: give this build a new Android version and cap both wait1/court vibration
# at 8 finite 3-pulse groups (or earlier if the user dismisses the alert).

replacements = (
    ('v1.2.9-background-registration.apk', 'v1.3.0-cap8.apk'),
    ('user-native-push-v1.2.9.txt', 'user-native-push-v1.3.0.txt'),
    ('VERSION="1.2.9"', 'VERSION="1.3.0"'),
    ('VERSION_CODE="129"', 'VERSION_CODE="130"'),
    ('versionCode 129', 'versionCode 130'),
    ("versionCode='129'", "versionCode='130'"),
    ("versionName '1.2.9'", "versionName '1.3.0'"),
    ("versionName='1.2.9'", "versionName='1.3.0'"),
    ('USER_APP_VERSION = "1.2.9"', 'USER_APP_VERSION = "1.3.0"'),
    ('JayumintonUserNative/1.2.9', 'JayumintonUserNative/1.3.0'),
    ('JayumintonNativeAndroid/1.2.9', 'JayumintonNativeAndroid/1.3.0'),
    ('APP_VERSION = "1.2.9"', 'APP_VERSION = "1.3.0"'),
    ('version=1.2.9', 'version=1.3.0'),
    ('version_code=129', 'version_code=130'),
)
for old, new in replacements:
    if old not in s:
        raise SystemExit('v130 version anchor missing: ' + old)
    s = s.replace(old, new)

controller_start = s.find('cat > "$VIBRATION_JAVA" <<\'JAVA\'\n')
controller_end = s.find('\nJAVA\n\n', controller_start)
if controller_start < 0 or controller_end < 0:
    raise SystemExit('v130 vibration controller segment missing')
controller = s[controller_start:controller_end]

# Hard guards for the already proven vibration pattern and race-safe stop behavior.
for required in (
    'private static final long[] GROUP_TIMINGS = new long[]{0, 650, 220, 650, 220, 650};',
    'private static final int[] GROUP_AMPLITUDES = new int[]{0, 255, 0, 255, 0, 255};',
    'private static final long GROUP_REPEAT_MS = 3490L;',
    'JAYUMINTON_V126_START_STOP_RACE_GUARD',
    'createWaveform(GROUP_TIMINGS, GROUP_AMPLITUDES, -1)',
):
    if required not in controller:
        raise SystemExit('v130 proven vibration marker missing: ' + required)

max_anchor = '    private static final long GROUP_REPEAT_MS = 3490L; // finite group + 1.1 s group gap\n'
if controller.count(max_anchor) != 1:
    raise SystemExit('v130 repeat interval anchor missing')
controller = controller.replace(
    max_anchor,
    max_anchor + '    private static final int MAX_GROUPS = 8;\n',
    1,
)

counter_anchor = '        final Runnable[] holder = new Runnable[1];\n'
if controller.count(counter_anchor) != 1:
    raise SystemExit('v130 runnable holder anchor missing')
controller = controller.replace(
    counter_anchor,
    counter_anchor + '        final int[] emittedGroups = new int[]{0};\n',
    1,
)

# Preserve the race-guarded synchronized block; only stop scheduling after group 8.
schedule_anchor = '''                        if (!active || generation != myGeneration || activeRunnable != this) return;
                        HANDLER.postDelayed(this, GROUP_REPEAT_MS);
                    }
                }'''
schedule_replacement = '''                        if (!active || generation != myGeneration || activeRunnable != this) return;
                        emittedGroups[0]++;
                        if (emittedGroups[0] >= MAX_GROUPS) {
                            active = false;
                            activeRunnable = null;
                            return;
                        }
                        HANDLER.postDelayed(this, GROUP_REPEAT_MS);
                    }
                }'''
if controller.count(schedule_anchor) != 1:
    raise SystemExit('v130 repeat scheduling anchor missing')
controller = controller.replace(schedule_anchor, schedule_replacement, 1)

s = s[:controller_start] + controller + s[controller_end:]

status_pairs = (
    (
        'wait1_vibration=controller-finite-3-pulse-groups-repeat-until-confirmed-repeat-switch-v128-current-member-only',
        'wait1_vibration=controller-finite-3-pulse-groups-max8-or-until-confirmed-repeat-switch-v128-current-member-only',
    ),
    (
        'court_vibration=controller-finite-3-pulse-groups-repeat-until-confirmed-repeat-switch-v128-current-member-only',
        'court_vibration=controller-finite-3-pulse-groups-max8-or-until-confirmed-repeat-switch-v128-current-member-only',
    ),
)
for old, new in status_pairs:
    if s.count(old) != 1:
        raise SystemExit('v130 status anchor missing: ' + old)
    s = s.replace(old, new, 1)

status_gap_anchor = 'group_gap_ms=1100\n'
if s.count(status_gap_anchor) != 1:
    raise SystemExit('v130 group-gap status anchor missing')
s = s.replace(status_gap_anchor, status_gap_anchor + 'vibration_max_groups=8\n', 1)

for required in (
    'VERSION="1.3.0"',
    'VERSION_CODE="130"',
    'versionCode 130',
    "versionName '1.3.0'",
    'APP_VERSION = "1.3.0"',
    'private static final int MAX_GROUPS = 8;',
    'final int[] emittedGroups = new int[]{0};',
    'if (emittedGroups[0] >= MAX_GROUPS)',
    'JAYUMINTON_V126_START_STOP_RACE_GUARD',
    'GROUP_REPEAT_MS = 3490L',
    'vibration_max_groups=8',
    'pulse_ms=650',
    'intra_pulse_gap_ms=220',
    'group_gap_ms=1100',
):
    if required not in s:
        raise SystemExit('missing v130 verification marker: ' + required)

# The new build must not accidentally retain the old Android app version metadata.
for forbidden in (
    'VERSION="1.2.9"',
    'VERSION_CODE="129"',
    "versionName '1.2.9'",
    'vibration_max_groups=10',
    'MAX_GROUPS = 10',
):
    if forbidden in s:
        raise SystemExit('v130 stale marker remained: ' + forbidden)

path.write_text(s, encoding='utf-8')
print('Prepared v1.3.0 code130: existing behavior preserved, both wait1/court capped at 8 groups of 3 pulses.')
