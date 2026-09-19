#!/usr/bin/env python3
"""Color-separate administrator-owned member info from member-owned memo."""

from pathlib import Path
import sys

MARKER = "JAYUMINTON_MEMBER_INFO_COLOR_SPLIT_V1"

ADDON = r'''
<style id="jayuminton-member-info-color-split-v1">
/* JAYUMINTON_MEMBER_INFO_COLOR_SPLIT_V1
   Administrator-owned grade/experience/admin memo = blue.
   Member-owned appended memo = purple/magenta. */
#memberApp [data-member-id]>.member-info-detail,
#memberApp [data-member-id] .member-info-detail,
#memberApp [data-member-id]>.member-public-memo,
#memberApp [data-member-id] .member-public-memo{
  color:#2563eb!important;
  opacity:1!important;
}
#memberApp [data-member-id]>.jm-user-owned-memo,
#memberApp [data-member-id] .jm-user-owned-memo{
  color:#c026d3!important;
  opacity:1!important;
}
</style>
'''

def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print("MEMBER_INFO_COLOR_SPLIT_ALREADY_OK")
        return
    close = text.lower().rfind("</body>")
    if close < 0:
        raise SystemExit("body close not found")
    text = text[:close] + ADDON + "\n" + text[close:]
    for required in (MARKER, "#2563eb", "#c026d3", "member-info-detail", "member-public-memo", "jm-user-owned-memo"):
        if required not in text:
            raise SystemExit("member info color split missing: " + required)
    path.write_text(text, encoding="utf-8")
    print("MEMBER_INFO_COLOR_SPLIT_OK")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_member_info_color_split_v1.py INDEX_HTML")
    patch(Path(sys.argv[1]))
