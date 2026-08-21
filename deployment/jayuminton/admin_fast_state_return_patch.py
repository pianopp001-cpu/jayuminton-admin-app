#!/usr/bin/env python3
"""Reduce admin mutation latency by avoiding an immediate full spreadsheet reread.

For selected mutation *Unlocked_ functions, replace the final getPublicState()
with makeState_ built from state objects that were already written in the same
function. Any component not safely available in-memory is reread individually.
This preserves the full response contract while cutting redundant sheet reads.
"""
from pathlib import Path
import re, sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
path = root / 'Code.js'
text = path.read_text(encoding='utf-8')

TARGETS = [
    'setMemberStatusUnlocked_', 'deleteMembersUnlocked_',
    'assignMembersToCourtUnlocked_', 'assignMembersToWaitGroupUnlocked_',
    'assignWaitGroupToCourtUnlocked_', 'autoFillCourtUnlocked_',
    'autoFillWaitGroupUnlocked_', 'moveOrSwapMemberUnlocked_',
    'swapCourtsUnlocked_', 'swapWaitGroupsUnlocked_',
    'adjustCourtMembersUnlocked_', 'adjustWaitGroupMembersUnlocked_',
    'removeFromCourtUnlocked_', 'removeFromWaitGroupUnlocked_',
    'decreaseSelectedGameCountsUnlocked_', 'resetSelectedGameCountsUnlocked_'
]
MARKER = 'JAYUMINTON_ADMIN_FAST_MUTATION_RETURN_V1'


def function_block(source, name):
    m = re.search(r'function\s+' + re.escape(name) + r'\s*\(', source)
    if not m:
        return None
    start = m.start()
    brace = source.find('{', m.end())
    depth = 0; quote = None; esc = False
    for i in range(brace, len(source)):
        ch = source[i]
        if quote:
            if esc: esc = False
            elif ch == '\\': esc = True
            elif ch == quote: quote = None
            continue
        if ch in "'\"`": quote = ch
        elif ch == '{': depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0: return start, i + 1, source[start:i + 1]
    raise SystemExit('unbalanced function: ' + name)


def written_var(block, writer):
    # Use an in-memory value only when the same variable is explicitly persisted.
    m = re.search(r'\b' + re.escape(writer) + r'\s*\(\s*([A-Za-z_$][\w$]*)', block)
    return m.group(1) if m else None


def court_vars(block):
    m = re.search(r'\bwriteCourts_\s*\(\s*([A-Za-z_$][\w$]*)\s*,\s*([A-Za-z_$][\w$]*)', block)
    return (m.group(1), m.group(2)) if m else (None, None)

changed = []
for name in TARGETS:
    found = function_block(text, name)
    if not found:
        continue
    a, b, block = found
    if MARKER in block or 'return getPublicState();' not in block:
        continue

    member_var = written_var(block, 'writeMembers_')
    wait_var = written_var(block, 'writeWaitGroups_')
    court_var, started_var = court_vars(block)

    # updateMemberStatuses_ persists a separate member snapshot, so do not trust
    # any older local member array unless this function itself writeMembers_ it.
    members_expr = member_var or 'readMembers_()'
    courts_expr = court_var or 'readCourts_()'
    wait_expr = wait_var or 'readWaitGroups_()'
    started_expr = started_var or 'readCourtStartedAt_()'

    replacement = (
        'return makeState_(' + members_expr + ', ' + courts_expr + ', ' +
        wait_expr + ', ' + started_expr + '); // ' + MARKER
    )
    pos = block.rfind('return getPublicState();')
    block = block[:pos] + replacement + block[pos + len('return getPublicState();'):]
    text = text[:a] + block + text[b:]
    changed.append(name)

if len(changed) < 8:
    raise SystemExit('fast mutation patch matched too few functions: ' + ','.join(changed))
if MARKER not in text:
    raise SystemExit('fast mutation marker missing')
path.write_text(text, encoding='utf-8')
print('ADMIN_FAST_MUTATION_RETURN_OK count=%d functions=%s' % (len(changed), ','.join(changed)))
