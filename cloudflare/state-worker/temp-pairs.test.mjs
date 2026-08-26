import assert from 'node:assert/strict';
import {
  emptyState,
  normalizeState,
  setTempPairsMutation,
  moveMutation,
  publicState,
} from './worker.js';

function fixture() {
  const state = emptyState();
  state.members = Array.from({ length: 12 }, (_, i) => ({
    id: String(i + 1), name: `회원${i + 1}`, games: 0, status: 'active'
  }));
  state.courts['1'] = ['1', '2', '3', '4'];
  state.waitGroups = [['5', '6', '7', '8'], ['9', '10', '11', '12']];
  return normalizeState(state);
}

// Same wait group: only the two explicitly clicked people are the one-shot team.
// Their seats MUST NOT move.
{
  const result = setTempPairsMutation(fixture(), [{ pairA: ['5','7'], zone: 'wait', createdAt: 1 }]);
  assert.deepEqual(result.state.waitGroups[0], ['5','6','7','8']);
  assert.deepEqual(result.state.tempPairs[0].pairA, ['5','7']);
  assert.deepEqual(result.state.tempPairs[0].pairB, []);
  assert.deepEqual(publicState(result.state, '5').tempPairs, result.state.tempPairs);
}

// Same court: one-shot pairing also never changes the existing seat order.
{
  const result = setTempPairsMutation(fixture(), [{ pairA: ['1','3'], zone: 'court', createdAt: 1 }]);
  assert.deepEqual(result.state.courts['1'], ['1','2','3','4']);
  assert.deepEqual(result.state.tempPairs[0].pairA, ['1','3']);
}

// Moving either paired member across wait/court boundaries removes only the
// one-shot overlay. Permanent bundle/team fields are independent.
{
  const paired = setTempPairsMutation(fixture(), [{ pairA: ['5','7'], zone: 'wait', createdAt: 1 }]).state;
  const moved = moveMutation(paired, ['5'], { type: 'court', key: '2' }).state;
  assert.deepEqual(moved.tempPairs, []);
  assert.deepEqual(publicState(moved, '7').tempPairs, []);
}

// Permanent team survives one-shot pairing unchanged.
{
  const state = fixture();
  state.members.find(m => m.id === '5').teamLabel = '팀 1';
  state.members.find(m => m.id === '5').bundleId = 'fixed-team-1';
  state.members.find(m => m.id === '7').teamLabel = '팀 1';
  state.members.find(m => m.id === '7').bundleId = 'fixed-team-1';
  const result = setTempPairsMutation(state, [{ pairA: ['5','6'], zone: 'wait', createdAt: 1 }]);
  assert.equal(result.state.members.find(m => m.id === '5').teamLabel, '팀 1');
  assert.equal(result.state.members.find(m => m.id === '5').bundleId, 'fixed-team-1');
  assert.deepEqual(result.state.tempPairs[0].pairA, ['5','6']);
}

// Invalid/duplicate pairs are discarded.
{
  const result = setTempPairsMutation(fixture(), [
    { pairA: ['5','5'], zone: 'wait' },
    { pairA: ['5','7'], zone: 'invalid' },
  ]);
  assert.deepEqual(result.state.tempPairs, []);
}

console.log('STATE_WORKER_TEMP_PAIRS_TESTS_OK pairAOnly=true reorder=false');
