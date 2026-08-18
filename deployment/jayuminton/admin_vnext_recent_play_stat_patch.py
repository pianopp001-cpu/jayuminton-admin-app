#!/usr/bin/env python3
"""Admin-only derived member statistic: recent play time from PairHistory."""
from pathlib import Path
import re,sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('source-snapshot/current-main')
p=root/'Code.js'; s=p.read_text(encoding='utf-8')

helper=r'''\nfunction readLastPlayedAtMap_() {\n  const out = {};\n  const sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_PAIR_HISTORY);\n  if (!sh || sh.getLastRow() < 2) return out;\n  sh.getRange(2, 1, sh.getLastRow() - 1, 3).getValues().forEach(function(row) {\n    const time = row[0];\n    const ids = String(row[2] || '').split(',').filter(Boolean);\n    if (!time || !ids.length) return;\n    ids.forEach(function(id) {\n      const prev = out[id];\n      if (!prev || new Date(time).getTime() > new Date(prev).getTime()) out[id] = new Date(time).toISOString();\n    });\n  });\n  return out;\n}\n'''
if 'function readLastPlayedAtMap_()' not in s:
    marker='function getPublicState() {'
    if marker not in s: raise SystemExit('getPublicState anchor not found')
    s=s.replace(marker,helper+'\n'+marker,1)

# Expose the derived statistic without adding another spreadsheet column.
# This deliberately uses regex so it survives small formatting differences in the
# existing member map while remaining fail-fast if the games property disappears.
pattern=r"(function getPublicState\(\)\s*\{[\s\S]*?const members = readMembers_\(\);)"
m=re.search(pattern,s)
if not m: raise SystemExit('getPublicState/readMembers anchor not found')
segment=m.group(1)
if 'const lastPlayedAtMap = readLastPlayedAtMap_();' not in s:
    s=s[:m.end(1)]+'\n  const lastPlayedAtMap = readLastPlayedAtMap_();'+s[m.end(1):]

# Add property after the first member games field inside getPublicState.
start=s.find('function getPublicState()')
end=s.find('\nfunction ',start+10)
if end<0: end=len(s)
chunk=s[start:end]
if 'lastPlayedAt:' not in chunk:
    chunk2=re.sub(r"(games:\s*Number\([^\n]+\))", r"\1,\n        lastPlayedAt: lastPlayedAtMap[member.id] || ''", chunk, count=1)
    if chunk2==chunk: raise SystemExit('games property anchor not found in getPublicState')
    s=s[:start]+chunk2+s[end:]

p.write_text(s,encoding='utf-8')
print('admin vNext recent-play statistic patch prepared')
