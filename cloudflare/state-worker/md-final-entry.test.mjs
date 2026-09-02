import fs from 'node:fs';
import assert from 'node:assert/strict';
import { eligibleAutoAssignPool, selectValidFill, targetArray } from './worker-md-entry.js';
import { liveIdsInGroup } from './worker-md-compat-entry.js';
import { normalizeMemberMemoArgs } from './worker-md-final-entry.js';

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
assert.deepEqual(normalizeMemberMemoArgs(['member-7','공개 메모']), [null,'member-7','공개 메모'], 'two-slot member memo call must be normalized');
assert.deepEqual(normalizeMemberMemoArgs([null,'member-7','공개 메모']), [null,'member-7','공개 메모'], 'three-slot member memo call must stay stable');
assert.ok(finalEntry.includes("String(body.name||'')==='updateMyProfile'"), 'member memo backend normalization route missing');

for (const name of ['assignWaitGroupToCourt','autoFillCourt','autoFillWaitGroup','moveOrSwapMember','swapCourts','swapWaitGroups','swapCourtAndWaitGroup','removeFromCourt','removeFromWaitGroup','adjustCourtMembers','adjustWaitGroupMembers']) {
  assert.ok(compatEntry.includes(name), `missing admin compat RPC: ${name}`);
}
assert.ok(compatEntry.includes('liveIdsInGroup(sourceA,body.idsA)'), 'court stale-selection guard missing');
assert.ok(compatEntry.includes('liveIdsInGroup(sourceB,body.idsB)'), 'second-source stale-selection guard missing');
// Court<->wait whole-group swap (clicking a court header then a wait-group header, or vice
// versa) used to be blocked with "코트끼리만/대기조끼리만 전체 교환할 수 있습니다." -- it must
// now be handled as its own kind, restricted to the full-swap action only (not partial adjust).
assert.ok(compatEntry.includes("kind==='cross'"), 'court<->wait whole-group swap kind missing');
assert.ok(compatEntry.includes("if(action!=='mdSwapLocations')throw new Error('invalid_location_kind')"), 'cross swap must stay restricted to full swaps, not partial member adjust');
assert.ok(compatEntry.includes("if(![1,2,3,4].includes(a))throw new Error('invalid_court')") || compatEntry.match(/kind==='cross'[\s\S]{0,400}invalid_court/), 'cross swap must validate the court index');
assert.ok(compatEntry.match(/kind==='cross'[\s\S]{0,400}invalid_wait_group/), 'cross swap must validate the wait-group index');
assert.ok(compatEntry.match(/kind==='cross'[\s\S]{0,1200}games:Math\.max\(0,\(Number\(m\.games\)\|\|0\)\+1\)/), 'members entering a court from a wait group via cross swap must gain a game credit like every other court-entry path');
assert.ok(mdEntry.includes('pair_stats'), 'D1 pair statistics missing');
assert.ok(schema.includes('CREATE TABLE IF NOT EXISTS pair_stats'), 'pair_stats missing from persistent schema');
assert.ok(mdEntry.includes("body.action === 'autoAssign'"), 'MD autoAssign entry missing');
assert.ok(mdEntry.includes("body.name === 'getPairStatistics'"), 'pair statistics compat RPC missing');
assert.ok(mdEntry.includes('pool.length <= free'), 'MD last-remainder autoassign rule missing');
assert.ok(mdEntry.includes('[[2, 2], [4, 0], [0, 4]]'), 'MD doubles composition rules missing');

const moveOneBlock = mdEntry.slice(mdEntry.indexOf('async function moveOne('), mdEntry.indexOf('async function mdAutoAssign('));
assert.ok(moveOneBlock.includes("action: 'moveMembers'"), 'autoassign moveOne action missing');
assert.equal(moveOneBlock.includes('recordPairTransitions('), false, 'autoassign pair statistics would be recorded twice');
const outerPairWrites = (mdEntry.match(/if \(before && out\?\.state\) await recordPairTransitions\(env, before, out\.state\);/g) || []).length;
assert.equal(outerPairWrites, 2, 'admin and compat autoassign must each record pair statistics exactly once');

assert.ok(mdEntry.includes("await env.DB.prepare('DELETE FROM pair_stats').run();"), 'operation reset must clear pair statistics');
assert.ok(mdEntry.includes("if (packet?.ok && options.clearPairStats) await clearPairStatistics(env);"), 'pair statistics must clear only after a successful core reset response');
assert.ok(mdEntry.includes("{ clearPairStats: body.action === 'resetAll' }"), 'direct admin resetAll pair-stat cleanup missing');
assert.ok(mdEntry.includes("const isRestore = body.name === 'restoreManualBackup';"), 'restore must have an explicit pair-stat consistency path');
assert.ok(mdEntry.includes('isRestore ? null : before'), 'restore must not record before/after location changes as new pair games');
assert.ok(mdEntry.includes("body.name === 'resetAllOperationData' || isRestore"), 'successful restore must clear stale pair statistics because backup state does not contain the separate pair_stats table');
const clearPairCalls = (mdEntry.match(/clearPairStats:/g) || []).length;
assert.equal(clearPairCalls, 2, 'pair-stat cleanup options must remain limited to admin reset and compat reset/restore handling');

// Administrator selected members from an older screen. If member 14 has since
// moved themself away, the live server group no longer contains 14 and the
// partial swap must skip that stale selection while retaining valid member 15.
assert.deepEqual(liveIdsInGroup(['15','16'], ['14','15','15']), ['15']);
assert.deepEqual(liveIdsInGroup(['7','8','9'], ['8','20']), ['8']);

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