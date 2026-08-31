#!/usr/bin/env python3
"""Play Console rejected versionCode 2001642 as already used by a prior upload
attempt; bump the integer versionCode only. versionName/VERSION stay '1.6.42'
since Play does not require versionName to be unique, only versionCode."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')

pairs = (
    ('VERSION_CODE="2001642"', 'VERSION_CODE="2001643"'),
    ('versionCode 2001642', 'versionCode 2001643'),
    ('version_code=2001642', 'version_code=2001643'),
    ("versionCode='2001642'", "versionCode='2001643'"),
)
for old, new in pairs:
    if old not in source:
        raise SystemExit('versionCode bump anchor missing: ' + old)
    source = source.replace(old, new, 1)

if '2001642' in source:
    raise SystemExit('stale versionCode 2001642 residue remains')

path.write_text(source, encoding='utf-8')
print('VERSION_CODE_2001643_OK')
