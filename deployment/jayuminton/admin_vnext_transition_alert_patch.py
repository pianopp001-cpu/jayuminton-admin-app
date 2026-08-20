#!/usr/bin/env python3
"""Admin-only Script patch: route court/wait transition notices through the native alert bridge.

The final Cloudflare v19 contract exposes window.__JAYUMINTON_TRANSITION_ALERT__.
Until that final script is present, the patched function safely falls back to
window.alert, so the isolated source remains syntactically/runtimely valid.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
path = root / 'Script.html'
source = path.read_text(encoding='utf-8')

name = 'function showPendingAlertsIfReady'
start = source.find(name)
if start < 0:
    raise SystemExit('showPendingAlertsIfReady function missing')
brace = source.find('{', start)
if brace < 0:
    raise SystemExit('showPendingAlertsIfReady opening brace missing')

def matching_brace(text, pos):
    depth = 0
    quote = ''
    escape = False
    for i in range(pos, len(text)):
        ch = text[i]
        if quote:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == quote:
                quote = ''
            continue
        if ch in ("'", '"', '`'):
            quote = ch
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i
    return -1

end = matching_brace(source, brace)
if end < 0:
    raise SystemExit('showPendingAlertsIfReady closing brace missing')
block = source[start:end+1]

if '__jmTransitionAlert' not in block:
    block = block[:block.find('{')+1] + "\n  const __jmTransitionAlert = (typeof window.__JAYUMINTON_TRANSITION_ALERT__ === 'function') ? window.__JAYUMINTON_TRANSITION_ALERT__ : function(value){ window.alert(value); };" + block[block.find('{')+1:]

# Only notification alerts inside this transition-event function are replaced.
# Validation/error alerts elsewhere retain the ordinary browser alert behavior.
block = block.replace('alert(', '__jmTransitionAlert(')
# Do not rewrite the fallback we just injected.
block = block.replace('window.__jmTransitionAlert(', 'window.alert(')
if '__jmTransitionAlert(' not in block:
    raise SystemExit('transition alert call was not wired')

source = source[:start] + block + source[end+1:]
if '__JAYUMINTON_ADMIN_TRANSITION_ALERT_BRIDGE_V1__' not in source:
    source += "\n<script>window.__JAYUMINTON_ADMIN_TRANSITION_ALERT_BRIDGE_V1__=true;</script>\n"

path.write_text(source, encoding='utf-8')
print('ADMIN_TRANSITION_ALERT_BRIDGE_OK')
