#!/usr/bin/env python3
"""Admin-only derived member statistic: recent play time from PairHistory."""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
path = root / 'Code.js'
source = path.read_text(encoding='utf-8')

helper = r"""
function readLastPlayedAtMap_() {
  const out = {};
  const sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_PAIR_HISTORY);
  if (!sh || sh.getLastRow() < 2) return out;
  sh.getRange(2, 1, sh.getLastRow() - 1, 3).getValues().forEach(function(row) {
    const time = row[0];
    const ids = String(row[2] || '').split(',').filter(Boolean);
    if (!time || !ids.length) return;
    ids.forEach(function(id) {
      const prev = out[id];
      if (!prev || new Date(time).getTime() > new Date(prev).getTime()) {
        out[id] = new Date(time).toISOString();
      }
    });
  });
  return out;
}

"""

marker = 'function getPublicState() {'
if marker not in source:
    raise SystemExit('getPublicState anchor not found')
if 'function readLastPlayedAtMap_()' not in source:
    source = source.replace(marker, helper + '\n' + marker, 1)

pattern = r"(function getPublicState\(\)\s*\{[\s\S]*?const members = readMembers_\(\);)"
match = re.search(pattern, source)
if not match:
    raise SystemExit('getPublicState/readMembers anchor not found')

injection = """
  const lastPlayedAtMap = readLastPlayedAtMap_();
  members.forEach(function(member) {
    member.lastPlayedAt = lastPlayedAtMap[member.id] || '';
  });"""

get_public_start = source.find('function getPublicState()')
get_public_end = source.find('\nfunction ', get_public_start + 10)
if get_public_end < 0:
    get_public_end = len(source)
get_public_chunk = source[get_public_start:get_public_end]

if 'member.lastPlayedAt = lastPlayedAtMap[member.id]' not in get_public_chunk:
    source = source[:match.end(1)] + injection + source[match.end(1):]

updated_start = source.find('function getPublicState()')
updated_end = source.find('\nfunction ', updated_start + 10)
updated_chunk = source[updated_start:updated_end if updated_end >= 0 else len(source)]
for required in [
    'const lastPlayedAtMap = readLastPlayedAtMap_();',
    "member.lastPlayedAt = lastPlayedAtMap[member.id] || '';"
]:
    if required not in updated_chunk:
        raise SystemExit('recent-play statistic injection missing: ' + required)

path.write_text(source, encoding='utf-8')
print('admin vNext recent-play statistic patch prepared')
