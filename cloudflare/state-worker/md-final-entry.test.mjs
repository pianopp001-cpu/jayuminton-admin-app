import fs from 'node:fs';
import assert from 'node:assert/strict';

const finalEntry = fs.readFileSync(new URL('./worker-md-final-entry.js', import.meta.url), 'utf8');
const compatEntry = fs.readFileSync(new URL('./worker-md-compat-entry.js', import.meta.url), 'utf8');
const mdEntry = fs.readFileSync(new URL('./worker-md-entry.js', import.meta.url), 'utf8');
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
assert.ok(mdEntry.includes("body.action === 'autoAssign'"), 'MD autoAssign entry missing');
assert.ok(mdEntry.includes("body.name === 'getPairStatistics'"), 'pair statistics compat RPC missing');

console.log('MD_FINAL_ENTRY_CONTRACT_OK');
