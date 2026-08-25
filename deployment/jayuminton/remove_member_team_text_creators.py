#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: remove_member_team_text_creators.py <html>')
p = Path(sys.argv[1])
text = p.read_text(encoding='utf-8')

patterns = [
    r'<style\s+id=["\']jayuminton-member-team-status-badges-v1["\'][^>]*>[\s\S]*?</style>\s*',
    r'<script[^>]*>[\s\S]*?JAYUMINTON_MEMBER_TEAM_STATUS_BADGES_V1[\s\S]*?</script>\s*',
    r'<style\s+id=["\']jayuminton-member-team-only-badges-v2["\'][^>]*>[\s\S]*?</style>\s*',
    r'<script[^>]*>[\s\S]*?JAYUMINTON_MEMBER_TEAM_ONLY_BADGES_V2[\s\S]*?</script>\s*',
]
removed = 0
for pat in patterns:
    text, n = re.subn(pat, '', text, flags=re.I)
    removed += n

# Remove any residual generated team badge containers without touching member cards/state.
text = re.sub(r'<span[^>]*class=["\'][^"\']*jm-member-badges[^"\']*["\'][^>]*>[\s\S]*?</span>\s*', '', text, flags=re.I)

p.write_text(text, encoding='utf-8')
print(f'MEMBER_TEAM_TEXT_CREATORS_REMOVED={removed}')
