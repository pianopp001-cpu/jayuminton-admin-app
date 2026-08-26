(function installJayumintonAdminTeamLayoutV2038(){
  'use strict';
  if(window.__JAYUMINTON_ADMIN_TEAM_LAYOUT_V2038__)return;
  window.__JAYUMINTON_ADMIN_TEAM_LAYOUT_V2038__=true;
  var CARD_SELECTOR='.member,.person,.quick-member,.member-card,.member-item,.wait-card,.wait-item,.player-card,.court-player,[data-member-id],[data-memberid],[data-player-id]';
  function killLegacyTeamSafety(){var old=document.getElementById('jayuminton-admin-team-safety-v2037');if(old)old.remove();}
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
    killLegacyTeamSafety();
    var app=root&&root.querySelectorAll?root:document;
    var cards=app.querySelectorAll('#adminApp '+CARD_SELECTOR.split(',').join(',#adminApp '));
    for(var i=0;i<cards.length;i++){
      var card=cards[i],team=teamOf(card);
      var nodes=card.querySelectorAll('[data-team-label],.member-team-badge,.jm-team-badge,.team-badge,.team-label,.jm-team-bottom-label');
      for(var j=0;j<nodes.length;j++){
        var node=nodes[j];
        if(normalizeTeam((node.getAttribute&&node.getAttribute('data-team-label'))||node.textContent)){
          node.textContent='';node.style.setProperty('display','none','important');node.setAttribute('aria-hidden','true');
        }
      }
      if(team){
        if(card.getAttribute('data-jm-team-text')!==team)card.setAttribute('data-jm-team-text',team);
        card.classList.add('has-member-team');
      }else{
        card.removeAttribute('data-jm-team-text');card.classList.remove('has-member-team');
      }
    }
  }
  function installStyle(){
    killLegacyTeamSafety();
    if(document.getElementById('jayuminton-admin-team-layout-v2038'))return;
    var style=document.createElement('style');style.id='jayuminton-admin-team-layout-v2038';
    style.textContent='#adminApp .member-team-badge,#adminApp .jm-team-badge,#adminApp .team-badge,#adminApp .team-label,#adminApp .jm-team-bottom-label,#adminApp [data-team-label]{display:none!important;visibility:hidden!important;width:0!important;height:0!important;margin:0!important;padding:0!important;border:0!important;overflow:hidden!important;pointer-events:none!important;font-size:0!important;line-height:0!important}#adminApp .has-member-team{border:2px solid var(--member-team-color)!important;outline:2px solid var(--member-team-color)!important;outline-offset:-5px!important;background-clip:padding-box!important}#adminApp .has-member-team:not(.jm-temp-pair){box-shadow:none!important}#adminApp .has-member-team.jm-temp-pair,#adminApp .jm-temp-pair{box-shadow:0 0 0 3px var(--jm-temp-pair-color)!important}';
    (document.head||document.documentElement).appendChild(style);
  }
  function apply(){killLegacyTeamSafety();installStyle();syncOfficialTeams(document);}
  function boot(){
    var app=document.getElementById('adminApp');if(!app){setTimeout(boot,150);return;}
    apply();
    if(document.head&&!document.head.__jmLegacyTeamSafetyGuard){document.head.__jmLegacyTeamSafetyGuard=true;new MutationObserver(killLegacyTeamSafety).observe(document.head,{childList:true});}
    if(app.__jmTeamLayoutV2038Observer)return;
    var scheduled=false;app.__jmTeamLayoutV2038Observer=new MutationObserver(function(){if(scheduled)return;scheduled=true;requestAnimationFrame(function(){scheduled=false;syncOfficialTeams(app);});});
    app.__jmTeamLayoutV2038Observer.observe(app,{childList:true,subtree:true});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else setTimeout(boot,0);
})();
