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

if '__JAYUMINTON_ADMIN_EMPTY_COURT_FINISH_V1__' not in script:
    close = script.rfind('</script>')
    if close < 0:
        raise SystemExit('Script.html closing wrapper missing')
    script = script[:close] + "\nwindow.__JAYUMINTON_ADMIN_EMPTY_COURT_FINISH_V1__=true;\n" + script[close:]

if '비어 있는 코트는 경기 종료할 수 없습니다.' in code:
    raise SystemExit('legacy empty-court backend rejection survived')
if '__JAYUMINTON_ADMIN_EMPTY_COURT_FINISH_V1__' not in script:
    raise SystemExit('empty-court admin marker missing')

code_path.write_text(code, encoding='utf-8')
script_path.write_text(script, encoding='utf-8')
print('ADMIN_EMPTY_COURT_FINISH_OK')