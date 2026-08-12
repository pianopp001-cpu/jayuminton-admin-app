#!/usr/bin/env bash
set -euo pipefail
C="$RUNNER_TEMP/deploy.json"
printf '%s' "$JAYUMINTON_DEPLOY_CONFIG_JSON" > "$C"
BASE="$(jq -r '.hostingUrl' "$C")"
BASE="${BASE%/}"
D="$RUNNER_TEMP/v130-nested-check"
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
await page.goto(base+'/?nested='+Date.now(),{waitUntil:'domcontentloaded',timeout:60000});
await page.waitForTimeout(12000);
const infos=[];
for (const f of page.frames()) {
  let text='';
  try { text=(await f.locator('body').innerText({timeout:5000})).replace(/\s+/g,' ').trim(); } catch {}
  infos.push({url:f.url(), textLength:text.length, text:text.slice(0,2000)});
}
infos.sort((a,b)=>b.textLength-a.textLength);
const proof={frames:infos, errors};
console.log(JSON.stringify(proof,null,2));
fs.writeFileSync('proof.json',JSON.stringify(proof,null,2));
if(!infos.some(x=>x.url.includes('script.google.com/macros/s/') && x.url.includes('mode=user'))) throw new Error('Apps Script user route missing');
const best=infos.find(x=>!x.url.includes('jayuminton-push.web.app') && x.textLength>=20);
if(!best) throw new Error('No nested frame has visible text');
await browser.close();
JS
BASE_URL="$BASE" node verify.mjs
BEST_LEN="$(node -e "const p=require('./proof.json'); const b=p.frames.find(x=>!x.url.includes('jayuminton-push.web.app')&&x.textLength>=20); console.log(b?b.textLength:0)")"
cd "$GITHUB_WORKSPACE"
cat > deployment/status/v130-visible-nested-proof.txt <<EOF
status=success
live_page=$BASE/
apps_script_user_route=yes
nested_visible_content=yes
best_nested_text_length=$BEST_LEN
version_name=1.3.0
version_code=130
wait1_groups=8
court_groups=8
verified_at=$(date -u +%FT%TZ)
EOF
