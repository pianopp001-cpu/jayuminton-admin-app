#!/usr/bin/env python3
"""The 2001648 upload attempt errored on Play Console (API level 35 < 36
required) before this fix landed. Play Console may mark a versionCode as
consumed even on an errored/discarded draft, so bump ahead defensively at
the same time as the targetSdk 36 fix to avoid a second round-trip."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')

pairs = (
    ('VERSION_CODE="2001648"', 'VERSION_CODE="2001649"'),
    ('versionCode 2001648', 'versionCode 2001649'),
    ('version_code=2001648', 'version_code=2001649'),
    ("versionCode='2001648'", "versionCode='2001649'"),
)
for old, new in pairs:
    if old not in source:
        raise SystemExit('versionCode bump anchor missing: ' + old)
    source = source.replace(old, new, 1)

if '2001648' in source:
    raise SystemExit('stale versionCode 2001648 residue remains')

path.write_text(source, encoding='utf-8')
print('VERSION_CODE_2001649_OK')
