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
