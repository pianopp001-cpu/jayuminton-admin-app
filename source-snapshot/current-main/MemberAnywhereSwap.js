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

function memberAnywhereLocationKey_(location){
  if(!location)return '';
  if(location.type==='court')return 'court:'+location.courtNo+':'+location.position;
  if(location.type==='wait')return 'wait:'+location.group+':'+location.position;
  if(location.type==='status')return 'status:'+location.status;
  return '';
}

function memberAnywhereSnapshot_(memberId){
  var location=memberAnywhereLocation_(memberId);
  return {memberId:String(memberId||''),locationKey:memberAnywhereLocationKey_(location)};
}

function memberAnywhereSwapSnapshot_(fromMemberId,toMemberId){
  return {
    from:memberAnywhereSnapshot_(fromMemberId),
    to:memberAnywhereSnapshot_(toMemberId)
  };
}

function memberAnywhereSwapCacheKey_(memberId){
  return 'ANYWHERE_SWAP_'+String(memberId||'');
}

function memberAnywhereSwapRequest_(requesterId,targetId){
  return {
    requesterId:String(requesterId||''),
    targetId:String(targetId||''),
    snapshot:memberAnywhereSwapSnapshot_(requesterId,targetId),
    createdAt:Date.now()
  };
}
