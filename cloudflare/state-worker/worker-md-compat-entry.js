import mdCore, { StateCoordinator as BaseStateCoordinator } from './worker-md-entry.js';

const HEADERS = {
  'content-type':'application/json; charset=utf-8',
  'cache-control':'no-store',
  'access-control-allow-origin':'*',
  'access-control-allow-methods':'GET,POST,OPTIONS',
  'access-control-allow-headers':'content-type,x-jayuminton-key,authorization',
};
const reply=(body,status=200)=>new Response(JSON.stringify(body),{status,headers:HEADERS});
const uniq=(xs)=>[...new Set((Array.isArray(xs)?xs:[]).map(String).filter(Boolean))];

// Partial admin swaps are selected from a UI snapshot. A member may move themself
// before the administrator submits. Only IDs that are still in the expected
// source group at execution time are eligible, so a stale admin selection can
// never pull a user's newer self-move back or duplicate that member elsewhere.
export function liveIdsInGroup(group,requested){
  const present=new Set((Array.isArray(group)?group:[]).map(String));
  return uniq(requested).filter(id=>present.has(id));
}

function syncStatuses(state){
  const playing=new Set(Object.values(state.courts||{}).flat().map(String));
  const waiting=new Set((state.waitGroups||[]).flat().map(String));
  state.members=(state.members||[]).map(m=>{
    const next={...m}, id=String(m.id||'');
    if(playing.has(id))next.status='playing';
    else if(waiting.has(id))next.status='waiting';
    else if(!['before','rest','away'].includes(String(next.status)))next.status='active';
    return next;
  });
}

async function readState(db){
  const row=await db.prepare('SELECT revision,state_json,updated_at FROM app_state WHERE id=1').first();
  if(!row)return null;
  const state=JSON.parse(row.state_json||'{}');
  state.revision=Number(row.revision)||0;
  state.updatedAt=String(row.updated_at||state.updatedAt||'');
  state.courts=state.courts||{'1':[],'2':[],'3':[],'4':[]};
  state.waitGroups=Array.isArray(state.waitGroups)?state.waitGroups:[[],[],[],[],[]];
  while(state.waitGroups.length<5)state.waitGroups.push([]);
  state.courtStartedAt=state.courtStartedAt||{'1':'','2':'','3':'','4':''};
  state.actionHistory=Array.isArray(state.actionHistory)?state.actionHistory:[];
  return state;
}

function undoSnapshot(state){
  const snap=structuredClone(state);
  snap.actionHistory=[];
  return snap;
}

async function writeCustom(db,state,action,event,before,operationId){
  state.actionHistory=Array.isArray(state.actionHistory)?state.actionHistory:[];
  state.actionHistory.push({operationId:String(operationId||crypto.randomUUID()),action,event,undoState:undoSnapshot(before),at:new Date().toISOString()});
  state.actionHistory=state.actionHistory.slice(-50);
  syncStatuses(state);
  state.revision=Math.max(0,Number(before.revision)||0)+1;
  state.updatedAt=new Date().toISOString();
  await db.prepare('INSERT INTO app_state(id,revision,state_json,updated_at) VALUES(1,?,?,?) ON CONFLICT(id) DO UPDATE SET revision=excluded.revision,state_json=excluded.state_json,updated_at=excluded.updated_at')
    .bind(state.revision,JSON.stringify(state),state.updatedAt).run();
  return state;
}

function assertInternal(request,env){
  if(!env.INTERNAL_KEY||String(request.headers.get('x-jayuminton-key')||'')!==String(env.INTERNAL_KEY))throw new Error('unauthorized');
}

export class StateCoordinator extends BaseStateCoordinator{
  async fetch(request){
    let body=null;
    try{body=await request.clone().json();}catch(_){}
    const action=String(body?.action||'');
    if(action==='mdSwapLocations'||action==='mdAdjustLocations'){
      try{
        assertInternal(request,this.env);
        const before=await readState(this.env.DB);
        if(!before)throw new Error('state_missing');
        const state=structuredClone(before);
        const kind=String(body.kind||'');
        const a=Number(body.a), b=Number(body.b);
        if(kind==='court'){
          if(![1,2,3,4].includes(a)||![1,2,3,4].includes(b)||a===b)throw new Error('invalid_court');
          const ka=String(a),kb=String(b);
          if(action==='mdSwapLocations'){
            [state.courts[ka],state.courts[kb]]=[state.courts[kb]||[],state.courts[ka]||[]];
            [state.courtStartedAt[ka],state.courtStartedAt[kb]]=[state.courtStartedAt[kb]||'',state.courtStartedAt[ka]||''];
          }else{
            const sourceA=(state.courts[ka]||[]).map(String);
            const sourceB=(state.courts[kb]||[]).map(String);
            const idsA=liveIdsInGroup(sourceA,body.idsA), idsB=liveIdsInGroup(sourceB,body.idsB);
            const ga=sourceA.filter(id=>!idsA.includes(id));
            const gb=sourceB.filter(id=>!idsB.includes(id));
            if(ga.length+idsB.length>4||gb.length+idsA.length>4)throw new Error('location_full');
            state.courts[ka]=ga.concat(idsB);
            state.courts[kb]=gb.concat(idsA);
            if(!state.courts[ka].length)state.courtStartedAt[ka]='';
            else if(!state.courtStartedAt[ka])state.courtStartedAt[ka]=new Date().toISOString();
            if(!state.courts[kb].length)state.courtStartedAt[kb]='';
            else if(!state.courtStartedAt[kb])state.courtStartedAt[kb]=new Date().toISOString();
          }
        }else if(kind==='wait'){
          if(a<0||a>4||b<0||b>4||a===b)throw new Error('invalid_wait_group');
          if(action==='mdSwapLocations'){
            [state.waitGroups[a],state.waitGroups[b]]=[state.waitGroups[b]||[],state.waitGroups[a]||[]];
          }else{
            const sourceA=(state.waitGroups[a]||[]).map(String);
            const sourceB=(state.waitGroups[b]||[]).map(String);
            const idsA=liveIdsInGroup(sourceA,body.idsA), idsB=liveIdsInGroup(sourceB,body.idsB);
            const ga=sourceA.filter(id=>!idsA.includes(id));
            const gb=sourceB.filter(id=>!idsB.includes(id));
            if(ga.length+idsB.length>4||gb.length+idsA.length>4)throw new Error('location_full');
            state.waitGroups[a]=ga.concat(idsB);
            state.waitGroups[b]=gb.concat(idsA);
          }
        }else throw new Error('invalid_location_kind');
        const event={type:action==='mdSwapLocations'?'locations_swapped':'locations_adjusted',kind,a,b};
        return reply({ok:true,state:await writeCustom(this.env.DB,state,action,event,before,body.operationId),event});
      }catch(error){return reply({ok:false,error:String(error?.message||error)},400);}
    }
    return super.fetch(request);
  }
}

async function adminState(request,env){
  const u=new URL(request.url);u.pathname='/api/admin/state';
  const r=await mdCore.fetch(new Request(u.toString(),{method:'GET',headers:request.headers}),env);
  const p=await r.json();if(!p.ok)throw new Error(p.error||'admin_state_failed');return p.state;
}

async function adminAction(request,env,action,body={}){
  const u=new URL(request.url);u.pathname='/api/admin/rpc';
  const h=new Headers(request.headers);h.set('content-type','application/json');
  const r=await mdCore.fetch(new Request(u.toString(),{method:'POST',headers:h,body:JSON.stringify({action,operationId:`md-compat-${Date.now()}-${crypto.randomUUID()}`,...body})}),env);
  const p=await r.json();if(!p.ok)throw new Error(p.error||'operation_failed');return p.state||p;
}

async function doCustom(request,env,action,body){
  const id=env.STATE_COORDINATOR.idFromName('global-state');
  const h=new Headers(request.headers);h.set('x-jayuminton-key',String(env.INTERNAL_KEY||''));h.set('content-type','application/json');
  const r=await env.STATE_COORDINATOR.get(id).fetch(new Request(request.url,{method:'POST',headers:h,body:JSON.stringify({action,operationId:`md-custom-${Date.now()}-${crypto.randomUUID()}`,...body})}));
  const p=await r.json();if(!p.ok)throw new Error(p.error||'custom_operation_failed');return p.state;
}

async function handleCompat(request,env,body){
  const name=String(body.name||'');
  const a=Array.isArray(body.args)?body.args:[];
  if(name==='mdAutoAssignTargets'){
    const u=new URL(request.url);u.pathname='/api/admin/rpc';
    const h=new Headers(request.headers);h.set('content-type','application/json');
    const r=await mdCore.fetch(new Request(u.toString(),{method:'POST',headers:h,body:JSON.stringify({action:'autoAssign',candidateIds:a[1]||[],destinations:a[2]||[]})}),env);
    const p=await r.json();if(!p.ok)throw new Error(p.error||'autoassign_failed');return p.state;
  }
  if(name==='autoFillCourt')return adminAction(request,env,'moveMembers',{memberIds:a[2]||[],destination:{type:'court',key:String(a[1])}});
  if(name==='autoFillWaitGroup')return adminAction(request,env,'moveMembers',{memberIds:a[2]||[],destination:{type:'wait',key:String(Number(a[1])+1)}});
  if(name==='setBundle')return adminAction(request,env,'setBundle',{memberIds:a[1]||[]});
  if(name==='clearBundle')return adminAction(request,env,'clearBundle',{memberIds:a[1]||[]});
  if(name==='moveOrSwapMember'){
    const id=String(a[1]||''), targetType=String(a[2]||''), targetIndex=a[3], other=String(a[4]||'');
    if(other)return adminAction(request,env,'swapMembers',{leftIds:[id],rightIds:[other]});
    const key=targetType==='wait'?String(Number(targetIndex)+1):String(targetIndex);
    return adminAction(request,env,'moveMembers',{memberIds:[id],destination:{type:targetType,key}});
  }
  if(name==='assignWaitGroupToCourt'){
    const state=await adminState(request,env);const ids=(state.waitGroups?.[Number(a[1])]||[]).map(String);
    if(!ids.length)return state;
    return adminAction(request,env,'moveMembers',{memberIds:ids,destination:{type:'court',key:String(a[2])}});
  }
  if(name==='removeFromCourt'||name==='removeFromWaitGroup')return adminAction(request,env,'setMemberStatus',{memberIds:[String(a[2]||'')],status:'active'});
  if(name==='swapCourts')return doCustom(request,env,'mdSwapLocations',{kind:'court',a:Number(a[1]),b:Number(a[2])});
  if(name==='swapWaitGroups')return doCustom(request,env,'mdSwapLocations',{kind:'wait',a:Number(a[1]),b:Number(a[2])});
  if(name==='adjustCourtMembers')return doCustom(request,env,'mdAdjustLocations',{kind:'court',a:Number(a[1]),b:Number(a[2]),idsA:a[3]||[],idsB:a[4]||[]});
  if(name==='adjustWaitGroupMembers')return doCustom(request,env,'mdAdjustLocations',{kind:'wait',a:Number(a[1]),b:Number(a[2]),idsA:a[3]||[],idsB:a[4]||[]});
  return null;
}

const OWN_COMPAT=new Set(['mdAutoAssignTargets','autoFillCourt','autoFillWaitGroup','setBundle','clearBundle','moveOrSwapMember','assignWaitGroupToCourt','removeFromCourt','removeFromWaitGroup','swapCourts','swapWaitGroups','adjustCourtMembers','adjustWaitGroupMembers']);

export default{
  async fetch(request,env){
    if(request.method==='OPTIONS')return new Response(null,{status:204,headers:HEADERS});
    const url=new URL(request.url);
    if(request.method==='POST'&&url.pathname==='/api/compat/rpc'){
      const body=await request.clone().json().catch(()=>({}));
      if(OWN_COMPAT.has(String(body.name||''))){
        try{return reply({ok:true,result:await handleCompat(request,env,body)});}
        catch(error){return reply({ok:false,error:String(error?.message||error)});}
      }
    }
    return mdCore.fetch(request,env);
  }
};
