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

# Replace each handler by function boundaries so existing formatting and
# double-tap implementation details do not matter.
def replace_function(text, name, replacement):
    start = text.find('function ' + name + '(')
    if start < 0:
        raise SystemExit(name + ' function missing')
    end = text.find('\nfunction ', start + len(name) + 10)
    if end < 0:
        raise SystemExit(name + ' function end missing')
    return text[:start] + replacement.rstrip() + '\n' + text[end:]

court = """function handleCourtMemberTap(courtNo, memberId, event) {
  if (event && event.target && event.target.closest('button.small')) return;
  if (consumeLongPressClick(memberId, event)) return;
  if (assignMemberToChosenEmpty(memberId, event)) return;
  if (event) { event.preventDefault(); event.stopPropagation(); }
  QUICK_PICK = null;
  toggleSelected(memberId);
}"""
wait = """function handleWaitMemberTap(groupIndex, memberId, event) {
  if (event && event.target && event.target.closest('button.small')) return;
  if (consumeLongPressClick(memberId, event)) return;
  if (assignMemberToChosenEmpty(memberId, event)) return;
  if (event) { event.preventDefault(); event.stopPropagation(); }
  QUICK_PICK = null;
  toggleSelected(memberId);
}"""
s = replace_function(s, 'handleCourtMemberTap', court)
s = replace_function(s, 'handleWaitMemberTap', wait)

p.write_text(s,encoding='utf-8')
print('admin vNext same-group multi-select patch prepared')
