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

export function normalizeMemberMemoArgs(args){
  const values=Array.isArray(args)?args.slice():[];
  if(values.length===2)return [null,values[0],values[1]];
  return values;
}

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
    const swapRequest=[...requests].reverse().find(item=>
      item&&String(item.status||'pending')==='pending'&&String(item.targetId||'')===memberId
    );
    if(!swapRequest)return null;
    const requester=(state.members||[]).find(member=>String(member&&member.id||'')===String(swapRequest.requesterId||''));
    return {...swapRequest,requesterName:String(requester&&requester.name||'')};
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

async function handleMemberMessageReply(request,env,body){
  const args=Array.isArray(body.args)?body.args:[];
  const sessionPacket=await memberState(request,env,args);
  const memberId=String(sessionPacket.memberId||'');
  const claimedId=String(args[1]||'');
  const messageId=String(args[2]||'').trim();
  const text=String(args[3]||'').trim().slice(0,80);
  if(!memberId)throw new Error('member_identity_required');
  if(claimedId&&claimedId!==memberId)throw new Error('member_identity_required');
  if(!messageId)throw new Error('message_required');
  if(!text)throw new Error('reply_required');

  const visibleMessages=Array.isArray(sessionPacket.state&&sessionPacket.state.memberMessages)
    ?sessionPacket.state.memberMessages:[];
  const received=visibleMessages.find(item=>item&&String(item.id||'')===messageId&&
    Array.isArray(item.memberIds)&&item.memberIds.map(String).includes(memberId));
  if(!received)throw new Error('reply_requires_received_message');

  for(let attempt=0;attempt<4;attempt+=1){
    const row=await env.DB.prepare('SELECT revision,state_json FROM app_state WHERE id=1').first();
    if(!row)throw new Error('state_missing');
    const revision=Math.max(0,Number(row.revision)||0);
    const state=JSON.parse(String(row.state_json||'{}'));
    state.memberMessages=Array.isArray(state.memberMessages)?state.memberMessages:[];
    const target=state.memberMessages.find(item=>item&&String(item.id||'')===messageId&&
      Array.isArray(item.memberIds)&&item.memberIds.map(String).includes(memberId));
    if(!target)throw new Error('reply_requires_received_message');
    const replies=Array.isArray(target.replies)?target.replies.slice(-19):[];
    const replyItem={
      id:`reply-${crypto.randomUUID()}`,
      memberId,
      text,
      createdAt:new Date().toISOString(),
      inReplyTo:messageId,
    };
    target.replies=[...replies,replyItem];
    const nextRevision=revision+1;
    const updatedAt=new Date().toISOString();
    state.revision=nextRevision;
    state.updatedAt=updatedAt;
    const result=await env.DB.prepare(
      'UPDATE app_state SET revision=?,state_json=?,updated_at=? WHERE id=1 AND revision=?'
    ).bind(nextRevision,JSON.stringify(state),updatedAt,revision).run();
    if(Number(result&&result.meta&&result.meta.changes||0)>0){
      return {ok:true,reply:replyItem,messageId};
    }
  }
  throw new Error('reply_conflict_retry');
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
      if(String(body.name||'')==='updateMyProfile'){
        const normalized={...body,args:normalizeMemberMemoArgs(body.args)};
        const headers=new Headers(request.headers);headers.set('content-type','application/json');
        return compatCore.fetch(new Request(request.url,{method:'POST',headers,body:JSON.stringify(normalized)}),env);
      }
      if(String(body.name||'')==='memberReplyToMessage'){
        try{return reply({ok:true,result:await handleMemberMessageReply(request,env,body)});}
        catch(error){return reply({ok:false,error:String(error&&error.message||error)});}
      }
      if(LEGACY_WAIT_SWAP.has(String(body.name||''))){
        try{return reply({ok:true,result:await handleLegacyWaitSwap(request,env,body)});}
        catch(error){return reply({ok:false,error:String(error&&error.message||error)});}
      }
    }
    return compatCore.fetch(request,env);
  }
};
