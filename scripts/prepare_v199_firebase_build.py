from __future__ import annotations

import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "app" / "src" / "main" / "assets"
MAIN_ACTIVITY = ROOT / "app" / "src" / "main" / "java" / "com" / "jayuminton" / "admin" / "MainActivity.java"
SOURCE_APK = ROOT / "bootstrap" / "jayuminton-v199-source.apk"
LOCAL_RELEASE_APK = ROOT / "releases" / "jayuminton-v199.3-reinstall.apk"
SOURCE_COMMIT = "4c5a79749f3b638dc389f7ddc419b6286fa25ece"
SOURCE_PATH = "releases/jayuminton-v199.3-reinstall.apk"

REQUIRED = (
    "admin-runtime.js",
    "court-orientation.js",
    "frame-repair.js",
    "page-repair.js",
)


def restore_source_apk() -> Path:
    SOURCE_APK.parent.mkdir(parents=True, exist_ok=True)
    if LOCAL_RELEASE_APK.exists() and LOCAL_RELEASE_APK.stat().st_size > 0:
        SOURCE_APK.write_bytes(LOCAL_RELEASE_APK.read_bytes())
        return SOURCE_APK

    result = subprocess.run(
        ["git", "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0 or not result.stdout:
        error = result.stderr.decode("utf-8", errors="replace")
        raise SystemExit(f"could not restore v199 source APK: {error}")
    SOURCE_APK.write_bytes(result.stdout)
    return SOURCE_APK


def extract_runtime() -> None:
    source = restore_source_apk()
    ASSETS.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(source) as archive:
            entries = archive.namelist()
            for required_name in REQUIRED:
                matches = [name for name in entries if Path(name).name == required_name]
                if not matches:
                    raise SystemExit(f"v199 source APK is missing {required_name}")
                preferred = next(
                    (name for name in matches if name == f"assets/{required_name}"),
                    matches[0],
                )
                data = archive.read(preferred)
                if len(data) < 100:
                    raise SystemExit(f"invalid v199 runtime file: {required_name}")
                (ASSETS / required_name).write_bytes(data)
    except zipfile.BadZipFile as exc:
        raise SystemExit(f"v199 source APK is not a valid APK/ZIP: {exc}") from exc


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
    extract_runtime()
    patch_admin_credential_bridge()
    patch_court_credential_reader()
    patch_main_activity()
    verify()
    print("v199 Firebase build prepared")
    for name in REQUIRED:
        path = ASSETS / name
        print(f"{name}: {path.stat().st_size} bytes")
