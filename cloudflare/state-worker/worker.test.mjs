import assert from 'node:assert/strict';
import { emptyState, normalizeState, finishCourtMutation, moveMutation, swapMutation } from './worker.js';

function fixture() {
  const state = emptyState();
  state.members = Array.from({ length: 17 }, (_, i) => ({ id: String(i + 1), name: `회원${i + 1}`, games: 0, status: 'active' }));
  state.courts['1'] = ['1', '2'];
  state.waitGroups = [['3', '4', '5', '6'], ['7', '8', '9', '10'], ['11'], ['12'], ['13']];
  return normalizeState(state);
}

{
  const { state, event } = finishCourtMutation(fixture(), 1, '2026-08-22T00:00:00.000Z');
  assert.deepEqual(state.courts['1'], ['3', '4', '5', '6']);
  assert.deepEqual(state.waitGroups, [['7', '8', '9', '10'], ['11'], ['12'], ['13'], []]);
  assert.deepEqual(event.finished, ['1', '2']);
  assert.deepEqual(event.courtEntrants.map(x => x.id), ['3', '4', '5', '6']);
  assert.deepEqual(event.wait1Entrants.map(x => x.id), ['7', '8', '9', '10']);
  assert.equal(state.members.find(x => x.id === '3').games, 1);
  assert.equal(state.members.find(x => x.id === '7').games, 0);
}
{
  const state = fixture(); state.courts['2'] = [];
  assert.deepEqual(finishCourtMutation(state, 2).state.courts['2'], ['3', '4', '5', '6']);
}
{
  const result = moveMutation(fixture(), ['7'], { type: 'court', key: '3' });
  assert.deepEqual(result.state.courts['3'], ['7']);
  assert.equal(result.state.waitGroups.flat().includes('7'), false);
  assert.equal(result.state.members.find(x => x.id === '7').games, 1);
}
{
  const result = swapMutation(fixture(), ['1', '2'], ['7', '8']);
  assert.deepEqual(result.state.courts['1'], ['7', '8']);
  assert.deepEqual(result.state.waitGroups[1], ['1', '2', '9', '10']);
  assert.equal(result.state.members.find(x => x.id === '7').games, 1);
}
{
  const state = fixture(); state.waitGroups[0].push('1');
  assert.equal(normalizeState(state).waitGroups.flat().includes('1'), false);
}
console.log('STATE_WORKER_CORE_TESTS_OK');
