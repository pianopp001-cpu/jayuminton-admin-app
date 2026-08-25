#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_member_self_longpress_v6.py <html-file>")

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

# User request: keep the original self-card long-press action popup only.
# Remove every later memo/profile addon that introduced an additional window
# or a card memo editor. Team-card rendering is owned by separate patches and
# is deliberately untouched here.
patterns = (
    r'\n?<style id="jayuminton-md6-self-longpress-v1">[\s\S]*?</script>\s*',
    r'\n?<style id="jayuminton-md6-self-longpress-v2">[\s\S]*?</script>\s*',
    r'\n?<style id="jayuminton-md7-single-action-popup">[\s\S]*?</script>\s*',
    r'\n?<style id="jayuminton-member-self-profile-edit-v1">[\s\S]*?</script>\s*',
    r'\n?<script>\s*/\* JAYUMINTON_MEMBER_SELF_MEMO_ONLY_V2 \*/[\s\S]*?</script>\s*',
)
removed = 0
for pattern in patterns:
    text, count = re.subn(pattern, '\n', text, count=1, flags=re.I)
    removed += count

# Defensive cleanup for static leftovers from the later injected popup.
text = re.sub(r'\n?<div id="jmSelfProfileModal"[\s\S]*?</div>\s*</div>\s*', '\n', text, count=1, flags=re.I)

for forbidden in (
    'JAYUMINTON_MD7_SINGLE_ACTION_POPUP_V1',
    'jayuminton-md7-single-action-popup',
    'jayuminton-member-self-profile-edit-v1',
    'JAYUMINTON_MEMBER_SELF_MEMO_ONLY_V2',
):
    if forbidden in text:
        raise SystemExit('memo/profile addon still present: ' + forbidden)

path.write_text(text, encoding="utf-8")
print(f"USER_SELF_MEMO_UI_REMOVED addons={removed}; original long-press UI preserved")
