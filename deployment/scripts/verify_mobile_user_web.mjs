import { chromium } from 'playwright';

const url = 'https://jayuminton-push.web.app/?mobileverify=' + Date.now();
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 412, height: 915 },
  deviceScaleFactor: 2.625,
  isMobile: true,
  hasTouch: true,
  userAgent: 'Mozilla/5.0 (Linux; Android 16; SM-S928N Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36'
});
const page = await context.newPage();
const errors = [];
page.on('pageerror', e => errors.push('pageerror:' + String(e.message || e)));
page.on('console', m => { if (m.type() === 'error') errors.push('console:' + m.text()); });
let navError = '';
try {
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
} catch (e) {
  navError = String(e.message || e);
}
await page.waitForTimeout(15000);
const frames = [];
for (const frame of page.frames()) {
  let text = '';
  try { text = (await frame.locator('body').innerText({ timeout: 3000 })).trim(); } catch {}
  frames.push({ url: frame.url(), text: text.slice(0, 500) });
}
const result = { mainUrl: page.url(), navError, frames, errors };
console.log(JSON.stringify(result, null, 2));
const visible = frames.some(f => /멤버 열람 비밀번호|자유민턴 코트배정 현황|확인/.test(f.text));
if (!visible) {
  await browser.close();
  throw new Error('Android mobile member screen not visible');
}
await browser.close();
console.log('ANDROID_MOBILE_MEMBER_SCREEN_VISIBLE');
