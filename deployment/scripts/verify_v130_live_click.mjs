import { chromium } from 'playwright';
import fs from 'fs';

const base = (process.env.HOSTING_URL || '').replace(/\/$/, '');
const expectedToken = process.env.EXPECTED_APK_TOKEN || 'Jayuminton-User-v1.3.0-code130-cap8.apk';
if (!base) throw new Error('HOSTING_URL missing');

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({
  acceptDownloads: true,
  userAgent: 'Mozilla/5.0 (Linux; Android 15; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36'
});
const page = await ctx.newPage();
page.on('dialog', d => d.accept());

let apkUrl = '';
ctx.on('request', r => {
  if (r.url().includes('.apk')) apkUrl = r.url();
});

await page.goto(base + '/badminton.html?v130cap8=' + Date.now(), {
  waitUntil: 'domcontentloaded',
  timeout: 60000
});
await page.waitForTimeout(7000);

const frames = [];
const candidates = [];
for (const frame of page.frames()) {
  let body = '';
  try {
    body = (await frame.locator('body').innerText({ timeout: 3000 })).replace(/\s+/g, ' ');
  } catch {}
  frames.push({ url: frame.url(), body });
  try {
    const els = frame.locator('button:visible,a:visible');
    const n = await els.count();
    for (let i = 0; i < n; i++) {
      const el = els.nth(i);
      let text = '';
      try { text = (await el.innerText()).trim(); } catch {}
      if (/앱\s*설치|다운로드|1\.3\.0/.test(text) && !/OFF/.test(text)) {
        candidates.push({ el, text });
      }
    }
  } catch {}
}

fs.writeFileSync('frames.json', JSON.stringify(frames, null, 2));
if (frames.some(x => x.body.includes('1.2.9'))) {
  throw new Error('Visible old 1.2.9 remains in rendered installer');
}
if (!candidates.length) throw new Error('No visible install/download control found');

let clicked = '';
for (const c of candidates) {
  try {
    const downloadPromise = page.waitForEvent('download', { timeout: 8000 }).catch(() => null);
    await c.el.click({ timeout: 5000 });
    clicked = c.text;
    const dl = await downloadPromise;
    if (dl) {
      apkUrl = dl.url();
      await dl.saveAs('clicked.apk');
    }
    await page.waitForTimeout(1000);
    if (apkUrl) break;
  } catch {}
}

fs.writeFileSync('clicked.json', JSON.stringify({ clicked, apkUrl }, null, 2));
if (!apkUrl.includes(expectedToken)) {
  throw new Error('Actual public click did not request expected APK: ' + apkUrl);
}

await browser.close();
