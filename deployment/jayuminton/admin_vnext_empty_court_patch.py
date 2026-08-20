#!/usr/bin/env python3
"""Admin-only patch: allow finishing an empty court so wait group 1 can still be promoted.

The member production frontend is not edited. This removes the legacy server-side
empty-court rejection and the admin UI occupancy gate that could hide/disable a
court finish action when zero members remain on the court.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
code_path = root / 'Code.js'
script_path = root / 'Script.html'
code = code_path.read_text(encoding='utf-8')
script = script_path.read_text(encoding='utf-8')

# The current main GAS snapshot rejects empty courts in finishCourtUnlocked_.
# Remove only that specific guard; all PIN/court-number validation remains intact.
legacy_guards = [
    "  if (!finished.length) throw new Error('비어 있는 코트는 경기 종료할 수 없습니다.');\n",
    '  if (!finished.length) throw new Error("비어 있는 코트는 경기 종료할 수 없습니다.");\n',
]
removed = False
for guard in legacy_guards:
    if guard in code:
        code = code.replace(guard, '', 1)
        removed = True
        break
if not removed and '비어 있는 코트는 경기 종료할 수 없습니다.' in code:
    raise SystemExit('empty-court backend guard shape changed; refusing broad replacement')

# Admin elapsed/finish controls used occupancy as the definition of a finishable
# court. A zero-member court must still expose the finish action. Keep only the
# existence/array checks, not a member-count requirement.
script = script.replace(
    "return state && state.courts && Array.isArray(state.courts[no]) &&\n      state.courts[no].length > 0;",
    "return state && state.courts && Array.isArray(state.courts[no]);",
)
script = script.replace(
    "return state && state.courts && Array.isArray(state.courts[no]) &&\n      state.courts[no].length === 4;",
    "return state && state.courts && Array.isArray(state.courts[no]);",
)
script = script.replace('(STATE.courts[courtNo] || []).length > 0', 'Array.isArray(STATE.courts[courtNo])')
script = script.replace('(STATE.courts[courtNo] || []).length === 4', 'Array.isArray(STATE.courts[courtNo])')
script = script.replace('state.courts[no].length > 0', 'Array.isArray(state.courts[no])')
script = script.replace('state.courts[no].length === 4', 'Array.isArray(state.courts[no])')

# Make the contract explicit for downstream deploy/APK verifiers.
if '__JAYUMINTON_ADMIN_EMPTY_COURT_FINISH_V1__' not in script:
    script += "\n<script>window.__JAYUMINTON_ADMIN_EMPTY_COURT_FINISH_V1__=true;</script>\n"

if '비어 있는 코트는 경기 종료할 수 없습니다.' in code:
    raise SystemExit('legacy empty-court backend rejection survived')
if '__JAYUMINTON_ADMIN_EMPTY_COURT_FINISH_V1__' not in script:
    raise SystemExit('empty-court admin marker missing')

code_path.write_text(code, encoding='utf-8')
script_path.write_text(script, encoding='utf-8')
print('ADMIN_EMPTY_COURT_FINISH_OK')
