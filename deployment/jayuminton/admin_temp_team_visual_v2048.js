(function installAdminTempTeamVisualV2048(){
  'use strict';
  if(window.__JAYUMINTON_ADMIN_TEMP_TEAM_VISUAL_V2048__)return;
  window.__JAYUMINTON_ADMIN_TEMP_TEAM_VISUAL_V2048__=true;
  var id='jayuminton-admin-temp-team-visual-v2048-style';
  function style(){
    var s=document.getElementById(id);
    if(!s){s=document.createElement('style');s.id=id;(document.head||document.documentElement).appendChild(s);}
    s.textContent=''
      +'#adminApp .jm-temp-team-v2047,'
      +'#adminApp .jm-temp-team-v2047.jm-temp-pair,'
      +'#adminApp .has-member-team.jm-temp-team-v2047,'
      +'#adminApp .has-member-team.jm-temp-team-v2047.jm-temp-pair{'
      +'box-shadow:0 0 0 4px #d4a017!important;'
      +'outline:2px solid rgba(212,160,23,.28)!important;outline-offset:1px!important}'
      +'#adminApp .jm-source-selected:not(.jm-temp-team-v2047),#adminApp .jm-target-selected:not(.jm-temp-team-v2047){box-shadow:0 0 0 4px #16a34a!important}'
      +'#adminApp .jm-temp-pair-pending{outline:none!important}'
      +'#adminApp .jm-temp-team-v2047 .member-team-badge{display:none!important}';
  }
  function scrub(){
    style();
    var app=document.getElementById('adminApp');if(!app)return;
    app.querySelectorAll('.jm-temp-team-v2047').forEach(function(card){card.style.removeProperty('--jm-temp-pair-color');});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',scrub,{once:true});else scrub();
  var pending=false;
  new MutationObserver(function(){if(pending)return;pending=true;(window.requestAnimationFrame||setTimeout)(function(){pending=false;scrub();},16);}).observe(document.documentElement,{childList:true,subtree:true});
})();
