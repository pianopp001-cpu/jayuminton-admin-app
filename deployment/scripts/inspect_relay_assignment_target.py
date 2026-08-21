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
    'sendAssignmentEventWithoutDiagnostics_',
    'makeWebFcmRequest_',
    'nativeTokenKind_',
    'sendNativeUserPush_',
    'sendFcmHttpV1_',
    'sendFcmMessage_',
    'sendWebPush_',
    'loadWebPushTokens_',
    'registerWebToken_',
    'cleanEvent_',
]

print('READ_ONLY_RELAY_ASSIGNMENT_INSPECTION_V3')
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
    fn = re.sub(r"(['\"])(?:ya29\.|AIza|eyJ)[^'\"]+\1", "'__REDACTED__'", fn)
    print(fn)

assignment = extract_function('sendAssignmentEvent_')
core = extract_function('sendAssignmentEventWithoutDiagnostics_')
request = extract_function('makeWebFcmRequest_')
print('\nSUMMARY')
for label, fn in [('wrapper', assignment), ('core', core), ('request', request)]:
    if not fn:
        print(label + '_found=False')
        continue
    print(label + '_found=True')
    print(label + '_targetMemberId_refs=' + str(len(re.findall(r'targetMemberId', fn))))
    print(label + '_memberId_refs=' + str(len(re.findall(r'\.memberId\b|\bmemberId\b|member\.id', fn))))
    print(label + '_token_refs=' + str(len(re.findall(r'\.token\b|\btoken\b', fn))))
    print(label + '_data_refs=' + str(len(re.findall(r'\bdata\b', fn))))
if request:
    if 'targetMemberId' not in request:
        print('result=REQUEST_MISSING_TARGET_MEMBER_ID')
    elif not re.search(r'targetMemberId\s*:\s*String\([^\n]*member[^\n]*\.id|targetMemberId\s*:\s*member\.id', request):
        print('result=REQUEST_TARGET_MEMBER_MAPPING_SUSPECT')
    else:
        print('result=REQUEST_TARGET_MEMBER_MAPPING_PRESENT')
elif core:
    print('result=REQUEST_FUNCTION_NOT_FOUND')
else:
    print('result=CORE_FUNCTION_NOT_FOUND')
