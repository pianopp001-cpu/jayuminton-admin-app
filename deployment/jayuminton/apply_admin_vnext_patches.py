#!/usr/bin/env python3
"""Apply admin-vNext patches in a fixed, fail-fast order.

Development tooling only. This script edits only the supplied snapshot path and
never deploys or changes the production user web/app.
"""
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path('source-snapshot/current-main').resolve()
CODE = ROOT / 'Code.js'

if not CODE.exists():
    raise SystemExit(f'Code.js not found: {CODE}')

patches = [
    HERE / 'admin_vnext_backend_patch.py',
    HERE / 'admin_vnext_member_fields_patch.py',
]

for patch in patches:
    if not patch.exists():
        raise SystemExit(f'patch not found: {patch}')
    print(f'[admin-vNext] applying {patch.name}')
    subprocess.run([sys.executable, str(patch), str(ROOT)], check=True)

text = CODE.read_text(encoding='utf-8')
required = [
    "const SHEET_PAIR_HISTORY = 'PairHistory';",
    "'IS_NEW', 'PUBLIC_MEMO', 'IS_SPONSOR', 'BUNDLE_ID'",
    'function adjustMemberGames(pin,id,delta)',
    'function setBundle(pin,ids)',
    'function clearBundle(pin,ids)',
    'function addMemberUnlocked_(pin, name, gender, grade, experience, extra)',
    'function updateMemberProfile(pin, memberId, name, gender, grade, experience, extra)',
    "publicMemo: String(member.publicMemo || '').slice(0, 40)",
]
missing = [needle for needle in required if needle not in text]
if missing:
    raise SystemExit('admin-vNext verification failed; missing: ' + ' | '.join(missing))

print('[admin-vNext] patch chain verified successfully')
