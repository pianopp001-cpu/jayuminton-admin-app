#!/usr/bin/env python3
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')

# Preview-only backend rule: preserve an existing court STARTED_AT while at least one
# player remains. Clear it only when the court becomes empty.
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

  // Keep the existing timer once a game has started.  Do not erase it merely
  // because an administrator pre-moves one or more players for the next game.
  if (!occupied) {
    startedAt[key] = '';
  }
}"""
if old_mark not in s:
    raise SystemExit('markCourtStartedIfFull marker missing')
s = s.replace(old_mark, new_mark, 1)

# Add preview bookkeeping helpers. We intentionally reuse STARTED_AT rather than
# introducing a second court timer. A per-start timestamp marker prevents duplicate +1.
anchor = "function readWaitGroups_() {"
helpers = r'''
function adminPreviewFiveMinuteMarkerKey_(courtNo, startedAt) {
  return 'ADMIN_PREVIEW_5MIN_COUNTED_' + String(courtNo) + '_' + String(startedAt || '');
}

function adminPreviewCreditFiveMinuteGame_(courtNo, participantIds, startedAt) {
  participantIds = normalizeIds_(participantIds);
  startedAt = String(startedAt || '');
  if (!participantIds.length || !startedAt) return false;

  const startedMs = new Date(startedAt).getTime();
  if (!isFinite(startedMs) || Date.now() - startedMs < 5 * 60 * 1000) return false;

  const key = adminPreviewFiveMinuteMarkerKey_(courtNo, startedAt);
  if (getSetting_(key) === '1') return false;

  const members = readMembers_();
  members.forEach(function(member) {
    if (participantIds.indexOf(member.id) >= 0) {
      member.games = (Number(member.games) || 0) + 1;
    }
  });
  writeMembers_(members);
  setSetting_(key, '1');
  return true;
}

'''
if anchor not in s:
    raise SystemExit('readWaitGroups anchor missing')
s = s.replace(anchor, helpers + anchor, 1)

# The exact finish function varies across snapshots. Patch its old game-count loop only
# when the recognizable block is present; otherwise fail rather than guessing.
needle = "function finishCourtUnlocked_("
pos = s.find(needle)
if pos < 0:
    raise SystemExit('finishCourtUnlocked missing')
end = s.find('\nfunction ', pos + len(needle))
if end < 0:
    end = len(s)
block = s[pos:end]

# Remove the legacy requirement that exactly four players must remain at finish.
for old in [
    "if (ids.length !== GROUP_SIZE) {\n    throw new Error('4명이 모두 배정된 코트만 경기 종료할 수 있습니다.');\n  }",
    "if (ids.length !== GROUP_SIZE) {\n      throw new Error('4명이 모두 배정된 코트만 경기 종료할 수 있습니다.');\n    }"
]:
    block = block.replace(old, "if (!ids.length) {\n    throw new Error('빈 코트는 경기 종료할 수 없습니다.');\n  }")

# Insert 5-minute credit immediately after ids/startedAt are available. This counts
# only the players still participating when Finish is pressed; no duplicate credit for
# the same STARTED_AT is possible.
insert_candidates = [
    "const ids = (courts[courtNo] || []).slice();",
    "const ids = courts[courtNo].slice();"
]
inserted = False
for candidate in insert_candidates:
    if candidate in block:
        block = block.replace(candidate, candidate + "\n  const previewStartedAt = String(startedAt[courtNo] || '');\n  adminPreviewCreditFiveMinuteGame_(courtNo, ids, previewStartedAt);", 1)
        inserted = True
        break
if not inserted:
    raise SystemExit('finish ids marker missing')

# Remove recognizable legacy +1 loops in finish to prevent double counting.
legacy_patterns = [
"""  members.forEach(function(member) {
    if (ids.indexOf(member.id) >= 0) {
      member.games = (Number(member.games) || 0) + 1;
    }
  });""",
"""    members.forEach(function(member) {
      if (ids.indexOf(member.id) >= 0) {
        member.games = (Number(member.games) || 0) + 1;
      }
    });"""
]
removed = False
for legacy in legacy_patterns:
    if legacy in block:
        block = block.replace(legacy, '', 1)
        removed = True
        break
if not removed:
    raise SystemExit('legacy finish game increment marker missing')

s = s[:pos] + block + s[end:]

required = [
    'adminPreviewCreditFiveMinuteGame_',
    "Date.now() - startedMs < 5 * 60 * 1000",
    "const started = actualCount > 0",
    "if (!occupied)",
]
for x in required:
    if x not in s:
        raise SystemExit('missing patched marker: ' + x)

p.write_text(s, encoding='utf-8')
