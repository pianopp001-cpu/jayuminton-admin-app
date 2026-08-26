import assert from 'node:assert/strict';
import { emptyState, normalizeState, setTempPairsMutation, moveMutation, publicState } from './worker.js';
function fixture(){const state=emptyState();state.members=Array.from({length:12},(_,i)=>({id:String(i+1),name:`회원${i+1}`,games:0,status:'active'}));state.courts['1']=['1','2','3','4'];state.waitGroups=[['5','6','7','8'],['9','10','11','12']];return normalizeState(state);}
// 대기: 클릭한 두 명만 1회성 팀. 남은 두 명은 무표시이며 자리 순서는 바꾸지 않는다.
{const r=setTempPairsMutation(fixture(),[{pairA:['5','7'],pairB:['6','8'],zone:'wait',createdAt:1}]);assert.deepEqual(r.state.waitGroups[0],['5','6','7','8']);assert.deepEqual(r.state.tempPairs[0].pairA,['5','7']);assert.deepEqual(r.state.tempPairs[0].pairB,[]);assert.deepEqual(publicState(r.state,'5').tempPairs,r.state.tempPairs);}
// 코트도 클릭한 두 명만 임시 팀이며 2+2 자동분리/자리 재정렬을 하지 않는다.
{const r=setTempPairsMutation(fixture(),[{pairA:['1','3'],pairB:['2','4'],zone:'court',createdAt:1}]);assert.deepEqual(r.state.courts['1'],['1','2','3','4']);assert.deepEqual(r.state.tempPairs[0].pairA,['1','3']);assert.deepEqual(r.state.tempPairs[0].pairB,[]);}
// 대기↔코트 등 위치 변경 시 1회성 테두리는 자동 제거.
{const paired=setTempPairsMutation(fixture(),[{pairA:['5','7'],pairB:[],zone:'wait',createdAt:1}]).state;const moved=moveMutation(paired,['5'],{type:'court',key:'2'}).state;assert.deepEqual(moved.tempPairs,[]);}
// 고정 팀의 teamLabel/bundleId(2중 테두리)는 1회성 팀과 독립적으로 유지.
{const s=fixture();for(const id of ['5','7']){const m=s.members.find(x=>x.id===id);m.teamLabel='팀 1';m.bundleId='fixed-team-1';}const r=setTempPairsMutation(s,[{pairA:['5','6'],pairB:[],zone:'wait',createdAt:1}]);assert.equal(r.state.members.find(m=>m.id==='5').teamLabel,'팀 1');assert.equal(r.state.members.find(m=>m.id==='5').bundleId,'fixed-team-1');assert.deepEqual(r.state.tempPairs[0].pairA,['5','6']);}
console.log('STATE_WORKER_TEMP_PAIRS_TESTS_OK clicked-two-only=true remaining-plain=true reorder=false');
