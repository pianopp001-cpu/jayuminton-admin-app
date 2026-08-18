#!/usr/bin/env python3
"""Pre-deployment gate for admin-vNext and the existing production FCM relay."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: admin_vnext_push_compatibility_check.py <patched-live-Code.js>')

source = Path(sys.argv[1]).read_text(encoding='utf-8')

required = [
    'JAYUMINTON_SERVER_STATE_PUSH_V1',
    'function sendStateTransitionPushes_(before, after)',
    "type: 'wait1_ready'",
    "type: 'court_assignment'",
    'function shouldCheckStatePush_(actionName)',
    'return true;',
    "WAIT_ONE_PROMOTED: 'WAIT_ONE_PROMOTED'",
    'adminVnextEvents: readAdminVnextEvents_()',
    "if (!finished.length) throw new Error('비어 있는 코트는 경기 종료할 수 없습니다.')",
    'if (waitOne.length > 0)'
]
missing = [item for item in required if item not in source]
if missing:
    raise SystemExit('production push compatibility failed: ' + ' | '.join(missing))

for obsolete in [
    'return (group || []).length === GROUP_SIZE;',
    'if (waitOne.length === GROUP_SIZE)',
    'if (finished.length !== GROUP_SIZE)'
]:
    if obsolete in source:
        raise SystemExit('obsolete four-person notification gate remains: ' + obsolete)

print('admin-vNext is compatible with existing wait1/court FCM transition delivery')
