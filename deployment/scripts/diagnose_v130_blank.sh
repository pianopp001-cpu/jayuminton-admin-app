#!/usr/bin/env bash
set -euo pipefail
C="$RUNNER_TEMP/deploy.json"
printf '%s' "$JAYUMINTON_DEPLOY_CONFIG_JSON" > "$C"
BASE="$(jq -r '.hostingUrl' "$C")"
BASE="${BASE%/}"

curl --fail --location --retry 5 -H 'Cache-Control: no-cache, no-store' "$BASE/config-v204.js?diag=$GITHUB_RUN_ID" -o "$RUNNER_TEMP/live-config.js"
curl --fail --location --retry 5 -H 'Cache-Control: no-cache, no-store' "$BASE/setup-v205.js?diag=$GITHUB_RUN_ID" -o "$RUNNER_TEMP/live-setup.js"
curl --fail --location --retry 5 -H 'Cache-Control: no-cache, no-store' "$BASE/?diag=$GITHUB_RUN_ID" -o "$RUNNER_TEMP/live-index.html"

python3 - <<'PY'
from pathlib import Path
import re, os
config=Path(os.environ['RUNNER_TEMP'])/'live-config.js'
setup=Path(os.environ['RUNNER_TEMP'])/'live-setup.js'
index=Path(os.environ['RUNNER_TEMP'])/'live-index.html'
c=config.read_text(encoding='utf-8', errors='replace')
s=setup.read_text(encoding='utf-8', errors='replace')
h=index.read_text(encoding='utf-8', errors='replace')

def snippet(src, token, radius=1200):
    i=src.find(token)
    if i<0: return f'NOT FOUND: {token}'
    a=max(0,i-radius); b=min(len(src),i+radius)
    return src[a:b]

out=[]
out.append('=== CONFIG ===')
out.append(c)
out.append('\n=== INDEX IFRAME ===')
m=re.search(r'<iframe[^>]+id=["\']courtFrame["\'][^>]*>',h)
out.append(m.group(0) if m else 'courtFrame iframe not found')
out.append('\n=== frame.src assignment ===')
out.append(snippet(s,'frame.src =',1600))
out.append('\n=== userOnlyMemberPageUrl ===')
out.append(snippet(s,'function userOnlyMemberPageUrl',2200))
out.append('\n=== cfg.memberPageUrl references ===')
for m in list(re.finditer(r'cfg\.memberPageUrl',s))[:8]:
    out.append(s[max(0,m.start()-500):min(len(s),m.end()+700)])
    out.append('\n---')
Path('deployment/status/v130-white-diagnostic.txt').write_text('\n'.join(out),encoding='utf-8')
PY
