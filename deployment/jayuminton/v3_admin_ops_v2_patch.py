#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v3_admin_ops_v2_patch.py WORKDIR')
work = Path(sys.argv[1])
admin = work / 'Admin.html'
script = work / 'Script.html'
code = work / 'Code.js'
style = work / 'Style.html'

# 1) Admin header refresh beside undo + explicit NEW checkbox.
a = admin.read_text(encoding='utf-8')
if 'id="headerRefreshButton"' not in a:
    needle = '''    <button\n      id="undoButton"\n      class="ghost-button undo-button header-undo-button"\n      onclick="undoLastAction()"\n      disabled\n    >\n      ↶ 실행 취소\n    </button>'''
    repl = needle + '''\n\n    <button\n      id="headerRefreshButton"\n      class="ghost-button header-refresh-button"\n      type="button"\n      onclick="adminRefreshNow()"\n      title="현황 새로고침"\n    >↻ 새로고침</button>'''
    if needle not in a:
        raise SystemExit('admin header undo marker missing')
    a = a.replace(needle, repl, 1)
if 'id="newIsNew"' not in a:
    needle = '''      <input\n        id="newExperience"\n        maxlength="20"\n        placeholder="구력(선택, 예: 3년)"\n      >'''
    repl = needle + '''\n\n      <label class="new-member-check" title="체크해서 등록한 회원만 NEW로 표시됩니다.">\n        <input id="newIsNew" type="checkbox">\n        <span>신규</span>\n      </label>'''
    if needle not in a:
        raise SystemExit('newExperience marker missing')
    a = a.replace(needle, repl, 1)
if 'id="quickMoveName"' not in a:
    needle = '<div id="quickMoveBar" class="quick-move-bar hidden" aria-label="길게 누른 멤버 관리">'
    repl = needle + '\n    <strong id="quickMoveName" class="quick-move-full-name">선택 회원</strong>'
    if needle not in a:
        raise SystemExit('quickMoveBar marker missing')
    a = a.replace(needle, repl, 1)
admin.write_text(a, encoding='utf-8')

# 2) Backend: explicit NEW flag in Settings map; never infer from createdAt.
c = code.read_text(encoding='utf-8')
helper = r'''

/* JAYUMINTON_ADMIN_NEW_FLAG_V2 */
function memberNewFlags_() {
  try {
    const raw = String(getSetting_('MEMBER_NEW_FLAGS_JSON') || '{}');
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch (error) {
    return {};
  }
}
function decorateMemberNewFlags_(members) {
  const flags = memberNewFlags_();
  (members || []).forEach(function(member) {
    if (member) member.isNew = flags[String(member.id || '')] === true;
  });
  return members;
}
function setMemberNewFlag_(memberId, enabled) {
  memberId = String(memberId || '');
  if (!memberId) return;
  const flags = memberNewFlags_();
  if (enabled) flags[memberId] = true;
  else delete flags[memberId];
  setSetting_('MEMBER_NEW_FLAGS_JSON', JSON.stringify(flags));
}
function addMemberV2(pin, name, gender, grade, experience, isNew) {
  return withDocumentLock_('멤버 등록', function() {
    const result = addMemberUnlocked_(pin, name, gender, grade, experience);
    if (result && result.member) {
      const enabled = isNew === true || String(isNew) === 'true';
      setMemberNewFlag_(result.member.id, enabled);
      result.member.isNew = enabled;
    }
    return result;
  });
}
function updateMemberNewFlag(pin, memberId, isNew) {
  return withDocumentLock_('신규 표시 변경', function() {
    auth_(pin);
    setMemberNewFlag_(memberId, isNew === true || String(isNew) === 'true');
    touch_();
    return getPublicState();
  });
}
'''
if 'JAYUMINTON_ADMIN_NEW_FLAG_V2' not in c:
    c += helper
pat = "function getPublicState() {\n  ensureSetup_();\n\n  const members = readMembers_();"
segment = c[c.find('function getPublicState()'):c.find('function makeState_')]
if 'decorateMemberNewFlags_(members);' not in segment:
    if pat not in c:
        raise SystemExit('getPublicState marker missing')
    c = c.replace(pat, pat + "\n  decorateMemberNewFlags_(members);", 1)
pat2 = "function makeState_(members, courts, waitGroups, courtStartedAt) {\n  return {"
if pat2 in c and 'function makeState_(members, courts, waitGroups, courtStartedAt) {\n  decorateMemberNewFlags_(members);' not in c:
    c = c.replace(pat2, "function makeState_(members, courts, waitGroups, courtStartedAt) {\n  decorateMemberNewFlags_(members);\n  return {", 1)
# Partial court finish: keep existing players, increment only those players, and cycle normally.
c = c.replace("  if (finished.length !== GROUP_SIZE) {\n    throw new Error(\n      '4명이 모두 배정된 코트만 경기 종료할 수 있습니다.'\n    );\n  }", "  /* Partial courts may be ended too. Existing players are cycled; an empty court is a no-op. */")
code.write_text(c, encoding='utf-8')

# 3) Script: no missing placeholders, explicit NEW registration, full long-press name, strong saving UI.
s = script.read_text(encoding='utf-8')
old = """  if (!grade && !experience) {\n    return '<span class=\"member-info-detail is-missing\">급수·구력 미입력</span>';\n  }\n\n  const gradeText = grade || '급수 미입력';\n  const experienceText = experience ? '구력 ' + experience : '구력 미입력';\n\n  return '<span class=\"member-info-detail' +\n    ((!grade || !experience) ? ' is-missing' : '') + '\">' +\n    escapeMemberInfo(gradeText) + ' · ' + escapeMemberInfo(experienceText) +\n    '</span>';"""
new = """  const adminParts = [];\n  if (grade) adminParts.push(escapeMemberInfo(grade));\n  if (experience) adminParts.push(escapeMemberInfo(experience));\n  if (!adminParts.length) return '';\n  return '<span class=\"member-info-detail\">' + adminParts.join(' · ') + '</span>';"""
if old in s:
    s = s.replace(old, new, 1)
s = s.replace("'addMember','setMemberStatus'", "'addMember','addMemberV2','updateMemberNewFlag','setMemberStatus'")
addon = r'''

/* JAYUMINTON_ADMIN_OPS_V2 */
(function installAdminOpsV2(){
  if (typeof IS_ADMIN !== 'undefined' && !IS_ADMIN) return;

  function decorateAdminNewCards(){
    document.querySelectorAll('#adminApp [data-member-id]').forEach(function(card){
      var id=String(card.getAttribute('data-member-id')||'');
      if(!id)return;
      var member=null;
      try{member=typeof memberById==='function'?memberById(id):null;}catch(e){}
      var nameEl=card.querySelector('.name');
      if(!nameEl)return;
      var existing=nameEl.querySelector('.member-new-inline');
      if(member&&member.isNew===true){
        nameEl.textContent=String(member.name||'');
        var badge=document.createElement('span');
        badge.className='member-new-inline';
        badge.textContent='NEW';
        nameEl.appendChild(badge);
      }else if(existing){
        existing.remove();
      }
    });
  }

  window.adminRefreshNow = function(){
    if (typeof showAdminSaving_ === 'function') showAdminSaving_('현황 새로고침 중...');
    return server('getPublicState',[]).then(function(state){
      STATE = normalizeStateMemberProfiles(state);
      SELECTED.clear();
      renderState();
      decorateAdminNewCards();
    }).catch(function(error){
      alert(String((error && error.message) || error || '새로고침에 실패했습니다.'));
    }).finally(function(){ if (typeof hideAdminSaving_ === 'function') hideAdminSaving_(); });
  };

  window.addMember = async function(){
    if (ADD_MEMBER_IN_FLIGHT) return;
    var nameInput=document.getElementById('newName');
    var genderInput=document.getElementById('newGender');
    var gradeInput=document.getElementById('newGrade');
    var experienceInput=document.getElementById('newExperience');
    var newInput=document.getElementById('newIsNew');
    var button=document.getElementById('addMemberButton');
    var name=String(nameInput&&nameInput.value||'').trim();
    var gender=String(genderInput&&genderInput.value||'');
    var grade=String(gradeInput&&gradeInput.value||'').trim();
    var experience=String(experienceInput&&experienceInput.value||'').trim();
    if(!name){alert('이름 또는 닉네임을 입력하세요.');if(nameInput)nameInput.focus();return;}
    if(!gender){alert('성별을 선택하세요.');if(genderInput)genderInput.focus();return;}
    ADD_MEMBER_IN_FLIGHT=true;
    if(button){button.disabled=true;button.textContent='저장 중…';}
    if(typeof showAdminSaving_==='function')showAdminSaving_('회원 저장 중...');
    try{
      var result=await server('addMemberV2',[ADMIN_PIN_VALUE,name,gender,grade,experience,!!(newInput&&newInput.checked)]);
      if(result&&result.member){
        var member=normalizeMemberProfile(result.member);
        var idx=STATE.members.findIndex(function(x){return String(x.id)===String(member.id);});
        if(idx>=0)STATE.members[idx]=member;else STATE.members.push(member);
        renderState();
        decorateAdminNewCards();
      }else{
        await adminRefreshNow();
      }
      if(nameInput)nameInput.value='';
      if(genderInput)genderInput.value='';
      if(gradeInput)gradeInput.value='';
      if(experienceInput)experienceInput.value='';
      if(newInput)newInput.checked=false;
    }catch(error){alert(String((error&&error.message)||error));}
    finally{
      ADD_MEMBER_IN_FLIGHT=false;
      if(button){button.disabled=false;button.textContent='등록';}
      if(typeof hideAdminSaving_==='function')hideAdminSaving_();
    }
  };

  var oldSetActionBusy = window.setActionBusy;
  if (typeof oldSetActionBusy === 'function') {
    window.setActionBusy = function(busy){
      oldSetActionBusy(busy);
      if (busy) { if (typeof showAdminSaving_==='function') showAdminSaving_('저장 중...'); }
      else { if (typeof hideAdminSaving_==='function') hideAdminSaving_(); }
    };
  }

  var oldRenderState=window.renderState;
  if(typeof oldRenderState==='function'){
    window.renderState=function(state){
      var result=oldRenderState(state);
      setTimeout(decorateAdminNewCards,0);
      return result;
    };
  }
})();
'''
if 'JAYUMINTON_ADMIN_OPS_V2' not in s:
    pos=s.rfind('</script>')
    if pos<0: raise SystemExit('Script closing tag missing')
    s=s[:pos]+addon+'\n'+s[pos:]
script.write_text(s, encoding='utf-8')

# 4) CSS: compact header pair, large saving overlay, tiny inline NEW after full name.
css = style.read_text(encoding='utf-8')
patch = r'''

/* JAYUMINTON_ADMIN_OPS_V2 */
#adminApp>header .wrap{flex-wrap:nowrap!important}
.header-undo-button,.header-refresh-button{flex:0 0 auto!important;min-height:34px!important;height:34px!important;padding:0 9px!important;border-radius:9px!important;font-size:10px!important;line-height:1!important;white-space:nowrap!important}
.header-refresh-button{font-weight:700!important;color:#475569!important}
.new-member-check{display:inline-flex!important;align-items:center!important;gap:5px!important;min-height:38px!important;padding:0 8px!important;border:1px solid #dbe3ef!important;border-radius:10px!important;background:#fff!important;font-size:11px!important;font-weight:800!important;white-space:nowrap!important}
.new-member-check input{min-height:0!important;width:15px!important;height:15px!important;margin:0!important}
.quick-move-full-name{max-width:180px!important;overflow:visible!important;text-overflow:clip!important;white-space:normal!important;font-size:12px!important;line-height:1.2!important}
.admin-saving-overlay{position:fixed!important;inset:0!important;z-index:99999!important;background:rgba(15,23,42,.42)!important;display:none!important;align-items:center!important;justify-content:center!important;pointer-events:all!important}
.admin-saving-overlay.show{display:flex!important}
.admin-saving-card{min-width:280px!important;padding:26px 30px!important;border-radius:20px!important;background:#fff!important;box-shadow:0 20px 60px rgba(15,23,42,.3)!important;text-align:center!important}
.admin-saving-card strong{font-size:22px!important;line-height:1.15!important;font-weight:950!important}
.admin-saving-card small{font-size:12px!important;color:#64748b!important}
.admin-saving-spinner{width:42px!important;height:42px!important;border-width:5px!important}
#adminApp .member-new-inline{display:inline-block!important;margin-left:3px!important;padding:0 2px!important;border-radius:3px!important;background:#f5f3ff!important;color:#7c3aed!important;font-size:6px!important;font-weight:900!important;line-height:9px!important;height:9px!important;vertical-align:middle!important;white-space:nowrap!important;box-shadow:none!important}
#adminApp .name:has(.member-new-inline){overflow:visible!important;text-overflow:clip!important;white-space:normal!important}
@media(max-width:620px){.header-undo-button,.header-refresh-button{font-size:9px!important;padding:0 6px!important;height:32px!important;min-height:32px!important}}
'''
if 'JAYUMINTON_ADMIN_OPS_V2' not in css:
    css = css.rstrip() + patch
style.write_text(css, encoding='utf-8')

checks = {
  admin:['headerRefreshButton','newIsNew','quickMoveName'],
  code:['JAYUMINTON_ADMIN_NEW_FLAG_V2','addMemberV2','decorateMemberNewFlags_','Partial courts may be ended too'],
  script:['JAYUMINTON_ADMIN_OPS_V2','회원 저장 중...','decorateAdminNewCards',"badge.textContent='NEW'"],
  style:['JAYUMINTON_ADMIN_OPS_V2','.header-refresh-button','.admin-saving-card strong','.member-new-inline']
}
for p, needles in checks.items():
    text=p.read_text(encoding='utf-8')
    for n in needles:
        if n not in text: raise SystemExit(f'missing {n!r} in {p.name}')
print('ADMIN_OPS_V2_OK')
