import assert from 'node:assert/strict';
import fs from 'node:fs';

const source = fs.readFileSync(
  new URL('./admin_card_interaction_v2042.js', import.meta.url),
  'utf8',
);

for (const marker of [
  '__JAYUMINTON_ADMIN_CONTINUE_SELECTION_V2067__',
  '__JAYUMINTON_ADMIN_FAST_MULTI_MOVE_V2067__',
  '3·4명 계속 선택 가능',
  'pointer-events:none',
  'pointer-events:auto',
  'selected.length<4',
  'applyMoveOrSwapLocally',
  '명 이동 저장 중',
]) {
  assert.ok(source.includes(marker), `missing admin multi-action contract: ${marker}`);
}

const clickHandler = source.slice(
  source.indexOf('function onClick(event)'),
  source.indexOf('async function refreshTeams'),
);
assert.ok(clickHandler.includes('if(same){if(selected.length<4){selected.push(id);renderGreen();renderPanel();return;}'));
assert.ok(clickHandler.includes('if(selected.length===3||selected.length===4){beginAutoTarget'));

const moveHandler = source.slice(
  source.indexOf('async function executeMove()'),
  source.indexOf('function addTarget('),
);
assert.ok(moveHandler.indexOf('applyMoveOrSwapLocally') < moveHandler.indexOf("await rpc('moveOrSwapMember'"),
  'optimistic render must happen before the network wait');

console.log('ADMIN_MULTI_ACTION_V2067_TEST_OK');
