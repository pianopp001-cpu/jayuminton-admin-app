#!/usr/bin/env python3
"""Normalize admin observer self-write variants before the Cloudflare WebView bridge.
Cloudflare/APK build helper only; never deploys or calls Apps Script.
"""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
path = root / 'Script.html'
s = path.read_text(encoding='utf-8')
original = s

# Normalize historical observer writes only when the real executable statement
# exists. Never append compatibility JavaScript/comment tokens to Script.html:
# some bundled snapshots render Script.html as plain body content, which would
# expose those tokens to users on the login screen.
patterns = [
    (r"^[ \t]*(?:if\s*\(\s*buttons\[0\]\.textContent\s*!==?\s*'실행취소'\s*\)\s*)?buttons\[0\]\.textContent\s*=\s*'실행취소';[ \t]*$",
     "      buttons[0].textContent='실행취소';"),
    (r"^[ \t]*if\s*\(\s*!buttons\[1\]\.disabled(?:\s*&&\s*buttons\[1\]\.textContent\s*!==?\s*'새로고침')?\s*\)\s*buttons\[1\]\.textContent\s*=\s*'새로고침';[ \t]*$",
     "      if(!buttons[1].disabled)buttons[1].textContent='새로고침';"),
    (r"^[ \t]*(?:if\s*\(\s*buttons\[2\]\.textContent\s*!==?\s*'자동배정'\s*\)\s*)?buttons\[2\]\.textContent\s*=\s*'자동배정';[ \t]*$",
     "      buttons[2].textContent='자동배정';"),
]
for pattern, canonical in patterns:
    s, _ = re.subn(pattern, canonical, s, count=1, flags=re.M)

# Defensive cleanup for APKs/snapshots produced by the previous broken helper.
# Remove only the exact compatibility lines it injected.
s = re.sub(r"^// JAYUMINTON_BRIDGE_COMPAT_TOKEN .*\n?", "", s, flags=re.M)

path.write_text(s, encoding='utf-8')
print('ADMIN_WEBVIEW_OBSERVER_COMPAT_OK' if s != original else 'ADMIN_WEBVIEW_OBSERVER_COMPAT_ALREADY_CANONICAL')
