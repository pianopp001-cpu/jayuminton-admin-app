#!/usr/bin/env python3
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')

old_write = """    const started = actualCount === GROUP_SIZE
      ? String(times[key] || '')
      : '';"""
new_write = """    const started = actualCount > 0
      ? String(times[key] || '')
      : '';"""
if old_write not in s:
    raise SystemExit('writeCourts started marker missing')
s = s.replace(old_write, new_write, 1)

old_mark = """function markCourtStartedIfFull_(courts, startedAt, courtNo) {
  const key = String(courtNo);
  const full = (courts[key] || []).length === GROUP_SIZE;

  if (full && !startedAt[key]) {
    startedAt[key] = new Date().toISOString();
  }

  if (!full) {
    startedAt[key] = '';
  }
}"""
new_mark = """function markCourtStartedIfFull_(courts, startedAt, courtNo) {
  const key = String(courtNo);
  const occupied = (courts[key] || []).length > 0;
  if (!occupied) startedAt[key] = '';
}"""
if old_mark not in s:
    raise SystemExit('markCourtStartedIfFull marker missing')
s = s.replace(old_mark, new_mark, 1)

# Removing one player during a live game must not erase the existing court timer.
s = s.replace("""  startedAt[courtNo] = '';
  writeCourts_(courts, startedAt);
  updateMemberStatuses_([id], 'active');""", """  if (!(courts[courtNo] || []).length) startedAt[courtNo] = '';
  writeCourts_(courts, startedAt);
  updateMemberStatuses_([id], 'active');""", 1)

anchor = "function readWaitGroups_() {"
helpers = r'''
function adminPreviewFiveMinuteMarkerKey_(courtNo, startedAt) {
  return 'ADMIN_PREVIEW_5MIN_COUNTED_' + String(courtNo) + '_' + String(startedAt || '');
}

function adminPreviewCreditFiveMinuteGame_(courtNo, participantIds, startedAt, members) {
  participantIds = normalizeIds_(participantIds);
  startedAt = String(startedAt || '');
  if (!participantIds.length || !startedAt) return false;
  const startedMs = new Date(startedAt).getTime();
  if (!isFinite(startedMs) || Date.now() - startedMs < 5 * 60 * 1000) return false;
  const key = adminPreviewFiveMinuteMarkerKey_(courtNo, startedAt);
  if (getSetting_(key) === '1') return false;
  members.forEach(function(member) {
    if (participantIds.indexOf(member.id) >= 0) member.games = (Number(member.games) || 0) + 1;
  });
  setSetting_(key, '1');
  return true;
}

'''
if anchor not in s:
    raise SystemExit('readWaitGroups anchor missing')
s = s.replace(anchor, helpers + anchor, 1)

old_finish_guard = """  if (finished.length !== GROUP_SIZE) {
    throw new Error(
      '4명이 모두 배정된 코트만 경기 종료할 수 있습니다.'
    );
  }

  const members = readMembers_();

  members.forEach(function(member) {
    if (finished.indexOf(member.id) >= 0) {
      member.games =
        (Number(member.games) || 0) + 1;
      member.status = 'active';
    }
  });"""
new_finish_guard = """  if (!finished.length) {
    throw new Error('빈 코트는 경기 종료할 수 없습니다.');
  }

  const members = readMembers_();
  const previewStartedAt = String(startedAt[courtNo] || '');
  adminPreviewCreditFiveMinuteGame_(courtNo, finished, previewStartedAt, members);

  members.forEach(function(member) {
    if (finished.indexOf(member.id) >= 0) {
      member.status = 'active';
    }
  });"""
if old_finish_guard not in s:
    raise SystemExit('actual finishCourt guard/count block missing')
s = s.replace(old_finish_guard, new_finish_guard, 1)

required = [
  'adminPreviewCreditFiveMinuteGame_',
  'Date.now() - startedMs < 5 * 60 * 1000',
  'const started = actualCount > 0',
  "if (!finished.length)",
  "if (!(courts[courtNo] || []).length) startedAt[courtNo] = '';"
]
for x in required:
    if x not in s:
        raise SystemExit('missing patched marker: ' + x)

p.write_text(s, encoding='utf-8')
