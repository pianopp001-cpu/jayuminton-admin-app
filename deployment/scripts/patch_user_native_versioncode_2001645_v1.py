#!/usr/bin/env python3
"""Hotfix Play release versionCode.

The public-test bundle 2001646 still inherited the administrator loading layout.
The repaired user-layout bundle must use an unused, strictly higher code, so this
historical final bump step now advances the generated user build from 2001643
directly to 2001647.
"""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')

pairs = (
    ('VERSION_CODE="2001643"', 'VERSION_CODE="2001647"'),
    ('versionCode 2001643', 'versionCode 2001647'),
    ('version_code=2001643', 'version_code=2001647'),
    ("versionCode='2001643'", "versionCode='2001647'"),
)
for old, new in pairs:
    if old not in source:
        raise SystemExit('versionCode bump anchor missing: ' + old)
    source = source.replace(old, new, 1)

if '2001643' in source:
    raise SystemExit('stale versionCode 2001643 residue remains')
if 'VERSION_CODE="2001647"' not in source:
    raise SystemExit('versionCode 2001647 patch failed')

path.write_text(source, encoding='utf-8')
print('VERSION_CODE_2001647_OK')
