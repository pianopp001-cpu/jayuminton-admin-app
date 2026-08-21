#!/usr/bin/env python3
"""Patch a pulled relay Code.js so FCM data contains the strict user-app target member id.
This script only edits the local file path passed to it; it does not push or deploy Apps Script.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_relay_target_member_id.py <relay-Code.js>')

p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')
marker = 'JAYUMINTON_TARGET_MEMBER_ID_CONTRACT_V1'

if marker in s and 'targetMemberId: String(member.id)' in s:
    print('targetMemberId contract already present')
    raise SystemExit(0)

needle = """  const data = {\n    type: event.type,\n    assignmentId: event.assignmentId,\n    memberId: member.id,\n    memberName: member.name,"""
replacement = """  const data = {\n    /* JAYUMINTON_TARGET_MEMBER_ID_CONTRACT_V1\n     * Native user app accepts an assignment only when targetMemberId exactly\n     * matches the member selected as 'me'. Keep legacy memberId too.\n     */\n    type: event.type,\n    assignmentId: event.assignmentId,\n    targetMemberId: String(member.id),\n    memberId: member.id,\n    memberName: member.name,"""

if s.count(needle) != 1:
    raise SystemExit('exact makeWebFcmRequest_ data block not found once')

s = s.replace(needle, replacement, 1)

required = [
    marker,
    'targetMemberId: String(member.id)',
    'memberId: member.id',
    'makeWebFcmRequest_',
]
for item in required:
    if item not in s:
        raise SystemExit('missing required target-member contract: ' + item)

p.write_text(s, encoding='utf-8')
print('Patched relay FCM data: targetMemberId now mirrors the matched member.id; no tokens or APK changed.')
