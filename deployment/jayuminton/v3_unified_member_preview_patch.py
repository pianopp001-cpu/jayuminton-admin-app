#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v3_unified_member_preview_patch.py WORKDIR')

work = Path(sys.argv[1])

# Preview-only backend/profile display widening. No spreadsheet write happens here.
code = work / 'Code.js'
s = code.read_text(encoding='utf-8')
s = s.replace("if (grade.length > 12)", "if (grade.length > 40)")
s = s.replace("급수는 12자 이내로 입력하세요.", "급수는 40자 이내로 입력하세요.")
s = s.replace("String(member.grade || '').slice(0, 12)", "String(member.grade || '').slice(0, 40)")
code.write_text(s, encoding='utf-8')

admin = work / 'Admin.html'
if admin.exists():
    a = admin.read_text(encoding='utf-8')
    a = a.replace('id="newGrade"\n        maxlength="12"', 'id="newGrade"\n        maxlength="40"')
    admin.write_text(a, encoding='utf-8')

controls = work / 'MemberControls.html'
c = controls.read_text(encoding='utf-8')
c = c.replace("ok.textContent='본인 맞아요'", "ok.textContent='네, 저예요'")
c = c.replace("[['대기',{type:'status',status:'active'}]", "[['코트배정대기',{type:'status',status:'active'}]")
controls.write_text(c, encoding='utf-8')

script = work / 'Script.html'
s = script.read_text(encoding='utf-8')
addon = r'''

/* JAYUMINTON_UNIFIED_MEMBER_PICK_PREVIEW_V1
   Same member interaction for installed Android WebView and normal web:
   - self card selected border
   - swap target selected border
   - empty destination selected border
   - self -> empty or empty -> self performs one-tap-per-card move
*/
(function installUnifiedMemberPickPreview(){
  if (typeof IS_ADMIN !== 'undefined' && IS_ADMIN) return;
  if (window.__JAYUMINTON_UNIFIED_MEMBER_PICK_PREVIEW_V1__) return;
  window.__JAYUMINTON_UNIFIED_MEMBER_PICK_PREVIEW_V1__ = true;

  var pendingDestination = null;
  var pendingDestinationElement = null;

  function selfId(){
    try { return String(typeof storedSelfMemberId === 'function' ? (storedSelfMemberId() || '') : ''); }
    catch (e) { return ''; }
  }

  function clearDestination(){
    document.querySelectorAll('.member-anywhere-destination-selected').forEach(function(el){
      el.classList.remove('member-anywhere-destination-selected');
    });
    pendingDestination = null;
    pendingDestinationElement = null;
  }

  function paintMemberRoles(ids){
    document.querySelectorAll('.member-anywhere-self-selected,.member-anywhere-target-selected').forEach(function(el){
      el.classList.remove('member-anywhere-self-selected','member-anywhere-target-selected');
    });
    var me = selfId();
    (ids || []).forEach(function(id){
      document.querySelectorAll('[data-member-id="'+String(id)+'"]').forEach(function(el){
        if (me && String(id) === me) el.classList.add('member-anywhere-self-selected');
        else el.classList.add('member-anywhere-target-selected');
      });
    });
  }

  function currentSelectedIds(){
    try {
      if (window.memberAnywhereSelection && typeof window.memberAnywhereSelection.current === 'function') {
        return window.memberAnywhereSelection.current().map(String);
      }
    } catch (e) {}
    return [];
  }

  function moveIfReady(){
    if (!pendingDestination) return false;
    var me = selfId();
    if (!me) return false;
    var ids = currentSelectedIds();
    if (ids.indexOf(me) < 0) return false;
    var destination = pendingDestination;
    clearDestination();
    try {
      if (typeof window.memberAnywhereMoveSelf === 'function') {
        window.memberAnywhereMoveSelf(destination);
        return true;
      }
    } catch (e) {}
    return false;
  }

  function destinationFromCard(card){
    if (!card) return null;
    var onclick = String(card.getAttribute('onclick') || '');
    var wait = onclick.match(/handleMemberWaitEmptyTap\((\d+),(\d+),event\)/);
    if (wait) return {type:'wait', group:Number(wait[1]), slotIndex:Number(wait[2])};
    var generic = onclick.match(/handleEmptySlotTap\('([^']+)'\s*,\s*'([^']+)'\s*,\s*(\d+)\s*,\s*event\)/);
    if (generic) {
      if (generic[1] === 'court') return {type:'court', courtNo:String(generic[2]), slotIndex:Number(generic[3])};
      if (generic[1] === 'wait') return {type:'wait', group:Number(generic[2]), slotIndex:Number(generic[3])};
    }
    return null;
  }

  document.addEventListener('click', function(event){
    var card = event.target && event.target.closest ? event.target.closest('.person.empty') : null;
    if (!card) return;
    var destination = destinationFromCard(card);
    if (!destination) return;

    event.preventDefault();
    event.stopImmediatePropagation();

    clearDestination();
    pendingDestination = destination;
    pendingDestinationElement = card;
    card.classList.add('member-anywhere-destination-selected');

    moveIfReady();
  }, true);

  document.addEventListener('memberAnywhereSelectionChanged', function(event){
    var ids = event && event.detail && Array.isArray(event.detail.ids) ? event.detail.ids.map(String) : [];
    paintMemberRoles(ids);
    if (!ids.length) {
      clearDestination();
      return;
    }
    if (ids.length > 1) {
      /* Person-to-person swap takes precedence over a previously picked empty slot. */
      clearDestination();
      return;
    }
    moveIfReady();
  });

  var style = document.createElement('style');
  style.id = 'jayuminton-unified-member-pick-preview-style';
  style.textContent = [
    '.member-self-star{position:static!important;inset:auto!important;transform:none!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;vertical-align:middle!important;min-width:22px!important;height:22px!important;padding:0 6px!important;margin:0 5px 2px 0!important;border-radius:999px!important;font-size:11px!important;line-height:22px!important;pointer-events:none!important;z-index:auto!important}',
    '.member-anywhere-selected,.member-anywhere-self-selected,.member-anywhere-target-selected{outline:4px solid #111!important;outline-offset:-4px!important;box-shadow:0 0 0 4px rgba(255,215,0,.95),0 5px 14px rgba(0,0,0,.24)!important;transform:scale(.97)!important}',
    '.member-anywhere-destination-selected{outline:4px solid #111!important;outline-offset:-4px!important;box-shadow:0 0 0 4px rgba(255,215,0,.95),0 5px 14px rgba(0,0,0,.24)!important;transform:scale(.97)!important}',
    '#memberApp .member-info-detail,#memberApp .member-info-detail *{white-space:normal!important;overflow:visible!important;text-overflow:clip!important;max-width:100%!important;overflow-wrap:anywhere!important;word-break:keep-all!important}',
    '#memberApp .person.member-info-card{height:auto!important;min-height:52px!important;overflow:visible!important}'
  ].join('');
  document.head.appendChild(style);
})();
'''

if 'JAYUMINTON_UNIFIED_MEMBER_PICK_PREVIEW_V1' not in s:
    pos = s.rfind('</script>')
    if pos < 0:
        raise SystemExit('Script.html closing script tag missing')
    s = s[:pos] + addon + '\n' + s[pos:]
script.write_text(s, encoding='utf-8')

# Sanity checks: fail the preview workflow instead of silently shipping a partial test build.
checks = {
    code: ['grade.length > 40', 'slice(0, 40)'],
    controls: ['네, 저예요', '코트배정대기'],
    script: ['JAYUMINTON_UNIFIED_MEMBER_PICK_PREVIEW_V1', 'member-anywhere-destination-selected', 'member-anywhere-target-selected']
}
for path, needles in checks.items():
    text = path.read_text(encoding='utf-8')
    for needle in needles:
        if needle not in text:
            raise SystemExit(f'missing unified preview patch {needle!r} in {path.name}')
