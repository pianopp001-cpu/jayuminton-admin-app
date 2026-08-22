#!/usr/bin/env python3
from pathlib import Path
import sys

p=Path(sys.argv[1])
s=p.read_text(encoding='utf-8')
include='function include(filename) {'
if include not in s:
    raise SystemExit('include marker missing')

if 'function memberSetOwnStatus(' not in s:
    self_fn=r'''
function memberSetOwnStatus(sessionToken,memberId,status){
  return withDocumentLock_('회원 본인 상태 변경',function(){
    memberId=memberSessionAuth_(sessionToken,memberId);
    status=String(status||'');
    if(['active','rest','away','before'].indexOf(status)<0)throw new Error('지원하지 않는 상태입니다.');
    const courts=readCourts_(),startedAt=readCourtStartedAt_(),waitGroups=readWaitGroups_();
    Object.keys(courts).forEach(function(k){
      const before=(courts[k]||[]).length;
      courts[k]=(courts[k]||[]).filter(function(id){return String(id)!==memberId;});
      if(courts[k].length!==before&&courts[k].length<GROUP_SIZE)startedAt[k]='';
    });
    for(let i=0;i<waitGroups.length;i+=1)waitGroups[i]=(waitGroups[i]||[]).filter(function(id){return String(id)!==memberId;});
    writeCourts_(courts,startedAt);writeWaitGroups_(waitGroups);updateMemberStatuses_([memberId],status);touch_();return getPublicState();
  });
}
'''
    s=s.replace(include,self_fn+'\n'+include,1)

if 'function memberCloudflareRpcV3_(e)' not in s:
    rpc=r'''
function memberCloudflareRpcV3_(e){
  ensureSetup_();
  const p=e&&e.parameter?e.parameter:{};
  const callback=String(p.callback||'');
  const name=String(p.rpc||'');
  const allowed={getPublicState:true,getMemberPasswordVersion:true,verifyMemberPassword:true,resumeMemberSession:true,memberMoveToWaitGroup:true,memberLeaveWaitGroup:true,memberSetOwnStatus:true,memberRequestWaitSwap:true,memberGetWaitSwapRequest:true,memberRespondWaitSwap:true};
  if(!/^[A-Za-z_$][A-Za-z0-9_$]{0,80}$/.test(callback))throw new Error('잘못된 callback입니다.');
  if(!allowed[name])return ContentService.createTextOutput(callback+'('+JSON.stringify({ok:false,error:'허용되지 않은 사용자 함수입니다.'})+');').setMimeType(ContentService.MimeType.JAVASCRIPT);
  let args=[];
  try{const encoded=String(p.payload||'');if(encoded){const normalized=encoded.replace(/-/g,'+').replace(/_/g,'/');const pad='='.repeat((4-normalized.length%4)%4);args=JSON.parse(Utilities.newBlob(Utilities.base64Decode(normalized+pad)).getDataAsString('UTF-8'));}if(!Array.isArray(args))throw new Error('args');}
  catch(error){return ContentService.createTextOutput(callback+'('+JSON.stringify({ok:false,error:'요청 데이터를 읽을 수 없습니다.'})+');').setMimeType(ContentService.MimeType.JAVASCRIPT);}
  try{
    let result;
    if(name==='getPublicState')result=getPublicState.apply(null,args);
    else if(name==='getMemberPasswordVersion')result=getMemberPasswordVersion.apply(null,args);
    else if(name==='verifyMemberPassword')result=verifyMemberPassword.apply(null,args);
    else if(name==='resumeMemberSession')result=resumeMemberSession.apply(null,args);
    else if(name==='memberMoveToWaitGroup')result=memberMoveToWaitGroup.apply(null,args);
    else if(name==='memberLeaveWaitGroup')result=memberLeaveWaitGroup.apply(null,args);
    else if(name==='memberSetOwnStatus')result=memberSetOwnStatus.apply(null,args);
    else if(name==='memberRequestWaitSwap')result=memberRequestWaitSwap.apply(null,args);
    else if(name==='memberGetWaitSwapRequest')result=memberGetWaitSwapRequest.apply(null,args);
    else if(name==='memberRespondWaitSwap')result=memberRespondWaitSwap.apply(null,args);
    else throw new Error('허용되지 않은 사용자 함수입니다.');
    return ContentService.createTextOutput(callback+'('+JSON.stringify({ok:true,result:result})+');').setMimeType(ContentService.MimeType.JAVASCRIPT);
  }catch(error){return ContentService.createTextOutput(callback+'('+JSON.stringify({ok:false,error:String(error&&error.message||error||'서버 오류')})+');').setMimeType(ContentService.MimeType.JAVASCRIPT);}
}
'''
    s=s.replace(include,rpc+'\n'+include,1)

branch="  if (e && e.parameter && e.parameter.memberRpc === '1' && e.parameter.rpc) {\n    return memberCloudflareRpcV3_(e);\n  }\n"
if branch not in s:
    marker='function doGet(e) {'
    if marker not in s:
        raise SystemExit('doGet marker missing')
    s=s.replace(marker,marker+'\n'+branch,1)

p.write_text(s,encoding='utf-8')
print('seat head patch ok')
