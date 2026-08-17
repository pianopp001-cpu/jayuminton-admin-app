#!/usr/bin/env python3
"""Admin vNext backend patcher.

Development helper only. It patches a copied Apps Script source tree; it does not deploy
or touch the frozen user Cloudflare/web/app production path.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
p = root / 'Code.js'
s = p.read_text(encoding='utf-8')

s = s.replace("const SHEET_LOGS = 'ActionLogs';", "const SHEET_LOGS = 'ActionLogs';\nconst SHEET_PAIR_HISTORY = 'PairHistory';")
s = s.replace("const setupKey = 'JAYUMINTON_SETUP_V11_' + ss.getId();", "const setupKey = 'JAYUMINTON_SETUP_ADMIN_VNEXT_1_' + ss.getId();")
s = s.replace("  ensureLogsSheet_(ss);\n  migrateLegacyDataIfNeeded_(ss);", "  ensureLogsSheet_(ss);\n  ensurePairHistorySheet_(ss);\n  migrateLegacyDataIfNeeded_(ss);")
old = """  sheet.getRange(1, 1, 1, 8).setValues([[
    'ID',
    'NAME',
    'GENDER',
    'GAMES',
    'STATUS',
    'CREATED_AT',
    'GRADE',
    'EXPERIENCE'
  ]]);"""
new = """  // Keep the original first 8 columns stable for backward compatibility.
  sheet.getRange(1, 1, 1, 12).setValues([[
    'ID', 'NAME', 'GENDER', 'GAMES', 'STATUS', 'CREATED_AT', 'GRADE', 'EXPERIENCE',
    'IS_NEW', 'PUBLIC_MEMO', 'IS_SPONSOR', 'BUNDLE_ID'
  ]]);"""
if old not in s:
    raise SystemExit('members header anchor not found')
s = s.replace(old, new)

anchor = "function withDocumentLock_(actionName, callback) {"
insert = r'''function ensurePairHistorySheet_(ss) {
  let sheet = ss.getSheetByName(SHEET_PAIR_HISTORY);
  if (!sheet) sheet = ss.insertSheet(SHEET_PAIR_HISTORY);
  sheet.getRange(1, 1, 1, 4).setValues([[
    'TIME', 'COURT_NO', 'MEMBER_IDS', 'PAIR_KEYS'
  ]]);
  sheet.setFrozenRows(1);
}

function pairKey_(a, b) {
  return [String(a), String(b)].sort().join('::');
}

function recordCourtEntryPairs_(courtNo, entrantIds, finalCourtIds) {
  entrantIds = normalizeIds_(entrantIds);
  finalCourtIds = normalizeIds_(finalCourtIds);
  if (!entrantIds.length) return;
  const pairKeys = [];
  entrantIds.forEach(function(a) {
    finalCourtIds.forEach(function(b) {
      if (a !== b) pairKeys.push(pairKey_(a, b));
    });
  });
  pairKeys.sort();
  const unique = pairKeys.filter(function(v, i, arr) { return i === 0 || v !== arr[i - 1]; });
  SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_PAIR_HISTORY).appendRow([
    new Date(), String(courtNo), finalCourtIds.join(','), unique.join(',')
  ]);
}

function incrementGamesForCourtEntrants_(members, entrantIds) {
  const entered = {};
  normalizeIds_(entrantIds).forEach(function(id) { entered[id] = true; });
  members.forEach(function(member) {
    if (entered[member.id]) member.games = Math.max(0, Number(member.games) || 0) + 1;
  });
}

function adjustMemberGames(pin, id, delta) {
  return withDocumentLock_('게임횟수 수동 보정', function() {
    auth_(pin);
    delta = Number(delta);
    if (delta !== 1 && delta !== -1) throw new Error('게임횟수는 +1 또는 -1만 조정할 수 있습니다.');
    const members = readMembers_();
    let found = false;
    members.forEach(function(member) {
      if (member.id === String(id)) {
        member.games = Math.max(0, (Number(member.games) || 0) + delta);
        found = true;
      }
    });
    if (!found) throw new Error('멤버를 찾을 수 없습니다.');
    writeMembers_(members); touch_();
    return getPublicState();
  });
}

function setBundle(pin, ids) {
  return withDocumentLock_('고정 묶음 지정', function() {
    auth_(pin); ids = normalizeIds_(ids);
    if (ids.length !== 2) throw new Error('고정 묶음은 정확히 2명을 선택하세요.');
    const bundleId = Utilities.getUuid();
    const members = readMembers_();
    members.forEach(function(member) { if (ids.indexOf(member.id) >= 0) member.bundleId = bundleId; });
    writeMembers_(members); touch_(); return getPublicState();
  });
}

function clearBundle(pin, ids) {
  return withDocumentLock_('고정 묶음 해제', function() {
    auth_(pin); ids = normalizeIds_(ids);
    const members = readMembers_();
    const bundleIds = {};
    members.forEach(function(member) { if (ids.indexOf(member.id) >= 0 && member.bundleId) bundleIds[member.bundleId] = true; });
    members.forEach(function(member) { if (bundleIds[member.bundleId]) member.bundleId = ''; });
    writeMembers_(members); touch_(); return getPublicState();
  });
}

'''
if anchor not in s:
    raise SystemExit('lock anchor not found')
s = s.replace(anchor, insert + anchor)

p.write_text(s, encoding='utf-8')
print('admin vNext backend foundation patch prepared')
