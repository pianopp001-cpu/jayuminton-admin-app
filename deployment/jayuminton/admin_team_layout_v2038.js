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
    var nodes=card.querySelectorAll?card.querySelectorAll('[data-team-label],.member-team-badge,.jm-team-badge,.team-badge,.team-label,.jm-team-bottom-label,span,label,b,strong,em,i'):[];
    for(var i=0;i<nodes.length;i++){
      var t=normalizeTeam((nodes[i].getAttribute&&nodes[i].getAttribute('data-team-label'))||nodes[i].textContent);
      if(t)return t;
    }
    return '';
  }
  function syncOfficialTeams(root){
    var app=root&&root.querySelectorAll?root:document;
    var cards=app.querySelectorAll('#adminApp '+CARD_SELECTOR.split(',').join(',#adminApp '));
    for(var i=0;i<cards.length;i++){
      var card=cards[i],team=teamOf(card);
      var nodes=card.querySelectorAll('[data-team-label],.member-team-badge,.jm-team-badge,.team-badge,.team-label');
      for(var j=0;j<nodes.length;j++){
        var node=nodes[j];
        if(normalizeTeam((node.getAttribute&&node.getAttribute('data-team-label'))||node.textContent)){
          node.style.setProperty('display','none','important');
          node.setAttribute('aria-hidden','true');
        }
      }
      var bottom=card.querySelector('.jm-team-bottom-label');
      if(team){
        card.setAttribute('data-jm-team-text',team);
        card.classList.add('has-member-team');
        if(!bottom){bottom=document.createElement('small');bottom.className='jm-team-bottom-label';card.appendChild(bottom);}
        bottom.textContent=team;
        if(card.lastElementChild!==bottom)card.appendChild(bottom);
      }else{
        card.removeAttribute('data-jm-team-text');
        card.classList.remove('has-member-team');
        if(bottom)bottom.remove();
      }
    }
  }
  function installStyle(){
    var old=document.getElementById('jayuminton-admin-team-layout-v2038');if(old)old.remove();
    var style=document.createElement('style');style.id='jayuminton-admin-team-layout-v2038';
    style.textContent='#adminApp .member-team-badge,#adminApp .jm-team-badge,#adminApp .team-badge,#adminApp .team-label,#adminApp [data-team-label]:not(.jm-team-bottom-label){display:none!important;visibility:hidden!important;width:0!important;height:0!important;margin:0!important;padding:0!important;border:0!important;overflow:hidden!important;pointer-events:none!important;font-size:0!important;line-height:0!important}#adminApp .jm-team-bottom-label{display:block!important;visibility:visible!important;position:static!important;float:none!important;clear:both!important;width:100%!important;height:auto!important;margin:3px 0 0!important;padding:0!important;border:0!important;text-align:left!important;font-size:9px!important;font-weight:900!important;line-height:1.1!important;white-space:nowrap!important;color:var(--member-team-color)!important;pointer-events:none!important}#adminApp .has-member-team{position:relative!important;border:2px solid var(--member-team-color)!important;outline:2px solid var(--member-team-color)!important;outline-offset:-5px!important;background-clip:padding-box!important;box-shadow:none!important;overflow:visible!important;padding-bottom:5px!important}#adminApp .has-member-team.jm-temp-pair,#adminApp .jm-temp-pair{box-shadow:0 0 0 3px var(--jm-temp-pair-color)!important}';
    (document.head||document.documentElement).appendChild(style);
  }
  function apply(){installStyle();syncOfficialTeams(document);}
  function boot(){
    var app=document.getElementById('adminApp');if(!app){setTimeout(boot,100);return;}
    apply();if(app.__jmTeamLayoutV2038Observer)return;
    var scheduled=false;app.__jmTeamLayoutV2038Observer=new MutationObserver(function(){if(scheduled)return;scheduled=true;setTimeout(function(){scheduled=false;apply();},16);});
    app.__jmTeamLayoutV2038Observer.observe(app,{childList:true,subtree:true,attributes:true,attributeFilter:['data-team-label','data-jm-team-text','class']});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else setTimeout(boot,0);
})();