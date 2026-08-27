#!/usr/bin/env python3
"""Restore essential member-page addons without changing its login/runtime."""

from pathlib import Path
import sys

from patch_member_user_requirements_v1 import (
    ADDON,
    AUTO_SYNC_ADDON,
    AUTO_SYNC_MARKER,
    MARKER,
    MEMBER_MESSAGE_ADDON,
    MEMBER_MESSAGE_MARKER,
    NATIVE_SYNC_ADDON,
    NATIVE_SYNC_MARKER,
)


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    closing = "</body>"
    for required in (
        "function initialize()",
        "function refreshMemberState()",
        "function server(name, args)",
        "function memberLogin()",
        "initialize();",
        closing,
    ):
        if required not in text:
            raise SystemExit(f"member login runtime missing before addon recovery: {required}")

    for marker, addon in (
        (MARKER, ADDON),
        (NATIVE_SYNC_MARKER, NATIVE_SYNC_ADDON),
        (AUTO_SYNC_MARKER, AUTO_SYNC_ADDON),
        (MEMBER_MESSAGE_MARKER, MEMBER_MESSAGE_ADDON),
    ):
        if marker not in text:
            text = text.replace(closing, addon + "\n" + closing, 1)

    for required in (
        MARKER,
        NATIVE_SYNC_MARKER,
        AUTO_SYNC_MARKER,
        MEMBER_MESSAGE_MARKER,
        "window.confirmJmDirectMessage=function()",
        "vibrationTimer=setInterval(vibrate,14500)",
        "setInterval(pollRevision, 1800)",
    ):
        if required not in text:
            raise SystemExit(f"member recovery addon missing: {required}")

    path.write_text(text, encoding="utf-8")
    print("MEMBER_LOGIN_RECOVERY_ADDONS_OK")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_member_login_recovery_addons.py INDEX_HTML")
    patch(Path(sys.argv[1]))
