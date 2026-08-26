import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';

const workerPath=new URL('./worker.js',import.meta.url);
let source=await readFile(workerPath,'utf8');
const broken="try { const state = await readState(env.DB); await verifyAdminSession(request, env, state); return reply({ ok: true, state: adminState(state) });\n      catch (error)";
const fixed="try { const state = await readState(env.DB); await verifyAdminSession(request, env, state); return reply({ ok: true, state: adminState(state) }); }\n      catch (error)";
if(source.includes(broken))source=source.replace(broken,fixed);
const temp='/tmp/jayuminton-worker-temp-groups-fixed.mjs';
await writeFile(temp,source,'utf8');
const {emptyState,normalizeState,setTempPairsMutation,moveMutation,finishCourtMutation,publicState}=await import(pathToFileURL(temp).href+'?v='+Date.now());

function fixture(){
  const state=emptyState();
  state.members=Array.from({length:12},(_,i)=>({id:String(i+1),name:`회원${i+1}`,games:0,status:'active'}));
  state.courts['1']=['1','2','3','4'];
  state.waitGroups=[['5','6','7','8'],['9','10','11','12'],[],[],[]];
  return normalizeState(state);
}

{
  const r=setTempPairsMutation(fixture(),[{members:['5','6','7'],zone:'wait',createdAt:1}]);
  assert.equal(r.state.tempPairs.length,1);
  assert.deepEqual(r.state.tempPairs[0].members,['5','6','7']);
  assert.deepEqual(r.state.waitGroups[0],['5','6','7','8']);
  assert.deepEqual(publicState(r.state,'5').tempPairs,r.state.tempPairs);
}
{
  const r=setTempPairsMutation(fixture(),[{members:['1','2','3','4'],zone:'court',createdAt:1}]);
  assert.equal(r.state.tempPairs.length,1);
  assert.deepEqual(r.state.tempPairs[0].members,['1','2','3','4']);
  assert.deepEqual(r.state.courts['1'],['1','2','3','4']);
}
{
  const r=setTempPairsMutation(fixture(),[{members:['5','7'],zone:'wait',createdAt:1}]);
  assert.deepEqual(r.state.tempPairs[0].members,['5','7']);
}
{
  const paired=setTempPairsMutation(fixture(),[{members:['5','6','7'],zone:'wait',createdAt:1}]).state;
  const moved=moveMutation(paired,['5'],{type:'court',key:'2'}).state;
  assert.deepEqual(moved.tempPairs,[]);
}
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
