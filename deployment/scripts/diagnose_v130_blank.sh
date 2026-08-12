#!/usr/bin/env bash
set -euo pipefail
C="$RUNNER_TEMP/deploy.json"
printf '%s' "$JAYUMINTON_DEPLOY_CONFIG_JSON" > "$C"
BASE="$(jq -r '.hostingUrl' "$C")"
BASE="${BASE%/}"

curl --fail --location --retry 5 -H 'Cache-Control: no-cache, no-store' "$BASE/config-v204.js?diag=$GITHUB_RUN_ID" -o "$RUNNER_TEMP/live-config.js"
curl --fail --location --retry 5 -H 'Cache-Control: no-cache, no-store' "$BASE/setup-v205.js?diag=$GITHUB_RUN_ID" -o "$RUNNER_TEMP/live-setup.js"
curl --fail --location --retry 5 -H 'Cache-Control: no-cache, no-store' "$BASE/?diag=$GITHUB_RUN_ID" -o "$RUNNER_TEMP/live-index.html"

D="$RUNNER_TEMP/pw-diag"
mkdir -p "$D"
cd "$D"
npm init -y >/dev/null 2>&1
npm i playwright@1.54.2 >/dev/null 2>&1
npx playwright install --with-deps chromium >/dev/null 2>&1
cat > verify.mjs <<'JS'
import { chromium } from 'playwright';
import fs from 'fs';
const base=process.env.BASE_URL;
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:412,height:915},userAgent:'Mozilla/5.0 (Linux; Android 15; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139 Mobile Safari/537.36'});
const errors=[];
page.on('pageerror',e=>errors.push('PAGE '+e.message));
page.on('console',m=>{if(m.type()==='error') errors.push('CONSOLE '+m.text());});
await page.goto(base+'/?diagframes='+Date.now(),{waitUntil:'domcontentloaded',timeout:60000});
await page.waitForTimeout(12000);
const infos=[];
for(const f of page.frames()){
  let text='';
  let htmlLen=0;
  try{text=(await f.locator('body').innerText({timeout:5000})).replace(/\s+/g,' ').trim();}catch{}
  try{htmlLen=(await f.content()).length;}catch{}
  infos.push({url:f.url(),textLength:text.length,htmlLength:htmlLen,text:text.slice(0,2000)});
}
infos.sort((a,b)=>b.textLength-a.textLength || b.htmlLength-a.htmlLength);
fs.writeFileSync('frames.json',JSON.stringify({infos,errors},null,2));
console.log(JSON.stringify({infos,errors},null,2));
await browser.close();
JS
BASE_URL="$BASE" node verify.mjs
cd "$GITHUB_WORKSPACE"

python3 - <<'PY'
from pathlib import Path
import re, os, json
config=Path(os.environ['RUNNER_TEMP'])/'live-config.js'
setup=Path(os.environ['RUNNER_TEMP'])/'live-setup.js'
index=Path(os.environ['RUNNER_TEMP'])/'live-index.html'
frames=Path(os.environ['RUNNER_TEMP'])/'pw-diag'/'frames.json'
c=config.read_text(encoding='utf-8', errors='replace')
s=setup.read_text(encoding='utf-8', errors='replace')
h=index.read_text(encoding='utf-8', errors='replace')
f=json.loads(frames.read_text(encoding='utf-8'))

def snippet(src, token, radius=800):
    i=src.find(token)
    if i<0: return f'NOT FOUND: {token}'
    return src[max(0,i-radius):min(len(src),i+radius)]

out=[]
out.append('=== CONFIG ===')
out.append(c)
out.append('\n=== INDEX IFRAME ===')
m=re.search(r'<iframe[^>]+id=["\']courtFrame["\'][^>]*>',h)
out.append(m.group(0) if m else 'courtFrame iframe not found')
out.append('\n=== RUNTIME FRAMES ===')
for x in f.get('infos',[]):
    out.append(f"URL={x.get('url')}\nTEXT_LENGTH={x.get('textLength')} HTML_LENGTH={x.get('htmlLength')}\nTEXT={x.get('text')}\n---")
out.append('\n=== ERRORS ===')
out.extend(f.get('errors',[]) or ['none'])
out.append('\n=== frame.src assignment ===')
out.append(snippet(s,'frame.src =',1200))
out.append('\n=== userOnlyMemberPageUrl ===')
out.append(snippet(s,'function userOnlyMemberPageUrl',1600))
Path('deployment/status/v130-white-diagnostic.txt').write_text('\n'.join(out),encoding='utf-8')
PY
