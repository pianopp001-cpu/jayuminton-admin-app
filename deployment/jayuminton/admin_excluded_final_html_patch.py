#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv)!=2: raise SystemExit('usage: admin_excluded_final_html_patch.py INDEX_HTML')
path=Path(sys.argv[1]); html=path.read_text(encoding='utf-8')
MARKER='__JAYUMINTON_ADMIN_EXCLUDED_ALWAYS_VISIBLE_V1__'

def balanced_element(source,start,name):
    tag=re.compile(r'</?'+re.escape(name)+r'\b[^>]*>',re.I)
    depth=0
    for match in tag.finditer(source,start):
        depth += -1 if match.group(0).startswith('</') else 1
        if depth==0: return source[start:match.end()],match.end()
    raise SystemExit('excluded panel closing tag missing')

if MARKER not in html:
    match=re.search(r'<(?P<tag>section|div)\b[^>]*class=["\'][^"\']*\bexcluded-panel\b[^"\']*["\'][^>]*>',html,re.I)
    if not match: raise SystemExit('excluded-panel section missing')
    excluded,excluded_end=balanced_element(html,match.start(),match.group('tag'))
    # Keep only the return-to-active control with the excluded roster. Game count
    # controls remain in the collapsible settings area.
    for handler in ('decreaseSelectedGames()','increaseSelectedGames()','resetSelectedGames()','selectAllMembers()'):
        excluded=re.sub(r'<button\b[^>]*onclick=["\']'+re.escape(handler)+r'["\'][^>]*>.*?</button>\s*','',excluded,count=1,flags=re.S|re.I)
    if 'setSelectedStatus' not in excluded or 'active' not in excluded:
        raise SystemExit('return-to-active control missing')
    excluded,n=re.subn(r'class=(["\'])([^"\']*\bexcluded-panel\b[^"\']*)\1',lambda m:'class='+m.group(1)+m.group(2).strip()+' admin-excluded-always-visible'+m.group(1),excluded,count=1,flags=re.I)
    if n!=1: raise SystemExit('excluded class update failed')
    # Remove original location first.
    html=html[:match.start()]+html[excluded_end:]
    # Place directly under Quick Assign, before wait summary.
    anchor=re.search(r'<section\b[^>]*class=["\'][^"\']*\bv4-wait-summary\b[^"\']*["\'][^>]*>',html,re.I)
    if not anchor: raise SystemExit('quick assignment wait-summary anchor missing')
    html=html[:anchor.start()]+excluded+'\n'+html[anchor.start():]
    style='''<style id="adminExcludedAlwaysVisibleFinalStyle">
#adminApp .admin-excluded-always-visible{display:block!important;visibility:visible!important;margin-top:12px!important}
#adminApp .admin-excluded-always-visible .roster{max-height:none!important;overflow:visible!important}
</style>\n<!-- '''+MARKER+''' -->\n'''
    if '</head>' not in html: raise SystemExit('head closing tag missing')
    html=html.replace('</head>',style+'</head>',1)

details_start=html.find('<details class="admin-setup-details"')
details_end=html.find('</details>',details_start)
visible_pos=html.find('admin-excluded-always-visible')
if details_start>=0 and details_end>=0 and details_start<visible_pos<details_end:
    raise SystemExit('excluded roster still collapsible')
if html.count('id="excludedMembers"')!=1: raise SystemExit('excluded roster must exist exactly once')
for required in (MARKER,'admin-excluded-always-visible','id="excludedMembers"','코트배정 대기로 복귀'):
    if required not in html: raise SystemExit('excluded final marker missing: '+required)
path.write_text(html,encoding='utf-8')
print('ADMIN_EXCLUDED_ALWAYS_VISIBLE_FINAL_OK')
