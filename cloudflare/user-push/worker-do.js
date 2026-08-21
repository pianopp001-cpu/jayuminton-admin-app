const FCM_SCOPE = 'https://www.googleapis.com/auth/firebase.messaging';
let cachedAccessToken = '';
let cachedAccessTokenUntil = 0;

const cors = {
  'access-control-allow-origin': '*',
  'access-control-allow-methods': 'GET,POST,OPTIONS',
  'access-control-allow-headers': 'content-type,authorization,x-jayuminton-key',
};
const responseJson = (value, status = 200) => new Response(JSON.stringify(value), {
  status,
  headers: { ...cors, 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
});
const clean = (value, max = 200) => String(value == null ? '' : value).trim().slice(0, max);

function base64url(bytes) {
  let s = '';
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
}
const text64url = text => base64url(new TextEncoder().encode(text));
async function sha256(text) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map(v => v.toString(16).padStart(2, '0')).join('');
}
function pemBytes(pem) {
  const raw = String(pem || '').replace(/-----BEGIN PRIVATE KEY-----|-----END PRIVATE KEY-----|\s+/g, '');
  const bin = atob(raw);
  return Uint8Array.from(bin, ch => ch.charCodeAt(0));
}
async function googleAccessToken(env) {
  const nowMs = Date.now();
  if (cachedAccessToken && cachedAccessTokenUntil - nowMs > 60000) return cachedAccessToken;
  const c = JSON.parse(env.FIREBASE_SERVICE_ACCOUNT_JSON || '{}');
  if (!c.client_email || !c.private_key || !c.project_id) throw new Error('firebase_service_account_missing');
  const now = Math.floor(nowMs / 1000);
  const head = text64url(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
  const claim = text64url(JSON.stringify({ iss: c.client_email, scope: FCM_SCOPE, aud: 'https://oauth2.googleapis.com/token', iat: now, exp: now + 3600 }));
  const unsigned = `${head}.${claim}`;
  const key = await crypto.subtle.importKey('pkcs8', pemBytes(c.private_key), { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', key, new TextEncoder().encode(unsigned));
  const assertion = `${unsigned}.${base64url(new Uint8Array(sig))}`;
  const r = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer', assertion }),
  });
  const j = await r.json();
  if (!r.ok || !j.access_token) throw new Error(`oauth_${r.status}`);
  cachedAccessToken = j.access_token;
  cachedAccessTokenUntil = nowMs + Math.max(60, Number(j.expires_in || 3600)) * 1000;
  return cachedAccessToken;
}
async function readBody(request) {
  const type = request.headers.get('content-type') || '';
  if (type.includes('application/json')) return await request.json();
  const params = new URLSearchParams(await request.text());
  if (params.get('payload')) return JSON.parse(params.get('payload'));
  return Object.fromEntries(params.entries());
}
const memberKey = (id, hash) => `m:${encodeURIComponent(id)}:${hash}`;
const tokenKey = hash => `t:${hash}`;

export class PushRegistry {
  constructor(state, env) { this.state = state; this.env = env; }
  async fetch(request) {
    const url = new URL(request.url);
    const body = request.method === 'POST' ? await request.json() : {};
    if (url.pathname === '/register') {
      const memberId = clean(body.memberId), memberName = clean(body.memberName, 80), token = clean(body.token, 4096), userAgent = clean(body.userAgent, 300);
      if (!memberId || token.length < 40) return responseJson({ ok: false, error: 'memberId_and_token_required' }, 400);
      const hash = await sha256(token);
      const old = await this.state.storage.get(tokenKey(hash));
      if (old?.memberId && old.memberId !== memberId) await this.state.storage.delete(memberKey(old.memberId, hash));
      const record = { memberId, memberName, token, userAgent, updatedAt: Date.now() };
      await this.state.storage.put({ [tokenKey(hash)]: record, [memberKey(memberId, hash)]: record });
      return responseJson({ ok: true, action: 'registered', memberId, memberName });
    }
    if (url.pathname === '/unregister') {
      const token = clean(body.token, 4096);
      if (!token) return responseJson({ ok: false, error: 'token_required' }, 400);
      const hash = await sha256(token), old = await this.state.storage.get(tokenKey(hash));
      const keys = [tokenKey(hash)]; if (old?.memberId) keys.push(memberKey(old.memberId, hash));
      await this.state.storage.delete(keys);
      return responseJson({ ok: true, action: 'unregistered' });
    }
    if (url.pathname === '/status') {
      const token = clean(body.token, 4096), memberId = clean(body.memberId);
      if (!token) return responseJson({ ok: true, registered: false });
      const old = await this.state.storage.get(tokenKey(await sha256(token)));
      return responseJson({ ok: true, registered: Boolean(old && (!memberId || old.memberId === memberId)), memberId: old?.memberId || '' });
    }
    if (url.pathname === '/targets') {
      const ids = Array.isArray(body.memberIds) ? body.memberIds.map(x => clean(x)).filter(Boolean) : [];
      const seen = new Set(), records = [];
      for (const id of ids) {
        const list = await this.state.storage.list({ prefix: `m:${encodeURIComponent(id)}:` });
        for (const record of list.values()) if (record?.token && !seen.has(record.token)) { seen.add(record.token); records.push(record); }
      }
      return responseJson({ ok: true, records });
    }
    if (url.pathname === '/has-mapping') {
      const list = await this.state.storage.list({ prefix: 't:', limit: 1 });
      return responseJson({ ok: true, mappingPresent: list.size > 0 });
    }
    return responseJson({ ok: false, error: 'registry_route' }, 404);
  }
}

function registry(env) {
  return env.PUSH_REGISTRY.get(env.PUSH_REGISTRY.idFromName('global-v1'));
}
async function registryCall(env, path, body = {}) {
  return registry(env).fetch(new Request(`https://registry${path}`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) }));
}
function authorized(request, env, body, url) {
  const auth = request.headers.get('authorization') || '';
  const supplied = clean(request.headers.get('x-jayuminton-key') || (auth.toLowerCase().startsWith('bearer ') ? auth.slice(7) : '') || body.internalKey || url.searchParams.get('key'), 512);
  return Boolean(env.INTERNAL_KEY) && supplied === String(env.INTERNAL_KEY);
}
function textFor(event, member) {
  if (event.type === 'wait1_ready') return { title: '대기 1 안내', body: `${member.name || ''}님, 대기 1입니다. 라켓 들고 준비해 주세요.` };
  return { title: '코트 입장 안내', body: `${member.name || ''}님, ${Number(event.courtNo || 0)}번 코트로 입장해 주세요.` };
}
async function sendOne(env, accessToken, projectId, event, member, record) {
  const copy = textFor(event, member);
  const data = {
    type: String(event.type), assignmentId: String(event.assignmentId), memberId: String(member.id), memberName: String(member.name || ''),
    title: copy.title, body: copy.body, courtNo: String(event.courtNo || ''), expectedCourtNo: String(event.expectedCourtNo || ''), repeatCount: '1',
  };
  const android = { priority: 'high', ttl: '600s' };
  if (/JayumintonNativeAndroid\//i.test(record.userAgent || '')) android.restricted_package_name = 'com.jayuminton.user';
  else if (/JayumintonMemberNative\//i.test(record.userAgent || '')) android.restricted_package_name = 'com.jayuminton.member';
  const r = await fetch(`https://fcm.googleapis.com/v1/projects/${encodeURIComponent(projectId)}/messages:send`, {
    method: 'POST', headers: { authorization: `Bearer ${accessToken}`, 'content-type': 'application/json' }, body: JSON.stringify({ message: { token: record.token, data, android } }),
  });
  const text = await r.text();
  if (!r.ok && (r.status === 404 || r.status === 410 || /UNREGISTERED|registration-token-not-registered/i.test(text))) await registryCall(env, '/unregister', { token: record.token });
  return r.ok;
}
async function sendEvent(request, env, body, url) {
  if (!authorized(request, env, body, url)) return responseJson({ ok: false, error: 'unauthorized' }, 403);
  const type = clean(body.type);
  if (!['wait1_ready', 'court_assignment'].includes(type)) return responseJson({ ok: false, error: 'invalid_type' }, 400);
  const members = Array.isArray(body.members) ? body.members.map(m => ({ id: clean(m?.id), name: clean(m?.name, 80) })).filter(m => m.id) : [];
  if (!members.length || members.length > 4) return responseJson({ ok: false, error: 'invalid_members' }, 400);
  const event = { type, assignmentId: clean(body.assignmentId, 500) || `${type}-${Date.now()}`, courtNo: Number(body.courtNo || 0), expectedCourtNo: Number(body.expectedCourtNo || 0) };
  const targetResponse = await registryCall(env, '/targets', { memberIds: members.map(m => m.id) });
  const targetJson = await targetResponse.json();
  const memberById = Object.fromEntries(members.map(m => [m.id, m]));
  const records = Array.isArray(targetJson.records) ? targetJson.records : [];
  if (!records.length) return responseJson({ ok: true, assignmentId: event.assignmentId, sent: 0, failed: 0, noRegisteredToken: members.length });
  const credentials = JSON.parse(env.FIREBASE_SERVICE_ACCOUNT_JSON || '{}'), accessToken = await googleAccessToken(env);
  const results = await Promise.all(records.map(record => sendOne(env, accessToken, credentials.project_id, event, memberById[record.memberId] || { id: record.memberId, name: record.memberName }, record)));
  const sent = results.filter(Boolean).length;
  return responseJson({ ok: sent === results.length, assignmentId: event.assignmentId, sent, failed: results.length - sent });
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    const url = new URL(request.url);
    try {
      if (request.method === 'GET' && (url.pathname === '/' || url.pathname === '/health')) {
        const r = await registryCall(env, '/has-mapping'); const j = await r.json();
        return responseJson({ ok: true, service: 'jayuminton-cloudflare-user-push', storage: 'durable-object', mappingPresent: Boolean(j.mappingPresent) });
      }
      if (request.method !== 'POST') return responseJson({ ok: false, error: 'method_not_allowed' }, 405);
      const body = await readBody(request), action = clean(body.action);
      if (url.pathname === '/api/push/register' || action === 'register_web_token' || action === 'register_token') return registryCall(env, '/register', body);
      if (url.pathname === '/api/push/unregister' || action === 'unregister_web_token' || action === 'unregister_token') return registryCall(env, '/unregister', body);
      if (url.pathname === '/api/push/status' || action === 'token_status') return registryCall(env, '/status', body);
      if (url.pathname === '/api/push/event' || action === 'main_state_event') return sendEvent(request, env, body, url);
      return responseJson({ ok: false, error: 'unknown_action' }, 400);
    } catch (error) {
      return responseJson({ ok: false, error: String(error?.message || error || 'unknown_error') }, 500);
    }
  },
};
