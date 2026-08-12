#!/usr/bin/env python3
from pathlib import Path
import re
import sys

# Unique, cache-busting release asset for the cap8 build.
APK_FILENAME = "Jayuminton-User-v1.3.0-code130-cap8.apk"
APK_BASE = "https://github.com/pianopp001-cpu/jayuminton-admin-app/releases/download/user-v1.3.0-cap8/" + APK_FILENAME
APK = APK_BASE + "?download=1&build=130-cap8-live"
MARKER = "JAYUMINTON_NATIVE_APK_DOWNLOAD_V130"

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_user_install_link_v130.py <hosting|main> <path>")
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

    # Remove any previous Android direct-download override before inserting exactly one.
    old_override = re.compile(
        re.escape(handler) +
        r"    if \(androidDevice\) \{\n"
        r"(?:.*\n){1,16}?"
        r"      window\.location\.href = JAYUMINTON_USER_APK_[A-Z0-9_]+;\n"
        r"      return;\n"
        r"    \}\n"
    )
    s = old_override.sub(handler, s, count=1)

    block = f"  /* {MARKER} */\n  const JAYUMINTON_USER_APK_V130 = '{APK}';\n\n"
    s = s.replace(handler, block + handler, 1)
    replacement = handler + '''    if (androidDevice) {
      localStorage.setItem(STORAGE.installChoice, 'on');
      setInstallMessage('자유민턴 사용자 앱 1.3.0을 다운로드합니다.', 'success');
      sendAppInstallStatus('APK 다운로드 시작');
      showToast('1.3.0 다운로드가 시작됩니다. 완료 후 APK를 실행해 주세요.');
      window.location.href = JAYUMINTON_USER_APK_V130;
      return;
    }
'''
    s = s.replace(handler, replacement, 1)
    s = s.replace('1.2.8', '1.3.0').replace('1.2.9', '1.3.0')
    s = s.replace('JAYUMINTON_USER_APK_V128', 'JAYUMINTON_USER_APK_V130')
    s = s.replace('JAYUMINTON_USER_APK_V129', 'JAYUMINTON_USER_APK_V130')
    s = s.replace('JAYUMINTON_NATIVE_APK_DOWNLOAD_V128', MARKER)
    s = s.replace('JAYUMINTON_NATIVE_APK_DOWNLOAD_V129', MARKER)

    if MARKER not in s or APK not in s:
        raise SystemExit("v1.3.0 hosting route missing")
    if '1.2.8' in s or '1.2.9' in s:
        raise SystemExit("stale installer version text remained in hosting setup")

elif mode == "main":
    # Normalize every known user APK URL to this one unique release asset.
    url_pattern = re.compile(
        r"https://(?:raw\.githubusercontent\.com|github\.com)/"
        r"pianopp001-cpu/jayuminton-admin-app/"
        r"[^'\"\s<>]*?\.apk(?:\?[^'\"\s<>]*)?"
    )
    s, n_urls = url_pattern.subn(APK, s)

    file_pattern = re.compile(
        r"(?:jayuminton-(?:courtstatus|user)[A-Za-z0-9._()\-]*\.apk|"
        r"Jayuminton-User-v[0-9.]+-code[0-9]+[A-Za-z0-9._()\-]*\.apk)"
    )
    s = file_pattern.sub(APK_FILENAME, s)

    # User-side installer labels only. Do not touch Admin/Code/Index/Style files.
    s = s.replace('1.2.8', '1.3.0').replace('1.2.9', '1.3.0')
    s = s.replace('V128', 'V130').replace('v128', 'v130')
    s = s.replace('V129', 'V130').replace('v129', 'v130')

    if APK not in s:
        raise SystemExit(f"v1.3.0 main APK route missing; normalized_urls={n_urls}")
    if '1.2.8' in s or '1.2.9' in s:
        raise SystemExit("stale installer version remained in main Script.html")
else:
    raise SystemExit("mode must be hosting or main")

path.write_text(s, encoding="utf-8")
print(f"Connected {mode} user install route to v1.3.0 code130 cap8 release asset.")
