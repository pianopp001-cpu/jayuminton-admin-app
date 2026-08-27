import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(
  new URL('./patch_member_single_tap_move_v1.py', import.meta.url),
  'utf8',
);
const match = source.match(/addon = r'''\n<script[^>]*>([\s\S]*?)<\/script>\n'''/);
assert.ok(match, 'single-tap addon script not found');

const calls = [];
const alerts = [];
const context = {
  console,
  setTimeout,
  clearTimeout,
  IS_ADMIN: false,
  MEMBER_WAIT_EMPTY_TAP: { key: '', tappedAt: 0, timer: null },
  STATE: {
    members: [{ id: 'member-1', name: '테스트', status: 'active' }],
    courts: { 1: [], 2: [], 3: [], 4: [] },
    waitGroups: [[], [], [], [], []],
  },
  alert(message) { alerts.push(String(message)); },
  memberWaitSeatSessionArgs() {
    return { member: { id: 'member-1', name: '테스트' }, token: 'session-token' };
  },
  clearMemberWaitSeatPick() {},
  renderState(state) { if (state) context.STATE = state; },
  async server(name, args) {
    calls.push({ name, args });
    const destination = args[2];
    const state = {
      members: [{
        id: 'member-1',
        name: '테스트',
        status: destination.type === 'court' ? 'playing' : 'waiting',
      }],
      courts: { 1: [], 2: [], 3: [], 4: [] },
      waitGroups: [[], [], [], [], []],
    };
    if (destination.type === 'court') state.courts[destination.key].push('member-1');
    else state.waitGroups[Number(destination.key) - 1].push('member-1');
    return { ok: true, state };
  },
};
context.window = context;
vm.createContext(context);
vm.runInContext(match[1], context);

const event = { preventDefault() {}, stopPropagation() {} };
context.window.handleEmptySlotTap('court', '1', 0, event);
await new Promise(resolve => setTimeout(resolve, 0));

assert.equal(calls[0].name, 'memberMoveSelf');
assert.equal(JSON.stringify(calls[0].args[2]), JSON.stringify({ type: 'court', key: '1' }));
assert.deepEqual(context.STATE.courts['1'], ['member-1']);
assert.equal(alerts.length, 0);

context.STATE.members[0].status = 'active';
context.STATE.courts['1'] = [];
context.window.handleMemberWaitEmptyTap(1, 0, event);
await new Promise(resolve => setTimeout(resolve, 0));

assert.equal(calls[1].name, 'memberMoveSelf');
assert.equal(JSON.stringify(calls[1].args[2]), JSON.stringify({ type: 'wait', key: '2' }));
assert.deepEqual(context.STATE.waitGroups[1], ['member-1']);
assert.equal(alerts.length, 0);

console.log('MEMBER_SINGLE_TAP_MOVE_TEST_OK');
