#!/usr/bin/env python3
"""Normalize legacy admin grade/experience placeholder variants before vNext patching.
Cloudflare/APK build helper only; does not deploy or call Apps Script.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
path = root / 'Script.html'
s = path.read_text(encoding='utf-8')
original = s

# Normalize every historical quoting/template variant. The downstream patch
# treats the mere presence of these legacy labels as a hard failure, so remove
# the literal text regardless of quote style.
for legacy in ('급수·구력 미입력', '급수 미입력', '구력 미입력'):
    s = s.replace(legacy, '')

# Remove historical "구력 " prefixes. The current MD contract shows the
# stored experience value itself.
s = s.replace("'구력 ' + experience", "experience")
s = s.replace('"구력 " + experience', 'experience')
s = s.replace('`구력 ${experience}`', 'experience')

if s != original:
    path.write_text(s, encoding='utf-8')
    print('admin legacy missing-value variants normalized')
else:
    print('admin legacy missing-value normalization already clean')
