import assert from 'node:assert/strict';
import { emptyState, normalizeState, setTempPairsMutation, moveMutation, publicState } from './worker.js';
function fixture(){const state=emptyState();state.members=Array.from({length:12},(_,i)=>({id:String(i+1),name:`회원${i+1}`,games:0,status:'active'}));state.courts['1']=['1','2','3','4'];state.waitGroups=[['5','6','7','8'],['9','10','11','12']];return normalizeState(state);}
// 대기: 같은 짝은 왼쪽 2칸(1,3), 반대 짝은 오른쪽 2칸(2,4).
{const r=setTempPairsMutation(fixture(),[{pairA:['5','7'],pairB:['6','8'],zone:'wait',createdAt:1}]);assert.deepEqual(r.state.waitGroups[0],['5','6','7','8']);assert.deepEqual(r.state.tempPairs[0].pairA,['5','7']);assert.deepEqual(r.state.tempPairs[0].pairB,['6','8']);assert.deepEqual(publicState(r.state,'5').tempPairs,r.state.tempPairs);}
// 코트: 같은 짝은 위 2명, 반대 짝은 아래 2명.
{const r=setTempPairsMutation(fixture(),[{pairA:['1','3'],pairB:['2','4'],zone:'court',createdAt:1}]);assert.deepEqual(r.state.courts['1'],['1','3','2','4']);assert.deepEqual(r.state.tempPairs[0].pairA,['1','3']);assert.deepEqual(r.state.tempPairs[0].pairB,['2','4']);}
// 대기↔코트 이동 시 1회성 실선만 제거.
{const paired=setTempPairsMutation(fixture(),[{pairA:['5','7'],pairB:['6','8'],zone:'wait',createdAt:1}]).state;const moved=moveMutation(paired,['5'],{type:'court',key:'2'}).state;assert.deepEqual(moved.tempPairs,[]);}
// 고정 팀의 teamLabel/bundleId는 1회성 짝과 독립적으로 유지.
{const s=fixture();for(const id of ['5','7']){const m=s.members.find(x=>x.id===id);m.teamLabel='팀 1';m.bundleId='fixed-team-1';}const r=setTempPairsMutation(s,[{pairA:['5','6'],pairB:['7','8'],zone:'wait',createdAt:1}]);assert.equal(r.state.members.find(m=>m.id==='5').teamLabel,'팀 1');assert.equal(r.state.members.find(m=>m.id==='5').bundleId,'fixed-team-1');}
console.log('STATE_WORKER_TEMP_PAIRS_TESTS_OK pairA+pairB=true wait=left-right court=top-bottom');
