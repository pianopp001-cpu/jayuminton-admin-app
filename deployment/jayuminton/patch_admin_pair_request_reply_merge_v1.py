#!/usr/bin/env python3
"""Replace the already-baked __JAYUMINTON_ADMIN_MEMBER_REPLIES_V1__ widget
script (verified byte-identical, minus a trailing blank line, to
deployment/jayuminton/admin_member_replies_v1_pre_pair_merge_reference.js --
a frozen copy kept solely so this patch has a drift-safe anchor) with the
current, merged deployment/jayuminton/admin_member_replies_v1.js.

The merge does two things the user asked for, in order:
  1. "관리자에서 회원답장이라는 말보다는 회원쪽지 라고 바꿔줘" -- every
     user-visible "회원 답장" label becomes "회원쪽지" (button, panel
     title, popup title, empty state, delete-confirm). Internal ids,
     classes, function names and RPC names are untouched.
  2. "관리자쪽에는 요청메모도 동시에 들어오게 하자" / "관리자쪽에 알람진동
     까지는 올필요 없고. 메모에 들어오면 돼." / user picked "기존
     회원쪽지(구 회원답장) 함에 통합" -- pending 짝요청(pair-play request)
     items with status 'accepted_awaiting_seat' now render as extra cards
     inside this same panel, with a green "완료" button (calls the
     existing dismissPairNotice RPC) instead of the reply cards' "삭제".

This operates on the already-built admin HTML (same convention as the other
admin_*_patch.py scripts invoked from build-admin-native-session-fix.yml),
not on Java/Android source.
"""
from pathlib import Path
import sys

html_path = Path(sys.argv[1])
html = html_path.read_text(encoding='utf-8')

old_block = Path('deployment/jayuminton/admin_member_replies_v1_pre_pair_merge_reference.js').read_text(encoding='utf-8')
new_block = Path('deployment/jayuminton/admin_member_replies_v1.js').read_text(encoding='utf-8')

MARKER = 'JAYUMINTON_ADMIN_PAIR_REQUEST_REPLY_MERGE_V1'

if MARKER in html:
    print('ADMIN_PAIR_REQUEST_REPLY_MERGE_V1_OK (already applied)')
    sys.exit(0)

if old_block not in html:
    raise SystemExit('pre-merge admin_member_replies_v1 block not found in HTML (baked content drifted)')

html = html.replace(old_block, new_block, 1)

required = (
    "id='jmAdminReplyButton';b.innerHTML='회원쪽지",
    '<strong>회원쪽지</strong>',
    "class=\"jm-admin-reply-popup-title\">회원쪽지 도착",
    'function flattenPairRequests(',
    'jm-admin-reply-complete',
    "server('dismissPairNotice',[null,requestId])",
)
for anchor in required:
    if anchor not in html:
        raise SystemExit('admin pair-request/reply merge patch failed, missing: ' + anchor)

stale = (
    "b.innerHTML='회원 답장",
    '<strong>회원 답장</strong>',
    '회원 답장 도착',
    '아직 받은 답장이 없습니다.',
    '이 답장을 삭제할까요?',
)
for anchor in stale:
    if anchor in html:
        raise SystemExit('stale pre-rename 회원 답장 label still present after merge patch: ' + anchor)

path_marker_comment = '/* ' + MARKER + ' */\n'
if path_marker_comment not in html:
    html = html.replace(new_block, path_marker_comment + new_block, 1)

if MARKER not in html:
    raise SystemExit('post-replace marker check failed')

html_path.write_text(html, encoding='utf-8')
print('ADMIN_PAIR_REQUEST_REPLY_MERGE_V1_OK')
