#!/usr/bin/env bash
set -euo pipefail

C="$RUNNER_TEMP/deploy.json"
printf '%s' "$JAYUMINTON_DEPLOY_CONFIG_JSON" > "$C"
FIREBASE_PROJECT_ID="$(jq -r '.firebaseProjectId' "$C")"
HOSTING_URL="$(jq -r '.hostingUrl' "$C")"
MAIN_DEPLOYMENT_ID="$(jq -r '.mainDeploymentId' "$C")"
PUSH_URL="$(jq -r '.pushUrl' "$C")"
MAIN_URL="https://script.google.com/macros/s/${MAIN_DEPLOYMENT_ID}/exec"
BASE="${HOSTING_URL%/}"
for value in "$FIREBASE_PROJECT_ID" "$BASE" "$MAIN_DEPLOYMENT_ID" "$PUSH_URL"; do
  test -n "$value"
  test "$value" != null
done

SRC="$GITHUB_WORKSPACE/deployment/jayuminton/v1637-web"
ROOT="$RUNNER_TEMP/v130-whitefix-hosting"
PUBLIC="$ROOT/public"
mkdir -p "$PUBLIC"
cp "$SRC/index.html" "$PUBLIC/index.html"
cp "$SRC/setup-v205.css" "$PUBLIC/setup-v205.css"
cp "$SRC/manifest.webmanifest" "$PUBLIC/manifest.webmanifest"
cp "$SRC/firebase-messaging-sw.js" "$PUBLIC/firebase-messaging-sw.js"
cp "$SRC/alert-self-test.js" "$PUBLIC/alert-self-test.js"

for asset in icon-198.png icon-512.png apple-touch-icon-180.png badge-96.png; do
  curl --fail --location --retry 5 "$BASE/$asset?source=v130-whitefix-$GITHUB_RUN_ID" -o "$PUBLIC/$asset"
done

cat "$SRC"/setup-v205.js.gz.b64.part-* | tr -d '\r\n' | base64 -d > "$RUNNER_TEMP/setup-v205.gz"
gzip -dc "$RUNNER_TEMP/setup-v205.gz" > "$PUBLIC/setup-v205.js"
python3 deployment/scripts/patch_push_setup_verification.py "$PUBLIC/setup-v205.js"
python3 deployment/scripts/patch_embedded_browser_push.py "$PUBLIC/setup-v205.js"
python3 deployment/scripts/patch_native_host_bridge.py "$PUBLIC/setup-v205.js"
python3 deployment/scripts/patch_user_install_link_v130.py hosting "$PUBLIC/setup-v205.js"

export WHITEFIX_MAIN_URL="${MAIN_URL}?build=v130-whitefix-${GITHUB_RUN_ID}"
export WHITEFIX_PUSH_URL="$PUSH_URL"
python3 - <<'PY'
from pathlib import Path
import os

public = Path(os.environ['RUNNER_TEMP']) / 'v130-whitefix-hosting' / 'public'
main = os.environ['WHITEFIX_MAIN_URL']
push = os.environ['WHITEFIX_PUSH_URL']
run_id = os.environ['GITHUB_RUN_ID']

template = Path('deployment/jayuminton/v1637-web/config-v204.template.js').read_text(encoding='utf-8')
config = template.replace('__MEMBER_PAGE_URL__', main).replace('__RELAY_URL__', push)
for name in ('config-v202.js', 'config-v203.js', 'config-v204.js'):
    (public / name).write_text(config, encoding='utf-8')

base = (public / 'index.html').read_text(encoding='utf-8')
old = '<iframe id="courtFrame" title="자유민턴 코트현황" scrolling="no" allow="clipboard-read; clipboard-write"></iframe>'
new = f'<iframe id="courtFrame" src="{main}" title="자유민턴 코트현황" scrolling="no" allow="clipboard-read; clipboard-write"></iframe>'
if old not in base:
    raise SystemExit('court iframe anchor missing')
base = base.replace(old, new, 1)
base = base.replace('/setup-v205.js?v=1637', f'/setup-v205.js?v=v130-whitefix-{run_id}')
base = base.replace('/config-v204.js?v=1637', f'/config-v204.js?v=v130-whitefix-{run_id}')
base = base.replace('</head>', f'<meta name="jayuminton-whitefix" content="v130-{run_id}"></head>')
for name in ('index.html', 'badminton.html'):
    (public / name).write_text(base, encoding='utf-8')

sw = public / 'firebase-messaging-sw.js'
text = sw.read_text(encoding='utf-8')
text += "\nself.addEventListener('install',()=>self.skipWaiting());\nself.addEventListener('activate',e=>e.waitUntil(caches.keys().then(ks=>Promise.all(ks.map(k=>caches.delete(k)))).then(()=>self.clients.claim())));\n"
sw.write_text(text, encoding='utf-8')
PY

grep -F 'src="https://script.google.com/macros/s/' "$PUBLIC/index.html" >/dev/null
grep -F 'Jayuminton-User-v1.3.0-code130-cap8.apk' "$PUBLIC/setup-v205.js" >/dev/null
grep -F 'JAYUMINTON_NATIVE_APK_DOWNLOAD_V130' "$PUBLIC/setup-v205.js" >/dev/null

cat > "$ROOT/firebase.json" <<'JSON'
{"hosting":{"public":"public","ignore":["firebase.json","**/.*","**/node_modules/**"],"headers":[{"source":"/index.html","headers":[{"key":"Cache-Control","value":"no-cache, no-store, must-revalidate"}]},{"source":"/badminton.html","headers":[{"key":"Cache-Control","value":"no-cache, no-store, must-revalidate"}]},{"source":"/setup-v205.js","headers":[{"key":"Cache-Control","value":"no-cache, no-store, must-revalidate"}]},{"source":"/config-v204.js","headers":[{"key":"Cache-Control","value":"no-cache, no-store, must-revalidate"}]},{"source":"/firebase-messaging-sw.js","headers":[{"key":"Cache-Control","value":"no-cache, no-store, must-revalidate"}]}],"rewrites":[{"source":"**","destination":"/index.html"}]}}
JSON

firebase deploy --only hosting --project "$FIREBASE_PROJECT_ID" --config "$ROOT/firebase.json" --non-interactive

curl --fail --location --retry 5 -H 'Cache-Control: no-cache, no-store' "$BASE/?verify=whitefix-$GITHUB_RUN_ID" -o "$RUNNER_TEMP/live-whitefix.html"
curl --fail --location --retry 5 -H 'Cache-Control: no-cache, no-store' "$BASE/setup-v205.js?verify=whitefix-$GITHUB_RUN_ID" -o "$RUNNER_TEMP/live-whitefix.js"
grep -F 'src="https://script.google.com/macros/s/' "$RUNNER_TEMP/live-whitefix.html" >/dev/null
grep -F 'jayuminton-whitefix' "$RUNNER_TEMP/live-whitefix.html" >/dev/null
grep -F 'Jayuminton-User-v1.3.0-code130-cap8.apk' "$RUNNER_TEMP/live-whitefix.js" >/dev/null

TARGET="$(sed -n "s/.*const JAYUMINTON_USER_APK_V130 = '\([^']*\)'.*/\1/p" "$RUNNER_TEMP/live-whitefix.js" | head -1)"
test -n "$TARGET"
curl --fail --location --retry 5 -H 'Cache-Control: no-cache, no-store' "$TARGET" -o "$RUNNER_TEMP/live-v130.apk"
LIVE_SHA="$(sha256sum "$RUNNER_TEMP/live-v130.apk" | awk '{print $1}')"
REPO_SHA="$(sha256sum releases/jayuminton-courtstatus-v1.3.0-cap8.apk | awk '{print $1}')"
test "$LIVE_SHA" = "$REPO_SHA"

AAPT=''
for p in "$ANDROID_HOME"/build-tools/*/aapt; do [ -x "$p" ] && AAPT="$p"; done
test -n "$AAPT"
"$AAPT" dump badging "$RUNNER_TEMP/live-v130.apk" > "$RUNNER_TEMP/live-v130-badging.txt"
grep -F "package: name='com.jayuminton.user'" "$RUNNER_TEMP/live-v130-badging.txt" >/dev/null
grep -F "versionCode='130'" "$RUNNER_TEMP/live-v130-badging.txt" >/dev/null
grep -F "versionName='1.3.0'" "$RUNNER_TEMP/live-v130-badging.txt" >/dev/null

cd "$RUNNER_TEMP"
mkdir -p whitefix-pw
cd whitefix-pw
npm init -y >/dev/null 2>&1
npm i playwright@1.54.2 >/dev/null 2>&1
npx playwright install --with-deps chromium >/dev/null 2>&1
cat > verify.mjs <<'JS'
import { chromium } from 'playwright';
import fs from 'fs';
const base = process.env.WHITEFIX_HOSTING_URL.replace(/\/$/, '');
const browser = await chromium.launch({headless:true});
const page = await browser.newPage({userAgent:'Mozilla/5.0 (Linux; Android 15; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139 Mobile Safari/537.36'});
const errors = [];
page.on('pageerror', e => errors.push(e.message));
await page.goto(base + '/?whitefix=' + Date.now(), {waitUntil:'domcontentloaded', timeout:60000});
await page.waitForTimeout(9000);
const frames = page.frames();
const target = frames.find(f => f !== page.mainFrame() && f.url().includes('script.google.com')) || frames.find(f => f !== page.mainFrame() && !f.url().startsWith('about:blank'));
let inner = '';
if (target) inner = (await target.locator('body').innerText({timeout:6000}).catch(()=>'' )).replace(/\s+/g,' ').trim();
const proof = { frameUrls: frames.map(f=>f.url()), inner: inner.slice(0,2000), errors };
fs.writeFileSync('proof.json', JSON.stringify(proof,null,2));
console.log(JSON.stringify(proof,null,2));
if (!target) throw new Error('court iframe did not load');
if (inner.length < 20) throw new Error('court iframe body is blank');
await browser.close();
JS
WHITEFIX_HOSTING_URL="$BASE" node verify.mjs

cd "$GITHUB_WORKSPACE"
cat > deployment/status/v130-white-screen-hotfix.txt <<EOF
status=success
live_page=$BASE/
visible_page=yes
direct_iframe_failsafe=yes
version_name=1.3.0
version_code=130
wait1_groups=8
court_groups=8
pulses_per_group=3
installer_asset=Jayuminton-User-v1.3.0-code130-cap8.apk
apk_sha256=$LIVE_SHA
verified_at=$(date -u +%FT%TZ)
EOF

echo "v1.3.0 white-screen hotfix deployed and browser-verified."
