#!/usr/bin/env python3
"""Final post-contract hardening for admin Cloudflare HTML.

Runs after admin_cloudflare_final_contract.py so later generic CSS cannot restore an
inner statistics scroll area that clips the last member's partner/count details.
"""
from pathlib import Path
import sys

path = Path(sys.argv[1])
html = path.read_text(encoding='utf-8')
marker = '</body>'
if marker not in html:
    raise SystemExit('body end marker missing')
addon = r'''
<style id="jayuminton-admin-post-contract-v19">
#pairStatisticsModal .pair-statistics-modal{overflow-y:auto!important;padding-bottom:max(32px,env(safe-area-inset-bottom))!important}
#pairStatisticsModal .pair-statistics-list{max-height:none!important;height:auto!important;overflow:visible!important;padding-bottom:max(56px,calc(env(safe-area-inset-bottom) + 40px))!important}
#pairStatisticsModal .pair-statistics-row{height:auto!important;max-height:none!important;overflow:visible!important}
#pairStatisticsModal .pair-statistics-row:last-child{margin-bottom:32px!important;padding-bottom:16px!important}
#pairStatisticsModal .pair-statistics-partners{height:auto!important;max-height:none!important;overflow:visible!important;white-space:normal!important}
</style>
<script>window.__JAYUMINTON_ADMIN_POST_CONTRACT_V19__=true;window.__JAYUMINTON_ADMIN_STATISTICS_NO_CLIP_FINAL__=true;</script>
'''
html = html.replace(marker, addon + '\n' + marker, 1)
for required in ('jayuminton-admin-post-contract-v19','__JAYUMINTON_ADMIN_STATISTICS_NO_CLIP_FINAL__','max-height:none!important','overflow:visible!important'):
    if required not in html:
        raise SystemExit('post-contract marker missing: '+required)
path.write_text(html, encoding='utf-8')
print('ADMIN_POST_CONTRACT_V19_OK')
