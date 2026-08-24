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

# The snapshot has accumulated several formatting variants over time.  The
# downstream vNext patch only cares that blank fields stay blank, so normalize
# the user-visible placeholder literals first instead of failing on whitespace
# or formatting differences in an old block.
replacements = {
    "'급수·구력 미입력'": "''",
    '"급수·구력 미입력"': '""',
    "'급수 미입력'": "''",
    '"급수 미입력"': '""',
    "'구력 미입력'": "''",
    '"구력 미입력"': '""',
}
for old, new in replacements.items():
    s = s.replace(old, new)

# Remove the legacy prefix where the snapshot still builds experience text as
# "구력 X".  The current MD contract shows the stored experience itself.
s = s.replace("'구력 ' + experience", "experience")
s = s.replace('"구력 " + experience', 'experience')

if s != original:
    path.write_text(s, encoding='utf-8')
    print('admin legacy missing-value variants normalized')
else:
    print('admin legacy missing-value normalization already clean')
