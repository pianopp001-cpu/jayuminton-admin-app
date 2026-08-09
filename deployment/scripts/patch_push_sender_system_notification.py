#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = root / 'Code.js'
s = p.read_text(encoding='utf-8')
old = """      android: {
        priority: 'high',
        ttl: '600s'
      },"""
new = """      android: {
        priority: 'high',
        ttl: '600s',
        restricted_package_name: 'com.jayuminton.user',
        notification: {
          title: data.title,
          body: data.body,
          icon: 'icon',
          sound: 'default',
          channel_id: event.type === 'court_assignment'
            ? 'jayuminton_court_system_v114'
            : 'jayuminton_wait1_system_v114',
          notification_priority: 'PRIORITY_MAX',
          visibility: 'PUBLIC',
          default_sound: true,
          vibrate_timings: event.type === 'court_assignment'
            ? ['0s','0.9s','0.22s','0.9s','0.22s','0.9s','1.1s','0.9s','0.22s','0.9s','0.22s','0.9s','1.1s','0.9s','0.22s','0.9s','0.22s','0.9s','1.1s','0.9s','0.22s','0.9s','0.22s','0.9s','1.1s','0.9s','0.22s','0.9s','0.22s','0.9s']
            : ['0s','0.9s','0.22s','0.9s','0.22s','0.9s','1.1s','0.9s','0.22s','0.9s','0.22s','0.9s','1.1s','0.9s','0.22s','0.9s','0.22s','0.9s']
        }
      },"""
if 'jayuminton_court_system_v114' not in s:
    if s.count(old) != 1:
        raise SystemExit('Android sender block expected once, found ' + str(s.count(old)))
    s = s.replace(old, new, 1)

for marker in (
    "restricted_package_name: 'com.jayuminton.user'",
    'jayuminton_court_system_v114',
    'jayuminton_wait1_system_v114',
    "notification_priority: 'PRIORITY_MAX'",
    "visibility: 'PUBLIC'",
    'vibrate_timings:',
):
    if marker not in s:
        raise SystemExit('missing system notification sender marker: ' + marker)

p.write_text(s, encoding='utf-8')
print('Patched Android FCM to system-rendered background notifications with long vibration.')
