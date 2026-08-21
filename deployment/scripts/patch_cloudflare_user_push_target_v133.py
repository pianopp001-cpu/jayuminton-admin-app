#!/usr/bin/env python3
from pathlib import Path
import sys

# CI retrigger: 2026-08-21 isolated v1.3.3 recovery

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_cloudflare_user_push_target_v133.py <worker.js>')

p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')

# v1.3.2 native app intentionally rejects assignment events without targetMemberId.
# Keep memberId for compatibility, but add the strict native targeting field.
needle = "type: String(event.type), assignmentId: String(event.assignmentId), memberId: String(member.id), memberName: String(member.name || ''),"
replacement = "type: String(event.type), assignmentId: String(event.assignmentId), targetMemberId: String(member.id), memberId: String(member.id), memberName: String(member.name || ''),"

if replacement in s:
    print('Cloudflare targetMemberId contract already present')
    raise SystemExit(0)
if s.count(needle) != 1:
    raise SystemExit('Cloudflare sendOne data anchor missing or ambiguous')

s = s.replace(needle, replacement, 1)
for required in (
    'targetMemberId: String(member.id)',
    'memberId: String(member.id)',
    "['wait1_ready', 'court_assignment']",
    "restricted_package_name = 'com.jayuminton.user'",
):
    if required not in s:
        raise SystemExit('missing Cloudflare push contract: ' + required)

p.write_text(s, encoding='utf-8')
print('Patched Cloudflare FCM data with targetMemberId; memberId and current-member routing preserved.')
