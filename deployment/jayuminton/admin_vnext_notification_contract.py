#!/usr/bin/env python3
"""Admin-only notification contract. No user frontend edits or deployment."""
from pathlib import Path
import sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('source-snapshot/current-main')
p=root/'Code.js'; s=p.read_text(encoding='utf-8')
needle="const SHEET_PAIR_HISTORY = 'PairHistory';"
if needle not in s: raise SystemExit('pair history anchor missing')
insert="""
const ADMIN_VNEXT_EVENTS = Object.freeze({
  COURT_PROMOTED: 'COURT_PROMOTED',
  COURT_FINISHED: 'COURT_FINISHED'
});
function buildAdminVnextEvent_(type, memberIds, courtNo) {
  return {type:String(type||''), memberIds:normalizeIds_(memberIds), courtNo:String(courtNo||''), at:new Date().toISOString()};
}
"""
if 'const ADMIN_VNEXT_EVENTS' not in s: s=s.replace(needle,needle+insert,1)
p.write_text(s,encoding='utf-8')
print('admin vNext notification contract prepared')
