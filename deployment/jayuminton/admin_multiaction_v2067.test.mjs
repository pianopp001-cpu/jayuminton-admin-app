import assert from 'node:assert/strict';
import fs from 'node:fs';

const source = fs.readFileSync(
  new URL('./admin_card_interaction_v2042.js', import.meta.url),
  'utf8',
);

for (const marker of [
  '__JAYUMINTON_ADMIN_CONTINUE_SELECTION_V2067__',
  '__JAYUMINTON_ADMIN_FAST_MULTI_MOVE_V2067__',
  'pointer-events:none',
  'pointer-events:auto',
  'selected.length<4',
  'applyMoveOrSwapLocally',
  '명 이동 저장 중',
  'selected.length===2&&samePlace(selected)',
  "if(ids.length!==2)throw new Error('팀설정은 2명 선택일 때만 사용할 수 있습니다.')",
]) {
  assert.ok(source.includes(marker), `missing admin multi-action behavior: ${marker}`);
}
assert.doesNotMatch(source,/selected\.length!==2/);

const clickHandler = source.slice(
  source.indexOf('function onClick(event)'),
  source.indexOf('async function refreshTeams'),
);
assert.ok(clickHandler.includes('if(same){if(selected.length<4){selected.push(id);renderGreen();renderPanel();return;}'));
assert.ok(clickHandler.includes('if(sourceEmpty&&sourceEmpty.closest(\'#adminApp\')&&selected.length)'));
assert.ok(clickHandler.includes('if(selected.length>=2&&selected.length<=4){beginAutoTarget'));

const activeHandler = source.slice(
  source.indexOf('async function moveSelectedToActive(ids)'),
  source.indexOf('async function saveTeam(ids)'),
);
assert.ok(activeHandler.includes('ids.length<2||ids.length>4||!samePlace(ids)'),
  'court-assignment waiting action must accept 2-4 selected members');

const moveHandler = source.slice(
  source.indexOf('async function executeMove()'),
  source.indexOf('function addTarget('),
);
assert.ok(moveHandler.indexOf('applyMoveOrSwapLocally') < moveHandler.indexOf("await rpc('moveOrSwapMember'"),
  'optimistic render must happen before the network wait');

console.log('ADMIN_MULTI_ACTION_V2067_TEST_OK');
