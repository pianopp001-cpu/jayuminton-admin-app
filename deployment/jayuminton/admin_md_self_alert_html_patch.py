#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = 'JAYUMINTON_ADMIN_SELF_ALERT_HTML_V1'
ADDON = r'''
<script>
/* JAYUMINTON_ADMIN_SELF_ALERT_HTML_V1 */
(function installAdminSelfAlertV1(){
  if (window.__JAYUMINTON_ADMIN_SELF_ALERT_HTML_V1__) return;
  window.__JAYUMINTON_ADMIN_SELF_ALERT_HTML_V1__ = true;
  var STORAGE_KEY = 'jayuminton_admin_self_member_v1';
  var previousState = null;

  function cloneState(state){
    try { return JSON.parse(JSON.stringify(state || {})); } catch (error) { return null; }
  }
  function selectedId(){
    try { return String(JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}').id || ''); }
    catch (error) { return ''; }
  }
  function selectedName(){
    try { return String(JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}').name || ''); }
    catch (error) { return ''; }
  }
  function memberLocation(state,id){
    id=String(id||'');
    if(!id||!state)return null;
    var courts=state.courts||{};
    for(var no=1;no<=4;no++) if((courts[String(no)]||[]).map(String).indexOf(id)>=0) return {type:'court',key:String(no)};
    var waits=Array.isArray(state.waitGroups)?state.waitGroups:[];
    for(var i=0;i<waits.length;i++) if((waits[i]||[]).map(String).indexOf(id)>=0) return {type:'wait',index:i};
    var m=(state.members||[]).find(function(x){return x&&String(x.id)===id;});
    return m?{type:String(m.status||'active')}:null;
  }
  function stopVibration(){
    try { if(window.NativeMemberAlert&&typeof window.NativeMemberAlert.stop==='function') window.NativeMemberAlert.stop(); } catch(error){}
    try { if(navigator.vibrate) navigator.vibrate(0); } catch(error){}
  }
  function vibrate(){
    stopVibration();
    try {
      if(window.NativeMemberAlert&&typeof window.NativeMemberAlert.vibrateThreeByEight==='function'){
        window.NativeMemberAlert.vibrateThreeByEight(); return;
      }
    } catch(error){}
    try {
      if(navigator.vibrate){
        var p=[];
        for(var g=0;g<8;g++)for(var n=0;n<3;n++){p.push(360);if(!(g===7&&n===2))p.push(n===2?520:150);}
        navigator.vibrate(p);
      }
    } catch(error){}
  }
  function closeAlert(){
    stopVibration();
    var old=document.getElementById('adminSelfAlertOverlay'); if(old)old.remove();
  }
  function showAlert(title,body){
    closeAlert(); vibrate();
    var overlay=document.createElement('div'); overlay.id='adminSelfAlertOverlay';
    overlay.style.cssText='position:fixed;inset:0;z-index:2147483600;background:rgba(15,23,42,.58);display:flex;align-items:center;justify-content:center;padding:18px';
    overlay.innerHTML='<div style="width:min(430px,100%);background:#fff;border-radius:20px;padding:22px;box-shadow:0 24px 70px rgba(0,0,0,.3);text-align:center">'
      +'<div style="font-size:22px;font-weight:950;margin-bottom:12px">'+String(title||'알림')+'</div>'
      +'<div style="font-size:17px;font-weight:800;line-height:1.55;white-space:pre-line">'+String(body||'')+'</div>'
      +'<button type="button" id="adminSelfAlertConfirm" style="margin-top:18px;width:100%;min-height:48px;border:0;border-radius:13px;background:#315efb;color:#fff;font-size:17px;font-weight:950">확인</button></div>';
    document.body.appendChild(overlay);
    document.getElementById('adminSelfAlertConfirm').onclick=closeAlert;
  }
  function previousWaitOneNames(state){
    var ids=state&&Array.isArray(state.waitGroups)&&Array.isArray(state.waitGroups[0])?state.waitGroups[0].slice(0,4):[];
    return ids.map(function(id){var m=(state.members||[]).find(function(x){return x&&String(x.id)===String(id);});return m?String(m.name||''):'';}).filter(Boolean);
  }
  function detect(before,after){
    var id=selectedId(); if(!id||!before||!after)return;
    var a=memberLocation(before,id), b=memberLocation(after,id); if(!a||!b)return;
    if(a.type==='wait'&&a.index===1&&b.type==='wait'&&b.index===0){
      showAlert('대기 1순위 안내','대기1순위 입니다. 라켓 들고 준비해주세요.');
    } else if(a.type==='wait'&&a.index===0&&b.type==='court'){
      var names=previousWaitOneNames(before); var roster=names.length?'\n'+names.join(', '):'';
      showAlert('코트 배정 안내',b.key+'번 코트 나왔습니다.'+roster+'\n'+b.key+'번 코트로 들어가주세요.');
    }
  }
  function members(){
    try { return (typeof STATE!=='undefined'&&STATE&&Array.isArray(STATE.members))?STATE.members:[]; } catch(error){ return []; }
  }
  function openChooser(){
    var old=document.getElementById('adminSelfChooserOverlay'); if(old)old.remove();
    var list=members().slice().sort(function(a,b){return String(a.name||'').localeCompare(String(b.name||''),'ko');});
    var overlay=document.createElement('div'); overlay.id='adminSelfChooserOverlay';
    overlay.style.cssText='position:fixed;inset:0;z-index:2147483500;background:rgba(15,23,42,.55);display:flex;align-items:center;justify-content:center;padding:16px';
    var options='<option value="">선택 안 함</option>'+list.map(function(m){return '<option value="'+String(m.id).replace(/"/g,'&quot;')+'">'+String(m.name||'')+'</option>';}).join('');
    overlay.innerHTML='<div style="width:min(430px,100%);background:white;border-radius:18px;padding:18px"><h3 style="margin:0 0 8px">관리자 본인 알림</h3><div style="font-size:13px;color:#64748b;margin-bottom:12px">관리자도 경기 참여자일 때 본인을 선택하세요. 선택한 본인에게만 대기1·코트 알림이 울립니다.</div><select id="adminSelfChooser" style="width:100%;min-height:46px">'+options+'</select><div style="display:flex;gap:8px;margin-top:14px"><button id="adminSelfChooserCancel" type="button" style="flex:1;min-height:44px">취소</button><button id="adminSelfChooserSave" type="button" style="flex:1;min-height:44px;background:#315efb;color:#fff;border:0;border-radius:10px;font-weight:900">저장</button></div></div>';
    document.body.appendChild(overlay);
    var select=document.getElementById('adminSelfChooser'); select.value=selectedId();
    document.getElementById('adminSelfChooserCancel').onclick=function(){overlay.remove();};
    document.getElementById('adminSelfChooserSave').onclick=function(){
      var id=String(select.value||''); var m=list.find(function(x){return String(x.id)===id;});
      if(id&&m)localStorage.setItem(STORAGE_KEY,JSON.stringify({id:id,name:String(m.name||'')})); else localStorage.removeItem(STORAGE_KEY);
      overlay.remove(); mountButton(); previousState=cloneState(typeof STATE!=='undefined'?STATE:null);
    };
  }
  function mountButton(){
    if(typeof IS_ADMIN!=='undefined'&&!IS_ADMIN)return;
    var header=document.querySelector('#adminApp header .wrap.toolbar')||document.querySelector('#adminApp header .wrap')||document.querySelector('#adminApp header');var host=header&&header.querySelector(':scope>div:first-child');
    if(!host)return;
    var btn=document.getElementById('adminSelfAlertSettingButton');
    if(!btn){btn=document.createElement('button');btn.id='adminSelfAlertSettingButton';btn.type='button';btn.className='ghost-button';btn.onclick=openChooser;host.appendChild(btn);}
    btn.textContent='내 알림';
    btn.title=selectedId()?'관리자 본인 알림: '+(selectedName()||'설정됨'):'관리자 본인 알림 설정';
    btn.setAttribute('aria-label',btn.title);
    btn.style.cssText='display:inline-flex;align-items:center;justify-content:center;width:auto;min-width:58px;min-height:26px;height:26px;margin:4px 0 0;padding:3px 9px;border-radius:999px;white-space:nowrap;font-size:11px;line-height:1;font-weight:900;vertical-align:middle';
  }

  var originalRender=window.renderState;
  if(typeof originalRender==='function'){
    window.renderState=function(state){
      var before=previousState||cloneState(typeof STATE!=='undefined'?STATE:null);
      var result=originalRender.apply(this,arguments);
      var after=state||((typeof STATE!=='undefined')?STATE:null);
      try{detect(before,after);}catch(error){}
      previousState=cloneState(after); setTimeout(mountButton,0); return result;
    };
  }
  function start(){previousState=cloneState(typeof STATE!=='undefined'?STATE:null);mountButton();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){setTimeout(start,100);},{once:true});else setTimeout(start,100);
  window.addEventListener('pagehide',stopVibration);
})();
</script>
'''

path=Path(sys.argv[1])
text=path.read_text(encoding='utf-8')
if MARKER not in text:
    if '</body>' not in text: raise SystemExit('admin body closing tag missing')
    text=text.replace('</body>',ADDON+'\n</body>',1)
for needle in (MARKER,'adminSelfAlertSettingButton','NativeMemberAlert.vibrateThreeByEight','대기1순위 입니다','번 코트 나왔습니다'):
    if needle not in text: raise SystemExit('admin self alert html contract missing: '+needle)
path.write_text(text,encoding='utf-8')
