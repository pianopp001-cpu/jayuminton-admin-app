from __future__ import annotations

import base64
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_B64 = ROOT / "bootstrap" / "v199-assets.zip.b64"
ARCHIVE_ZIP = ROOT / "bootstrap" / "v199-assets.zip"
ASSETS = ROOT / "app" / "src" / "main" / "assets"
MAIN_ACTIVITY = ROOT / "app" / "src" / "main" / "java" / "com" / "jayuminton" / "admin" / "MainActivity.java"

REQUIRED = (
    "admin-runtime.js",
    "court-orientation.js",
    "frame-repair.js",
    "page-repair.js",
)


def decode_and_extract() -> None:
    raw = "".join(ARCHIVE_B64.read_text(encoding="utf-8").split())
    ARCHIVE_ZIP.write_bytes(base64.b64decode(raw, validate=True))
    ASSETS.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARCHIVE_ZIP) as archive:
        for name in REQUIRED:
            data = archive.read(name)
            (ASSETS / name).write_bytes(data)


def patch_admin_credential_bridge() -> None:
    path = ASSETS / "admin-runtime.js"
    text = path.read_text(encoding="utf-8")
    marker = "  ADMIN_PIN_VALUE = credential;"
    addition = """  ADMIN_PIN_VALUE = credential;
  try {
    window.__JAYUMINTON_ADMIN_CREDENTIAL__ = String(credential || '');
    localStorage.setItem('jayuminton_admin_session_v1', String(credential || ''));
    sessionStorage.setItem('jayuminton_admin_session_v1', String(credential || ''));
  } catch (ignored) {}
"""
    if "__JAYUMINTON_ADMIN_CREDENTIAL__" not in text:
        if marker not in text:
            raise SystemExit("admin credential assignment was not found")
        text = text.replace(marker, addition, 1)
    path.write_text(text, encoding="utf-8")


def patch_court_credential_reader() -> None:
    path = ASSETS / "court-orientation.js"
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"  function administratorCredential\(\) \{.*?\n  \}\n",
        re.DOTALL,
    )
    replacement = """  function administratorCredential() {
    try {
      if (window.__JAYUMINTON_ADMIN_CREDENTIAL__) {
        return String(window.__JAYUMINTON_ADMIN_CREDENTIAL__);
      }
    } catch (ignored) {}

    try {
      if (typeof ADMIN_PIN_VALUE !== 'undefined' && ADMIN_PIN_VALUE) {
        return String(ADMIN_PIN_VALUE);
      }
    } catch (ignored) {}

    var keys = [
      'jayuminton_admin_session_v1',
      'adminSession',
      'adminPin',
      'adminPIN'
    ];
    for (var index = 0; index < keys.length; index += 1) {
      try {
        var stored = localStorage.getItem(keys[index]);
        if (stored) return String(stored);
      } catch (ignored) {}
      try {
        var sessionStored = sessionStorage.getItem(keys[index]);
        if (sessionStored) return String(sessionStored);
      } catch (ignored) {}
    }

    var input = document.getElementById('adminPinInput');
    return input ? String(input.value || '') : '';
  }
"""
    next_text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise SystemExit("administratorCredential function was not patched")
    path.write_text(next_text, encoding="utf-8")


def patch_main_activity() -> None:
    text = MAIN_ACTIVITY.read_text(encoding="utf-8")
    call = "                V199RuntimeBridge.install(MainActivity.this, view);\n"
    if call not in text:
        marker = "                view.evaluateJavascript(PUSH_HOOK_SCRIPT, null);"
        if marker not in text:
            raise SystemExit("MainActivity page-finished marker was not found")
        text = text.replace(marker, call + marker, 1)
    MAIN_ACTIVITY.write_text(text, encoding="utf-8")


def verify() -> None:
    for name in REQUIRED:
        path = ASSETS / name
        if not path.exists() or path.stat().st_size < 100:
            raise SystemExit(f"invalid v199 asset: {name}")
    admin = (ASSETS / "admin-runtime.js").read_text(encoding="utf-8")
    court = (ASSETS / "court-orientation.js").read_text(encoding="utf-8")
    main = MAIN_ACTIVITY.read_text(encoding="utf-8")
    if "__JAYUMINTON_ADMIN_CREDENTIAL__" not in admin:
        raise SystemExit("admin credential bridge is missing")
    if "jayuminton_admin_session_v1" not in court:
        raise SystemExit("court PIN fallback is missing")
    if "V199RuntimeBridge.install" not in main:
        raise SystemExit("v199 runtime install call is missing")


if __name__ == "__main__":
    decode_and_extract()
    patch_admin_credential_bridge()
    patch_court_credential_reader()
    patch_main_activity()
    verify()
    print("v199 Firebase build prepared")
    for name in REQUIRED:
        path = ASSETS / name
        print(f"{name}: {path.stat().st_size} bytes")
