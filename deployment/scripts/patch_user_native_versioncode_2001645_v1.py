#!/usr/bin/env python3
"""Play Console permanently burns a versionCode once uploaded to any draft,
even after the draft is deleted. 2001642 and 2001643 are both already
consumed by earlier upload attempts, so jump ahead with a small buffer."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')

pairs = (
    ('VERSION_CODE="2001643"', 'VERSION_CODE="2001645"'),
    ('versionCode 2001643', 'versionCode 2001645'),
    ('version_code=2001643', 'version_code=2001645'),
    ("versionCode='2001643'", "versionCode='2001645'"),
)
for old, new in pairs:
    if old not in source:
        raise SystemExit('versionCode bump anchor missing: ' + old)
    source = source.replace(old, new, 1)

if '2001643' in source:
    raise SystemExit('stale versionCode 2001643 residue remains')

path.write_text(source, encoding='utf-8')
print('VERSION_CODE_2001645_OK')
