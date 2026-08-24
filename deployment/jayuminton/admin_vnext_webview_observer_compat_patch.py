#!/usr/bin/env python3
"""Normalize admin observer self-write variants before the Cloudflare WebView bridge.
Cloudflare/APK build helper only; never deploys or calls Apps Script.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
path = root / 'Script.html'
s = path.read_text(encoding='utf-8')
original = s

# inject_cloudflare_v6_frontend_bridge.py applies the final guarded forms.
# Earlier admin patches may already have guarded these writes or changed spacing;
# collapse those variants back to the bridge's canonical input form first.
variants = {
    "if(buttons[0].textContent!=='실행취소')buttons[0].textContent='실행취소';": "buttons[0].textContent='실행취소';",
    "if (buttons[0].textContent !== '실행취소') buttons[0].textContent = '실행취소';": "buttons[0].textContent='실행취소';",
    "if(!buttons[1].disabled&&buttons[1].textContent!=='새로고침')buttons[1].textContent='새로고침';": "if(!buttons[1].disabled)buttons[1].textContent='새로고침';",
    "if (!buttons[1].disabled && buttons[1].textContent !== '새로고침') buttons[1].textContent = '새로고침';": "if(!buttons[1].disabled)buttons[1].textContent='새로고침';",
    "if(buttons[2].textContent!=='자동배정')buttons[2].textContent='자동배정';": "buttons[2].textContent='자동배정';",
    "if (buttons[2].textContent !== '자동배정') buttons[2].textContent = '자동배정';": "buttons[2].textContent='자동배정';",
}
for old, new in variants.items():
    s = s.replace(old, new)

# Normalize harmless whitespace differences for the three toolbar writes.
s = s.replace("buttons[0].textContent = '실행취소';", "buttons[0].textContent='실행취소';")
s = s.replace("if (!buttons[1].disabled) buttons[1].textContent = '새로고침';", "if(!buttons[1].disabled)buttons[1].textContent='새로고침';")
s = s.replace("buttons[2].textContent = '자동배정';", "buttons[2].textContent='자동배정';")

path.write_text(s, encoding='utf-8')
print('ADMIN_WEBVIEW_OBSERVER_COMPAT_OK' if s != original else 'ADMIN_WEBVIEW_OBSERVER_COMPAT_ALREADY_CANONICAL')
