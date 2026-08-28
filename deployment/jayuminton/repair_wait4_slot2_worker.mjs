import fs from 'node:fs';
const path='cloudflare/state-worker/worker.js';
let s=fs.readFileSync(path,'utf8');
const old=`  const occupied = new Set();
  for (const no of ['1', '2', '3', '4']) {
    state.courts[no] = uniqueIds(state.courts[no]).filter(id => !occupied.has(id));
    state.courts[no].forEach(id => occupied.add(id));
  }
  state.waitGroups = state.waitGroups.map(group => uniqueIds(group).filter(id => {
    if (occupied.has(id)) return false;
    occupied.add(id); return true;
  }));`;
const next=`  // Physical slots may only contain IDs that still exist in members.
  // This removes stale/ghost IDs that made a visible empty wait slot return location_full.
  const validMemberIds = new Set(state.members.map(member => String(member?.id || '')).filter(Boolean));
  const occupied = new Set();
  for (const no of ['1', '2', '3', '4']) {
    state.courts[no] = uniqueIds(state.courts[no]).filter(id => validMemberIds.has(id) && !occupied.has(id));
    state.courts[no].forEach(id => occupied.add(id));
  }
  state.waitGroups = state.waitGroups.map(group => uniqueIds(group).filter(id => {
    if (!validMemberIds.has(id) || occupied.has(id)) return false;
    occupied.add(id); return true;
  }));`;
if(!s.includes(old)) throw new Error('normalizeState target block not found');
s=s.replace(old,next);
fs.writeFileSync(path,s);
console.log('wait4 stale occupancy normalization patched');
