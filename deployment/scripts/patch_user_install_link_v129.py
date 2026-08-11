#!/usr/bin/env python3
from pathlib import Path
import re
import sys

# Live hotfix trigger 2026-08-11: force the actual rendered installer route to 1.2.9.
APK_FILENAME = "Jayuminton-User-v1.2.9-code129-R2.apk"
APK = "https://github.com/pianopp001-cpu/jayuminton-admin-app/releases/download/user-v1.2.9-r2/" + APK_FILENAME + "?download=1&build=129-live-main"
MARKER = "JAYUMINTON_NATIVE_APK_DOWNLOAD_V129"

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_user_install_link_v129.py <hosting|main> <path>")
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
        r"(?:.*\n){1,14}?"
        r"      window\.location\.href = JAYUMINTON_USER_APK_[A-Z0-9_]+;\n"
        r"      return;\n"
        r"    \}\n"
    )
    s = old_override.sub(handler, s, count=1)
    block = f"  /* {MARKER} */\n  const JAYUMINTON_USER_APK_V129 = '{APK}';\n\n"
    s = s.replace(handler, block + handler, 1)
    replacement = handler + '''    if (androidDevice) {
      localStorage.setItem(STORAGE.installChoice, 'on');
      setInstallMessage('자유민턴 사용자 앱 1.2.9을 다운로드합니다.', 'success');
      sendAppInstallStatus('APK 다운로드 시작');
      showToast('1.2.9 다운로드가 시작됩니다. 완료 후 APK를 실행해 주세요.');
      window.location.href = JAYUMINTON_USER_APK_V129;
      return;
    }
'''
    s = s.replace(handler, replacement, 1)
    s = s.replace('1.2.8', '1.2.9')
    s = s.replace('JAYUMINTON_USER_APK_V128', 'JAYUMINTON_USER_APK_V129')
    s = s.replace('JAYUMINTON_NATIVE_APK_DOWNLOAD_V128', MARKER)
    if MARKER not in s or APK not in s:
        raise SystemExit("v1.2.9 hosting route missing")

elif mode == "main":
    # Normalize every known user APK URL to the single release asset.
    url_pattern = re.compile(
        r"https://(?:raw\.githubusercontent\.com|github\.com)/"
        r"pianopp001-cpu/jayuminton-admin-app/"
        r"[^'\"\s<>]*?\.apk(?:\?[^'\"\s<>]*)?"
    )
    s, n_urls = url_pattern.subn(APK, s)

    # Normalize any bare historic user APK filename token.
    file_pattern = re.compile(r"jayuminton-(?:courtstatus|user)[A-Za-z0-9._()\-]*\.apk|Jayuminton-User-v1\.2\.9-code129-R2\.apk")
    s = file_pattern.sub(APK_FILENAME, s)

    # The live user iframe still exposed 1.2.8 in the install UI. Script.html is user-side only;
    # change the displayed installer version and historical installer identifiers there.
    s = s.replace('1.2.8', '1.2.9')
    s = s.replace('V128', 'V129').replace('v128', 'v129')

    # Ensure at least one install route exists and points to the verified v1.2.9 asset.
    if APK not in s:
        raise SystemExit(f"v1.2.9 main APK route missing; normalized_urls={n_urls}")
    if 'jayuminton-courtstatus-v1.2.8-repeat-switch.apk' in s:
        raise SystemExit("old v1.2.8 APK filename remained in main Script.html")
else:
    raise SystemExit("mode must be hosting or main")

path.write_text(s, encoding="utf-8")
print(f"Connected {mode} user install route to v1.2.9 code129 release asset.")
