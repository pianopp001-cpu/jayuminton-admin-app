#!/usr/bin/env python3
import re, sys
from pathlib import Path
p=Path(sys.argv[1]); s=p.read_text(encoding='utf-8')

s=s.replace('선택 위치 자동배정','자동배정').replace('위치 자동배정','자동배정').replace('위치자동배정','자동배정')
# Finish voice must run for every non-empty court, not only a full four-player court.
s=s.replace("VOICE_GUIDE_ENABLED &&\n    'speechSynthesis' in window &&\n    (STATE.courts[courtNo] || []).length === 4", "VOICE_GUIDE_ENABLED &&\n    'speechSynthesis' in window &&\n    (STATE.courts[courtNo] || []).length >= 1")
# Partial courts are active games too: timer/ranking/local assignment must not revert to waiting.
s=s.replace("STATE.courts[courtNo].length === 4\n        ? new Date().toISOString()\n        : ''", "STATE.courts[courtNo].length > 0\n        ? (STATE.courtStartedAt[courtNo] || new Date().toISOString())\n        : ''")
s=s.replace("if (STATE.courts[key].length < 4) {\n      STATE.courtStartedAt[key] = '';\n    }", "if (STATE.courts[key].length === 0) {\n      STATE.courtStartedAt[key] = '';\n    }")
s=s.replace("STATE.courts[no].length === 4 && courtElapsedSeconds(no) > 0", "STATE.courts[no].length > 0 && courtElapsedSeconds(no) > 0")
s=s.replace("(ids.length === 4 ? formatElapsed(courtElapsedSeconds(courtNo)) : '대기')", "(ids.length > 0 ? formatElapsed(courtElapsedSeconds(courtNo)) : '대기')")

mobile_pat=re.compile(r'<div class="mobile-quick-bar">.*?</div>', re.S)
mobile_new='''<div class="mobile-quick-bar admin-bottom-controls" id="adminBottomControls">
    <button id="mobileUndoButton" class="ghost-button undo-button mobile-undo-button" onclick="undoLastAction()" disabled>실행취소</button>
    <button id="adminBottomRefresh" class="ghost-button" type="button" onclick="adminForceRefresh(this)">새로고침</button>
    <button id="adminBottomAutoAssign" class="primary mobile-assign-button" type="button" onclick="smartAssignSelected()">자동배정</button>
  </div>'''
s,n=mobile_pat.subn(mobile_new,s,count=1)
if n != 1: raise SystemExit('actual mobile-quick-bar marker missing')

patch=r'''<style id="jayuminton-admin-bottom-controls-style">
#adminBottomControls{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;align-items:stretch!important;gap:8px!important;width:100%!important;position:sticky!important;bottom:0!important;z-index:120!important;padding:10px!important;margin:12px 0 0!important;background:rgba(255,255,255,.96)!important;box-sizing:border-box!important}
#adminBottomControls button{display:block!important;width:100%!important;min-width:0!important;margin:0!important;white-space:nowrap!important;font-size:16px!important;font-weight:800!important;opacity:1!important;min-height:46px!important}
#mobileUndoButton{color:#111!important;background:#fff!important;border:2px solid #555!important;-webkit-text-fill-color:#111!important}
#mobileUndoButton:disabled{color:#333!important;background:#f3f3f3!important;border-color:#777!important;opacity:1!important;-webkit-text-fill-color:#333!important}
#adminApp .jm-multi-selected{outline:3px solid currentColor!important;outline-offset:2px!important;box-shadow:0 0 0 2px rgba(255,255,255,.85) inset!important}
#adminApp .jm-new-fullname{white-space:normal!important;overflow:visible!important;text-overflow:clip!important;max-width:none!important;width:auto!important;font-weight:800!important}
</style>
<script id="jayuminton-admin-behavior-preview-v10">
(function(){
  var activated=false, renderTimer=0;
  function app(){return document.getElementById('adminApp');}
  function visible(el){if(!el)return false;var cs=getComputedStyle(el);return !el.hidden&&cs.display!=='none'&&cs.visibility!=='hidden';}
  function adminVisible(){return visible(app());}
  window.adminForceRefresh=async function(button){var old=button&&button.textContent;if(button){button.disabled=true;button.textContent='갱신 중…';}try{await loadState();if(typeof loadSystemStatus==='function')await loadSystemStatus();}catch(e){alert(e&&e.message||e);}finally{if(button){button.disabled=false;button.textContent=old||'새로고침';}}};
  function hideDuplicateRefresh(){var keep=document.getElementById('adminBottomRefresh');document.querySelectorAll('#adminApp button,#adminApp a,[role="button"]').forEach(function(b){if(b===keep)return;var text=(b.textContent||'').replace(/\s+/g,'').trim(),aria=String(b.getAttribute('aria-label')||'').replace(/\s+/g,''),title=String(b.getAttribute('title')||'').replace(/\s+/g,''),id=String(b.id||'').toLowerCase(),cls=String(b.className||'').toLowerCase();if(text.indexOf('새로고침')>=0||aria.indexOf('새로고침')>=0||title.indexOf('새로고침')>=0||id.indexOf('refresh')>=0||cls.indexOf('refresh')>=0){b.hidden=true;b.style.setProperty('display','none','important');b.setAttribute('aria-hidden','true');}});}
  function enforceBottomControls(){var row=document.getElementById('adminBottomControls');if(!row)return;var buttons=row.querySelectorAll('button');if(buttons.length!==3)return;buttons[0].textContent='실행취소';if(!buttons[1].disabled)buttons[1].textContent='새로고침';buttons[2].textContent='자동배정';hideDuplicateRefresh();}
  function memberId(card){return String(card&&(card.getAttribute('data-member-id')||(card.dataset&&card.dataset.memberId))||'');}
  function selected(){return (typeof SELECTED!=='undefined'&&SELECTED)?SELECTED:null;}
  function syncSelectionPaint(){var set=selected(),a=app();if(!set||!a)return;a.querySelectorAll('[data-member-id]').forEach(function(card){var on=set.has(memberId(card));card.classList.toggle('selected',on);card.classList.toggle('jm-multi-selected',on);});if(typeof renderSelectionCount==='function')renderSelectionCount();}
  function locationOf(id){if(typeof STATE==='undefined'||!STATE)return null;for(var c=1;c<=4;c++){if((STATE.courts[c]||[]).indexOf(id)>=0)return{type:'court',index:c};}for(var w=0;w<(STATE.waitGroups||[]).length;w++){if((STATE.waitGroups[w]||[]).indexOf(id)>=0)return{type:'wait',index:w};}return{type:'other',index:-1};}
  function selectedLocations(){var set=selected();if(!set)return[];return Array.from(set).map(locationOf).filter(Boolean);}
  function sameSource(type,index){var locs=selectedLocations();return locs.length&&locs.every(function(x){return x.type===type&&Number(x.index)===Number(index);});}
  function toggleGroupMember(type,index,id,ev){var set=selected();if(!set)return;if(ev){ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();}if(set.has(id)){set.delete(id);syncSelectionPaint();return;}if(set.size&&!sameSource(type,index))set.clear();if(set.size>=4){alert('한 번에 최대 4명까지 선택할 수 있습니다.');return;}set.add(id);syncSelectionPaint();}
  function installGroupedSelection(){window.handleCourtMemberTap=function(courtNo,memberId,event){if(event&&event.target&&event.target.closest('button.small'))return;if(typeof consumeLongPressClick==='function'&&consumeLongPressClick(memberId,event))return;if(typeof assignMemberToChosenEmpty==='function'&&assignMemberToChosenEmpty(memberId,event))return;toggleGroupMember('court',Number(courtNo),String(memberId),event);};window.handleWaitMemberTap=function(groupIndex,memberId,event){if(event&&event.target&&event.target.closest('button.small'))return;if(typeof consumeLongPressClick==='function'&&consumeLongPressClick(memberId,event))return;if(typeof assignMemberToChosenEmpty==='function'&&assignMemberToChosenEmpty(memberId,event))return;toggleGroupMember('wait',Number(groupIndex),String(memberId),event);};}
  function targetGroup(type,index){return type==='court'?(STATE.courts[Number(index)]||[]):(STATE.waitGroups[Number(index)]||[]);}
  function groupedTargetTap(type,index,targetId,event){var set=selected();if(!set||!set.size)return false;var ids=Array.from(set),locs=ids.map(locationOf);if(!locs.every(function(x){return x&&x.type===locs[0].type&&Number(x.index)===Number(locs[0].index);}))return false;if(locs[0].type===type&&Number(locs[0].index)===Number(index))return false;var target=targetGroup(type,index),targetIds=[];if(targetId){var pos=target.indexOf(targetId);if(pos<0)return false;targetIds=target.slice(pos,pos+ids.length);if(targetIds.length!==ids.length){alert('교환할 상대 인원이 부족합니다.');return true;}}if(event){event.preventDefault();event.stopPropagation();event.stopImmediatePropagation();}if(targetIds.length){var source=locs[0],method=source.type==='court'&&type==='court'?'adjustCourtMembers':source.type==='wait'&&type==='wait'?'adjustWaitGroupMembers':'';if(!method){alert('코트와 대기조 사이는 빈 칸으로 이동해 주세요.');return true;}set.clear();runAction(method,[ADMIN_PIN_VALUE,Number(source.index),Number(index),ids,targetIds]);return true;}return false;}
  function interceptTargets(){var a=app();if(!a||a.__jmGroupCapture)return;a.__jmGroupCapture=true;a.addEventListener('click',function(ev){var card=ev.target&&ev.target.closest&&ev.target.closest('[data-member-id]');if(!card||ev.target.closest('button.small'))return;var id=memberId(card),loc=locationOf(id);if(loc)groupedTargetTap(loc.type,loc.index,id,ev);},true);}
  function isNewMember(m){return !!(m&&(m.isNew||m.newMember||m.is_new||m.new===true||m.newFlag||m.isNewMember));}
  function fullNewNames(){if(typeof STATE==='undefined'||!STATE||!Array.isArray(STATE.members))return;STATE.members.forEach(function(m){if(!isNewMember(m))return;document.querySelectorAll('#adminApp [data-member-id="'+String(m.id)+'"]').forEach(function(card){var name=card.querySelector('.member-name,.quick-member-name,.partial-name,.name');if(name){name.textContent=String(m.name||m.fullName||'');name.classList.add('jm-new-fullname');}});});}
  function afterRender(){if(!activated||!adminVisible())return;enforceBottomControls();fullNewNames();syncSelectionPaint();}
  function scheduleRender(){clearTimeout(renderTimer);renderTimer=setTimeout(afterRender,30);}
  function activate(){if(activated||!adminVisible())return false;activated=true;installGroupedSelection();interceptTargets();var a=app();new MutationObserver(scheduleRender).observe(a,{childList:true,subtree:true,attributes:true,attributeFilter:['class','hidden','style']});afterRender();setInterval(hideDuplicateRefresh,500);return true;}
  function waitForAdmin(){if(activate())return;var timer=setInterval(function(){if(activate())clearInterval(timer);},250);setTimeout(function(){clearInterval(timer);},120000);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',waitForAdmin,{once:true});else setTimeout(waitForAdmin,0);
})();
</script>'''
if '</body>' not in s: raise SystemExit('body marker missing')
s=s.replace('</body>',patch+'\n</body>',1)
for required in ['adminForceRefresh','jayuminton-admin-behavior-preview-v10','installGroupedSelection','fullNewNames','STATE.courts[no].length > 0']:
    if required not in s: raise SystemExit('missing '+required)
p.write_text(s,encoding='utf-8')
