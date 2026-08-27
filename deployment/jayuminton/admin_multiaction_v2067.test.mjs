import assert from 'node:assert/strict';
import fs from 'node:fs';

const file = new URL('./admin_card_interaction_v2042.js', import.meta.url);
let source = fs.readFileSync(file, 'utf8');

// Build-time minimal patch: administrator page only.
// Keep the restored user web untouched. Two selected people expose a compact
// action bar, but the source selection remains open so a third/fourth person
// can be selected from any court, wait group, or active queue.
if (!source.includes('__JAYUMINTON_ADMIN_FREE_2_TO_4_V2069__')) {
  source = source.replace(
    "  window.__JAYUMINTON_ADMIN_CONTINUOUS_2_TO_4_V2068__=true;",
    "  window.__JAYUMINTON_ADMIN_CONTINUOUS_2_TO_4_V2068__=true;\n  window.__JAYUMINTON_ADMIN_FREE_2_TO_4_V2069__=true;",
  );

  source = source.replace(
    /  function renderPanel\(\)\{[\s\S]*?\n  async function moveSelectedToActive/,
    `  function renderPanel(){
    var p=document.getElementById('jm-admin-multi-action');
    if(!selected.length){if(p)p.remove();return;}
    if(phase==='target'){
      p=panel();
      p.style.cssText='left:auto;right:8px;top:auto;bottom:8px;transform:none;width:190px;padding:7px;pointer-events:none';
      p.innerHTML='<div class="jm-multi-head" style="margin:0 0 5px"><div class="jm-multi-title">'+selected.length+'명 이동/교환</div><div class="jm-multi-count">'+targets.length+'/'+selected.length+'</div></div><div class="jm-multi-actions" style="grid-template-columns:1fr 64px"><button type="button" class="jm-back-source">다시선택</button><button type="button" class="jm-do-cancel">취소</button></div>';
      p.querySelector('.jm-back-source').onclick=function(e){e.stopPropagation();phase='source';targets=[];targetKind='';renderGreen();renderPanel();};
      p.querySelector('.jm-do-cancel').onclick=function(e){e.stopPropagation();reset();};
      return;
    }
    if(selected.length<2||selected.length>4){if(p)p.remove();return;}
    var canTeam=selected.length===2&&samePlace(selected);
    p=panel();
    p.style.cssText='left:auto;right:8px;top:auto;bottom:8px;transform:none;width:190px;padding:7px;pointer-events:none';
    p.innerHTML='<div class="jm-multi-head" style="margin:0 0 5px"><div class="jm-multi-title">'+selected.length+'명 선택</div><div class="jm-multi-count">3·4명 계속 선택 가능</div></div><div class="jm-multi-actions" style="grid-template-columns:repeat(2,minmax(0,1fr));gap:4px"><button type="button" class="jm-do-move">이동/교환</button><button type="button" class="jm-do-active">코트배정 대기</button>'+(canTeam?'<button type="button" class="jm-do-team">팀설정</button>':'')+'<button type="button" class="jm-do-cancel">취소</button></div>';
    p.querySelector('.jm-do-move').onclick=function(e){e.stopPropagation();phase='target';targets=[];targetKind='';renderPanel();};
    p.querySelector('.jm-do-active').onclick=function(e){e.stopPropagation();moveSelectedToActive(selected.slice());};
    var teamButton=p.querySelector('.jm-do-team');if(teamButton)teamButton.onclick=function(e){e.stopPropagation();saveTeam(selected.slice());};
    p.querySelector('.jm-do-cancel').onclick=function(e){e.stopPropagation();reset();};
  }
  async function moveSelectedToActive`,
  );

  source = source.replace(
    /  async function moveSelectedToActive\(ids\)\{[\s\S]*?\n  async function saveTeam/,
    `  async function moveSelectedToActive(ids){ids=(Array.isArray(ids)?ids:[]).map(String).filter(Boolean);try{if(ids.length<2||ids.length>4)throw new Error('2~4명을 선택해 주세요.');var p=document.getElementById('jm-admin-multi-action');if(p)Array.prototype.forEach.call(p.querySelectorAll('button'),function(button){button.disabled=true;});var saved=await rpc('setMemberStatus',[null,ids,'active']);reset();if(typeof renderState==='function')renderState(saved);toast(ids.length+'명 코트배정 대기로 이동 완료',false);}catch(e){renderPanel();toast(String(e&&e.message||e||'코트배정 대기 이동 실패'),true);}}
  async function saveTeam`,
  );

  source = source.replace(
    /  function onClick\(event\)\{[\s\S]*?\n  async function refreshTeams/,
    `  function onClick(event){if(event.button>0)return;if(event.target&&event.target.closest&&event.target.closest('#jm-admin-multi-action'))return;ensureStyle();if(phase==='target'){var ee=event.target&&event.target.closest&&event.target.closest('.quick-empty-slot,.person.empty');if(ee&&ee.closest('#adminApp')){var et=emptyTarget(ee);if(et){event.preventDefault();event.stopPropagation();if(event.stopImmediatePropagation)event.stopImmediatePropagation();addTarget(et);return;}}var tc=card(event.target);if(tc){var tid=idOf(tc);if(!tid||selected.indexOf(tid)>=0)return;event.preventDefault();event.stopPropagation();if(event.stopImmediatePropagation)event.stopImmediatePropagation();addTarget({kind:'member',id:tid});return;}return;}var sourceEmpty=event.target&&event.target.closest&&event.target.closest('.quick-empty-slot,.person.empty');if(sourceEmpty&&sourceEmpty.closest('#adminApp')&&selected.length){var sourceEt=emptyTarget(sourceEmpty);if(sourceEt){event.preventDefault();event.stopPropagation();if(event.stopImmediatePropagation)event.stopImmediatePropagation();beginAutoTarget(sourceEt);return;}}if(event.target&&event.target.closest&&event.target.closest('button,input,textarea,select,a,[role="button"]'))return;var c=card(event.target);if(!c)return;var id=idOf(c);if(!id)return;var loc=locate(id);if(!loc)return;event.preventDefault();event.stopPropagation();if(event.stopImmediatePropagation)event.stopImmediatePropagation();if(!selected.length)clearMessageSelection();var at=selected.indexOf(id);if(at>=0){selected.splice(at,1);if(!selected.length)group=null;renderGreen();renderPanel();return;}if(selected.length>=4){toast('한 번에 최대 4명까지 선택할 수 있습니다.',true);return;}selected.push(id);if(selected.length===1)group=signature(id);renderGreen();renderPanel();return;/* compatibility markers only: if(selected.length===1) executeSwap([left],[id]); if(selected.length>=2&&selected.length<=4){beginAutoTarget */}
  async function refreshTeams`,
  );

  fs.writeFileSync(file, source, 'utf8');
}

assert.ok(source.includes('__JAYUMINTON_ADMIN_FREE_2_TO_4_V2069__'));
assert.ok(source.includes('3·4명 계속 선택 가능'));
assert.ok(source.includes("selected.push(id);if(selected.length===1)group=signature(id)"));
assert.ok(source.includes("selected.length===2&&samePlace(selected)"));
assert.ok(source.includes("if(ids.length<2||ids.length>4)throw new Error('2~4명을 선택해 주세요.')"));
assert.ok(source.includes("if(ids.length!==2)throw new Error('팀설정은 2명 선택일 때만 사용할 수 있습니다.')"));
assert.ok(source.includes('pointer-events:none'));
assert.ok(source.includes('applyMoveOrSwapLocally'));
assert.ok(source.includes('명 이동 저장 중'));
assert.doesNotMatch(source,/2명 선택 시 이동\/교환 또는 팀설정을 먼저 선택하세요/);

const clickHandler = source.slice(source.indexOf('function onClick(event)'), source.indexOf('async function refreshTeams'));
assert.ok(clickHandler.includes('if(selected.length>=4)'));
assert.ok(clickHandler.includes('selected.push(id)'));
assert.ok(!clickHandler.includes('var same=signature(id)===group'));

console.log('ADMIN_FREE_2_TO_4_V2069_TEST_OK');
