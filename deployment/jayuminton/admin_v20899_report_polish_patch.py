#!/usr/bin/env python3
from pathlib import Path
import base64
import re
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'app/src/main/assets/admin/index.html')
s=p.read_text(encoding='utf-8')
MARKER='JAYUMINTON_GAME_REPORT_POLISH_V20899'
if MARKER in s:
    print('ADMIN_GAME_REPORT_POLISH_V20899_ALREADY_OK'); raise SystemExit(0)
for token in ('JAYUMINTON_GAME_REPORT_POSTER_V20895','JAYUMINTON_GAME_REPORT_HEADER_V20897','JAYUMINTON_GAME_REPORT_USABILITY_V20898','window.__JAYUMINTON_GAME_REPORT_V20895__'):
    if token not in s: raise SystemExit('v208.99 prerequisite missing: '+token)

css_path=Path(__file__).with_name('v20899_report_polish.css')
css=css_path.read_text(encoding='utf-8')
if 'JAYUMINTON_GAME_REPORT_POLISH_V20899_CSS' not in css: raise SystemExit('v208.99 css marker missing')
if '</head>' not in s: raise SystemExit('head anchor missing')
s=s.replace('</head>','<style id="jmReportPolishV20899Style">\n'+css+'\n</style>\n</head>',1)

# Remove the duplicated English rendering of the Korean club name.
if 'JAYUMINTON · BADMINTON CLUB' not in s: raise SystemExit('v208.97 kicker anchor missing')
s=s.replace('JAYUMINTON · BADMINTON CLUB','BADMINTON CLUB')

# Replace the v208.98 raster mascot with a simple dog visibly holding the racket handle in its paw.
dog_svg='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 130"><ellipse cx="66" cy="119" rx="43" ry="6" fill="#d7eee8"/><path d="M34 38C23 24 14 26 14 37s11 16 22 13M94 38c11-14 20-12 20-1s-11 16-22 13" fill="#f3c276" stroke="#17384a" stroke-width="4"/><path d="M31 55c0-24 15-37 34-37 21 0 36 14 35 38-1 20-15 31-35 31S31 75 31 55" fill="#fff8e9" stroke="#17384a" stroke-width="4"/><circle cx="52" cy="55" r="3.3" fill="#17384a"/><circle cx="77" cy="55" r="3.3" fill="#17384a"/><path d="M56 69c6 7 14 7 20 0" fill="none" stroke="#17384a" stroke-width="3" stroke-linecap="round"/><path d="M42 88c6-9 14-11 23-11 12 0 22 5 26 16l5 22c-9 7-18 10-31 10s-23-3-31-10z" fill="#d9f7ea" stroke="#17384a" stroke-width="4"/><path d="M88 91l17-7" stroke="#17384a" stroke-width="7" stroke-linecap="round"/><path d="M105 84l24-30" stroke="#146d87" stroke-width="5" stroke-linecap="round"/><ellipse cx="140" cy="40" rx="16" ry="22" transform="rotate(34 140 40)" fill="#fff" fill-opacity=".82" stroke="#146d87" stroke-width="4"/><path d="M129 29l22 19m-25-10 23 17m-12-35 20 17m-29 13 25-23" stroke="#74b7c4" stroke-width="1.5"/><circle cx="105" cy="84" r="6" fill="#fff8e9" stroke="#17384a" stroke-width="3"/></svg>'''
dog_uri='data:image/svg+xml;base64,'+base64.b64encode(dog_svg.encode('utf-8')).decode('ascii')
s,n=re.subn(r"var DOG='data:image/webp;base64,[^']+',SHUTTLE=",lambda m:"var DOG='"+dog_uri+"',SHUTTLE=",s,count=1)
if n!=1: raise SystemExit('v208.98 dog data anchor mismatch')

# Force the existing v208.95 partner button handler to run in capture phase.
# It expands inside the row and stops older click handlers from turning the action into a popup/no-op.
needle="document.addEventListener('click',function(ev){var m=ev.target&&ev.target.closest?ev.target.closest('.j95-more,.j95-collapse'):null;if(!m)return;"
start=s.find(needle)
if start<0: raise SystemExit('v208.95 partner handler start missing')
end=s.find("\nfunction install(){var api=window.__JAYUMINTON_GAME_REPORT_V20893__;",start)
if end<0: raise SystemExit('v208.95 partner handler end missing')
handler=s[start:end]
if not handler.endswith('});') or 'ev.preventDefault();' not in handler: raise SystemExit('v208.95 partner handler shape mismatch')
handler=handler.replace('ev.preventDefault();','ev.preventDefault();ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();',1)
handler=handler[:-3]+'},true);'
s=s[:start]+handler+s[end:]

for token in (MARKER,'BADMINTON CLUB','JAYUMINTON_GAME_REPORT_POLISH_V20899_CSS','min-height:29px!important','body:has(#pairStatisticsModal:not(.hidden))','data:image/svg+xml;base64,',"document.addEventListener('click',function(ev)",'},true);'):
    if token not in s: raise SystemExit('v208.99 contract missing: '+token)
p.write_text(s,encoding='utf-8')
print('ADMIN_GAME_REPORT_POLISH_V20899_OK')
