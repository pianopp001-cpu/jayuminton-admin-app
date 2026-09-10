#!/usr/bin/env python3
from pathlib import Path
import re,sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'app/src/main/assets/admin/index.html')
s=p.read_text(encoding='utf-8')
MARKER='JAYUMINTON_GAME_REPORT_HARD_APPLY_V20903'
if MARKER in s:
    print('V20903_ALREADY_OK'); raise SystemExit(0)
for token in ('JAYUMINTON_GAME_REPORT_POSTER_V20895','JAYUMINTON_GAME_REPORT_USABILITY_V20898','JAYUMINTON_GAME_REPORT_VISUAL_FIX_V20900','JAYUMINTON_GAME_REPORT_EXPAND_EXPORT_V20901'):
    if token not in s: raise SystemExit('v209.03 prerequisite missing: '+token)

DOG="data:image/webp;base64,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"

s,n=re.subn(r"var DOG='data:image/[^']+',SHUTTLE=",lambda m:"var DOG='"+DOG+"',SHUTTLE=",s,count=1)
if n!=1: raise SystemExit('DOG variable replacement failed')

old="""hero.insertAdjacentHTML('beforeend','<img class=\"j98-shuttle\" alt=\"\" src=\"'+SHUTTLE+'\"><img class=\"j98-dog-top\" alt=\"\" src=\"'+DOG+'\">');"""
new="""hero.insertAdjacentHTML('beforeend','<img class=\"j98-dog-top\" alt=\"\" src=\"'+DOG+'\">');"""
if old not in s: raise SystemExit('v208.98 visual insertion anchor missing')
s=s.replace(old,new,1)

pairs=[
(".j95-card{min-height:148px;padding:20px 17px;", ".j95-card{min-height:104px;padding:13px 14px 10px;"),
(".j95-card strong{display:block;margin-top:15px;", ".j95-card strong{display:block;margin-top:7px;"),
(".j95-card{min-height:108px;padding:12px 8px;border-radius:15px}", ".j95-card{min-height:84px;padding:8px 7px 6px;border-radius:15px}"),
(".j95-card strong{margin-top:8px}", ".j95-card strong{margin-top:5px}")
]
for a,b in pairs:
    if a not in s: raise SystemExit('card CSS anchor missing: '+a[:35])
    s=s.replace(a,b,1)

patterns=[
(r"\.j98-dog-top\{right:4\.1%!important;top:19%!important;width:12\.5%!important;min-width:72px!important;max-width:110px!important;transform:none!important;z-index:8!important\}",
 ".j98-dog-top{right:2.5%!important;top:14.8%!important;width:12.8%!important;min-width:72px!important;max-width:108px!important;transform:none!important;clip-path:none!important;z-index:9!important;object-fit:contain!important}"),
(r"\.j100-racket-held\{position:absolute;right:\.8%;top:12\.8%;width:8\.8%;min-width:54px;max-width:80px;z-index:7;",
 ".j100-racket-held{position:absolute;right:9.0%;top:9.2%;width:8.2%;min-width:50px;max-width:74px;z-index:8;"),
(r"\.j98-dog-bottom\{right:4%!important;bottom:-24px!important;width:84px!important;min-width:0!important;max-width:84px!important;transform:none!important;clip-path:inset\(0 0 36% 0\)!important;z-index:6!important\}",
 ".j98-dog-bottom{right:2.8%!important;bottom:6px!important;width:72px!important;min-width:0!important;max-width:72px!important;transform:none!important;clip-path:none!important;opacity:1!important;z-index:8!important;object-fit:contain!important}"),
(r"\.j98-dog-top\{right:3\.2%!important;top:18\.5%!important;width:16%!important;min-width:58px!important;max-width:78px!important\}",
 ".j98-dog-top{right:2.2%!important;top:14.6%!important;width:15.5%!important;min-width:58px!important;max-width:78px!important}"),
(r"\.j100-racket-held\{right:-\.1%;top:12\.8%;width:11\.5%;min-width:43px;max-width:59px\}",
 ".j100-racket-held{right:10.2%;top:8.8%;width:10.5%;min-width:41px;max-width:56px}"),
(r"\.j98-dog-bottom\{right:3%!important;bottom:-20px!important;width:68px!important;max-width:68px!important;clip-path:inset\(0 0 34% 0\)!important\}",
 ".j98-dog-bottom{right:2.3%!important;bottom:5px!important;width:58px!important;max-width:58px!important;clip-path:none!important}")
]
for pat,rep in patterns:
    s,n=re.subn(pat,rep,s,count=1)
    if n!=1: raise SystemExit('visual CSS replacement failed: '+pat[:30])

oldbar=".j95-actions{flex-wrap:wrap!important;align-items:center!important;gap:7px!important;padding:9px 10px!important}"
newbar=".j95-actions{position:sticky!important;bottom:94px!important;z-index:9999!important;flex-wrap:wrap!important;align-items:center!important;justify-content:center!important;gap:6px!important;padding:8px 8px 10px!important;background:linear-gradient(180deg,rgba(218,248,234,.42),rgba(218,248,234,.99) 24%)!important}"
if oldbar not in s: raise SystemExit('v209.01 action bar anchor missing')
s=s.replace(oldbar,newbar,1)

guard=r'''
<style id="jmReportHardApplyV20903Style">
/* JAYUMINTON_GAME_REPORT_HARD_APPLY_V20903 */
.j98-shuttle{display:none!important;visibility:hidden!important}
.j95-sum{align-items:stretch!important}
.j95-card{height:auto!important}
#pairStatisticsModal .pair-statistics-modal{padding-bottom:86px!important}
.j98-dog-top,.j98-dog-bottom{background:transparent!important}
.j95-actions .j101-tool,.j95-actions .j95-save,.j95-actions .j95-close{visibility:visible!important;opacity:1!important}
</style>
'''
if '</head>' not in s: raise SystemExit('head anchor missing')
s=s.replace('</head>',guard+'\n</head>',1)

for token in (MARKER,DOG,'전체 펼침','전체 접힘','window.jmSaveGameReportImage=saveFullImage','bottom:94px!important','clip-path:none!important'):
    if token not in s: raise SystemExit('v209.03 contract missing: '+token[:40])
p.write_text(s,encoding='utf-8')
print('ADMIN_GAME_REPORT_HARD_APPLY_V20903_OK')
