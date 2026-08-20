#!/usr/bin/env python3
"""Make admin-vNext member badges clean at the source before Cloudflare assembly."""
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path('source-snapshot/current-main').resolve()
script = root / 'Script.html'
if not script.exists():
    raise SystemExit(f'Script.html not found: {script}')

text = script.read_text(encoding='utf-8')
legacy = '<span class="member-vnext-badge new-badge" aria-label="신규 회원">NEW <small>신규</small></span>'
clean = '<span class="member-vnext-badge new-badge" aria-label="신규 회원"><small>신규</small></span>'

if legacy in text:
    text = text.replace(legacy, clean)

if 'NEW <small>신규</small>' in text:
    raise SystemExit('legacy NEW badge renderer still present after cleanup')
if clean not in text:
    raise SystemExit('clean Korean 신규 badge renderer missing')
if '🎁 찬조' not in text:
    raise SystemExit('sponsor badge renderer missing')

script.write_text(text, encoding='utf-8')
print('ADMIN_VNEXT_BADGE_CLEANUP_OK')
