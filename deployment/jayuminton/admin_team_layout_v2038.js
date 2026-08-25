(function installJayumintonAdminTeamLayoutV2038(){
  'use strict';
  if(window.__JAYUMINTON_ADMIN_TEAM_LAYOUT_V2038__)return;
  window.__JAYUMINTON_ADMIN_TEAM_LAYOUT_V2038__=true;
  var CARD_SELECTOR='.member,.person,.quick-member,.member-card,.member-item,.wait-card,.wait-item,.player-card,.court-player,[data-member-id],[data-memberid],[data-player-id]';
  function normalizeTeam(value){
    var text=String(value||'').replace(/\s+/g,'').trim();
    if(/^TEAM\d+$/i.test(text))text=text.replace(/^TEAM/i,'팀');
    return /^팀\d+$/.test(text)?text:'';
  }
  function teamOf(card){
    if(!card)return '';
    var direct=normalizeTeam(card.getAttribute&&card.getAttribute('data-jm-team-text'));
    if(direct)return direct;
    var nodes=card.querySelectorAll?card.querySelectorAll('[data-team-label],.member-team-badge,.jm-team-badge,.team-badge,.team-label,.jm-team-bottom-label,span,small,label,b,strong,em,i'):[];
    for(var i=0;i<nodes.length;i++){
      var t=normalizeTeam((nodes[i].getAttribute&&nodes[i].getAttribute('data-team-label'))||nodes[i].textContent);
      if(t)return t;
    }
    return '';
  }
  function rememberOfficialTeamAndRemoveText(root){
    var app=root&&root.querySelectorAll?root:document;
    var cards=app.querySelectorAll('#adminApp '+CARD_SELECTOR.split(',').join(',#adminApp '));
    for(var i=0;i<cards.length;i++){
      var card=cards[i],team=teamOf(card);
      if(team){
        card.setAttribute('data-jm-team-text',team);
        card.classList.add('has-member-team');
        card.style.removeProperty('box-shadow');
      }
      var nodes=card.querySelectorAll('[data-team-label],.member-team-badge,.jm-team-badge,.team-badge,.team-label,.jm-team-bottom-label,span,small,label,b,strong,em,i');
      for(var j=0;j<nodes.length;j++){
        var node=nodes[j];
        if(normalizeTeam((node.getAttribute&&node.getAttribute('data-team-label'))||node.textContent)){
          node.remove();
        }
      }
    }
  }
  function directCardChildren(parent){
    if(!parent||!parent.children)return [];
    var out=[];
    for(var i=0;i<parent.children.length;i++){
      var child=parent.children[i];
      if(child.matches&&child.matches(CARD_SELECTOR))out.push(child);
    }
    return out;
  }
  function teamNumber(team){var m=String(team||'').match(/(\d+)$/);return m?Number(m[1]):999999;}
  function tempPairKey(card){
    if(!card)return '';
    var keys=['data-jm-temp-pair-id','data-jm-temp-pair-key','data-temp-pair-id','data-pair-id','data-pair-key'];
    for(var i=0;i<keys.length;i++){
      var v=String(card.getAttribute&&card.getAttribute(keys[i])||'').trim();
      if(v)return 'P:'+v;
    }
    if(card.classList&&card.classList.contains('jm-temp-pair')){
      var inline=card.style&&card.style.getPropertyValue('--jm-temp-pair-color');
      if(inline)return 'C:'+inline.trim();
      try{
        var computed=getComputedStyle(card).getPropertyValue('--jm-temp-pair-color');
        if(computed&&computed.trim())return 'C:'+computed.trim();
      }catch(e){}
      return 'P:temp';
    }
    return '';
  }
  function orderedByPairOrOfficial(cards){
    if(cards.length!==4)return cards.slice();
    var tempGroups={},tempPlain=[];
    cards.forEach(function(card){var k=tempPairKey(card);if(k){if(!tempGroups[k])tempGroups[k]=[];tempGroups[k].push(card);}else tempPlain.push(card);});
    var tempKeys=Object.keys(tempGroups).filter(function(k){return tempGroups[k].length>=2;});
    if(tempKeys.length){
      var next=[];
      tempKeys.forEach(function(k){tempGroups[k].slice(0,2).forEach(function(card){if(next.indexOf(card)<0)next.push(card);});});
      cards.forEach(function(card){if(next.indexOf(card)<0)next.push(card);});
      return next.slice(0,4);
    }
    var groups={},plain=[];
    cards.forEach(function(card){var t=teamOf(card);if(t){if(!groups[t])groups[t]=[];groups[t].push(card);}else plain.push(card);});
    var keys=Object.keys(groups).filter(function(t){return groups[t].length>=2;}).sort(function(a,b){return teamNumber(a)-teamNumber(b);});
    if(!keys.length)return cards.slice();
    var next2=[];
    keys.forEach(function(t){groups[t].slice(0,2).forEach(function(card){if(next2.indexOf(card)<0)next2.push(card);});});
    cards.forEach(function(card){if(next2.indexOf(card)<0)next2.push(card);});
    return next2.slice(0,4);
  }
  function compactPairsInParent(parent){
    var cards=directCardChildren(parent);
    if(cards.length!==4)return;
    var next=orderedByPairOrOfficial(cards);
    var changed=false;
    for(var i=0;i<cards.length;i++){if(cards[i]!==next[i]){changed=true;break;}}
    if(changed)next.forEach(function(card){parent.appendChild(card);});
  }
  function compactSameTeams(){
    var app=document.getElementById('adminApp');if(!app)return;
    var parents=[];
    var cards=app.querySelectorAll(CARD_SELECTOR);
    for(var i=0;i<cards.length;i++){
      var p=cards[i].parentElement;
      if(p&&parents.indexOf(p)<0)parents.push(p);
    }
    parents.forEach(compactPairsInParent);
  }
  function installStyle(){
    var old=document.getElementById('jayuminton-admin-team-layout-v2038');if(old)old.remove();
    var style=document.createElement('style');
    style.id='jayuminton-admin-team-layout-v2038';
    style.textContent='#adminApp .member-team-badge,#adminApp .jm-team-badge,#adminApp .team-badge,#adminApp .team-label,#adminApp .jm-team-bottom-label,#adminApp [data-team-label]{display:none!important;visibility:hidden!important;width:0!important;height:0!important;margin:0!important;padding:0!important;border:0!important;overflow:hidden!important;pointer-events:none!important;font-size:0!important;line-height:0!important}#adminApp .has-member-team{position:relative!important;border:2px solid var(--member-team-color)!important;outline:2px solid var(--member-team-color)!important;outline-offset:-5px!important;background-clip:padding-box!important}#adminApp .has-member-team.jm-temp-pair{box-shadow:inset 0 0 0 3px var(--jm-temp-pair-color),0 0 0 2px var(--jm-temp-pair-color)!important}#adminApp .jm-temp-pair:not(.has-member-team){box-shadow:inset 0 0 0 3px var(--jm-temp-pair-color),0 0 0 2px var(--jm-temp-pair-color)!important}';
    (document.head||document.documentElement).appendChild(style);
  }
  function apply(){installStyle();rememberOfficialTeamAndRemoveText(document);compactSameTeams();rememberOfficialTeamAndRemoveText(document);}
  function boot(){
    var app=document.getElementById('adminApp');if(!app){setTimeout(boot,100);return;}
    apply();
    if(app.__jmTeamLayoutV2038Observer)return;
    var scheduled=false;
    app.__jmTeamLayoutV2038Observer=new MutationObserver(function(){
      if(scheduled)return;scheduled=true;
      setTimeout(function(){scheduled=false;apply();},16);
    });
    app.__jmTeamLayoutV2038Observer.observe(app,{childList:true,subtree:true,attributes:true,attributeFilter:['data-team-label','data-jm-team-text','data-jm-temp-pair-id','data-jm-temp-pair-key','data-pair-id','data-pair-key','class','style']});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else setTimeout(boot,0);
})();
