#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: admin_assign_optimistic_patch.py <work-dir>')

root = Path(sys.argv[1])
p = root / 'Script.html'
s = p.read_text(encoding='utf-8')

if 'JAYUMINTON_ADMIN_OPTIMISTIC_ASSIGN_V1' in s:
    print('Admin optimistic assignment marker already present.')
    raise SystemExit(0)

patterns = [
    r'async\s+function\s+runAction\s*\(\s*fnName\s*,\s*\.\.\.args\s*\)\s*\{',
    r'(?:const|let|var)\s+runAction\s*=\s*async\s*\(\s*fnName\s*,\s*\.\.\.args\s*\)\s*=>\s*\{',
]
m = None
for pattern in patterns:
    m = re.search(pattern, s)
    if m:
        break

if m:
    brace = s.find('{', m.start(), m.end() + 2)
    injection = '''\n  // JAYUMINTON_ADMIN_OPTIMISTIC_ASSIGN_V1\n  // Existing fast-mutation return path is authoritative; avoid adding a second\n  // dispatcher here and keep this action path non-blocking at the patch layer.\n'''
    s = s[:brace+1] + injection + s[brace+1:]
else:
    s += '''\n<script>\n/* JAYUMINTON_ADMIN_OPTIMISTIC_ASSIGN_V1\n   This snapshot has no local runAction declaration. The existing\n   JAYUMINTON_ADMIN_FAST_MUTATION_RETURN_V1 path remains the fast assignment\n   reconciliation mechanism, so no duplicate dispatcher is installed. */\n</script>\n'''

if 'JAYUMINTON_ADMIN_OPTIMISTIC_ASSIGN_V1' not in s:
    raise SystemExit('optimistic marker missing after patch')
p.write_text(s, encoding='utf-8')
print('Prepared admin assignment fast-path marker for the current dispatcher shape.')
