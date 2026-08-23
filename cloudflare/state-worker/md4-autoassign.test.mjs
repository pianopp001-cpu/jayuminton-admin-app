import assert from 'node:assert/strict';
import { autoAssignMutation } from './worker.js';

function member(id, gender) {
  return { id, name: id, gender, games: 0, status: 'active' };
}

function base(members) {
  return {
    members,
    courts: { '1': [], '2': [], '3': [], '4': [] },
    waitGroups: [[], [], [], [], []],
    courtStartedAt: { '1': '', '2': '', '3': '', '4': '' },
    settings: {},
    swapRequests: [],
    actionHistory: [],
  };
}

{
  const state = base([
    member('m1','male'), member('m2','male'), member('m3','male'), member('m4','male'),
    member('f1','female'), member('f2','female'),
  ]);
  const out = autoAssignMutation(state, ['m1','m2','m3','m4','f1','f2'], [{type:'court',key:'1'}]).state;
  const ids = out.courts['1'];
  assert.equal(ids.length, 4);
  assert.equal(ids.filter(id => id.startsWith('m')).length, 2, 'mixed 2M2F should be preferred when feasible');
  assert.equal(ids.filter(id => id.startsWith('f')).length, 2);
}

{
  const state = base([member('f1','female'),member('f2','female'),member('f3','female'),member('f4','female')]);
  const out = autoAssignMutation(state, ['f1','f2','f3','f4'], [{type:'court',key:'1'}]).state;
  assert.deepEqual(new Set(out.courts['1']), new Set(['f1','f2','f3','f4']), '4F composition must work');
}

{
  const state = base([member('m1','male'),member('m2','male'),member('m3','male')]);
  const out = autoAssignMutation(state, ['m1','m2','m3'], [{type:'court',key:'1'}]).state;
  assert.equal(out.courts['1'].length, 3, 'remainder must be assigned even when fewer than four');
}

{
  const state = base([member('m1','male'),member('m2','male'),member('f1','female'),member('f2','female')]);
  state.courts['1'] = ['m1','m2'];
  state.members[0].status = 'playing';
  state.members[1].status = 'playing';
  const out = autoAssignMutation(state, ['f1','f2'], [{type:'court',key:'1'}]).state;
  assert.deepEqual(new Set(out.courts['1']), new Set(['m1','m2','f1','f2']), 'existing 2M must be completed with 2F');
}

console.log('MD4_AUTOASSIGN_TESTS_OK');
