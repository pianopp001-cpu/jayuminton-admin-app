#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: admin_assign_optimistic_patch.py <work-dir>')

root = Path(sys.argv[1])
p = root / 'Script.html'
s = p.read_text(encoding='utf-8')

anchor = '''async function runAction(fnName, ...args) {\n  showLoading("저장 중...");'''
if anchor not in s:
    raise SystemExit('runAction anchor not found')

replacement = '''async function runAction(fnName, ...args) {\n  // JAYUMINTON_ADMIN_OPTIMISTIC_ASSIGN_V1\n  // Court assignment is the operator's hottest path. Paint the move and queue\n  // promotion immediately, then reconcile with the authoritative server state.\n  if (fnName === "assignWaitGroupToCourt") {\n    const gi = Number(args[0]);\n    const ci = Number(args[1]);\n    const group = state && Array.isArray(state.waitGroups) ? state.waitGroups[gi] : null;\n    const court = state && Array.isArray(state.courts) ? state.courts[ci] : null;\n    if (Array.isArray(group) && group.length && court) {\n      const backup = JSON.parse(JSON.stringify(state));\n      try {\n        state.waitGroups.splice(gi, 1);\n        while (state.waitGroups.length < 5) state.waitGroups.push([]);\n        court.players = group.slice();\n        if (typeof simulateFrontQueueEffectsLocally === "function") simulateFrontQueueEffectsLocally();\n        if (typeof promoteNormalOverflowLocally === "function") promoteNormalOverflowLocally();\n        render();\n        const next = await server(fnName, ...args);\n        state = next;\n        render();\n        return next;\n      } catch (e) {\n        state = backup;\n        render();\n        if (typeof showToast === "function") showToast((e && e.message) ? e.message : String(e));\n        else console.error(e);\n        return null;\n      }\n    }\n  }\n  showLoading("저장 중...");'''

s = s.replace(anchor, replacement, 1)
if 'JAYUMINTON_ADMIN_OPTIMISTIC_ASSIGN_V1' not in s:
    raise SystemExit('optimistic marker missing after patch')
p.write_text(s, encoding='utf-8')
print('Applied immediate admin court-assignment rendering with server reconciliation.')
