#!/usr/bin/env python3
"""Admin-only recent-played display. User frontend remains untouched."""
from pathlib import Path
import sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('source-snapshot/current-main')
p=root/'Script.html'; s=p.read_text(encoding='utf-8')
marker="""function adminVnextMemberBadges(member) {"""
if marker not in s: raise SystemExit('member badge helper anchor not found')
helper='''function adminVnextRecentPlayed(member) {
  if (!member || !member.lastPlayedAt) return '';
  const d = new Date(member.lastPlayedAt);
  if (isNaN(d.getTime())) return '';
  const mm=String(d.getMonth()+1).padStart(2,'0');
  const dd=String(d.getDate()).padStart(2,'0');
  const hh=String(d.getHours()).padStart(2,'0');
  const mi=String(d.getMinutes()).padStart(2,'0');
  return '<span class="member-vnext-recent">최근 '+mm+'/'+dd+' '+hh+':'+mi+'</span>';
}

'''
s=s.replace(marker,helper+marker,1)
s=s.replace("memberInfoDetailHtml(member) + adminVnextMemberBadges(member) +", "memberInfoDetailHtml(member) + adminVnextMemberBadges(member) + adminVnextRecentPlayed(member) +")
s=s.replace("memberInfoDetailHtml(member, '코트배정 대기') + adminVnextMemberBadges(member) +", "memberInfoDetailHtml(member, '코트배정 대기') + adminVnextMemberBadges(member) + adminVnextRecentPlayed(member) +")
style='''\n<style id="adminVnextRecentPlayedStyle">.member-vnext-recent{font-size:11px;opacity:.72;margin-left:4px;white-space:nowrap}</style>\n'''
script_end = s.rfind('</script>')
if script_end < 0: raise SystemExit('script end anchor not found')
s = s[:script_end + len('</script>')] + style + s[script_end + len('</script>'):]
p.write_text(s,encoding='utf-8')
print('admin vNext recent-played UI patch prepared')
