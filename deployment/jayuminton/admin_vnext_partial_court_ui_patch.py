#!/usr/bin/env python3
"""Admin Script patch: treat any occupied court as active/finishable. User frontend remains untouched."""
from pathlib import Path
import sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('source-snapshot/current-main')
p=root/'Script.html'; s=p.read_text(encoding='utf-8')
old="""    return state && state.courts && Array.isArray(state.courts[no]) &&
      state.courts[no].length === 4;"""
new="""    return state && state.courts && Array.isArray(state.courts[no]) &&
      state.courts[no].length > 0;"""
if old not in s: raise SystemExit('elapsed court full-only anchor not found')
s=s.replace(old,new,1)
# Defensive cleanup for admin-only messages/buttons that still describe full courts as the only finishable state.
s=s.replace('4명이 모두 배정된 코트만', '1명 이상 배정된 코트는')
s=s.replace('4명이 모두 채워진 코트만', '1명 이상 배정된 코트는')
p.write_text(s,encoding='utf-8')
print('admin vNext partial-court UI patch prepared')
