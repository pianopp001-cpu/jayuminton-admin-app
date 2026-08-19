#!/usr/bin/env python3
"""Expose a compact sponsor badge in the shared member view only."""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
p = root / 'Style.html'
s = p.read_text(encoding='utf-8')

style = '''
<style id="memberSponsorPublicStyle">
  .member-vnext-badge.sponsor-badge{
    display:inline-flex!important;
    align-items:center!important;
    width:auto!important;
    max-width:100%!important;
    margin:2px!important;
    padding:1px 4px!important;
    font-size:8px!important;
    line-height:11px!important;
    border-radius:5px!important;
    white-space:nowrap!important;
  }
</style>
'''

s = re.sub(r'<style id="memberSponsorPublicStyle">[\s\S]*?</style>\s*', '', s)
if '</body>' in s:
    s = s.replace('</body>', style + '\n</body>', 1)
else:
    s += '\n' + style

if s.count('id="memberSponsorPublicStyle"') != 1:
    raise SystemExit('public sponsor badge style must be unique')

p.write_text(s, encoding='utf-8')
print('compact public sponsor badge style prepared')
