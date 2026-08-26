import assert from 'node:assert/strict';
import { emptyState, normalizeState, setTempPairsMutation, moveMutation, finishCourtMutation, publicState } from './worker.js';

function fixture(){
  const state=emptyState();
  state.members=Array.from({length:12},(_,i)=>({id:String(i+1),name:`회원${i+1}`,games:0,status:'active'}));
  state.courts['1']=['1','2','3','4'];
  state.waitGroups=[['5','6','7','8'],['9','10','11','12'],[],[],[]];
  return normalizeState(state);
}

// 같은 대기에서 3명을 고르면 세 명 전체가 하나의 임시 노란 팀으로 저장되어야 한다.
{
  const r=setTempPairsMutation(fixture(),[{members:['5','6','7'],zone:'wait',createdAt:1}]);
  assert.equal(r.state.tempPairs.length,1);
  assert.deepEqual(r.state.tempPairs[0].members,['5','6','7']);
  assert.deepEqual(r.state.waitGroups[0],['5','6','7','8']);
  assert.deepEqual(publicState(r.state,'5').tempPairs,r.state.tempPairs);
}

// 같은 코트에서 4명까지 하나의 임시 팀으로 저장한다. 자리 재정렬은 하지 않는다.
{
  const r=setTempPairsMutation(fixture(),[{members:['1','2','3','4'],zone:'court',createdAt:1}]);
  assert.equal(r.state.tempPairs.length,1);
  assert.deepEqual(r.state.tempPairs[0].members,['1','2','3','4']);
  assert.deepEqual(r.state.courts['1'],['1','2','3','4']);
}

// 2명도 같은 그룹 형식으로 유지한다.
{
  const r=setTempPairsMutation(fixture(),[{members:['5','7'],zone:'wait',createdAt:1}]);
  assert.deepEqual(r.state.tempPairs[0].members,['5','7']);
}

// 임시 팀 중 한 명이라도 다른 위치로 이동하면 노란 임시 테두리는 자동 해제되어야 한다.
{
  const paired=setTempPairsMutation(fixture(),[{members:['5','6','7'],zone:'wait',createdAt:1}]).state;
  const moved=moveMutation(paired,['5'],{type:'court',key:'2'}).state;
  assert.deepEqual(moved.tempPairs,[]);
}

// 경기 종료로 위치가 바뀌어도 임시 노란 팀은 사라지고, 영구 팀 정보는 남아야 한다.
{
  const s=fixture();
  for(const id of ['1','2','3']){const m=s.members.find(x=>x.id===id);m.teamLabel='팀 1';m.bundleId='fixed-team-1';}
  const paired=setTempPairsMutation(s,[{members:['1','2','3'],zone:'court',createdAt:1}]).state;
  const finished=finishCourtMutation(paired,1).state;
  assert.deepEqual(finished.tempPairs,[]);
  assert.equal(finished.members.find(m=>m.id==='1').teamLabel,'팀 1');
  assert.equal(finished.members.find(m=>m.id==='1').bundleId,'fixed-team-1');
}

console.log('STATE_WORKER_TEMP_GROUPS_TESTS_OK members=2..4 yellow=true movement-clears=true persistent-team-kept=true');
