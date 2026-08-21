#!/usr/bin/env python3
"""Read-only relay source inspector. Never writes to Apps Script or deploys anything."""
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: inspect_relay_assignment_target.py <relay-Code.js>')

src = Path(sys.argv[1]).read_text(encoding='utf-8')


def extract_function(name):
    m = re.search(r'function\s+' + re.escape(name) + r'\s*\([^)]*\)\s*\{', src)
    if not m:
        return ''
    start = m.start()
    brace = src.find('{', m.start())
    depth = 0
    quote = None
    esc = False
    for i in range(brace, len(src)):
        c = src[i]
        if quote:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == quote:
                quote = None
            continue
        if c in "'\"`":
            quote = c
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return src[start:i + 1]
    return ''

names = [
    'sendAssignmentEvent_',
    'sendFcmMessage_',
    'sendWebPush_',
    'loadWebPushTokens_',
    'registerWebToken_',
    'cleanEvent_',
]

print('READ_ONLY_RELAY_ASSIGNMENT_INSPECTION_V1')
print('has_targetMemberId=' + str('targetMemberId' in src))
print('has_memberId=' + str('memberId' in src))
print('has_wait1_ready=' + str('wait1_ready' in src))
print('has_court_assignment=' + str('court_assignment' in src))

for name in names:
    fn = extract_function(name)
    print('\n=== ' + name + ' ===')
    if not fn:
        print('NOT_FOUND')
        continue
    # redact obvious secrets/tokens while preserving control flow and field names
    fn = re.sub(r"(['\"])(?:ya29\.|AIza|eyJ)[^'\"]+\1", "'__REDACTED__'", fn)
    print(fn)

assignment = extract_function('sendAssignmentEvent_')
if assignment:
    target_refs = len(re.findall(r'targetMemberId', assignment))
    member_refs = len(re.findall(r'\.memberId\b|\bmemberId\b', assignment))
    token_refs = len(re.findall(r'\.token\b|\btoken\b', assignment))
    print('\nSUMMARY')
    print('sendAssignmentEvent_targetMemberId_refs=' + str(target_refs))
    print('sendAssignmentEvent_memberId_refs=' + str(member_refs))
    print('sendAssignmentEvent_token_refs=' + str(token_refs))
    if target_refs == 0:
        print('result=SUSPECT_MISSING_TARGET_MEMBER_ID')
    else:
        print('result=TARGET_MEMBER_ID_PRESENT_REVIEW_MAPPING')
else:
    print('\nSUMMARY\nresult=SEND_ASSIGNMENT_EVENT_NOT_FOUND')
