import fs from 'node:fs';
import assert from 'node:assert/strict';
import { eligibleAutoAssignPool, selectValidFill, targetArray } from './worker-md-entry.js';

const finalEntry = fs.readFileSync(new URL('./worker-md-final-entry.js', import.meta.url), 'utf8');
const compatEntry = fs.readFileSync(new URL('./worker-md-compat-entry.js', import.meta.url), 'utf8');
const mdEntry = fs.readFileSync(new URL('./worker-md-entry.js', import.meta.url), 'utf8');
const schema = fs.readFileSync(new URL('./schema.sql', import.meta.url), 'utf8');
const wrangler = fs.readFileSync(new URL('./wrangler.toml.template', import.meta.url), 'utf8');

for (const name of ['memberRequestWaitSwap','memberGetWaitSwapRequest','memberRespondWaitSwap']) {
  assert.ok(finalEntry.includes(name), `missing legacy wait-swap bridge: ${name}`);
}
assert.ok(finalEntry.includes("action:'requestSwap'"), 'requestSwap bridge missing');
assert.ok(finalEntry.includes("action:'respondSwap'"), 'respondSwap bridge missing');
assert.ok(finalEntry.includes("url.pathname='/api/member/state'"), 'member state bridge missing');
assert.ok(wrangler.includes('main = "worker-md-final-entry.js"'), 'wrangler does not deploy final entry');

for (const name of ['assignWaitGroupToCourt','autoFillCourt','autoFillWaitGroup','moveOrSwapMember','swapCourts','swapWaitGroups','removeFromCourt','removeFromWaitGroup','adjustCourtMembers','adjustWaitGroupMembers']) {
  assert.ok(compatEntry.includes(name), `missing admin compat RPC: ${name}`);
}
assert.ok(mdEntry.includes('pair_stats'), 'D1 pair statistics missing');
assert.ok(schema.includes('CREATE TABLE IF NOT EXISTS pair_stats'), 'pair_stats missing from persistent schema');
assert.ok(mdEntry.includes("body.action === 'autoAssign'"), 'MD autoAssign entry missing');
assert.ok(mdEntry.includes("body.name === 'getPairStatistics'"), 'pair statistics compat RPC missing');
assert.ok(mdEntry.includes('pool.length <= free'), 'MD last-remainder autoassign rule missing');
assert.ok(mdEntry.includes('[[2, 2], [4, 0], [0, 4]]'), 'MD doubles composition rules missing');

const member=(id,gender,status='active')=>({id,name:id,gender,status,games:0});
const autoState={
  members:[member('wm','male','queued'),member('m1','male'),member('m2','male'),member('m3','male'),member('f1','female'),member('f2','female'),member('rest','male','rest')],
  courts:{'1':[],'2':[],'3':[],'4':[]},
  waitGroups:[['wm'],[],[],[],[]],
};
assert.deepEqual(targetArray(autoState,{type:'wait',key:'1'}),['wm'],'wait destination occupancy is ignored');
const autoPool=eligibleAutoAssignPool(autoState,[]);
assert.ok(autoPool.includes('m1')&&autoPool.includes('f1'),'automatic candidate fallback is empty');
assert.ok(!autoPool.includes('wm')&&!autoPool.includes('rest'),'occupied/excluded members leaked into automatic pool');
const autoById=new Map(autoState.members.map(m=>[m.id,m]));
assert.equal(selectValidFill(autoState,autoPool,{type:'wait',key:'1'},autoById).length,3,'wait group free-position count is wrong');

console.log('MD_FINAL_ENTRY_CONTRACT_OK');
