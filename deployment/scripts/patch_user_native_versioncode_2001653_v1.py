#!/usr/bin/env python3
"""Bump versionCode for the incoming-짝요청 alert native vibration bridge."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')

pairs = (
    ('VERSION_CODE="2001652"', 'VERSION_CODE="2001653"'),
    ('versionCode 2001652', 'versionCode 2001653'),
    ('version_code=2001652', 'version_code=2001653'),
    ("versionCode='2001652'", "versionCode='2001653'"),
)
for old, new in pairs:
    if old not in source:
        raise SystemExit('versionCode bump anchor missing: ' + old)
    source = source.replace(old, new, 1)

for old, new in pairs:
    if old in source:
        raise SystemExit('stale versionCode residue remains: ' + old)

path.write_text(source, encoding='utf-8')
print('VERSION_CODE_2001653_OK')
