#!/usr/bin/env python3
"""Google Play now requires targetSdk 36+ for new releases (raised again
from 35). AGP 8.5.2 does not support compileSdk 36, so this also bumps the
Android Gradle Plugin to 8.9.1, which in turn requires Gradle 8.11.1+
(the workflow that calls this must supply that Gradle version)."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')

pairs = (
    ("id 'com.android.application' version '8.5.2' apply false",
     "id 'com.android.application' version '8.9.1' apply false"),
    ('compileSdk 35', 'compileSdk 36'),
    ('targetSdk 35', 'targetSdk 36'),
)
for old, new in pairs:
    if old not in source:
        raise SystemExit('targetSdk36 patch anchor missing: ' + old)
    source = source.replace(old, new, 1)

if 'targetSdk 35' in source or 'compileSdk 35' in source or "version '8.5.2'" in source:
    raise SystemExit('stale SDK35/AGP8.5.2 residue remains')
if 'targetSdk 36' not in source or 'compileSdk 36' not in source:
    raise SystemExit('targetSdk/compileSdk 36 patch failed')

path.write_text(source, encoding='utf-8')
print('TARGET_SDK_36_OK')
