#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding='utf-8')

# v1.3.1 / code131: recover native vibration without changing member targeting,
# FCM delivery, UI, overlay, or the proven 3-pulse x max-8 controller timing.
for old, new in (
    ('v1.3.0-cap8.apk', 'v1.3.1-vibration-recovery.apk'),
    ('user-native-push-v1.3.0.txt', 'user-native-push-v1.3.1.txt'),
    ('VERSION="1.3.0"', 'VERSION="1.3.1"'),
    ('VERSION_CODE="130"', 'VERSION_CODE="131"'),
    ('versionCode 130', 'versionCode 131'),
    ("versionCode='130'", "versionCode='131'"),
    ("versionName '1.3.0'", "versionName '1.3.1'"),
    ("versionName='1.3.0'", "versionName='1.3.1'"),
    ('USER_APP_VERSION = "1.3.0"', 'USER_APP_VERSION = "1.3.1"'),
    ('JayumintonUserNative/1.3.0', 'JayumintonUserNative/1.3.1'),
    ('JayumintonNativeAndroid/1.3.0', 'JayumintonNativeAndroid/1.3.1'),
    ('APP_VERSION = "1.3.0"', 'APP_VERSION = "1.3.1"'),
    ('version=1.3.0', 'version=1.3.1'),
    ('version_code=130', 'version_code=131'),
    ('jayuminton_wait1_native_v129', 'jayuminton_wait1_native_v131'),
    ('jayuminton_court_native_v129', 'jayuminton_court_native_v131'),
):
    if old in s:
        s = s.replace(old, new)

service_start = s.find('cat > "$SERVICE_JAVA" <<\'JAVA\'\n')
service_end = s.find('\nJAVA\n\n', service_start)
if service_start < 0 or service_end < 0:
    raise SystemExit('v131 service segment missing')
service = s[service_start:service_end]

# The old native channel explicitly disabled vibration. Android persists channel
# settings by channel id, so use fresh v131 channel ids and allow vibration at
# the OS layer as a fallback. The app-owned controller remains the authoritative
# 3-pulse x max-8 pattern and stop-on-confirm implementation.
if 'channel.enableVibration(false);' not in service:
    raise SystemExit('v131 disabled channel vibration anchor missing')
service = service.replace(
    'channel.enableVibration(false);',
    'channel.enableVibration(true);\n            channel.setVibrationPattern(new long[]{0, 650, 220, 650, 220, 650});',
    1,
)

# Hard guard: an accepted current-member assignment must start the controller.
if 'AlertVibrationController.start(this, assignmentId);' not in service:
    raise SystemExit('v131 controller start missing from FCM service')

s = s[:service_start] + service + s[service_end:]

# Ensure the persisted user preference cannot be left false by stale WebView sync
# when the user explicitly expects assignment vibration. The bridge still exists,
# but receiving a valid current-member assignment always uses the controller.
registrar_start = s.find('cat > "$REGISTRAR_JAVA" <<JAVA\n')
registrar_end = s.find('\nJAVA\n\ncat > "$REG_JOB_JAVA"', registrar_start)
if registrar_start < 0:
    registrar_end = s.find('\nJAVA\n\ncat > "$REPORTER_JAVA"', registrar_start)
if registrar_start < 0 or registrar_end < 0:
    raise SystemExit('v131 registrar segment missing')
registrar = s[registrar_start:registrar_end]
if 'public static boolean vibrationEnabled(Context context)' in registrar:
    old = '        return prefs(context).getBoolean(KEY_VIBRATION, true);'
    if old in registrar:
        registrar = registrar.replace(old, '        return true; // assignment vibration is mandatory in v1.3.1', 1)
s = s[:registrar_start] + registrar + s[registrar_end:]

for required in (
    'VERSION="1.3.1"',
    'VERSION_CODE="131"',
    'versionCode 131',
    "versionName '1.3.1'",
    'APP_VERSION = "1.3.1"',
    'private static final int MAX_GROUPS = 8;',
    'AlertVibrationController.start(this, assignmentId);',
    'channel.enableVibration(true);',
    'channel.setVibrationPattern(new long[]{0, 650, 220, 650, 220, 650});',
    'jayuminton_wait1_native_v131',
    'jayuminton_court_native_v131',
    'JAYUMINTON_V126_START_STOP_RACE_GUARD',
):
    if required not in s:
        raise SystemExit('missing v131 recovery marker: ' + required)

path.write_text(s, encoding='utf-8')
print('Prepared v1.3.1 code131: fresh vibration channels + mandatory native 3-pulse x max8 controller.')
