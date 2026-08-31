#!/usr/bin/env python3
"""Google Play now requires targetSdk 35+ for new releases; bump it from 34."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')

old = '        targetSdk 34\n'
new = '        targetSdk 35\n'
if old not in source:
    raise SystemExit('targetSdk 34 anchor missing or already changed')
source = source.replace(old, new, 1)

if 'targetSdk 35' not in source or 'targetSdk 34' in source:
    raise SystemExit('targetSdk 35 patch failed')

path.write_text(source, encoding='utf-8')
print('TARGET_SDK_35_OK')
