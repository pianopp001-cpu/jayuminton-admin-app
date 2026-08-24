#!/usr/bin/env python3
"""Inject the Cloudflare RPC bridge into rendered Jayuminton HTML.
Cloudflare-only build helper. It intentionally does not rewrite admin member fields.
"""
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: inject_cloudflare_v6_frontend_bridge.py HTML_FILE')

path = Path(sys.argv[1])
html = path.read_text(encoding='utf-8')
bridge = (Path(__file__).with_name('cloudflare_v6_frontend_bridge.js')).read_text(encoding='utf-8')

# Guard known observer self-writes when present. These are compatibility fixes,
# not build requirements: newer snapshots may already contain guarded forms.
replacements = [
    (
        "  el.textContent = '전체 ' + total + ' · 남 ' + male + ' · 여 ' + female;",
        "  const nextText = '전체 ' + total + ' · 남 ' + male + ' · 여 ' + female;\n  if (el.textContent !== nextText) el.textContent = nextText;",
    ),
    (
        "    label.textContent = member && isAdminNewMember(member) ? String(member.name || '') : '';",
        "    var nextLabel = member && isAdminNewMember(member) ? String(member.name || '') : '';\n    if (label.textContent !== nextLabel) label.textContent = nextLabel;",
    ),
    (
        "      more.textContent = expanded ? '접기' : '+' + hiddenCount + '명';",
        "      var nextMoreText = expanded ? '접기' : '+' + hiddenCount + '명';\n      if (more.textContent !== nextMoreText) more.textContent = nextMoreText;",
    ),
    (
        "      buttons[0].textContent='실행취소';",
        "      if(buttons[0].textContent!=='실행취소')buttons[0].textContent='실행취소';",
    ),
    (
        "      if(!buttons[1].disabled)buttons[1].textContent='새로고침';",
        "      if(!buttons[1].disabled&&buttons[1].textContent!=='새로고침')buttons[1].textContent='새로고침';",
    ),
    (
        "      buttons[2].textContent='자동배정';",
        "      if(buttons[2].textContent!=='자동배정')buttons[2].textContent='자동배정';",
    ),
]
for old, new in replacements:
    if old in html:
        html = html.replace(old, new, 1)

# Do not consolidate/rename mdPublicMemo/mdIsNew/mdIsSponsor here. The current
# admin patch stack owns those fields and the APK contract verifies them.

# Avoid duplicate installation when rebuilding an already-rendered file.
if '__JAYUMINTON_CLOUDFLARE_RPC_V6__' not in html:
    if '</body>' not in html:
        raise SystemExit('rendered HTML has no </body> anchor')
    html = html.replace('</body>', '<script>\n' + bridge + '\n</script>\n</body>', 1)

# Cloudflare-only contract: a rendered APK page must not contain a live GAS URL.
if re.search(r'https?://script\.google\.com', html, flags=re.I):
    raise SystemExit('GAS URL survived in rendered Cloudflare HTML')

path.write_text(html, encoding='utf-8')
print('CLOUDFLARE_V6_FRONTEND_BRIDGE_OK')
