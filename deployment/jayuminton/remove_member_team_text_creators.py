#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: remove_member_team_text_creators.py <html>')
p = Path(sys.argv[1])
text = p.read_text(encoding='utf-8')

patterns = [
    r'<style\s+id=["\']jayuminton-member-team-status-badges-v1["\'][^>]*>[\s\S]*?</style>\s*',
    r'<style\s+id=["\']jayuminton-member-team-only-badges-v2["\'][^>]*>[\s\S]*?</style>\s*',
]
removed = 0
for pat in patterns:
    text, n = re.subn(pat, '', text, flags=re.I)
    removed += n

# Inspect each script block independently. The former cross-tag regex could
# start at the application's main <script> and continue through a later team
# marker, deleting the entire login/runtime script before that marker.
def remove_marked_script(match: re.Match) -> str:
    global removed
    block = match.group(0)
    if (
        'JAYUMINTON_MEMBER_TEAM_STATUS_BADGES_V1' in block
        or 'JAYUMINTON_MEMBER_TEAM_ONLY_BADGES_V2' in block
    ):
        removed += 1
        return ''
    return block

text = re.sub(
    r'<script(?:\s[^>]*)?>[\s\S]*?</script>\s*',
    remove_marked_script,
    text,
    flags=re.I,
)

# Remove any residual generated team badge containers without touching member cards/state.
text = re.sub(r'<span[^>]*class=["\'][^"\']*jm-member-badges[^"\']*["\'][^>]*>[\s\S]*?</span>\s*', '', text, flags=re.I)

p.write_text(text, encoding='utf-8')
print(f'MEMBER_TEAM_TEXT_CREATORS_REMOVED={removed}')
