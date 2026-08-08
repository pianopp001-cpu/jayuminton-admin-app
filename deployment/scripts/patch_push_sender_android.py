#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = root / 'Code.js'
s = p.read_text(encoding='utf-8')

old_repeat = "repeatCount: event.type === 'court_assignment' ? '3' : '1',"
new_repeat = "repeatCount: event.type === 'court_assignment' ? '5' : '3',"
if old_repeat in s:
    s = s.replace(old_repeat, new_repeat, 1)
elif new_repeat not in s:
    raise SystemExit('push repeatCount expression not found')

needle = "      data: data,\n      webpush: {"
replacement = "      data: data,\n      android: {\n        priority: 'high',\n        ttl: '600s'\n      },\n      webpush: {"
if needle in s:
    s = s.replace(needle, replacement, 1)
elif "priority: 'high'" not in s or "ttl: '600s'" not in s:
    raise SystemExit('push payload insertion point not found')

if new_repeat not in s:
    raise SystemExit('push repeat count verification failed')
if "android: {" not in s or "priority: 'high'" not in s or "ttl: '600s'" not in s:
    raise SystemExit('android high priority verification failed')

p.write_text(s, encoding='utf-8')
print('Applied FCM sender: Android high priority, TTL 600s, wait1 repeat=3, court repeat=5.')
