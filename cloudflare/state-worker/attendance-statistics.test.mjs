import assert from 'node:assert/strict';
import fs from 'node:fs';
import { emptyState, normalizeState, setMemberStatusMutation, adminState } from './worker.js';

const base = emptyState();
base.members = [
  { id: '1', name: '도착회원', games: 3, status: 'before' },
  { id: '2', name: '휴식회원', games: 1, status: 'rest' },
];

const arrivedAt = '2026-09-08T09:05:00.000Z';
const departedAt = '2026-09-08T13:17:00.000Z';

const arrived = setMemberStatusMutation(normalizeState(base), ['1'], 'active', arrivedAt);
const arrivedMember = arrived.state.members.find(m => m.id === '1');
assert.equal(arrivedMember.status, 'active');
assert.equal(arrivedMember.arrivedAt, arrivedAt);
assert.equal(arrivedMember.departedAt, '');
assert.deepEqual(arrived.event.arrivedMemberIds, ['1']);
assert.deepEqual(arrived.event.departedMemberIds, []);

const departed = setMemberStatusMutation(arrived.state, ['1'], 'away', departedAt);
const departedMember = departed.state.members.find(m => m.id === '1');
assert.equal(departedMember.status, 'away');
assert.equal(departedMember.arrivedAt, arrivedAt);
assert.equal(departedMember.departedAt, departedAt);
assert.deepEqual(departed.event.arrivedMemberIds, []);
assert.deepEqual(departed.event.departedMemberIds, ['1']);

// A non-assignment-pool status must not create a false departure timestamp.
const restingAway = setMemberStatusMutation(normalizeState(base), ['2'], 'away', departedAt);
assert.equal(restingAway.state.members.find(m => m.id === '2').departedAt, undefined);
assert.deepEqual(restingAway.event.departedMemberIds, []);

// A new before -> active transition starts a fresh attendance session and clears stale departure.
const secondSession = normalizeState(departed.state);
secondSession.members = secondSession.members.map(m => m.id === '1' ? { ...m, status: 'before' } : m);
const arrivedAgain = setMemberStatusMutation(secondSession, ['1'], 'active', '2026-09-09T09:30:00.000Z');
const secondMember = arrivedAgain.state.members.find(m => m.id === '1');
assert.equal(secondMember.arrivedAt, '2026-09-09T09:30:00.000Z');
assert.equal(secondMember.departedAt, '');

// Admin state must expose the attendance fields to the statistics UI.
const safe = adminState(departed.state).members.find(m => m.id === '1');
assert.equal(safe.arrivedAt, arrivedAt);
assert.equal(safe.departedAt, departedAt);

// The pair-statistics API contract must return both attendance timestamps.
const entry = fs.readFileSync(new URL('./worker-md-entry.js', import.meta.url), 'utf8');
assert.ok(entry.includes('JAYUMINTON_ATTENDANCE_STATS_RESPONSE_V1'));
assert.ok(entry.includes("arrivedAt: String(m.arrivedAt || '')"));
assert.ok(entry.includes("departedAt: String(m.departedAt || '')"));

console.log('ATTENDANCE_STATISTICS_V1_OK');
