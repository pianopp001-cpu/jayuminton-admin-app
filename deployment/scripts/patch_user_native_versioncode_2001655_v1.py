#!/usr/bin/env python3
"""Bump the Play build above the currently published 2001654."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')
pairs = (
    ('VERSION_CODE="2001654"', 'VERSION_CODE="2001655"'),
    ('versionCode 2001654', 'versionCode 2001655'),
    ('version_code=2001654', 'version_code=2001655'),
    ("versionCode='2001654'", "versionCode='2001655'"),
)
for old, new in pairs:
    if old not in source:
        raise SystemExit('versionCode bump anchor missing: ' + old)
    source = source.replace(old, new, 1)
for old, _ in pairs:
    if old in source:
        raise SystemExit('stale versionCode residue remains: ' + old)
path.write_text(source, encoding='utf-8')
print('VERSION_CODE_2001655_OK')
