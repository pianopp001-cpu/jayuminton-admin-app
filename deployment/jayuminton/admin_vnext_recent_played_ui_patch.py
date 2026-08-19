#!/usr/bin/env python3
"""Remove noisy recent/partner statistics from admin member cards."""
from pathlib import Path
import re
import sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('source-snapshot/current-main')
p=root/'Script.html'; s=p.read_text(encoding='utf-8')
marker="""function adminVnextMemberBadges(member) {"""
if marker not in s: raise SystemExit('member badge helper anchor not found')

def remove_function(text, name):
    needle = 'function ' + name + '('
    while needle in text:
        start = text.find(needle)
        brace = text.find('{', start)
        if brace < 0: raise SystemExit(name + ' function boundary missing')
        depth = 0
        quote = ''
        escape = False
        end = -1
        for i in range(brace, len(text)):
            ch = text[i]
            if quote:
                if escape: escape = False
                elif ch == '\\': escape = True
                elif ch == quote: quote = ''
                continue
            if ch in ("'", '"', '`'): quote = ch
            elif ch == '{': depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end < 0: raise SystemExit(name + ' function end missing')
        text = text[:start] + text[end:].lstrip('\n')
    return text

# Remove every previous deployment's helper/call/style before installing one
# canonical compact line. This also repairs the repeated timestamp regression.
s = remove_function(s, 'adminVnextRecentPlayed')
s = s.replace('adminVnextRecentPlayed(member) + ', '')
s = re.sub(r'<style id="adminVnextRecentPlayedStyle">[\s\S]*?</style>\s*', '', s)

helper='''function adminVnextRecentPlayed(member) {
  return '';
}

'''
s=s.replace(marker,helper+marker,1)
s=s.replace('adminVnextRecentPlayed(member) + ', '')
style='''\n<style id="adminVnextRecentPlayedStyle">.member-vnext-recent{display:none!important}</style>\n'''
script_end = s.rfind('</script>')
if script_end < 0: raise SystemExit('script end anchor not found')
s = s[:script_end + len('</script>')] + style + s[script_end + len('</script>'):]
if s.count('function adminVnextRecentPlayed(member)') != 1 or s.count('id="adminVnextRecentPlayedStyle"') != 1:
    raise SystemExit('compact partner UI must be unique')
p.write_text(s,encoding='utf-8')
print('admin vNext card statistics cleanup prepared')
