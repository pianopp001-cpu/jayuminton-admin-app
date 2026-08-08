#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = root / 'Script.html'
s = p.read_text(encoding='utf-8')

def replace_function(src, signature, replacement):
    start = src.find(signature)
    if start < 0:
        raise SystemExit(f'missing function: {signature}')
    brace = src.find('{', start)
    if brace < 0:
        raise SystemExit(f'missing opening brace: {signature}')
    depth = 0
    quote = None
    escape = False
    i = brace
    while i < len(src):
        ch = src[i]
        if quote:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == quote:
                quote = None
        else:
            if ch in ('"', "'", '`'):
                quote = ch
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return src[:start] + replacement + src[i+1:]
        i += 1
    raise SystemExit(f'unbalanced function: {signature}')

s = replace_function(s, 'function memberAlertRepeatCount(type) {', """function memberAlertRepeatCount(type) {
  if (type === 'court_assignment') return 5;
  if (type === 'wait1_ready') return 3;
  return 1;
}""")

s = replace_function(s, 'function memberVibrationPattern(type) {', """function memberVibrationPattern(type) {
  return [650, 220, 650, 220, 650];
}""")

old = '    }, index * 1700);'
if old not in s:
    old = '    }, index * 2000);'
if old not in s:
    old = '    }, index * 1300);'
if old not in s:
    raise SystemExit('member alert repeat interval not found')
s = s.replace(old, '    }, index * 3500);', 1)

if "if (type === 'court_assignment') return 5;" not in s:
    raise SystemExit('court repeat 5 verification failed')
if "if (type === 'wait1_ready') return 3;" not in s:
    raise SystemExit('wait1 repeat 3 verification failed')
if '[650, 220, 650, 220, 650]' not in s:
    raise SystemExit('long vibration pattern verification failed')
if 'index * 3500' not in s:
    raise SystemExit('repeat spacing verification failed')

p.write_text(s, encoding='utf-8')
print('Applied user foreground alert: wait1=3 pulses x3 groups, court=3 pulses x5 groups.')
