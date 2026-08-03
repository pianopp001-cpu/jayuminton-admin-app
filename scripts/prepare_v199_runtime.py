from __future__ import annotations

import base64
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "bootstrap"
ASSETS = ROOT / "app" / "src" / "main" / "assets"
ARCHIVE_B64 = BOOTSTRAP / "v199-assets.zip.b64"
ARCHIVE_ZIP = BOOTSTRAP / "v199-assets.zip"

REQUIRED = (
    "admin-runtime.js",
    "court-orientation.js",
    "frame-repair.js",
    "page-repair.js",
)


def rebuild_base64() -> None:
    parts = sorted(BOOTSTRAP.glob("v199-assets.part-*.txt"))
    if not parts:
        raise SystemExit("No v199 runtime chunk files were found")
    ARCHIVE_B64.write_text(
        "".join(part.read_text(encoding="utf-8").strip() for part in parts),
        encoding="utf-8",
    )


def decode_archive() -> None:
    payload = base64.b64decode(ARCHIVE_B64.read_text(encoding="utf-8"), validate=True)
    ARCHIVE_ZIP.write_bytes(payload)


def extract_assets() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARCHIVE_ZIP) as archive:
        for name in REQUIRED:
            try:
                source = archive.open(name)
            except KeyError as exc:
                raise SystemExit(f"Missing runtime asset: {name}") from exc
            with source, (ASSETS / name).open("wb") as target:
                shutil.copyfileobj(source, target)


def patch_member_credential() -> None:
    path = ASSETS / "court-orientation.js"
    text = path.read_text(encoding="utf-8")

    old = """  function administratorCredential() {
    try {
      if (typeof ADMIN_PIN_VALUE !== 'undefined' && ADMIN_PIN_VALUE) {
        return String(ADMIN_PIN_VALUE);
      }
    } catch (ignored) {}

    return '';
  }
"""

    new = """  function administratorCredential() {
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

    return '';
  }
"""

    if old in text:
        text = text.replace(old, new, 1)
    elif "jayuminton_admin_session_v1" not in text:
        raise SystemExit("administratorCredential patch target was not found")

    path.write_text(text, encoding="utf-8")


def verify() -> None:
    for name in REQUIRED:
        path = ASSETS / name
        if not path.is_file() or path.stat().st_size == 0:
            raise SystemExit(f"Invalid runtime asset: {name}")

    court = (ASSETS / "court-orientation.js").read_text(encoding="utf-8")
    if "jayuminton_admin_session_v1" not in court:
        raise SystemExit("PIN/session fallback patch is missing")

    frame = (ASSETS / "frame-repair.js").read_text(encoding="utf-8")
    if "__JAYUMINTON_ADMIN_RUNTIME_JSON__" not in frame:
        raise SystemExit("frame-repair runtime placeholder is missing")


if __name__ == "__main__":
    rebuild_base64()
    decode_archive()
    extract_assets()
    patch_member_credential()
    verify()
    print("Prepared v199 runtime assets:")
    for asset_name in REQUIRED:
        asset = ASSETS / asset_name
        print(f"- {asset_name}: {asset.stat().st_size} bytes")
