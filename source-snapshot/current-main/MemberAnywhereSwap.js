function memberAnywhereLocation_(memberId){
  memberId=String(memberId||'');
  var courts=readCourts_();
  var courtKeys=Object.keys(courts);
  for(var c=0;c<courtKeys.length;c+=1){
    var courtNo=courtKeys[c];
    var court=(courts[courtNo]||[]);
    var courtPos=court.indexOf(memberId);
    if(courtPos>=0)return {type:'court',courtNo:String(courtNo),position:courtPos};
  }
  var waitGroups=readWaitGroups_();
  for(var g=0;g<waitGroups.length;g+=1){
    var waitPos=(waitGroups[g]||[]).indexOf(memberId);
    if(waitPos>=0)return {type:'wait',group:g,position:waitPos};
  }
  var member=readMembers_().find(function(item){return item&&String(item.id)===memberId;});
  return member?{type:'status',status:String(member.status||'active')}:null;
}

function memberAnywhereLocationKey_(location){if(!location)return '';if(location.type==='court')return 'court:'+location.courtNo+':'+location.position;if(location.type==='wait')return 'wait:'+location.group+':'+location.position;if(location.type==='status')return 'status:'+location.status;return '';}
function memberAnywhereSnapshot_(memberId){var location=memberAnywhereLocation_(memberId);return {memberId:String(memberId||''),locationKey:memberAnywhereLocationKey_(location)};}
function memberAnywhereSwapSnapshot_(fromMemberId,toMemberId){return {from:memberAnywhereSnapshot_(fromMemberId),to:memberAnywhereSnapshot_(toMemberId)};}
function memberAnywhereSwapCacheKey_(memberId){return 'ANYWHERE_SWAP_'+String(memberId||'');}
function memberAnywhereSwapRequest_(requesterId,targetId){return {requesterId:String(requesterId||''),targetId:String(targetId||''),snapshot:memberAnywhereSwapSnapshot_(requesterId,targetId),createdAt:Date.now()};}
function memberAnywherePutSwapRequest_(targetId,request){CacheService.getDocumentCache().put(memberAnywhereSwapCacheKey_(targetId),JSON.stringify(request),300);}
function memberAnywhereReadSwapRaw_(memberId){return CacheService.getDocumentCache().get(memberAnywhereSwapCacheKey_(memberId));}
function memberAnywhereClearSwapRequest_(memberId){CacheService.getDocumentCache().remove(memberAnywhereSwapCacheKey_(memberId));}
function memberAnywhereReadSwapRequest_(memberId){var raw=memberAnywhereReadSwapRaw_(memberId);if(!raw)return null;try{return JSON.parse(raw);}catch(error){memberAnywhereClearSwapRequest_(memberId);return null;}}
function memberGetAnywhereSwapRequest(sessionToken,memberId){memberId=memberSessionAuth_(sessionToken,memberId);var request=memberAnywhereReadSwapRequest_(memberId);if(!request||String(request.targetId)!==memberId)return null;return request;}
function memberRejectAnywhereSwap(sessionToken,memberId){memberId=memberSessionAuth_(sessionToken,memberId);memberAnywhereClearSwapRequest_(memberId);return {ok:true,message:'자리 교환 요청을 거절했어요.'};}
function memberAnywhereSnapshotStillValid_(snapshot){if(!snapshot||!snapshot.from||!snapshot.to)return false;return memberAnywhereSnapshot_(snapshot.from.memberId).locationKey===snapshot.from.locationKey&&memberAnywhereSnapshot_(snapshot.to.memberId).locationKey===snapshot.to.locationKey;}
function memberAnywhereReplaceAtLocation_(location,memberId,courts,waitGroups){if(location.type==='court'){courts[String(location.courtNo)][Number(location.position)]=memberId;return;}if(location.type==='wait')waitGroups[Number(location.group)][Number(location.position)]=memberId;}
function memberAnywhereSwapPlacedMembers_(firstId,secondId,firstLocation,secondLocation){var courts=readCourts_();var waitGroups=readWaitGroups_();memberAnywhereReplaceAtLocation_(firstLocation,secondId,courts,waitGroups);memberAnywhereReplaceAtLocation_(secondLocation,firstId,courts,waitGroups);writeCourts_(courts,readCourtStartedAt_());writeWaitGroups_(waitGroups);}
function memberAnywhereStatusForLocation_(location){if(location.type==='court')return 'playing';if(location.type==='wait')return 'waiting';return String(location.status||'active');}
function memberAnywhereApplyStatus_(member,location){member.status=memberAnywhereStatusForLocation_(location);}
function memberAnywhereMemberById_(members,memberId){return members.find(function(member){return String(member.id)===String(memberId);})||null;}
function memberAnywhereApplyPairStatus_(members,firstId,secondId,firstLocation,secondLocation){var first=memberAnywhereMemberById_(members,firstId);var second=memberAnywhereMemberById_(members,secondId);if(!first||!second)return false;memberAnywhereApplyStatus_(first,secondLocation);memberAnywhereApplyStatus_(second,firstLocation);return true;}
function memberAnywhereSavePairStatus_(firstId,secondId,firstLocation,secondLocation){var members=readMembers_();if(!memberAnywhereApplyPairStatus_(members,firstId,secondId,firstLocation,secondLocation))return false;writeMembers_(members);return true;}
function memberAnywhereSwapAll_(firstId,secondId,firstLocation,secondLocation){memberAnywhereSwapPlacedMembers_(firstId,secondId,firstLocation,secondLocation);return memberAnywhereSavePairStatus_(firstId,secondId,firstLocation,secondLocation);}

function memberAcceptAnywhereSwap(sessionToken,memberId){
  memberId=memberSessionAuth_(sessionToken,memberId);
  var request=memberAnywhereReadSwapRequest_(memberId);
  if(!request||String(request.targetId)!==memberId)return {ok:false,message:'교환 요청이 없거나 만료됐어요.'};
  if(!memberAnywhereSnapshotStillValid_(request.snapshot)){
    memberAnywhereClearSwapRequest_(memberId);
    return {ok:false,message:'자리 상태가 변경되어 교환할 수 없어요.'};
  }
  var firstLocation=memberAnywhereLocation_(request.requesterId);
  var secondLocation=memberAnywhereLocation_(memberId);
  var ok=memberAnywhereSwapAll_(request.requesterId,memberId,firstLocation,secondLocation);
  memberAnywhereClearSwapRequest_(memberId);
  return ok?{ok:true,message:'자리 교환이 완료됐어요.'}:{ok:false,message:'회원 정보를 확인할 수 없어요.'};
}
