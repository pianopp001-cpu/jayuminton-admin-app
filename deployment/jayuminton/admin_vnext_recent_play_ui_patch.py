#!/usr/bin/env python3
"""Admin Script-only UI patch for derived recent-play statistic."""
from pathlib import Path
import sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('source-snapshot/current-main')
p=root/'Script.html'; s=p.read_text(encoding='utf-8')
marker="""function adminVnextMemberBadges(member) {"""
if marker not in s: raise SystemExit('adminVnextMemberBadges anchor not found')
old="""  if (member.publicMemo) html += '<span class=\"member-vnext-memo\">' + escapeMemberInfo(member.publicMemo) + '</span>';\n  return html;"""
new="""  if (member.publicMemo) html += '<span class=\"member-vnext-memo\">' + escapeMemberInfo(member.publicMemo) + '</span>';\n  if (member.lastPlayedAt) {\n    const d=new Date(member.lastPlayedAt);\n    if(!isNaN(d.getTime())) html += '<span class=\"member-vnext-recent\">최근 ' + (d.getMonth()+1) + '/' + d.getDate() + ' ' + String(d.getHours()).padStart(2,'0') + ':' + String(d.getMinutes()).padStart(2,'0') + '</span>';\n  }\n  return html;"""
if old not in s: raise SystemExit('recent stat badge anchor not found')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('admin vNext recent-play card display patch prepared')
