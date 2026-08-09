#!/usr/bin/env python3
from pathlib import Path
import re
import sys


root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
path = root / "Script.html"
source = path.read_text(encoding="utf-8")
target = (
    "https://raw.githubusercontent.com/pianopp001-cpu/jayuminton-admin-app/"
    "main/releases/jayuminton-courtstatus-v1.1.5-test.apk"
)
source, count = re.subn(
    r"https://raw\.githubusercontent\.com/pianopp001-cpu/jayuminton-admin-app/"
    r"main/releases/jayuminton-courtstatus-v[0-9.]+-(?:fresh-install|test)\.apk",
    target,
    source,
    count=1,
)
if count != 1 and target not in source:
    raise SystemExit("v1.1.5 test APK link replacement failed")
source = re.sub(
    r"/JayumintonUserNative\\/1\\\.[0-9]+\\\.[0-9]+/i",
    r"/JayumintonUserNative\\/1\\.1\\.5/i",
    source,
    count=1,
)
if target not in source:
    raise SystemExit("v1.1.5 test APK link verification failed")
path.write_text(source, encoding="utf-8")
print("Updated only the user app-install button to the v1.1.5 test APK.")
