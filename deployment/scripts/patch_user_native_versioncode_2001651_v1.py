#!/usr/bin/env python3
"""Bump versionCode for the foreground-alert-suppression + in-page vibration hotfix."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')

pairs = (
    ('VERSION_CODE="2001650"', 'VERSION_CODE="2001651"'),
    ('versionCode 2001650', 'versionCode 2001651'),
    ('version_code=2001650', 'version_code=2001651'),
    ("versionCode='2001650'", "versionCode='2001651'"),
)
for old, new in pairs:
    if old not in source:
        raise SystemExit('versionCode bump anchor missing: ' + old)
    source = source.replace(old, new, 1)

for old, new in pairs:
    if old in source:
        raise SystemExit('stale versionCode residue remains: ' + old)

path.write_text(source, encoding='utf-8')
print('VERSION_CODE_2001651_OK')
