#!/usr/bin/env python3
"""Admin vNext backend patcher. Development only; never deploys user production."""
from pathlib import Path
import sys
root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
p = root / 'Code.js'
s = p.read_text(encoding='utf-8')

def rep(old, new, label):
    global s
    if old not in s: raise SystemExit(label + ' anchor not found')
    s = s.replace(old, new, 1)

s = s.replace("const SHEET_LOGS = 'ActionLogs';", "const SHEET_LOGS = 'ActionLogs';\nconst SHEET_PAIR_HISTORY = 'PairHistory';", 1)
s = s.replace("const setupKey = 'JAYUMINTON_SETUP_V11_' + ss.getId();", "const setupKey = 'JAYUMINTON_SETUP_ADMIN_VNEXT_1_' + ss.getId();", 1)
s = s.replace("  ensureLogsSheet_(ss);\n  migrateLegacyDataIfNeeded_(ss);", "  ensureLogsSheet_(ss);\n  ensurePairHistorySheet_(ss);\n  migrateLegacyDataIfNeeded_(ss);", 1)
rep("""  sheet.getRange(1, 1, 1, 8).setValues([[
    'ID',
    'NAME',
    'GENDER',
    'GAMES',
    'STATUS',
    'CREATED_AT',
    'GRADE',
    'EXPERIENCE'
  ]]);""", """  // Preserve columns 1-8; append admin-vNext fields only.
  sheet.getRange(1, 1, 1, 12).setValues([[
    'ID', 'NAME', 'GENDER', 'GAMES', 'STATUS', 'CREATED_AT', 'GRADE', 'EXPERIENCE',
    'IS_NEW', 'PUBLIC_MEMO', 'IS_SPONSOR', 'BUNDLE_ID'
  ]]);""", 'members header')

anchor = "function withDocumentLock_(actionName, callback) {"
insert = r'''function ensurePairHistorySheet_(ss) {
  let sheet = ss.getSheetByName(SHEET_PAIR_HISTORY);
  if (!sheet) sheet = ss.insertSheet(SHEET_PAIR_HISTORY);
  sheet.getRange(1, 1, 1, 4).setValues([['TIME','COURT_NO','MEMBER_IDS','PAIR_KEYS']]);
  sheet.setFrozenRows(1);
}
function pairKey_(a,b){ return [String(a),String(b)].sort().join('::'); }
function recordCourtEntryPairs_(courtNo, entrantIds, finalCourtIds) {
  entrantIds=normalizeIds_(entrantIds); finalCourtIds=normalizeIds_(finalCourtIds); if(!entrantIds.length)return;
  const keys=[]; entrantIds.forEach(function(a){finalCourtIds.forEach(function(b){if(a!==b)keys.push(pairKey_(a,b));});});
  keys.sort(); const unique=keys.filter(function(v,i,a){return i===0||v!==a[i-1];});
  SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_PAIR_HISTORY).appendRow([new Date(),String(courtNo),finalCourtIds.join(','),unique.join(',')]);
}
function incrementGamesForCourtEntrants_(members, entrantIds) {
  const entered={}; normalizeIds_(entrantIds).forEach(function(id){entered[id]=true;});
  members.forEach(function(m){if(entered[m.id])m.games=Math.max(0,Number(m.games)||0)+1;});
}
function adjustMemberGames(pin,id,delta){return withDocumentLock_('게임횟수 수동 보정',function(){auth_(pin);delta=Number(delta);if(delta!==1&&delta!==-1)throw new Error('게임횟수는 +1 또는 -1만 조정할 수 있습니다.');const members=readMembers_();let found=false;members.forEach(function(m){if(m.id===String(id)){m.games=Math.max(0,(Number(m.games)||0)+delta);found=true;}});if(!found)throw new Error('멤버를 찾을 수 없습니다.');writeMembers_(members);touch_();return getPublicState();});}
function setBundle(pin,ids){return withDocumentLock_('고정 묶음 지정',function(){auth_(pin);ids=normalizeIds_(ids);if(ids.length!==2)throw new Error('고정 묶음은 정확히 2명을 선택하세요.');const bundleId=Utilities.getUuid();const members=readMembers_();members.forEach(function(m){if(ids.indexOf(m.id)>=0)m.bundleId=bundleId;});writeMembers_(members);touch_();return getPublicState();});}
function clearBundle(pin,ids){return withDocumentLock_('고정 묶음 해제',function(){auth_(pin);ids=normalizeIds_(ids);const members=readMembers_(),bundleIds={};members.forEach(function(m){if(ids.indexOf(m.id)>=0&&m.bundleId)bundleIds[m.bundleId]=true;});members.forEach(function(m){if(bundleIds[m.bundleId])m.bundleId='';});writeMembers_(members);touch_();return getPublicState();});}
'''
rep(anchor, insert+anchor, 'lock')

# Read/write storage: adapt common 8-column row mapping patterns without changing old columns.
s = s.replace("sheet.getRange(2, 1, lastRow - 1, 8)", "sheet.getRange(2, 1, lastRow - 1, 12)")
s = s.replace("sheet.getRange(2, 1, rows.length, 8)", "sheet.getRange(2, 1, rows.length, 12)")
# Member object mapping, anchored on experience property where present.
s = s.replace("experience: String(row[7] || '')", "experience: String(row[7] || ''),\n      isNew: String(row[8] || '') === '1',\n      publicMemo: String(row[9] || ''),\n      isSponsor: String(row[10] || '') === '1',\n      bundleId: String(row[11] || '')")
# Member serialization row, anchored on experience final cell where present.
s = s.replace("member.experience || ''\n    ];", "member.experience || '',\n      member.isNew ? '1' : '',\n      member.publicMemo || '',\n      member.isSponsor ? '1' : '',\n      member.bundleId || ''\n    ];")

# Extend normalized member payloads wherever grade/experience are copied together.
s = s.replace("experience: String(member.experience || '')", "experience: String(member.experience || ''),\n      isNew: Boolean(member.isNew),\n      publicMemo: String(member.publicMemo || ''),\n      isSponsor: Boolean(member.isSponsor),\n      bundleId: String(member.bundleId || '')")

p.write_text(s, encoding='utf-8')
print('admin vNext backend storage foundation patched')
