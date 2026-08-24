import compatCore, { StateCoordinator } from './worker-md-compat-entry.js';

export { StateCoordinator };

const HEADERS = {
  'content-type':'application/json; charset=utf-8',
  'cache-control':'no-store',
  'access-control-allow-origin':'*',
  'access-control-allow-methods':'GET,POST,OPTIONS',
  'access-control-allow-headers':'content-type,x-jayuminton-key,authorization',
};
const reply=(body,status=200)=>new Response(JSON.stringify(body),{status,headers:HEADERS});

function authHeaders(request,args){
  const headers=new Headers(request.headers);
  headers.set('content-type','application/json');
  if(!headers.get('authorization')){
    const token=String(Array.isArray(args)?args[0]||'':'');
    if(token)headers.set('authorization','Bearer '+token);
  }
  return headers;
}

async function memberRpc(request,env,args,body){
  const url=new URL(request.url);
  url.pathname='/api/member/rpc';
  const response=await compatCore.fetch(new Request(url.toString(),{
    method:'POST',
    headers:authHeaders(request,args),
    body:JSON.stringify(body),
  }),env);
  const packet=await response.json();
  if(!packet.ok)throw new Error(packet.error||'member_rpc_failed');
  return packet;
}

async function memberState(request,env,args){
  const url=new URL(request.url);
  url.pathname='/api/member/state';
  const response=await compatCore.fetch(new Request(url.toString(),{
    method:'GET',
    headers:authHeaders(request,args),
  }),env);
  const packet=await response.json();
  if(!packet.ok)throw new Error(packet.error||'member_state_failed');
  return packet;
}

async function handleLegacyWaitSwap(request,env,body){
  const name=String(body.name||'');
  const args=Array.isArray(body.args)?body.args:[];
  const selfId=String(args[1]||'');

  if(name==='memberRequestWaitSwap'){
    const targetId=String(args[2]||'');
    if(!targetId)throw new Error('swap_target_required');
    const packet=await memberRpc(request,env,args,{
      action:'requestSwap',
      operationId:`legacy-wait-swap-request-${Date.now()}-${crypto.randomUUID()}`,
      targetId,
    });
    return {ok:true,message:'자리 교환을 요청했어요.',state:packet.state||null};
  }

  if(name==='memberGetWaitSwapRequest'){
    const packet=await memberState(request,env,args);
    const memberId=String(packet.memberId||selfId||'');
    const state=packet.state||{};
    const requests=Array.isArray(state.swapRequests)?state.swapRequests:[];
    const request=[...requests].reverse().find(item=>
      item&&String(item.status||'pending')==='pending'&&String(item.targetId||'')===memberId
    );
    if(!request)return null;
    const requester=(state.members||[]).find(member=>String(member&&member.id||'')===String(request.requesterId||''));
    return {...request,requesterName:String(requester&&requester.name||'')};
  }

  if(name==='memberRespondWaitSwap'){
    const requestId=String(args[2]||'');
    if(!requestId)throw new Error('swap_request_required');
    const packet=await memberRpc(request,env,args,{
      action:'respondSwap',
      operationId:`legacy-wait-swap-response-${Date.now()}-${crypto.randomUUID()}`,
      requestId,
      accept:Boolean(args[3]),
    });
    return packet.state||packet;
  }

  throw new Error('unsupported_wait_swap_rpc');
}

const LEGACY_WAIT_SWAP=new Set([
  'memberRequestWaitSwap',
  'memberGetWaitSwapRequest',
  'memberRespondWaitSwap',
]);

export default {
  async fetch(request,env){
    if(request.method==='OPTIONS')return new Response(null,{status:204,headers:HEADERS});
    const url=new URL(request.url);
    if(request.method==='POST'&&url.pathname==='/api/compat/rpc'){
      const body=await request.clone().json().catch(()=>({}));
      if(LEGACY_WAIT_SWAP.has(String(body.name||''))){
        try{return reply({ok:true,result:await handleLegacyWaitSwap(request,env,body)});}
        catch(error){return reply({ok:false,error:String(error&&error.message||error)});}
      }
    }
    return compatCore.fetch(request,env);
  }
};
