#!/usr/bin/env python3
from pathlib import Path
import re, sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = root / 'Code.js'
s = p.read_text(encoding='utf-8')
patterns = [
    r"repeatCount:\s*event\.type\s*===\s*'court_assignment'\s*\?\s*'5'\s*:\s*'3'\s*,",
    r"repeatCount:\s*event\.type\s*===\s*'court_assignment'\s*\?\s*'3'\s*:\s*'1'\s*,",
]
replaced = False
for pat in patterns:
    s2, n = re.subn(pat, "repeatCount: '1',", s, count=1)
    if n:
        s = s2
        replaced = True
        break
if not replaced and "repeatCount: '1'," not in s:
    raise SystemExit('repeatCount expression not found')
if "priority: 'high'" not in s:
    raise SystemExit('Android high priority missing')
if "Urgency: 'high'" not in s:
    raise SystemExit('Web high urgency missing')
p.write_text(s, encoding='utf-8')
print('Push sender normalized: one FCM delivery per event; device handles 3x3/3x5 vibration locally.')
