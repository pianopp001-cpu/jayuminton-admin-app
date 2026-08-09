#!/usr/bin/env python3
from pathlib import Path
import re, sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = root / 'Script.html'
s = p.read_text(encoding='utf-8')
s, count = re.subn(
    r'https://raw\.githubusercontent\.com/pianopp001-cpu/jayuminton-admin-app/main/releases/jayuminton-courtstatus-v[0-9.]+-fresh-install\.apk',
    'https://raw.githubusercontent.com/pianopp001-cpu/jayuminton-admin-app/main/releases/jayuminton-courtstatus-v1.1.4-fresh-install.apk',
    s,
    count=1,
)
if count != 1:
    raise SystemExit('v1.1.4 APK link replacement failed')
s = re.sub(r'/JayumintonUserNative\\/1\\\.[0-9]+\\\.[0-9]+/i',
           r'/JayumintonUserNative\\/1\\.1\\.4/i', s, count=1)
if 'jayuminton-courtstatus-v1.1.4-fresh-install.apk' not in s:
    raise SystemExit('v1.1.4 APK link verification failed')
p.write_text(s, encoding='utf-8')
print('Updated only the user APK link and native v1.1.4 hint.')
