#!/usr/bin/env python3
"""Fail closed when the production member path stops being Cloudflare based."""
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path('.').resolve()
workflow = (root / '.github/workflows/deploy-unified-member-web-production.yml').read_text(encoding='utf-8')
badge = (root / 'deployment/jayuminton/v3_member_badges_patch.py').read_text(encoding='utf-8')
guardrails = (root / 'docs/PRODUCTION_USER_WEB_APP_RECOVERY_GUARDRAILS.md').read_text(encoding='utf-8')

required_workflow = [
    'https://jayuminton-push.web.app/',
    'https://shy-morning-f0e4.pianopp001.workers.dev/',
    'AKfycbyc1igSCIWFWMLp2qgMGxB4lsSVfcZk3TDk-A6cB3OrQm2fIS7ZLnz8b9jeAIXyCMy-cQ',
    '! grep -Eqi \'<iframe\'',
    "! grep -F 'script.google.com/macros/s/'",
    'MAIN_ADMIN_DEPLOYMENTS_NOT_UPDATED',
]
required_badge = [
    "badge.textContent='NEW 신규'",
    "sponsor.textContent='🎁 찬조'",
    "sponsor.setAttribute('aria-label','찬조 회원')",
    'member-status-list',
    'flex-direction:column!important',
    'height:auto!important',
]
required_guardrails = [
    '항상 Cloudflare Worker RPC를 사용하는 Firebase Hosting',
    '사용자에게 Apps Script URL을 안내하거나 사용자 운영 URL로 기록하지 않는다',
    'https://jayuminton-push.web.app/',
]

missing = []
missing += ['workflow:' + value for value in required_workflow if value not in workflow]
missing += ['badge:' + value for value in required_badge if value not in badge]
missing += ['guardrails:' + value for value in required_guardrails if value not in guardrails]
if missing:
    raise SystemExit('Cloudflare user lock failed: ' + ' | '.join(missing))

print('Cloudflare user lock verified: canonical Hosting + Worker RPC, tiny NEW/gift icons, no MAIN/ADMIN deployment update')
