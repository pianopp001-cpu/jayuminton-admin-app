from pathlib import Path
import re

p = Path('deployment/jayuminton/cloudflare_v6_frontend_bridge.js')
s = p.read_text(encoding='utf-8')
original = s

# Cloudflare shared temp-team state is a 2-4 member group, not a two-person pair.
pat = re.compile(r"  function validTempPairs\(value\)\{.*?\n  \}\n  function loadLegacyTempPairs", re.S)
replacement = """  function validTempPairs(value){
    var used={};
    return (Array.isArray(value)?value:[]).map(function(x){
      if(!x||['wait','court'].indexOf(String(x.zone))<0)return null;
      var raw=(Array.isArray(x.members)&&x.members.length?x.members:[]).concat(Array.isArray(x.pairA)?x.pairA:[]).concat(Array.isArray(x.pairB)?x.pairB:[]);
      var ids=[];raw.forEach(function(v){v=String(v||'');if(v&&ids.indexOf(v)<0)ids.push(v);});ids=ids.slice(0,4);
      if(ids.length<2||ids.some(function(id){return !!used[id];}))return null;
      ids.forEach(function(id){used[id]=1;});
      return {members:ids,pairA:ids.slice(0,2),pairB:ids.slice(2,4),zone:String(x.zone),createdAt:Number(x.createdAt)||Date.now()};
    }).filter(Boolean);
  }
  function tempTeamIds(group){
    var raw=(Array.isArray(group&&group.members)?group.members:[]).concat(Array.isArray(group&&group.pairA)?group.pairA:[]).concat(Array.isArray(group&&group.pairB)?group.pairB:[]);
    var ids=[];raw.forEach(function(v){v=String(v||'');if(v&&ids.indexOf(v)<0)ids.push(v);});return ids.slice(0,4);
  }
  function loadLegacyTempPairs"""
s, n = pat.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('validTempPairs block not found')

# Every member of the temporary group gets one dark-yellow border. Do not repaint only pairA.
s = s.replace("loadTempPairs().forEach(function(group,index){var color=TEMP_PAIR_COLORS[index%TEMP_PAIR_COLORS.length];group.pairA.forEach(function(id){desired[String(id)]=color;});});",
              "loadTempPairs().forEach(function(group){tempTeamIds(group).forEach(function(id){desired[String(id)]='#d4a017';});});")

# Disable the old two-click/confirm pair controller whenever the v2047+ multi-action controller is installed.
s = s.replace("function handlePairClick(event){\n      if(event.defaultPrevented||event.button>0)return;",
              "function handlePairClick(event){\n      if(window.__JAYUMINTON_ADMIN_MULTI_ACTION_V2047__)return;\n      if(event.defaultPrevented||event.button>0)return;")

# Old safety CSS must not resize member cards or move NEW/name text after the new controller exists.
s = s.replace("function installAdminTeamSafetyStyle(){\n      if(document.getElementById('jayuminton-admin-team-safety-v2037'))return;",
              "function installAdminTeamSafetyStyle(){\n      if(window.__JAYUMINTON_ADMIN_MULTI_ACTION_V2047__)return;\n      if(document.getElementById('jayuminton-admin-team-safety-v2037'))return;")

# Any legacy pending two-person state is ignored by the new controller.
s = s.replace("function recordTempPair(first,second,group){",
              "function recordTempPair(first,second,group){\n      if(window.__JAYUMINTON_ADMIN_MULTI_ACTION_V2047__)return;")

if s == original:
    raise SystemExit('bridge was not changed')
if "tempTeamIds(group).forEach" not in s or "#d4a017" not in s:
    raise SystemExit('2-4 yellow team bridge patch missing')
if "if(window.__JAYUMINTON_ADMIN_MULTI_ACTION_V2047__)return;" not in s:
    raise SystemExit('legacy pair guard missing')

p.write_text(s, encoding='utf-8')
print('PATCH_BRIDGE_ADMIN_MULTISELECT_V2048_OK')
