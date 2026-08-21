#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: admin_assign_optimistic_patch.py <work-dir>')

root = Path(sys.argv[1])
p = root / 'Script.html'
s = p.read_text(encoding='utf-8')

signature = 'async function runAction(fnName, ...args)'
start = s.find(signature)
if start < 0:
    raise SystemExit('runAction function not found')
brace = s.find('{', start)
if brace < 0:
    raise SystemExit('runAction opening brace missing')
if 'JAYUMINTON_ADMIN_OPTIMISTIC_ASSIGN_V1' in s[start:start+5000]:
    print('Optimistic assignment patch already present.')
    raise SystemExit(0)

insert = r'''
  // JAYUMINTON_ADMIN_OPTIMISTIC_ASSIGN_V1
  // Paint the hottest operator action immediately; reconcile with authoritative
  // server state afterwards. This deliberately avoids the full-screen save wait.
  if (fnName === "assignWaitGroupToCourt") {
    const gi = Number(args[0]);
    const ci = Number(args[1]);
    const group = state && Array.isArray(state.waitGroups) ? state.waitGroups[gi] : null;
    const court = state && Array.isArray(state.courts) ? state.courts[ci] : null;
    if (Array.isArray(group) && group.length && court) {
      const backup = JSON.parse(JSON.stringify(state));
      try {
        state.waitGroups.splice(gi, 1);
        while (state.waitGroups.length < 5) state.waitGroups.push([]);
        court.players = group.slice();
        if (typeof simulateFrontQueueEffectsLocally === "function") simulateFrontQueueEffectsLocally();
        if (typeof promoteNormalOverflowLocally === "function") promoteNormalOverflowLocally();
        render();
        const next = await server(fnName, ...args);
        state = next;
        render();
        return next;
      } catch (e) {
        state = backup;
        render();
        if (typeof showToast === "function") showToast((e && e.message) ? e.message : String(e));
        else console.error(e);
        return null;
      }
    }
  }
'''
s = s[:brace+1] + insert + s[brace+1:]
if 'JAYUMINTON_ADMIN_OPTIMISTIC_ASSIGN_V1' not in s:
    raise SystemExit('optimistic marker missing after patch')
p.write_text(s, encoding='utf-8')
print('Applied immediate admin court-assignment rendering with server reconciliation.')
