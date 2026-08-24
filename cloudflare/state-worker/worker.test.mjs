import assert from 'node:assert/strict';
import { emptyState, normalizeState, finishCourtMutation, moveMutation, swapMutation, swapLocationsMutation, autoAssignMutation, upsertMemberMutation, setMemberStatusMutation, setBundleMutation, sendMemberMessageMutation, adjustGamesMutation, requestSwapMutation, respondSwapMutation, cancelSwapMutation, publicState, adminState, assignmentTransitions } from './worker.js';

function fixture() {
  const state = emptyState();
  state.members = Array.from({ length: 17 }, (_, i) => ({ id: String(i + 1), name: `회원${i + 1}`, games: 0, status: 'active' }));
  state.courts['1'] = ['1', '2'];
  state.waitGroups = [['3', '4', '5', '6'], ['7', '8', '9', '10'], ['11'], ['12'], ['13']];
  return normalizeState(state);
}
{
  const grouped = setBundleMutation(fixture(), ['7', '8', '9']);
  const members = grouped.state.members.filter(m => ['7', '8', '9'].includes(m.id));
  assert.equal(members.every(m => m.teamLabel === '팀 1'), true);
  assert.equal(new Set(members.map(m => m.bundleId)).size, 1);
  assert.equal(publicState(grouped.state, '7').members.find(m => m.id === '7').teamLabel, '팀 1');
}
{
  const sent = sendMemberMessageMutation(fixture(), ['7', '8'], '라켓을 준비해 주세요.');
  assert.equal(publicState(sent.state, '7').memberMessages[0].text, '라켓을 준비해 주세요.');
  assert.equal(publicState(sent.state, '9').memberMessages.length, 0);
  assert.equal(sent.event.type, 'member_message_sent');
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
  const { state: finished, event } = finishCourtMutation(state, 2);
  assert.deepEqual(finished.courts['2'], ['3', '4', '5', '6']);
  assert.deepEqual(finished.waitGroups, [['7', '8', '9', '10'], ['11'], ['12'], ['13'], []]);
  assert.deepEqual(event.finished, []);
  assert.deepEqual(event.courtEntrants.map(x => x.id), ['3', '4', '5', '6']);
  assert.deepEqual(event.wait1Entrants.map(x => x.id), ['7', '8', '9', '10']);
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
  const state = fixture();
  state.courts['1'] = ['1', '2', '14'];
  const result = swapMutation(state, ['1', '2', '14'], ['7', '8', '9']);
  assert.deepEqual(result.state.courts['1'], ['7', '8', '9']);
  assert.deepEqual(result.state.waitGroups[1], ['1', '2', '14', '10']);
}
{
  const state = fixture();
  state.courts['2'] = ['14', '15', '16', '17'];
  const result = swapLocationsMutation(state, { type: 'court', key: '1' }, { type: 'court', key: '2' });
  assert.deepEqual(result.state.courts['1'], ['14', '15', '16', '17']);
  assert.deepEqual(result.state.courts['2'], ['1', '2']);
}
{
  const result = swapLocationsMutation(fixture(), { type: 'wait', key: '1' }, { type: 'wait', key: '3' });
  assert.deepEqual(result.state.waitGroups[0], ['11']);
  assert.deepEqual(result.state.waitGroups[2], ['3', '4', '5', '6']);
}
{
  assert.throws(() => swapMutation(fixture(), ['1', '2'], ['7']), /equal_swap_groups_required/);
}
{
  const state = fixture(); state.waitGroups[0].push('1');
  assert.equal(normalizeState(state).waitGroups.flat().includes('1'), false);
}
{
  const result = autoAssignMutation(fixture(), ['14', '15', '16', '17'], [{ type: 'court', key: '2' }]);
  assert.deepEqual(result.state.courts['2'], ['14', '15', '16', '17']);
  assert.equal(result.event.assigned[0].memberIds.length, 4);
}
{
  // 사용자 자기배정이 먼저 저장된 경우, 관리자의 오래된 자동배정 후보 목록이 그 자리를 덮어쓰면 안 된다.
  const userFirst = moveMutation(fixture(), ['14'], { type: 'wait', key: '5' }).state;
  const adminAfter = autoAssignMutation(userFirst, ['14', '15', '16', '17'], [{ type: 'court', key: '2' }]);
  assert.deepEqual(adminAfter.state.waitGroups[4], ['13', '14']);
  assert.deepEqual(adminAfter.state.courts['2'], ['15', '16', '17']);
  assert.equal(adminAfter.state.members.find(x => x.id === '14').games, 0);
}
{
  const created = upsertMemberMutation(fixture(), { id: '18', name: '신규회원', gender: '여', isNew: true });
  assert.equal(created.state.members.find(m => m.id === '18').status, 'active');
  assert.equal(created.state.members.find(m => m.id === '18').gender, 'female');
  const resting = setMemberStatusMutation(created.state, ['18'], 'rest');
  assert.equal(resting.state.members.find(m => m.id === '18').status, 'rest');
  const counted = adjustGamesMutation(resting.state, ['18'], 1);
  assert.equal(counted.state.members.find(m => m.id === '18').games, 1);
  const away = setMemberStatusMutation(counted.state, ['18'], 'away');
  assert.equal(away.state.members.find(m => m.id === '18').status, 'away');
}
{
  const requested = requestSwapMutation(fixture(), '1', '7', 1000);
  const cancelled = cancelSwapMutation(requested.state, '1');
  assert.equal(cancelled.state.swapRequests[0].status, 'cancelled');
}
{
  const requested = requestSwapMutation(fixture(), '1', '7', 1000);
  assert.equal(requested.event.request.expiresAt, 301000);
  const accepted = respondSwapMutation(requested.state, requested.event.request.id, '7', true, 2000);
  assert.equal(accepted.event.type, 'swap_accepted');
  assert.equal(accepted.state.courts['1'].includes('7'), true);
}
{
  const requested = requestSwapMutation(fixture(), '1', '7', 1000);
  const expired = respondSwapMutation(requested.state, requested.event.request.id, '7', true, 301001);
  assert.equal(expired.event.type, 'swap_expired');
  assert.equal(expired.state.courts['1'].includes('1'), true);
}
{
  const state = fixture(); state.settings.memberPassword = 'secret'; state.actionHistory = [{ operationId: 'private' }];
  const safe = publicState(state, '1');
  assert.equal('memberPassword' in safe.settings, false);
  assert.equal('actionHistory' in safe, false);
}
{
  const state = fixture(); state.settings.adminPin = '1234';
  const safe = adminState(state);
  assert.equal('adminPin' in safe.settings, false);
}
{
  const before = fixture(); const after = finishCourtMutation(before, 1).state;
  const transitions = assignmentTransitions(before, after);
  assert.deepEqual(transitions.courtGroups['1'].map(m => m.id), ['3', '4', '5', '6']);
  assert.deepEqual(transitions.wait1.map(m => m.id), ['7', '8', '9', '10']);
  assert.equal(transitions.courtGroups['2'].length, 0);
}
console.log('STATE_WORKER_CORE_TESTS_OK');
