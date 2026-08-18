#!/usr/bin/env python3
"""Admin vNext repairData compatibility patch. Run after the backend patch."""
from pathlib import Path
import sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('source-snapshot/current-main')
p=root/'Code.js'
s=p.read_text(encoding='utf-8')
old="""  Object.keys(courts).forEach(function(key) {
    markCourtStartedIfFull_(courts, startedAt, key);
  });"""
new="""  Object.keys(courts).forEach(function(key) {
    // Admin vNext: an occupied court is already in progress even with fewer than 4 players.
    if ((courts[key] || []).length > 0) {
      if (!startedAt[key]) startedAt[key] = new Date().toISOString();
    } else {
      startedAt[key] = '';
    }
  });"""
if old not in s:
    raise SystemExit('repairData court-start anchor not found')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('admin vNext repairData partial-court rule patched')
