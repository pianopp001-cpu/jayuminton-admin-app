#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_member_single_popup_cleanup_v7.py INDEX_HTML')

path = Path(sys.argv[1])
text = path.read_text(encoding='utf-8')

# The old self-profile addon created a second full-screen modal. Remove that
# whole addon, including its modal markup and old handlers. The MD7 patch owns
# the single action popup and inline memo editor.
text, removed_profile = re.subn(
    r'\n?<style id="jayuminton-member-self-profile-edit-v1">[\s\S]*?</script>\s*',
    '\n', text, count=1, flags=re.I,
)
text, removed_memo_override = re.subn(
    r'\n?<script>\s*/\* JAYUMINTON_MEMBER_SELF_MEMO_ONLY_V2 \*/[\s\S]*?</script>\s*',
    '\n', text, count=1, flags=re.I,
)

if 'JAYUMINTON_MD7_SINGLE_ACTION_POPUP_V1' not in text:
    raise SystemExit('MD7 single popup patch missing before cleanup')
if '어디로 이동할까요?' not in text:
    raise SystemExit('single popup title missing')
if '>내정보 입력</button>' not in text:
    raise SystemExit('single popup self-info button missing')
if '<div id="jmSelfProfileModal"' in text:
    raise SystemExit('legacy second self profile modal still present')

path.write_text(text, encoding='utf-8')
print(f'MD7 legacy profile cleanup applied profile={removed_profile} memoOverride={removed_memo_override}')
