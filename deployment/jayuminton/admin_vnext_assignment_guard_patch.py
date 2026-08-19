#!/usr/bin/env python3
"""Admin-only auto-assignment hardening. Never edits/deploys user frontend."""
from pathlib import Path
import sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('source-snapshot/current-main')
p=root/'Code.js'; s=p.read_text(encoding='utf-8')

def rep(a,b,label):
 global s
 if a not in s: raise SystemExit(label+' anchor not found')
 s=s.replace(a,b,1)

# Pair history previously recorded only pairs touching a new entrant.  For a four-person
# game we need one history event for all six pairs, otherwise repeated fixed occupants
# can escape the third-game guard.
old="""function recordCourtEntryPairs_(courtNo, entrantIds, finalCourtIds) {
  entrantIds=normalizeIds_(entrantIds); finalCourtIds=normalizeIds_(finalCourtIds); if(!entrantIds.length)return;
  const keys=[]; entrantIds.forEach(function(a){finalCourtIds.forEach(function(b){if(a!==b)keys.push(pairKey_(a,b));});});
  keys.sort(); const unique=keys.filter(function(v,i,a){return i===0||v!==a[i-1];});
  SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_PAIR_HISTORY).appendRow([new Date(),String(courtNo),finalCourtIds.join(','),unique.join(',')]);
}"""
new="""function recordCourtEntryPairs_(courtNo, entrantIds, finalCourtIds) {
  entrantIds=normalizeIds_(entrantIds); finalCourtIds=normalizeIds_(finalCourtIds); if(!entrantIds.length)return;
  const keys=[];
  for(let i=0;i<finalCourtIds.length;i++) for(let j=i+1;j<finalCourtIds.length;j++) keys.push(pairKey_(finalCourtIds[i],finalCourtIds[j]));
  SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_PAIR_HISTORY).appendRow([new Date(),String(courtNo),finalCourtIds.join(','),keys.join(',')]);
}"""
if old in s:
 s=s.replace(old,new,1)
elif 'for(let i=0;i<finalCourtIds.length;i++) for(let j=i+1;j<finalCourtIds.length;j++)' not in s:
 start=s.find('function recordCourtEntryPairs_(')
 end=s.find('\nfunction ',start+1)
 if start<0 or end<0: raise SystemExit('recordCourtEntryPairs_ function boundary not found')
 s=s[:start]+new+'\n'+s[end:]

# Prefer fair skill patterns in this order: 2 skilled + 2 developing, then all-skilled
# or all-developing.  1/3 splits are allowed only when needed.
old="""  if(maxPair>=2) score+=100000; // avoid a third shared game whenever another valid group exists
  score+=totalPair*1000;
  if(ids.length===4 && !(skilled===0||skilled===2||skilled===4)) score+=300;
  score+=games;"""
new="""  if(maxPair>=2) score+=1000000; // third shared game is the strongest avoidable penalty
  score+=totalPair*1000;
  if(ids.length===4) {
    if(skilled===2) score+=0;
    else if(skilled===0||skilled===4) score+=80;
    else score+=400;
  }
  // Among otherwise similar groups, favor members who have played fewer games.
  score+=games*5;"""
if old in s:
 s=s.replace(old,new,1)
elif 'score+=1000000' not in s:
 raise SystemExit('fairness score implementation missing')

# Bundle integrity must include bundle mates in the active candidate universe. A bundled
# pair is never silently split by auto assignment.
old="""  const pool=members.filter(function(m){return m.status==='active'&&fixedIds.indexOf(m.id)<0;}).map(function(m){return m.id;});"""
new="""  const pool=members.filter(function(m){return m.status==='active'&&fixedIds.indexOf(m.id)<0;}).map(function(m){return m.id;});
  const activeSet={}; fixedIds.concat(pool).forEach(function(id){activeSet[id]=true;});
  Object.keys(map).forEach(function(id){
    const m=map[id];
    if(!m||!m.bundleId||!activeSet[id]) return;
    const mates=Object.keys(map).filter(function(k){return map[k].bundleId===m.bundleId;});
    if(mates.some(function(k){return !activeSet[k];})) delete activeSet[id];
  });"""
if 'const activeSet={};' in s:
 pass
elif old in s:
 s=s.replace(old,new,1)
else:
 raise SystemExit('bundle active universe implementation missing')

# Apply activeSet to candidate walk so a temporarily unavailable bundle mate prevents
# the other member from being auto-picked alone.
old="""    for(let i=start;i<pool.length;i++){picked.push(pool[i]);walk(i+1,picked);picked.pop();}"""
new="""    for(let i=start;i<pool.length;i++){if(!activeSet[pool[i]])continue;picked.push(pool[i]);walk(i+1,picked);picked.pop();}"""
if 'if(!activeSet[pool[i]])continue' in s:
 pass
elif old in s:
 s=s.replace(old,new,1)
else:
 raise SystemExit('bundle candidate filter implementation missing')

p.write_text(s,encoding='utf-8')
print('admin vNext assignment fairness guard patch prepared')
