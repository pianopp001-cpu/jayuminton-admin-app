#!/usr/bin/env python3
from pathlib import Path
import re, sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'app/src/main/assets/admin/index.html')
s=p.read_text(encoding='utf-8')
# Normalize the existing statistics control label without changing its handler.
s,n=re.subn(r'(<button[^>]+onclick=["\']openPairStatistics\(\)["\'][^>]*>)(.*?)(</button>)',lambda m:m.group(1)+'📊 게임 통계'+m.group(3),s,count=1,flags=re.S)
if n!=1: raise SystemExit('game statistics button anchor missing')
# Make the partner overflow chip genuinely toggle open/closed.
needle="var box=more.closest('.jm-report-partners');box.innerHTML=(r.partners||[]).map(function(p){"
replacement="var box=more.closest('.jm-report-partners');if(String(more.textContent||'').trim()==='접기'){box.innerHTML=partnerHtml(r);return;}box.innerHTML=(r.partners||[]).map(function(p){"
if needle not in s: raise SystemExit('partner overflow toggle anchor missing')
s=s.replace(needle,replacement,1)
for token in ('📊 게임 통계',"trim()==='접기'",'partnerHtml(r)'):
    if token not in s: raise SystemExit('final report contract missing: '+token)
p.write_text(s,encoding='utf-8')
print('ADMIN_GAME_REPORT_V20893_FINAL_OK')
