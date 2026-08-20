#!/usr/bin/env python3
"""Static and behavioral checks for admin-vNext transition notifications."""
from pathlib import Path
import sys

code_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/tmp/admin-vnext-source/Code.js')
source = code_path.read_text(encoding='utf-8')

required = [
    "COURT_FINISHED: 'COURT_FINISHED'",
    "COURT_PROMOTED: 'COURT_PROMOTED'",
    "WAIT_ONE_PROMOTED: 'WAIT_ONE_PROMOTED'",
    'function publishAdminVnextEvents_(events)',
    'function readAdminVnextEvents_()',
    'adminVnextEvents: readAdminVnextEvents_()',
    'if (waitOne.length > 0)',
    'const nextWaitOne = (waitGroups[1] || []).slice();'
]
missing = [item for item in required if item not in source]
if missing:
    raise SystemExit('missing notification contract markers: ' + ' | '.join(missing))

for forbidden in [
    "if (!finished.length) throw new Error('비어 있는 코트는 경기 종료할 수 없습니다.')",
    'if (!finished.length) throw new Error("비어 있는 코트는 경기 종료할 수 없습니다.")',
    "finished.length !== GROUP_SIZE",
    "waitOne.length === GROUP_SIZE",
    "4명이 모두 배정된 코트만 경기 종료할 수 있습니다."
]:
    if forbidden in source:
        raise SystemExit('obsolete finish restriction remains: ' + forbidden)

def transition_events(finished, wait_groups, court_no):
    events = [('COURT_FINISHED', tuple(finished), str(court_no))]
    wait_one = list(wait_groups[0] if wait_groups else [])
    if wait_one:
        events.append(('COURT_PROMOTED', tuple(wait_one), str(court_no)))
    next_wait_one = list(wait_groups[1] if len(wait_groups) > 1 else [])
    if next_wait_one:
        events.append(('WAIT_ONE_PROMOTED', tuple(next_wait_one), ''))
    return events

for size in range(0, 5):
    finished = ['f' + str(i) for i in range(size)]
    old_wait_one = ['p1', 'p2']
    next_wait_one = ['w1', 'w2']
    events = transition_events(finished, [old_wait_one, next_wait_one, [], [], []], 2)
    assert events[0][1] == tuple(finished)
    assert events[1][1] == tuple(old_wait_one)
    assert events[2][1] == tuple(next_wait_one)

empty_with_promotion = transition_events([], [['p1','p2'], ['w1','w2'], [], [], []], 3)
assert empty_with_promotion == [
    ('COURT_FINISHED', (), '3'),
    ('COURT_PROMOTED', ('p1','p2'), '3'),
    ('WAIT_ONE_PROMOTED', ('w1','w2'), '')
]

only_finish = transition_events(['f1'], [[], [], [], [], []], 1)
assert only_finish == [('COURT_FINISHED', ('f1',), '1')]

print('admin-vNext notification contract supports 0-4 finished members plus court/wait1 promotion')