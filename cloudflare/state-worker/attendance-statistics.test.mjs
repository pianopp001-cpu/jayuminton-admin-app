import assert from 'node:assert/strict';
import fs from 'node:fs';
import { emptyState, normalizeState, setMemberStatusMutation, setMemberKokInactiveMutation, adminState } from './worker.js';

const base = emptyState();
base.members = [
  { id: '1', name: '도착회원', games: 3, status: 'before', kokInactive: false },
  { id: '2', name: '휴식회원', games: 1, status: 'rest', kokInactive: false },
];

const arrivedAt = '2026-09-08T09:05:00.000Z';
const departedAt = '2026-09-08T13:17:00.000Z';

// before -> active must NOT create arrival anymore.
const movedToActive = setMemberStatusMutation(normalizeState(base), ['1'], 'active', '2026-09-08T08:55:00.000Z');
assert.equal(movedToActive.state.members.find(m => m.id === '1').arrivedAt, undefined);
assert.deepEqual(movedToActive.event.arrivedMemberIds, []);

// 콕제출체크 완료(false -> true) is the official attendance clock-in.
const arrived = setMemberKokInactiveMutation(movedToActive.state, ['1'], true, arrivedAt);
const arrivedMember = arrived.state.members.find(m => m.id === '1');
assert.equal(arrivedMember.kokInactive, true);
assert.equal(arrivedMember.arrivedAt, arrivedAt);
assert.equal(arrivedMember.departedAt, '');
assert.deepEqual(arrived.event.arrivedMemberIds, ['1']);

// Repeating 완료 without a 복귀 must be idempotent and keep the original time.
const repeated = setMemberKokInactiveMutation(arrived.state, ['1'], true, '2026-09-08T09:10:00.000Z');
assert.equal(repeated.state.members.find(m => m.id === '1').arrivedAt, arrivedAt);
assert.deepEqual(repeated.event.arrivedMemberIds, []);

// 코트배정 대기(active assignment pool) -> 귀가 records departure.
const departed = setMemberStatusMutation(arrived.state, ['1'], 'away', departedAt);
const departedMember = departed.state.members.find(m => m.id === '1');
assert.equal(departedMember.status, 'away');
assert.equal(departedMember.arrivedAt, arrivedAt);
assert.equal(departedMember.departedAt, departedAt);
assert.deepEqual(departed.event.departedMemberIds, ['1']);

// A non-assignment-pool status must not create a false departure timestamp.
const restingAway = setMemberStatusMutation(normalizeState(base), ['2'], 'away', departedAt);
assert.equal(restingAway.state.members.find(m => m.id === '2').departedAt, undefined);
assert.deepEqual(restingAway.event.departedMemberIds, []);

// A deliberate 복귀 -> 완료 starts a fresh attendance session and clears stale departure.
const returned = setMemberKokInactiveMutation(departed.state, ['1'], false, '2026-09-09T09:20:00.000Z');
const arrivedAgain = setMemberKokInactiveMutation(returned.state, ['1'], true, '2026-09-09T09:30:00.000Z');
const secondMember = arrivedAgain.state.members.find(m => m.id === '1');
assert.equal(secondMember.arrivedAt, '2026-09-09T09:30:00.000Z');
assert.equal(secondMember.departedAt, '');

// Admin state must expose the attendance fields to the statistics UI.
const safe = adminState(departed.state).members.find(m => m.id === '1');
assert.equal(safe.arrivedAt, arrivedAt);
assert.equal(safe.departedAt, departedAt);

// The pair-statistics API contract must return both attendance timestamps.
const entry = fs.readFileSync(new URL('./worker-md-entry.js', import.meta.url), 'utf8');
assert.ok(entry.includes('JAYUMINTON_ATTENDANCE_STATS_RESPONSE_V2'));
assert.ok(entry.includes("arrivedAt: String(m.arrivedAt || '')"));
assert.ok(entry.includes("departedAt: String(m.departedAt || '')"));

console.log('ATTENDANCE_STATISTICS_V2_KOK_ARRIVAL_OK');
