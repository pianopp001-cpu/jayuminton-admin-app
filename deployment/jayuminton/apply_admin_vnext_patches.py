#!/usr/bin/env python3
"""Apply admin-vNext patches in fixed fail-fast order. Never deploys user production.

Operations MD sync: immediate promoted-wait return and MD-only controls v1.
"""
from pathlib import Path
import subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('source-snapshot/current-main').resolve()
CODE=ROOT/'Code.js'; ADMIN=ROOT/'Admin.html'; SCRIPT=ROOT/'Script.html'; STYLE=ROOT/'Style.html'
for target in (CODE,ADMIN,SCRIPT,STYLE):
 if not target.exists(): raise SystemExit(f'required source not found: {target}')
patches=[
 HERE/'admin_vnext_backend_patch.py', HERE/'admin_vnext_assignment_guard_patch.py', HERE/'admin_vnext_notification_contract.py', HERE/'admin_vnext_recent_play_stat_patch.py',
 HERE/'admin_vnext_member_fields_patch.py', HERE/'admin_vnext_ui_patch.py', HERE/'admin_vnext_missing_value_prepatch.py', HERE/'admin_vnext_script_patch.py', HERE/'admin_vnext_fast_save_patch.py', HERE/'v3_admin_overlay_guarantee.py', HERE/'admin_vnext_badge_cleanup_patch.py',
 HERE/'admin_vnext_multiselect_patch.py', HERE/'admin_vnext_partial_court_ui_patch.py', HERE/'admin_vnext_recent_played_ui_patch.py', HERE/'admin_vnext_transition_alert_patch.py', HERE/'admin_vnext_empty_court_patch.py', HERE/'admin_finish_fast_return_patch.py', HERE/'admin_fast_state_return_patch.py', HERE/'admin_md_ui_cleanup_patch.py', HERE/'admin_excluded_always_visible_patch.py', HERE/'admin_vnext_md_exact_patch.py', HERE/'admin_vnext_webview_observer_compat_patch.py',
]
for patch in patches:
 if not patch.exists(): raise SystemExit(f'patch not found: {patch}')
 print(f'[admin-vNext] applying {patch.name}')
 subprocess.run([sys.executable,str(patch),str(ROOT)],check=True)
code=CODE.read_text(encoding='utf-8'); admin=ADMIN.read_text(encoding='utf-8'); script=SCRIPT.read_text(encoding='utf-8'); style=STYLE.read_text(encoding='utf-8')
required_code=["const SHEET_PAIR_HISTORY = 'PairHistory';","const ADMIN_VNEXT_EVENTS = Object.freeze({","function buildAdminVnextEvent_(type, memberIds, courtNo)","function publishAdminVnextEvents_(events)","function readAdminVnextEvents_()","WAIT_ONE_PROMOTED: 'WAIT_ONE_PROMOTED'","adminVnextEvents: readAdminVnextEvents_()","'IS_NEW', 'PUBLIC_MEMO', 'IS_SPONSOR', 'BUNDLE_ID'",'function adjustMemberGames(pin,id,delta)','function setBundle(pin,ids)','function clearBundle(pin,ids)','function addMemberUnlocked_(pin, name, gender, grade, experience, extra)','function updateMemberProfile(pin, memberId, name, gender, grade, experience, extra)',"publicMemo: String(member.publicMemo || '').slice(0, 40)","function getPairStatistics(pin)","const pairCounts = readPairCounts_();","getRange(2, 1, lastRow - 1, 12).getValues()","isNew: String(row[8] || '') === '1'","sheet.getRange(index + 2, 1, 1, 12).setValues","sheet.getRange(2, 1, rows.length, 12).setValues(rows);","return {ok: true, member: members[index]","JAYUMINTON_ADMIN_FAST_ADD_MEMBER_V1","JAYUMINTON_ADMIN_FAST_FINISH_RETURN_V1","JAYUMINTON_ADMIN_FAST_MUTATION_RETURN_V1","for(let i=0;i<finalCourtIds.length;i++) for(let j=i+1;j<finalCourtIds.length;j++)","score+=1000000","if(!activeSet[pool[i]])continue","JAYUMINTON_MEMBER_ASSIGNMENT_BUSY_V1","memberPriority ? 15000 : 3500"]
required_admin=['id="newIsNew"','id="newIsSponsor"','id="newPublicMemo"','id="newGradeExperience"','class="member-gender-radio"','게임횟수 +1','>자동배정</button>','admin-vnext-bottom-bar','mobile-refresh-button','id="pairStatisticsModal"','id="pairStatisticsList"','__JAYUMINTON_ADMIN_MD_UI_CLEANUP_V6__','__JAYUMINTON_ADMIN_EXCLUDED_ALWAYS_VISIBLE_V1__','__JAYUMINTON_ADMIN_MD_EXACT_V1__','admin-excluded-always-visible','게임횟수 카운트 조정',"setLongPressedMemberStatus('active')","setLongPressedMemberStatus('before')","setLongPressedMemberStatus('rest')","setLongPressedMemberStatus('away')",'deleteLongPressedMembers()']
required_script=['function increaseSelectedGames()','function setSelectedBundle()','function clearSelectedBundle()',"server('adjustMemberGames'","runAction('setBundle'","runAction('clearBundle'",'function handleCourtMemberTap(courtNo, memberId, event)','function handleWaitMemberTap(groupIndex, memberId, event)','toggleSelected(memberId);','function adminVnextMemberBadges(member)','function adminVnextCardName(member)','__JAYUMINTON_ADMIN_TRANSITION_ALERT_BRIDGE_V1__','__JAYUMINTON_ADMIN_EMPTY_COURT_FINISH_V1__','function adminVnextRecentPlayed(member)','function openPairStatistics()','function renderPairStatistics()','__JAYUMINTON_ADMIN_FAST_SAVE_CLIENT_V1__','JAYUMINTON_ADMIN_SAVING_GUARANTEE_V1','__JAYUMINTON_ADMIN_SAVING_GUARANTEE_V2__','<span class="member-vnext-badge new-badge" aria-label="신규 회원"><small>신규</small></span>','🎁 찬조','__JAYUMINTON_ADMIN_MD_EXACT_SCRIPT_V1__','function syncAdminMemberCounts()','function setLongPressedMemberStatus(','function deleteLongPressedMembers(']
required_style=['JAYUMINTON_ADMIN_SAVING_BLOCKING_CSS_V2','z-index:2147483647!important','pointer-events:auto!important','body.admin-saving-active']
missing=([f'Code:{x}' for x in required_code if x not in code]+[f'Admin:{x}' for x in required_admin if x not in admin]+[f'Script:{x}' for x in required_script if x not in script]+[f'Style:{x}' for x in required_style if x not in style])
if missing: raise SystemExit('admin-vNext verification failed; missing: '+' | '.join(missing))
if '비어 있는 코트는 경기 종료할 수 없습니다.' in code: raise SystemExit('admin-vNext verification failed; empty-court backend rejection still present')
if 'NEW <small>신규</small>' in script: raise SystemExit('admin-vNext verification failed; legacy English NEW badge still present')
if 'onclick="testVoiceGuide()"' in admin or 'onclick="setSelectedBundle()"' in admin or 'compact-admin-tools' in admin: raise SystemExit('admin-vNext verification failed; unnecessary MD controls survived')
details_start=admin.find('<details class="admin-setup-details"'); details_end=admin.find('</details>',details_start); excluded_pos=admin.find('admin-excluded-always-visible')
if details_start < 0 or details_end < 0 or details_start < excluded_pos < details_end: raise SystemExit('admin-vNext verification failed; excluded roster still collapses with settings')
finish_start=code.find('function finishCourtUnlocked_('); finish_end=code.find('\nfunction ',finish_start+20); finish=code[finish_start:finish_end]
if 'waitGroups = [(waitGroups[1]||[]).slice()' not in finish or 'return makeState_(members, courts, waitGroups, startedAt)' not in finish: raise SystemExit('admin-vNext verification failed; finish must return promoted wait groups immediately')
longpress_start=admin.find('id="quickMoveBar"'); longpress_end=admin.find('</div>',longpress_start)
if longpress_start < 0 or longpress_end < 0 or admin[longpress_start:longpress_end].count('<button') != 6: raise SystemExit('admin-vNext verification failed; long-press menu must have exactly six buttons')
print('[admin-vNext] admin-only patches verified: blocking save overlay, empty-court finish, member-only alerts, fast add/finish/all-mutation state returns, notification contract, recent-play statistic, Korean 신규 badge, MD-exact registration and six-action long-press UI')
