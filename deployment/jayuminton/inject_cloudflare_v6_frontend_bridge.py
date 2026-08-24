#!/usr/bin/env python3
"""Replace legacy JSONP/GAS bridges in an already-rendered admin or member HTML file."""
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: inject_cloudflare_v6_frontend_bridge.py HTML_FILE')
path = Path(sys.argv[1]); html = path.read_text(encoding='utf-8')
bridge = (Path(__file__).with_name('cloudflare_v6_frontend_bridge.js')).read_text(encoding='utf-8')

# The v200.8 UI has observers that unconditionally rewrite nodes inside their
# own observation roots. Android WebView can then remain in a self-sustaining
# microtask/render loop before onPageFinished. Guard every self-write so the
# latest UI remains intact without starving the native page lifecycle.
replacements = {
    "  el.textContent = '전체 ' + total + ' · 남 ' + male + ' · 여 ' + female;":
        "  const nextText = '전체 ' + total + ' · 남 ' + male + ' · 여 ' + female;\n"
        "  if (el.textContent !== nextText) el.textContent = nextText;",
    "    label.textContent = member && isAdminNewMember(member) ? String(member.name || '') : '';":
        "    var nextLabel = member && isAdminNewMember(member) ? String(member.name || '') : '';\n"
        "    if (label.textContent !== nextLabel) label.textContent = nextLabel;",
    "      more.textContent = expanded ? '접기' : '+' + hiddenCount + '명';":
        "      var nextMoreText = expanded ? '접기' : '+' + hiddenCount + '명';\n"
        "      if (more.textContent !== nextMoreText) more.textContent = nextMoreText;",
    "      buttons[0].textContent='실행취소';":
        "      if(buttons[0].textContent!=='실행취소')buttons[0].textContent='실행취소';",
    "      if(!buttons[1].disabled)buttons[1].textContent='새로고침';":
        "      if(!buttons[1].disabled&&buttons[1].textContent!=='새로고침')buttons[1].textContent='새로고침';",
    "      buttons[2].textContent='자동배정';":
        "      if(buttons[2].textContent!=='자동배정')buttons[2].textContent='자동배정';",
}
for old, new in replacements.items():
    count = html.count(old)
    if count != 1:
        raise SystemExit(f'WebView observer guard target mismatch ({count}): {old[:72]}')
    html = html.replace(old, new, 1)

html = re.sub(r'<script\b[^>]*id=["\']jayuminton-admin-cloudflare-rpc["\'][^>]*>.*?</script>\s*', '', html, flags=re.S | re.I)
html = re.sub(r'<script\b[^>]*id=["\']jayumintonCloudflareRpcV6["\'][^>]*>.*?</script>\s*', '', html, flags=re.S | re.I)
comment = '/* jayuminton-v3-cloudflare-member-preview */'
if comment in html:
    pos = html.index(comment); start = html.rfind('<script', 0, pos); end = html.find('</script>', pos)
    if start < 0 or end < 0: raise SystemExit('member legacy bridge boundary missing')
    html = html[:start] + html[end + len('</script>'):]

marker = re.search(r'<script>\s*const IS_ADMIN\s*=\s*(?:true|false);\s*</script>', html)
if not marker: raise SystemExit('IS_ADMIN marker missing')
injected = marker.group(0) + '\n<script id="jayumintonCloudflareRpcV6">\n' + bridge + '\n</script>'
html = html[:marker.start()] + injected + html[marker.end():]

if html.count('__JAYUMINTON_CLOUDFLARE_RPC_V6__') != 1: raise SystemExit('v6 bridge count mismatch')
if 'script.google.com/macros/s/' in html: raise SystemExit('direct GAS URL remains')
if "if (el.textContent !== nextText) el.textContent = nextText;" not in html:
    raise SystemExit('member count observer guard missing')
path.write_text(html, encoding='utf-8')
print('CLOUDFLARE_V6_FRONTEND_BRIDGE_OK')
