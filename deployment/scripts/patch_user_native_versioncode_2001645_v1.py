#!/usr/bin/env python3
"""Hotfix Play release versionCode.

2001648 adds native vibration for administrator direct messages while preserving
all existing user/admin communication and current-member FCM behavior.
"""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')

pairs = (
    ('VERSION_CODE="2001643"', 'VERSION_CODE="2001648"'),
    ('versionCode 2001643', 'versionCode 2001648'),
    ('version_code=2001643', 'version_code=2001648'),
    ("versionCode='2001643'", "versionCode='2001648'"),
)
for old, new in pairs:
    if old not in source:
        raise SystemExit('versionCode bump anchor missing: ' + old)
    source = source.replace(old, new, 1)

if '2001643' in source:
    raise SystemExit('stale versionCode 2001643 residue remains')
if 'VERSION_CODE="2001648"' not in source:
    raise SystemExit('versionCode 2001648 patch failed')

path.write_text(source, encoding='utf-8')
print('VERSION_CODE_2001648_OK')
