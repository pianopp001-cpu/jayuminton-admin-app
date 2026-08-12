#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding='utf-8')

# Vibration-only safety patch for the already verified v1.2.9 user build.
# Do not touch UI, FCM delivery, member switching, notification text, registration,
# pulse strength/duration, or the existing dismissal/stop routes.
controller_start = s.find('cat > "$VIBRATION_JAVA" <<\'JAVA\'\n')
controller_end = s.find('\nJAVA\n\n', controller_start)
if controller_start < 0 or controller_end < 0:
    raise SystemExit('v129 vibration controller segment missing')
controller = s[controller_start:controller_end]

# Guard the proven timing before making the single requested behavior change.
for required in (
    'private static final long[] GROUP_TIMINGS = new long[]{0, 650, 220, 650, 220, 650};',
    'private static final int[] GROUP_AMPLITUDES = new int[]{0, 255, 0, 255, 0, 255};',
    'private static final long GROUP_REPEAT_MS = 3490L;',
    'AlertVibrationController.stop(',
):
    if required not in s:
        raise SystemExit('v129 proven vibration marker missing: ' + required)

max_anchor = '    private static final long GROUP_REPEAT_MS = 3490L; // finite group + 1.1 s group gap\n'
if controller.count(max_anchor) != 1:
    raise SystemExit('v129 group repeat anchor missing')
controller = controller.replace(
    max_anchor,
    max_anchor + '    private static final int MAX_GROUPS = 10;\n',
    1,
)

counter_anchor = '        final Runnable[] holder = new Runnable[1];\n'
if controller.count(counter_anchor) != 1:
    raise SystemExit('v129 vibration runnable holder anchor missing')
controller = controller.replace(
    counter_anchor,
    counter_anchor + '        final int[] emittedGroups = new int[]{0};\n',
    1,
)

schedule_anchor = '''                    synchronized (LOCK) {
                        if (!active || generation != myGeneration || activeRunnable != this) return;
                        HANDLER.postDelayed(this, GROUP_REPEAT_MS);
                    }'''
schedule_replacement = '''                    synchronized (LOCK) {
                        if (!active || generation != myGeneration || activeRunnable != this) return;
                        emittedGroups[0]++;
                        if (emittedGroups[0] >= MAX_GROUPS) {
                            active = false;
                            activeRunnable = null;
                            return;
                        }
                        HANDLER.postDelayed(this, GROUP_REPEAT_MS);
                    }'''
if controller.count(schedule_anchor) != 1:
    raise SystemExit('v129 vibration repeat scheduling anchor missing')
controller = controller.replace(schedule_anchor, schedule_replacement, 1)

s = s[:controller_start] + controller + s[controller_end:]

# Keep the existing status evidence, changing only the repeat ceiling description.
status_pairs = (
    (
        'wait1_vibration=controller-finite-3-pulse-groups-repeat-until-confirmed-repeat-switch-v128-current-member-only',
        'wait1_vibration=controller-finite-3-pulse-groups-max10-or-until-confirmed-repeat-switch-v128-current-member-only',
    ),
    (
        'court_vibration=controller-finite-3-pulse-groups-repeat-until-confirmed-repeat-switch-v128-current-member-only',
        'court_vibration=controller-finite-3-pulse-groups-max10-or-until-confirmed-repeat-switch-v128-current-member-only',
    ),
)
for old, new in status_pairs:
    if s.count(old) != 1:
        raise SystemExit('v129 vibration status anchor missing: ' + old)
    s = s.replace(old, new, 1)

status_gap_anchor = 'group_gap_ms=1100\n'
if s.count(status_gap_anchor) != 1:
    raise SystemExit('v129 group-gap status anchor missing')
s = s.replace(status_gap_anchor, status_gap_anchor + 'vibration_max_groups=10\n', 1)

# Hard gates: the only behavioral difference is the finite 10-group ceiling.
for required in (
    'private static final int MAX_GROUPS = 10;',
    'final int[] emittedGroups = new int[]{0};',
    'emittedGroups[0]++;',
    'if (emittedGroups[0] >= MAX_GROUPS)',
    'HANDLER.postDelayed(this, GROUP_REPEAT_MS);',
    'createWaveform(GROUP_TIMINGS, GROUP_AMPLITUDES, -1)',
    'pulse_ms=650',
    'intra_pulse_gap_ms=220',
    'group_gap_ms=1100',
    'vibration_max_groups=10',
):
    if required not in s:
        raise SystemExit('missing v129 cap10 verification marker: ' + required)

if 'repeat-until-confirmed-repeat-switch-v128-current-member-only' in s:
    raise SystemExit('uncapped v129 vibration status still present')

path.write_text(s, encoding='utf-8')
print('Prepared v1.2.9 vibration-only cap: 3 strong pulses per group, unchanged timing, maximum 10 groups, early dismissal still stops immediately.')
