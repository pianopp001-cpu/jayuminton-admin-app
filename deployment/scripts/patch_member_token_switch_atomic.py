#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
path = root / 'Code.js'
s = path.read_text(encoding='utf-8')
marker = 'JAYUMINTON_MEMBER_TOKEN_SWITCH_ATOMIC_V1'

if marker not in s:
    start = s.find('function unregisterWebToken_(body) {')
    if start < 0:
        raise SystemExit('unregisterWebToken_ missing')
    end = s.find('\n}', start)
    if end < 0:
        raise SystemExit('unregisterWebToken_ end missing')
    # Expand through the function's balanced braces.
    i = s.find('{', start) + 1
    depth = 1
    quote = None
    escape = False
    while i < len(s) and depth:
        ch = s[i]
        if quote:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == quote:
                quote = None
        else:
            if ch in ('\'', '"', '`'):
                quote = ch
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
        i += 1
    if depth != 0:
        raise SystemExit('unregisterWebToken_ parse failed')
    end = i
    fn = s[start:end]

    token_anchor = "  const token = cleanToken_(body.token);\n"
    if token_anchor not in fn:
        raise SystemExit('unregister token anchor missing')
    fn = fn.replace(
        token_anchor,
        token_anchor + "  const memberId = cleanText_(body.memberId, 200);\n",
        1,
    )

    filter_old = '''    const next = records.filter(function(record) {
      return record && record.token !== token;
    });'''
    filter_new = '''    const next = records.filter(function(record) {
      if (!record) return false;
      if (record.token !== token) return true;
      // JAYUMINTON_MEMBER_TOKEN_SWITCH_ATOMIC_V1
      // A delayed unregister for the previously selected member must never
      // delete the same device token after registerWebToken_ has atomically
      // reassigned that token to a newly selected member.
      if (memberId && String(record.memberId || '') !== memberId) return true;
      return false;
    });'''
    if filter_old not in fn:
        raise SystemExit('unregister filter anchor missing')
    fn = fn.replace(filter_old, filter_new, 1)
    s = s[:start] + fn + s[end:]

for required in (
    marker,
    'const memberId = cleanText_(body.memberId, 200);',
    "if (memberId && String(record.memberId || '') !== memberId) return true;",
    'record.token !== token',
):
    if required not in s:
        raise SystemExit('missing atomic member switch marker: ' + required)

path.write_text(s, encoding='utf-8')
print('Patched member-token switch: stale old-member unregister cannot remove a token reassigned to the new member.')
