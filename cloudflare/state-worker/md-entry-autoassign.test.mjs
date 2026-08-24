import assert from 'node:assert/strict';
import { eligibleAutoAssignPool, selectValidFill, targetArray } from './worker-md-entry.js';

const member=(id,gender,status='active')=>({id,name:id,gender,status,games:0});
const state={
  members:[
    member('wm','male','queued'),
    member('m1','male'),member('m2','male'),member('m3','male'),member('m4','male'),
    member('f1','female'),member('f2','female'),member('rest','male','rest'),
  ],
  courts:{'1':[],'2':[],'3':[],'4':[]},
  waitGroups:[['wm'],[],[],[],[]],
};

assert.deepEqual(targetArray(state,{type:'wait',key:'1'}),['wm'],'wait occupancy must be counted');
const pool=eligibleAutoAssignPool(state,[]);
assert.ok(!pool.includes('wm'),'already queued member must not be a candidate');
assert.ok(!pool.includes('rest'),'rest member must not be auto assigned');
assert.ok(pool.includes('m1')&&pool.includes('f1'),'active fallback pool must be populated when candidateIds are omitted');

const byId=new Map(state.members.map(m=>[m.id,m]));
const picked=selectValidFill(state,pool,{type:'wait',key:'1'},byId);
assert.equal(picked.length,3,'wait1 with one occupant has exactly three free positions');
const final=['wm',...picked];
const men=final.filter(id=>String(byId.get(id)?.gender).toLowerCase()==='male').length;
assert.ok([0,2,4].includes(men),'filled 4-person wait group must respect doubles composition');

const remainderState={
  members:[member('r1','male'),member('r2','male'),member('r3','female')],
  courts:{'1':[],'2':[],'3':[],'4':[]},waitGroups:[[],[],[],[],[]],
};
const remainderById=new Map(remainderState.members.map(m=>[m.id,m]));
const remainderPool=eligibleAutoAssignPool(remainderState,[]);
assert.equal(selectValidFill(remainderState,remainderPool,{type:'court',key:'1'},remainderById).length,3,'final remainder under four must be assigned maximally');

console.log('MD_ENTRY_AUTOASSIGN_TESTS_OK');
