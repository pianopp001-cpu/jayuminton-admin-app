#!/usr/bin/env python3
"""Color-separate administrator-owned grade/experience/memo from member-owned memo in admin APK."""

from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/assets/admin/index.html")
text = path.read_text(encoding="utf-8")
MARKER = "JAYUMINTON_ADMIN_MEMBER_INFO_COLOR_SPLIT_V20917"

if MARKER in text:
    print("ADMIN_V20917_MEMBER_INFO_COLOR_SPLIT_ALREADY_OK")
    raise SystemExit(0)

addon = r'''
<style id="jayuminton-admin-member-info-color-split-v20917">
/* JAYUMINTON_ADMIN_MEMBER_INFO_COLOR_SPLIT_V20917
   관리자 입력 급수·구력·관리자 메모 = blue.
   사용자 직접 입력 추가 메모 = purple/magenta. */
#adminApp [data-member-id]>.member-info-detail,
#adminApp [data-member-id] .member-info-detail,
#adminApp [data-member-id]>.member-public-memo,
#adminApp [data-member-id] .member-public-memo,
#adminApp [data-member-id]>.jm-public-memo,
#adminApp [data-member-id] .jm-public-memo{
  color:#2563eb!important;
  opacity:1!important;
}
#adminApp [data-member-id]>.jm-member-owned-memo,
#adminApp [data-member-id] .jm-member-owned-memo{
  color:#c026d3!important;
  opacity:1!important;
}
</style>
'''

close = text.lower().rfind("</body>")
if close < 0:
    raise SystemExit("admin body close not found")
text = text[:close] + addon + "\n" + text[close:]

for required in (MARKER, "#2563eb", "#c026d3", "member-info-detail", "member-public-memo", "jm-member-owned-memo"):
    if required not in text:
        raise SystemExit("v209.17 output missing: " + required)

path.write_text(text, encoding="utf-8")
print("ADMIN_V20917_MEMBER_INFO_COLOR_SPLIT_OK")
