#!/usr/bin/env python3
"""Fail closed unless the admin web remains separate and Cloudflare-routed."""
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path('.').resolve()
workflow = (root / '.github/workflows/preview-admin-cloudflare.yml').read_text(encoding='utf-8')
builder = (root / 'deployment/jayuminton/admin_cloudflare_rpc.py').read_text(encoding='utf-8')
guardrails = (root / 'docs/PRODUCTION_ADMIN_WEB_ARCHITECTURE_GUARDRAILS.md').read_text(encoding='utf-8')

required_workflow = [
    'ADMIN_WORKER_NAME: jayuminton-admin-rpc',
    'admin_cloudflare_rpc.py build-frontend',
    'ADMIN_WORKER_URL',
    'MAIN_ADMIN_PRODUCTION_NOT_UPDATED',
    'MEMBER_PRODUCTION_NOT_UPDATED',
]
required_builder = [
    'window.__JAYUMINTON_ADMIN_CLOUDFLARE__=true',
    "if 'script.google.com/macros/s/' in index",
    "raise SystemExit('direct Apps Script URL remains')",
    'adminCloudflareLoginButton',
]
required_guardrails = [
    '관리자 페이지는 Google Apps Script `/exec` 페이지가 아니다',
    '사용자와 관리자는 운영 데이터만 공유한다',
    'https://jayuminton-admin-rpc.pianopp001.workers.dev/',
    'HTML, CSS, 화면 구성, 버튼, 기능 흐름과 배포 경로는 공유하지 않는다',
]

missing = []
missing += ['workflow:' + value for value in required_workflow if value not in workflow]
missing += ['builder:' + value for value in required_builder if value not in builder]
missing += ['guardrails:' + value for value in required_guardrails if value not in guardrails]
if 'firebase deploy --only hosting' in workflow:
    missing.append('workflow:must not deploy user production Hosting')
if missing:
    raise SystemExit('Cloudflare admin lock failed: ' + ' | '.join(missing))

print('Cloudflare admin lock verified: separate admin frontend + Worker RPC; Apps Script is backend only')
