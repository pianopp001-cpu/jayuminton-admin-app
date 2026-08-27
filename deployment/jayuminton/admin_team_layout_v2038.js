(function installJayumintonAdminTeamLayoutV2064(){
  'use strict';
  if(window.__JAYUMINTON_ADMIN_TEAM_LAYOUT_V2064__)return;
  window.__JAYUMINTON_ADMIN_TEAM_LAYOUT_V2038__=true;
  window.__JAYUMINTON_ADMIN_TEAM_LAYOUT_V2064__=true;
  window.__JAYUMINTON_ADMIN_TEAM_CONTRACT_V2064__=true;

  var CARD_SELECTOR='.member,.person,.quick-member,.member-card,.member-item,.player-card,.court-player,[data-member-id],[data-memberid],[data-player-id]';
  var PALETTE=[
    '#6d28d9','#0891b2','#c2410c','#0f766e',
    '#be185d','#4f46e5','#15803d','#a16207',
    '#b91c1c','#0369a1','#7e22ce','#047857',
    '#c026d3','#1d4ed8','#4d7c0f','#9f1239'
  ];

  function app(){return document.getElementById('adminApp');}
  function memberId(card){
    if(!card||!card.getAttribute)return '';
    var attrs=['data-member-id','data-memberid','data-player-id','data-id','data-member'];
    for(var i=0;i<attrs.length;i++){
      var value=card.getAttribute(attrs[i]);
      if(value)return String(value);
    }
    var nested=card.querySelector&&card.querySelector('[data-member-id],[data-memberid],[data-player-id],[data-id],[data-member]');
    return nested?memberId(nested):'';
  }
  function members(){
    try{return typeof STATE!=='undefined'&&STATE&&Array.isArray(STATE.members)?STATE.members:[];}
    catch(_){return [];}
  }
  function memberById(id){
    return members().find(function(member){return String(member.id||'')===String(id);})||null;
  }
  function teamKey(member){
    return String(member&&(member.bundleId||member.teamId||member.teamLabel||member.team||member.teamName)||'').trim();
  }
  function teamLabel(member){
    return String(member&&(member.teamLabel||member.teamName||member.team)||'').trim();
  }
  function teamOrder(){
    var groups={};
    members().forEach(function(member){
      var key=teamKey(member);
      if(key&&!groups[key])groups[key]={key:key,label:teamLabel(member)};
    });
    return Object.keys(groups).map(function(key){return groups[key];}).sort(function(left,right){
      var leftNumber=Number((left.label.match(/\d+/)||[])[0]);
      var rightNumber=Number((right.label.match(/\d+/)||[])[0]);
      if(Number.isFinite(leftNumber)&&Number.isFinite(rightNumber)&&leftNumber!==rightNumber)return leftNumber-rightNumber;
      if(left.label!==right.label)return left.label<right.label?-1:1;
      return left.key<right.key?-1:left.key>right.key?1:0;
    }).map(function(group){return group.key;});
  }
  function colorFor(team){
    var index=teamOrder().indexOf(String(team||''));
    if(index<0)index=0;
    if(index<PALETTE.length)return PALETTE[index];
    return 'hsl('+Math.round((index*137.508)%360)+',72%,38%)';
  }
  function cards(){
    var root=app(),out=[];
    if(!root)return out;
    Array.prototype.forEach.call(root.querySelectorAll(CARD_SELECTOR),function(card){
      if(card.matches&&card.matches('.wait-card,.wait-item'))return;
      if(memberId(card)&&out.indexOf(card)<0)out.push(card);
    });
    return out;
  }
  function removeLegacyStyles(){
    [
      'jayuminton-admin-team-safety-v2037',
      'jayuminton-admin-team-layout-v2038',
      'jayuminton-admin-team-layout-v2060',
      'jayuminton-admin-team-layout-v2061',
      'jayuminton-admin-team-layout-v2062',
      'jm-team-v2063'
    ].forEach(function(id){var old=document.getElementById(id);if(old)old.remove();});
  }
  function hideTeamWords(card){
    var nodes=card.querySelectorAll?card.querySelectorAll('[data-team-label],.member-team-badge,.jm-team-badge,.team-badge,.team-label,.jm-team-bottom-label'):[];
    Array.prototype.forEach.call(nodes,function(node){
      node.style.setProperty('display','none','important');
      node.setAttribute('aria-hidden','true');
    });
  }
  function flagNewCard(card,member){
    var isNew=!!(member&&(member.isNew===true||String(member.isNew)==='1'||String(member.isNew).toLowerCase()==='true'));
    card.classList.toggle('jm-admin-new-card',isNew);
  }
  function sync(){
    var root=app();
    if(!root)return;
    removeLegacyStyles();
    Array.prototype.forEach.call(root.querySelectorAll('.wait-card,.wait-item'),function(container){
      container.classList.remove('has-member-team','jm-temp-team-v2047','jm-temp-pair');
      container.style.removeProperty('--member-team-color');
    });
    cards().forEach(function(card){
      var member=memberById(memberId(card));
      var team=teamKey(member);
      hideTeamWords(card);
      if(team){
        card.classList.add('has-member-team');
        card.setAttribute('data-jm-team-text',teamLabel(member)||team);
        // Do not trust a duplicated legacy teamColor value. The live team list
        // determines a unique color for every different permanent team.
        card.style.setProperty('--member-team-color',colorFor(team));
      }else{
        card.classList.remove('has-member-team');
        card.removeAttribute('data-jm-team-text');
        card.style.removeProperty('--member-team-color');
      }
      flagNewCard(card,member);
    });
  }
  function installStyle(){
    removeLegacyStyles();
    if(document.getElementById('jm-team-v2064'))return;
    var style=document.createElement('style');
    style.id='jm-team-v2064';
    style.textContent=''
      +'#adminApp .member-team-badge,#adminApp .jm-team-badge,#adminApp .team-badge,#adminApp .team-label,#adminApp .jm-team-bottom-label,#adminApp [data-team-label]{display:none!important;visibility:hidden!important;width:0!important;height:0!important;margin:0!important;padding:0!important;border:0!important;overflow:hidden!important;pointer-events:none!important;font-size:0!important;line-height:0!important}'
      +'#adminApp .has-member-team{position:relative!important;border-color:transparent!important;outline:1px solid var(--member-team-color,#6d28d9)!important;outline-offset:2px!important;box-shadow:0 0 0 4px rgba(255,255,255,.98),0 0 0 5px var(--member-team-color,#6d28d9)!important;overflow:visible!important;background-clip:padding-box!important}'
      +'#adminApp .has-member-team.jm-temp-team-v2047,#adminApp .has-member-team.jm-temp-pair,#adminApp .jm-temp-team-v2047,#adminApp .jm-temp-pair{outline:3px solid #d4a017!important;outline-offset:1px!important;box-shadow:none!important}'
      +'#adminApp .jm-admin-new-card{min-height:88px!important;padding-bottom:28px!important;overflow:visible!important}';
    (document.head||document.documentElement).appendChild(style);
  }
  function boot(){
    var root=app();
    if(!root){setTimeout(boot,100);return;}
    installStyle();
    sync();
    if(root.__jmTeamV2064)return;
    var queued=false;
    root.__jmTeamV2064=new MutationObserver(function(){
      if(queued)return;
      queued=true;
      requestAnimationFrame(function(){queued=false;sync();});
    });
    root.__jmTeamV2064.observe(root,{childList:true,subtree:true});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});
  else setTimeout(boot,0);
})();
