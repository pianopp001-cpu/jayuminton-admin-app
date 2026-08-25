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
  function syncBottomTeamLabels(root){
    var app=root&&root.querySelectorAll?root:document;
    var cards=app.querySelectorAll('#adminApp '+CARD_SELECTOR.split(',').join(',#adminApp '));
    for(var i=0;i<cards.length;i++){
      var card=cards[i],team=teamOf(card);
      if(team){
        card.setAttribute('data-jm-team-text',team);
        card.classList.add('has-member-team');
        // Persistent team identity is always the two-line border/outline.
        // Never leave an inline box-shadow:none!important here because that
        // would suppress the temporary match-pair color layered above it.
        card.style.removeProperty('box-shadow');
      }
      var nodes=card.querySelectorAll('[data-team-label],.member-team-badge,.jm-team-badge,.team-badge,.team-label,span,small,label,b,strong,em,i');
      for(var j=0;j<nodes.length;j++){
        var node=nodes[j];
        if(node.classList&&node.classList.contains('jm-team-bottom-label'))continue;
        if(normalizeTeam((node.getAttribute&&node.getAttribute('data-team-label'))||node.textContent)){
          node.textContent='';
          node.style.setProperty('display','none','important');
          node.style.setProperty('visibility','hidden','important');
          node.setAttribute('aria-hidden','true');
        }
      }
      var bottom=card.querySelector(':scope > .jm-team-bottom-label');
      if(team){
        if(!bottom){bottom=document.createElement('div');bottom.className='jm-team-bottom-label';card.appendChild(bottom);}
        bottom.textContent=team;
        bottom.setAttribute('data-team-label',team);
      }else if(bottom){bottom.remove();}
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
  function compactTeamsInParent(parent){
    var cards=directCardChildren(parent);
    if(cards.length<2)return;
    var groups={},plain=[];
    cards.forEach(function(card){
      var t=teamOf(card);
      if(t){if(!groups[t])groups[t]=[];groups[t].push(card);}else plain.push(card);
    });
    var teamKeys=Object.keys(groups).filter(function(t){return groups[t].length>1;}).sort(function(a,b){return teamNumber(a)-teamNumber(b);});
    if(!teamKeys.length)return;
    var next=[];
    teamKeys.forEach(function(t){groups[t].forEach(function(card){next.push(card);});});
    cards.forEach(function(card){var t=teamOf(card);if(t&&groups[t]&&groups[t].length<=1)next.push(card);});
    plain.forEach(function(card){next.push(card);});
    if(next.length!==cards.length)return;
    var changed=false;
    for(var i=0;i<cards.length;i++){if(cards[i]!==next[i]){changed=true;break;}}
    if(!changed)return;
    next.forEach(function(card){parent.appendChild(card);});
  }
  function compactSameTeams(){
    var app=document.getElementById('adminApp');if(!app)return;
    var parents=[];
    var cards=app.querySelectorAll(CARD_SELECTOR);
    for(var i=0;i<cards.length;i++){
      var p=cards[i].parentElement;
      if(p&&parents.indexOf(p)<0)parents.push(p);
    }
    parents.forEach(compactTeamsInParent);
  }
  function installStyle(){
    if(document.getElementById('jayuminton-admin-team-layout-v2038'))return;
    var style=document.createElement('style');
    style.id='jayuminton-admin-team-layout-v2038';
    style.textContent='#adminApp .member-team-badge,#adminApp .jm-team-badge,#adminApp .team-badge,#adminApp .team-label,#adminApp [data-team-label]:not(.jm-team-bottom-label){display:none!important;visibility:hidden!important;width:0!important;height:0!important;min-width:0!important;max-width:0!important;margin:0!important;padding:0!important;border:0!important;overflow:hidden!important;pointer-events:none!important;font-size:0!important;line-height:0!important}#adminApp .has-member-team{position:relative!important;border:2px solid var(--member-team-color)!important;outline:2px solid var(--member-team-color)!important;outline-offset:-5px!important;padding-right:inherit!important}#adminApp .has-member-team.jm-temp-pair{box-shadow:0 0 0 3px var(--jm-temp-pair-color)!important}#adminApp .jm-team-bottom-label{position:static!important;display:block!important;visibility:visible!important;width:100%!important;height:auto!important;min-height:0!important;margin:2px 0 0!important;padding:0!important;border:0!important;background:transparent!important;text-align:center!important;font-size:7px!important;line-height:1.1!important;font-weight:900!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:clip!important;pointer-events:none!important}';
    (document.head||document.documentElement).appendChild(style);
  }
  function apply(){installStyle();syncBottomTeamLabels(document);compactSameTeams();syncBottomTeamLabels(document);}
  function boot(){
    var app=document.getElementById('adminApp');if(!app){setTimeout(boot,100);return;}
    apply();
    if(app.__jmTeamLayoutV2038Observer)return;
    var scheduled=false;
    app.__jmTeamLayoutV2038Observer=new MutationObserver(function(){
      if(scheduled)return;scheduled=true;
      setTimeout(function(){scheduled=false;apply();},0);
    });
    app.__jmTeamLayoutV2038Observer.observe(app,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['data-team-label','data-jm-team-text','class','style']});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else setTimeout(boot,0);
})();
