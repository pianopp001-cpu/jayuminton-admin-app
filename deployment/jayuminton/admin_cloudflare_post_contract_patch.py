#!/usr/bin/env python3
"""Cloudflare admin post-contract hardening. No Google Apps Script writes/deploys."""
# recovery verification trigger 2026-08-25: force direct Cloudflare admin deploy under workflow-result watcher
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
html = path.read_text(encoding='utf-8')
marker = '</body>'
if marker not in html:
    raise SystemExit('body end marker missing')

def matching_brace(text, open_pos):
    depth = 0; quote = ''; escape = False
    for i in range(open_pos, len(text)):
        ch = text[i]
        if quote:
            if escape: escape = False
            elif ch == '\\': escape = True
            elif ch == quote: quote = ''
            continue
        if ch in ('\"', "'", '`'): quote = ch
        elif ch == '{': depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0: return i
    return -1

# Empty court finish remains legal.
for old, new in (
    ('(STATE.courts[courtNo] || []).length === 4', 'Array.isArray(STATE.courts[courtNo])'),
    ('(STATE.courts[courtNo] || []).length > 0', 'Array.isArray(STATE.courts[courtNo])'),
    ('state.courts[no].length === 4', 'Array.isArray(state.courts[no])'),
    ('state.courts[no].length > 0', 'Array.isArray(state.courts[no])'),
): html = html.replace(old, new)

md_finish = "function finishText(courtNo,members){var calls=(members||[]).map(cleanName).filter(Boolean).map(function(n){return n+' 님';});var base=Number(courtNo)+'번 코트 나왔습니다.';return calls.length?base+'\\n'+calls.join(', ')+'\\n'+Number(courtNo)+'번 코트로 들어가 주세요.':base+'\\n대기 1번에 입장할 인원이 없습니다.';}"
finish_start = html.find('function finishText(courtNo,members)')
if finish_start < 0: finish_start = html.find('function finishText(courtNo, members)')
if finish_start >= 0:
    open_brace = html.find('{', finish_start); close_brace = matching_brace(html, open_brace)
    if open_brace >= 0 and close_brace >= 0: html = html[:finish_start] + md_finish + html[close_brace + 1:]
html = html.replace("courtNo + '번 코트 경기가 종료되었습니다. '", "courtNo + '번 코트 나왔습니다. '")
html = html.replace("courtNo + '번 코트 경기가 종료되었습니다.'", "courtNo + '번 코트 나왔습니다.'")
html = html.replace("window.NativeVoice.speak('court_finish_'+Date.now(),text,.88,1,'')", "window.NativeVoice.speak('court_finish_'+Date.now(),text,.82,1,'')", 1)
html = html.replace('heldUtterance.rate=.88', 'heldUtterance.rate=.82', 1)

# Remove older post-contract addons so this deploy is a true upgrade.
html = re.sub(r'\n?<style id="jayuminton-admin-post-contract-v2[1234]">[\s\S]*?</script>\s*', '\n', html, count=1, flags=re.I)

addon = r'''
<style id="jayuminton-admin-post-contract-v24">
/* JAYUMINTON_ADMIN_CLOUDFLARE_SAVE_LOCK_V24 */
#pairStatisticsModal .pair-statistics-modal{overflow-y:auto!important;padding-bottom:max(32px,env(safe-area-inset-bottom))!important}
#pairStatisticsModal .pair-statistics-list{max-height:none!important;height:auto!important;overflow:visible!important;padding-bottom:max(56px,calc(env(safe-area-inset-bottom) + 40px))!important}
#pairStatisticsModal .pair-statistics-row,#pairStatisticsModal .pair-statistics-partners{height:auto!important;max-height:none!important;overflow:visible!important;white-space:normal!important}
#jmAdminSavingLock{position:fixed!important;z-index:2147483000!important;inset:0!important;display:none!important;background:rgba(15,23,42,.20)!important;backdrop-filter:blur(1.5px)!important;pointer-events:none!important}
body.jm-admin-saving #jmAdminSavingLock{display:block!important}
#jmAdminSavingLock .jm-saving-pill{position:fixed!important;left:50%!important;top:max(18px,env(safe-area-inset-top))!important;transform:translateX(-50%)!important;padding:11px 18px!important;border-radius:999px!important;background:#111827!important;color:#fff!important;font-size:14px!important;font-weight:900!important;box-shadow:0 10px 32px rgba(0,0,0,.28)!important}
body.jm-admin-saving #adminApp button:not(.jm-voice-allowed),body.jm-admin-saving #adminApp input,body.jm-admin-saving #adminApp select,body.jm-admin-saving #adminApp textarea{cursor:not-allowed!important}
body.jm-admin-saving .court-voice-controls,body.jm-admin-saving .admin-voice-controls,body.jm-admin-saving [data-voice-control],body.jm-admin-saving [id*="voice" i]{position:relative!important;z-index:2147483645!important;pointer-events:auto!important}
#adminApp .member-public-memo,#adminApp .jm-public-memo{display:block!important;width:100%!important;margin-top:2px!important;font-size:9px!important;line-height:1.15!important;font-weight:700!important;color:#536178!important;text-align:center!important;white-space:normal!important;overflow-wrap:anywhere!important;word-break:keep-all!important}
</style>
<script id="jayuminton-admin-post-contract-v24-script">
(function(){
  if(window.__JAYUMINTON_ADMIN_POST_CONTRACT_V24__) return;
  window.__JAYUMINTON_ADMIN_POST_CONTRACT_V24__=true;
  window.__JAYUMINTON_ADMIN_EMPTY_COURT_FINISH_MD4__=true;
  window.__JAYUMINTON_ADMIN_STATISTICS_NO_CLIP_FINAL__=true;
  window.__JAYUMINTON_ADMIN_ALERT_ROLE_V24__={memberWaitAlert:'member-device-only',memberCourtAlert:'member-device-only',adminWaitVoice:false,adminTransitionVibration:false,adminCourtVoice:true,voiceRepeatCount:3,vibrationSets:8,vibrationsPerSet:3,fullCourtVoiceSet:true,finishWording:'court-number-roster-enter',voiceRate:.82};
  window.__JAYUMINTON_TRANSITION_ALERT__=function(){return;};

  var busyCount=0;
  var MUTATIONS=new Set(['addMember','updateMemberProfile','setMemberStatus','setBundle','clearBundle','sendMemberMessage','deleteMembers','assignMembersToCourt','assignMembersToWaitGroup','smartAssignSelected','finishCourt','swapMembers','swapCourts','swapWaitGroups','moveOrSwapMember','undoLastAction','adjustMemberGames','decreaseSelectedGameCounts','resetSelectedGameCounts','resetAllOperationData','createManualBackup','restoreManualBackup','changeMemberPassword']);
  function isVoice(el){
    if(!el||!el.closest)return false;
    return !!el.closest('.court-voice-controls,.admin-voice-controls,[data-voice-control],[id*="voice" i],.voice-controls,.voice-control');
  }
  function ensureLock(){
    var el=document.getElementById('jmAdminSavingLock');
    if(!el){el=document.createElement('div');el.id='jmAdminSavingLock';el.innerHTML='<div class="jm-saving-pill">저장중 · 잠시만 기다려 주세요</div>';document.body.appendChild(el);}
    return el;
  }
  function setBusy(on){busyCount=Math.max(0,busyCount+(on?1:-1));ensureLock();document.body.classList.toggle('jm-admin-saving',busyCount>0);window.__JAYUMINTON_ADMIN_SAVING__=busyCount>0;}
  window.jmAdminSetSaving=function(on){setBusy(!!on);};

  ['pointerdown','click','dblclick','contextmenu'].forEach(function(type){
    document.addEventListener(type,function(e){
      if(!window.__JAYUMINTON_ADMIN_SAVING__||isVoice(e.target))return;
      e.preventDefault();e.stopImmediatePropagation();
    },true);
  });
  document.addEventListener('keydown',function(e){
    if(!window.__JAYUMINTON_ADMIN_SAVING__||isVoice(e.target))return;
    if(e.key==='Tab')return;
    e.preventDefault();e.stopImmediatePropagation();
  },true);

  function wrapServer(){
    var original=window.server;
    if(typeof original!=='function'||original.__jmCloudflareSaveLockV24)return false;
    function wrapped(name,args){
      var mutation=MUTATIONS.has(String(name||''));
      if(!mutation)return original.apply(this,arguments);
      setBusy(true);
      try{
        var result=original.apply(this,arguments);
        return Promise.resolve(result).finally(function(){setBusy(false);});
      }catch(error){setBusy(false);throw error;}
    }
    wrapped.__jmCloudflareSaveLockV24=true;wrapped.__original=original;window.server=wrapped;return true;
  }

  function syncPublicMemos(){
    var s=null;try{s=window.STATE||(typeof STATE!=='undefined'?STATE:null);}catch(_){return;}
    if(!s||!Array.isArray(s.members))return;
    var byId=new Map(s.members.map(function(m){return [String(m.id),String(m.publicMemo||'').trim()];}));
    document.querySelectorAll('#adminApp [data-member-id]').forEach(function(card){
      var memo=byId.get(String(card.getAttribute('data-member-id')||''))||'';
      var node=card.querySelector('.member-public-memo,.jm-public-memo');
      if(memo&&!node){node=document.createElement('span');node.className='member-public-memo';var target=card.querySelector('.member-info-detail')||card;target.insertAdjacentElement('afterend',node);}
      if(node){node.textContent=memo;node.hidden=!memo;}
    });
  }

  ensureLock();wrapServer();syncPublicMemos();
  var tries=0, timer=setInterval(function(){wrapServer();syncPublicMemos();if(++tries>120)clearInterval(timer);},500);
  new MutationObserver(function(){syncPublicMemos();}).observe(document.documentElement,{childList:true,subtree:true});
})();
</script>
'''
html = html.replace(marker, addon + '\n' + marker, 1)

for required in (
    'JAYUMINTON_ADMIN_CLOUDFLARE_SAVE_LOCK_V24','저장중 · 잠시만 기다려 주세요','jm-admin-saving',
    'court-voice-controls','__JAYUMINTON_ADMIN_SAVING__','MUTATIONS','member-public-memo','publicMemo','font-size:9px!important',
    '__JAYUMINTON_ADMIN_EMPTY_COURT_FINISH_MD4__','__JAYUMINTON_ADMIN_STATISTICS_NO_CLIP_FINAL__'
):
    if required not in html: raise SystemExit('post-contract marker missing: '+required)
for forbidden in ('(STATE.courts[courtNo] || []).length === 4','(STATE.courts[courtNo] || []).length > 0'):
    if forbidden in html: raise SystemExit('MD4 empty-court finish gate survived: '+forbidden)

path.write_text(html, encoding='utf-8')
print('ADMIN_POST_CONTRACT_V24_CLOUDFLARE_SAVE_LOCK_MEMO_OK')
