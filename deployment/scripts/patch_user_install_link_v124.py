#!/usr/bin/env python3
from pathlib import Path
import re
import sys

APK = "https://raw.githubusercontent.com/pianopp001-cpu/jayuminton-admin-app/main/releases/jayuminton-courtstatus-v1.2.5-confirm-stop.apk"

mode = sys.argv[1]
path = Path(sys.argv[2])
s = path.read_text(encoding="utf-8")

if mode == "hosting":
    marker = "JAYUMINTON_NATIVE_APK_DOWNLOAD_V125"
    if marker not in s:
        anchor = "  function handleAppInstallButton(fromDirectUserTap) {"
        block = f'''  /* {marker} */
  const JAYUMINTON_USER_APK_V125 = '{APK}';

'''
        if s.count(anchor) != 1:
            raise SystemExit("hosting install handler not found once")
        s = s.replace(anchor, block + anchor, 1)

        handler = anchor + "\n"
        replacement = handler + '''    if (androidDevice) {
      localStorage.setItem(STORAGE.installChoice, 'on');
      setInstallMessage('자유민턴 사용자 앱 전체 설치본을 다운로드합니다.', 'success');
      sendAppInstallStatus('APK 다운로드 시작');
      showToast('다운로드가 시작됩니다. 완료 후 APK를 실행해 주세요.');
      window.location.href = JAYUMINTON_USER_APK_V125;
      return;
    }
'''
        s = s.replace(handler, replacement, 1)

    for required in (marker, APK, "window.location.href = JAYUMINTON_USER_APK_V125"):
        if required not in s:
            raise SystemExit("missing hosting APK marker: " + required)

elif mode == "main":
    # Replace only native user APK release URLs; never touch admin assets.
    pattern = re.compile(
        r"https://(?:raw\.githubusercontent\.com/pianopp001-cpu/jayuminton-admin-app/main/releases/|github\.com/pianopp001-cpu/jayuminton-admin-app/raw/refs/heads/main/releases/)"
        r"jayuminton-(?:courtstatus|user)[A-Za-z0-9._-]*\.apk"
    )
    s, count = pattern.subn(APK, s)
    if count < 1 and APK not in s:
        raise SystemExit("native user APK URL not found in main Script.html")
    if APK not in s:
        raise SystemExit("v1.2.5 APK URL missing from main Script.html")
else:
    raise SystemExit("mode must be hosting or main")

path.write_text(s, encoding="utf-8")
print(f"Connected {mode} user install button to v1.2.5 full APK.")
