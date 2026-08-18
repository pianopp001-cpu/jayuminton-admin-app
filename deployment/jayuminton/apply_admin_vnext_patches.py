#!/usr/bin/env python3
"""Apply admin-vNext patches in fixed fail-fast order. Never deploys user production."""
from pathlib import Path
import subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('source-snapshot/current-main').resolve()
CODE=ROOT/'Code.js'; ADMIN=ROOT/'Admin.html'; SCRIPT=ROOT/'Script.html'
for target in (CODE,ADMIN,SCRIPT):
 if not target.exists(): raise SystemExit(f'required source not found: {target}')
patches=[
 HERE/'admin_vnext_backend_patch.py',
 HERE/'admin_vnext_member_fields_patch.py',
 HERE/'admin_vnext_ui_patch.py',
 HERE/'admin_vnext_script_patch.py',
 HERE/'admin_vnext_multiselect_patch.py',
]
for patch in patches:
 if not patch.exists(): raise SystemExit(f'patch not found: {patch}')
 print(f'[admin-vNext] applying {patch.name}')
 subprocess.run([sys.executable,str(patch),str(ROOT)],check=True)
code=CODE.read_text(encoding='utf-8'); admin=ADMIN.read_text(encoding='utf-8'); script=SCRIPT.read_text(encoding='utf-8')
required_code=["const SHEET_PAIR_HISTORY = 'PairHistory';","'IS_NEW', 'PUBLIC_MEMO', 'IS_SPONSOR', 'BUNDLE_ID'",'function adjustMemberGames(pin,id,delta)','function setBundle(pin,ids)','function clearBundle(pin,ids)','function addMemberUnlocked_(pin, name, gender, grade, experience, extra)','function updateMemberProfile(pin, memberId, name, gender, grade, experience, extra)',"publicMemo: String(member.publicMemo || '').slice(0, 40)"]
required_admin=['id="newIsNew"','id="newIsSponsor"','id="newPublicMemo"','게임횟수 +1','묶음 지정','>자동배정</button>']
required_script=['function increaseSelectedGames()','function setSelectedBundle()','function clearSelectedBundle()',"server('adjustMemberGames'","runAction('setBundle'","runAction('clearBundle'",'function handleCourtMemberTap(courtNo, memberId, event)','function handleWaitMemberTap(groupIndex, memberId, event)','toggleSelected(memberId);','function adminVnextMemberBadges(member)']
missing=([f'Code:{x}' for x in required_code if x not in code]+[f'Admin:{x}' for x in required_admin if x not in admin]+[f'Script:{x}' for x in required_script if x not in script])
if missing: raise SystemExit('admin-vNext verification failed; missing: '+' | '.join(missing))
print('[admin-vNext] all admin-only patches verified successfully')
