#!/usr/bin/env python3
from pathlib import Path
import re
import sys

# Keep the verified v1.2.8 APK bytes, but use a fresh cache-busting URL so a
# phone/browser cannot reuse an earlier downloaded APK response.
APK = "https://raw.githubusercontent.com/pianopp001-cpu/jayuminton-admin-app/main/releases/jayuminton-courtstatus-v1.2.8-repeat-switch.apk?build=128-repeat-switch&r=20260810-2113"
MARKER = "JAYUMINTON_NATIVE_APK_DOWNLOAD_V128"

mode = sys.argv[1]
path = Path(sys.argv[2])
s = path.read_text(encoding="utf-8")

if mode == "hosting":
    block_pattern = re.compile(
        r"  /\* JAYUMINTON_NATIVE_APK_DOWNLOAD_[A-Z0-9_]+ \*/\n"
        r"  const JAYUMINTON_USER_APK_[A-Z0-9_]+ = '[^']+';\n\n"
    )
    s = block_pattern.sub("", s)
    handler = "  function handleAppInstallButton(fromDirectUserTap) {\n"
    if s.count(handler) != 1:
        raise SystemExit("hosting install handler not found exactly once")
    old_override = re.compile(
        re.escape(handler) +
        r"    if \(androidDevice\) \{\n"
        r"(?:.*\n){1,12}?"
        r"      window\.location\.href = JAYUMINTON_USER_APK_[A-Z0-9_]+;\n"
        r"      return;\n"
        r"    \}\n"
    )
    s = old_override.sub(handler, s, count=1)
    block = f"  /* {MARKER} */\n  const JAYUMINTON_USER_APK_V128 = '{APK}';\n\n"
    s = s.replace(handler, block + handler, 1)
    replacement = handler + '''    if (androidDevice) {
      localStorage.setItem(STORAGE.installChoice, 'on');
      setInstallMessage('자유민턴 사용자 앱 1.2.8을 다운로드합니다.', 'success');
      sendAppInstallStatus('APK 다운로드 시작');
      showToast('다운로드가 시작됩니다. 완료 후 APK를 실행해 주세요.');
      window.location.href = JAYUMINTON_USER_APK_V128;
      return;
    }
'''
    s = s.replace(handler, replacement, 1)
    for required in (MARKER, APK, "window.location.href = JAYUMINTON_USER_APK_V128"):
        if required not in s:
            raise SystemExit("missing v1.2.8 hosting APK marker: " + required)

elif mode == "main":
    pattern = re.compile(
        r"https://(?:raw\.githubusercontent\.com/pianopp001-cpu/jayuminton-admin-app/main/releases/|github\.com/pianopp001-cpu/jayuminton-admin-app/raw/refs/heads/main/releases/)"
        r"jayuminton-(?:courtstatus|user)[A-Za-z0-9._-]*\.apk(?:\?build=[A-Za-z0-9._-]+(?:&r=[A-Za-z0-9._-]+)?)?"
    )
    s, count = pattern.subn(APK, s)
    if count < 1 and APK not in s:
        raise SystemExit("native user APK URL not found in main Script.html")
    if APK not in s:
        raise SystemExit("v1.2.8 APK URL missing from main Script.html")
else:
    raise SystemExit("mode must be hosting or main")

path.write_text(s, encoding="utf-8")
print(f"Connected {mode} user install button to cache-busted v1.2.8 repeated-switch APK.")
