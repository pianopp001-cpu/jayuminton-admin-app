#!/usr/bin/env python3
"""Admin-only same-group multi-select patch. Never edits user frontend."""
from pathlib import Path
import sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('source-snapshot/current-main')
p=root/'Script.html'; s=p.read_text(encoding='utf-8')

def rep(a,b,label):
 global s
 if a not in s: raise SystemExit(label+' anchor not found')
 s=s.replace(a,b,1)

# Replace the legacy one-person QUICK_PICK behavior for court/wait taps.
# Same group: each tap toggles membership in SELECTED (1 -> 2 -> 3 -> 4).
# Cross-group actions remain explicit via empty-slot/action buttons.
old='''function handleCourtMemberTap(courtNo, memberId, event) {
  if (event && event.target && event.target.closest('button.small')) return;
  if (consumeLongPressClick(memberId, event)) return;
  if (assignMemberToChosenEmpty(memberId, event)) return;
  const now = Date.now();
  const isDoubleTap = LAST_COURT_MEMBER_TAP.memberId === memberId &&
    now - LAST_COURT_MEMBER_TAP.tappedAt <= 420;
  LAST_COURT_MEMBER_TAP = isDoubleTap
    ? { memberId:'', tappedAt:0 }
    : { memberId:memberId, tappedAt:now };
  if (isDoubleTap) {
    if (event) { event.preventDefault(); event.stopPropagation(); }
    cancelQuickPick();
    runAction('setMemberStatus', [ADMIN_PIN_VALUE, [memberId], 'active']);
    return;
  }
  quickPickMember('court', courtNo, memberId, event);
}'''
new='''function handleCourtMemberTap(courtNo, memberId, event) {
  if (event && event.target && event.target.closest('button.small')) return;
  if (consumeLongPressClick(memberId, event)) return;
  if (assignMemberToChosenEmpty(memberId, event)) return;
  if (event) { event.preventDefault(); event.stopPropagation(); }
  QUICK_PICK = null;
  toggleSelected(memberId);
}'''
rep(old,new,'court multiselect')

old='''function handleWaitMemberTap(groupIndex, memberId, event) {
  if (event && event.target && event.target.closest('button.small')) return;
  if (consumeLongPressClick(memberId, event)) return;
  if (assignMemberToChosenEmpty(memberId, event)) return;
  const now = Date.now();
  const isDoubleTap = LAST_WAIT_MEMBER_TAP.memberId === memberId &&
    now - LAST_WAIT_MEMBER_TAP.tappedAt <= 420;
  LAST_WAIT_MEMBER_TAP = isDoubleTap
    ? { memberId:'', tappedAt:0 }
    : { memberId:memberId, tappedAt:now };
  if (isDoubleTap) {
    if (event) { event.preventDefault(); event.stopPropagation(); }
    cancelQuickPick();
    runAction('setMemberStatus', [ADMIN_PIN_VALUE, [memberId], 'active']);
    return;
  }
  quickPickMember('wait', groupIndex, memberId, event);
}'''
new='''function handleWaitMemberTap(groupIndex, memberId, event) {
  if (event && event.target && event.target.closest('button.small')) return;
  if (consumeLongPressClick(memberId, event)) return;
  if (assignMemberToChosenEmpty(memberId, event)) return;
  if (event) { event.preventDefault(); event.stopPropagation(); }
  QUICK_PICK = null;
  toggleSelected(memberId);
}'''
rep(old,new,'wait multiselect')

p.write_text(s,encoding='utf-8')
print('admin vNext same-group multi-select patch prepared')
