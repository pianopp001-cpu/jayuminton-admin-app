#!/usr/bin/env python3
from pathlib import Path
import re
import sys

# Keep the verified v1.2.8 APK bytes, but use a fresh cache-busting URL so a
# phone/browser cannot reuse an earlier downloaded APK response.
APK_FILENAME = "jayuminton-courtstatus-v1.2.8-repeat-switch.apk"
APK = "https://raw.githubusercontent.com/pianopp001-cpu/jayuminton-admin-app/main/releases/" + APK_FILENAME + "?build=128-repeat-switch&r=20260810-2139"
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
    original = s

    # First replace every complete GitHub/raw user-APK URL we can recognize,
    # regardless of the historical URL form or query string.
    url_pattern = re.compile(
        r"https://(?:raw\.githubusercontent\.com|github\.com)/"
        r"pianopp001-cpu/jayuminton-admin-app/"
        r"[^'\"\s<>]*?"
        r"jayuminton-(?:courtstatus|user)[A-Za-z0-9._()\-]*\.apk"
        r"(?:\?[^'\"\s<>]*)?"
    )
    s, url_count = url_pattern.subn(APK, s)

    # Some older page revisions assembled the URL around only the filename.
    # Normalize every user APK filename token in Script.html to the v1.2.8 file.
    filename_pattern = re.compile(
        r"jayuminton-(?:courtstatus|user)[A-Za-z0-9._()\-]*\.apk"
    )
    filenames_before = filename_pattern.findall(s)
    s = filename_pattern.sub(APK_FILENAME, s)

    # If the page contains a direct v1.2.8 raw URL without our fresh query,
    # normalize that full URL as well.
    current_plain = (
        "https://raw.githubusercontent.com/pianopp001-cpu/jayuminton-admin-app/main/releases/"
        + APK_FILENAME
    )
    s = re.sub(re.escape(current_plain) + r"(?:\?[^'\"\s<>]*)?", APK, s)

    if APK_FILENAME not in s:
        raise SystemExit("v1.2.8 APK filename missing from main Script.html")
    stale = [name for name in filename_pattern.findall(s) if name != APK_FILENAME]
    if stale:
        raise SystemExit("stale user APK filename remained in main Script.html")
    if url_count < 1 and not filenames_before and APK not in original:
        raise SystemExit("native user APK route not found in main Script.html")

    print(
        "main-route-normalized",
        "full_urls=", url_count,
        "filename_tokens=", len(filenames_before),
        "v128_tokens=", s.count(APK_FILENAME),
    )
else:
    raise SystemExit("mode must be hosting or main")

path.write_text(s, encoding="utf-8")
print(f"Connected {mode} user install button to cache-busted v1.2.8 repeated-switch APK.")
