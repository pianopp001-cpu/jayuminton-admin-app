const FCM_SCOPE = 'https://www.googleapis.com/auth/firebase.messaging';
let cachedAccessToken = null;
let cachedAccessTokenUntil = 0;

const json = (value, status = 200, extra = {}) => new Response(JSON.stringify(value), {
  status,
  headers: {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
    'access-control-allow-origin': '*',
    'access-control-allow-methods': 'GET,POST,OPTIONS',
    'access-control-allow-headers': 'content-type,authorization,x-jayuminton-key',
    ...extra,
  },
});

function clean(value, max = 200) {
  return String(value == null ? '' : value).trim().slice(0, max);
}

function base64url(bytes) {
  let binary = '';
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
}

function text64url(text) {
  return base64url(new TextEncoder().encode(text));
}

async function sha256(text) {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return [...new Uint8Array(digest)].map(v => v.toString(16).padStart(2, '0')).join('');
}

function pemBytes(pem) {
  const b64 = String(pem || '').replace(/-----BEGIN PRIVATE KEY-----|-----END PRIVATE KEY-----|\s+/g, '');
  const binary = atob(b64);
  const out = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) out[i] = binary.charCodeAt(i);
  return out;
}

async function googleAccessToken(env) {
  const nowMs = Date.now();
  if (cachedAccessToken && cachedAccessTokenUntil - nowMs > 60000) return cachedAccessToken;
  const credentials = JSON.parse(env.FIREBASE_SERVICE_ACCOUNT_JSON || '{}');
  if (!credentials.client_email || !credentials.private_key || !credentials.project_id) {
    throw new Error('firebase_service_account_missing');
  }
  const now = Math.floor(nowMs / 1000);
  const header = text64url(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
  const claim = text64url(JSON.stringify({
    iss: credentials.client_email,
    scope: FCM_SCOPE,
    aud: 'https://oauth2.googleapis.com/token',
    iat: now,
    exp: now + 3600,
  }));
  const input = `${header}.${claim}`;
  const key = await crypto.subtle.importKey(
    'pkcs8',
    pemBytes(credentials.private_key),
    { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
    false,
    ['sign'],
  );
  const sig = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', key, new TextEncoder().encode(input));
  const assertion = `${input}.${base64url(new Uint8Array(sig))}`;
  const response = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
      assertion,
    }),
  });
  const result = await response.json();
  if (!response.ok || !result.access_token) throw new Error(`oauth_${response.status}`);
  cachedAccessToken = result.access_token;
  cachedAccessTokenUntil = nowMs + Math.max(60, Number(result.expires_in || 3600)) * 1000;
  return cachedAccessToken;
}

async function readBody(request) {
  const contentType = request.headers.get('content-type') || '';
  if (contentType.includes('application/json')) return await request.json();
  const text = await request.text();
  const params = new URLSearchParams(text);
  const payload = params.get('payload');
  if (payload) return JSON.parse(payload);
  return Object.fromEntries(params.entries());
}

function memberKey(memberId, tokenHash) {
  return `m:${encodeURIComponent(memberId)}:${tokenHash}`;
}
function tokenKey(tokenHash) {
  return `t:${tokenHash}`;
}

async function register(env, body) {
  const memberId = clean(body.memberId);
  const memberName = clean(body.memberName, 80);
  const token = clean(body.token, 4096);
  const userAgent = clean(body.userAgent || body.platform, 300);
  if (!memberId || !token || token.length < 40) return json({ ok: false, error: 'memberId_and_token_required' }, 400);
  const hash = await sha256(token);
  const existing = await env.PUSH_TOKENS.get(tokenKey(hash), 'json');
  if (existing && existing.memberId && existing.memberId !== memberId) {
    await env.PUSH_TOKENS.delete(memberKey(existing.memberId, hash));
  }
  const record = { memberId, memberName, token, userAgent, updatedAt: Date.now() };
  await Promise.all([
    env.PUSH_TOKENS.put(tokenKey(hash), JSON.stringify(record), { expirationTtl: 180 * 24 * 60 * 60 }),
    env.PUSH_TOKENS.put(memberKey(memberId, hash), JSON.stringify(record), { expirationTtl: 180 * 24 * 60 * 60 }),
  ]);
  return json({ ok: true, action: 'registered', memberId, memberName });
}

async function unregister(env, body) {
  const token = clean(body.token, 4096);
  if (!token) return json({ ok: false, error: 'token_required' }, 400);
  const hash = await sha256(token);
  const existing = await env.PUSH_TOKENS.get(tokenKey(hash), 'json');
  await env.PUSH_TOKENS.delete(tokenKey(hash));
  if (existing && existing.memberId) await env.PUSH_TOKENS.delete(memberKey(existing.memberId, hash));
  return json({ ok: true, action: 'unregistered' });
}

async function tokenStatus(env, body) {
  const token = clean(body.token, 4096);
  const memberId = clean(body.memberId);
  if (!token) return json({ ok: true, registered: false });
  const hash = await sha256(token);
  const existing = await env.PUSH_TOKENS.get(tokenKey(hash), 'json');
  return json({ ok: true, registered: Boolean(existing && (!memberId || existing.memberId === memberId)), memberId: existing?.memberId || '' });
}

function authorized(request, env, body, url) {
  const expected = String(env.INTERNAL_KEY || '');
  if (!expected) return false;
  const auth = request.headers.get('authorization') || '';
  const supplied = clean(
    request.headers.get('x-jayuminton-key') ||
    (auth.toLowerCase().startsWith('bearer ') ? auth.slice(7) : '') ||
    body.internalKey || url.searchParams.get('key'),
    512,
  );
  return supplied === expected;
}

async function memberRecords(env, memberId) {
  const prefix = `m:${encodeURIComponent(memberId)}:`;
  const records = [];
  let cursor;
  do {
    const page = await env.PUSH_TOKENS.list({ prefix, cursor, limit: 1000 });
    for (const key of page.keys) {
      const record = await env.PUSH_TOKENS.get(key.name, 'json');
      if (record?.token) records.push(record);
    }
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);
  return records;
}

function notificationText(event, member) {
  if (event.type === 'wait1_ready') {
    return { title: '대기 1 안내', body: `${member.name || ''}님, 대기 1입니다. 라켓 들고 준비해 주세요.` };
  }
  return { title: '코트 입장 안내', body: `${member.name || ''}님, ${Number(event.courtNo || 0)}번 코트로 입장해 주세요.` };
}

async function removeRecord(env, record) {
  const hash = await sha256(record.token);
  await Promise.all([
    env.PUSH_TOKENS.delete(tokenKey(hash)),
    env.PUSH_TOKENS.delete(memberKey(record.memberId, hash)),
  ]);
}

async function sendFcm(env, accessToken, projectId, event, member, record) {
  const copy = notificationText(event, member);
  const data = {
    type: String(event.type),
    assignmentId: String(event.assignmentId || ''),
    memberId: String(member.id || ''),
    memberName: String(member.name || ''),
    title: copy.title,
    body: copy.body,
    courtNo: String(event.courtNo || ''),
    expectedCourtNo: String(event.expectedCourtNo || ''),
    repeatCount: '1',
  };
  const android = { priority: 'high', ttl: '600s' };
  if (/JayumintonNativeAndroid\//i.test(record.userAgent || '')) {
    android.restricted_package_name = 'com.jayuminton.user';
  } else if (/JayumintonMemberNative\//i.test(record.userAgent || '')) {
    android.restricted_package_name = 'com.jayuminton.member';
  }
  const response = await fetch(`https://fcm.googleapis.com/v1/projects/${encodeURIComponent(projectId)}/messages:send`, {
    method: 'POST',
    headers: { authorization: `Bearer ${accessToken}`, 'content-type': 'application/json' },
    body: JSON.stringify({ message: { token: record.token, data, android } }),
  });
  const text = await response.text();
  if (!response.ok && (response.status === 404 || response.status === 410 || /UNREGISTERED|registration-token-not-registered/i.test(text))) {
    await removeRecord(env, record);
  }
  return response.ok;
}

async function sendEvent(request, env, body, url) {
  if (!authorized(request, env, body, url)) return json({ ok: false, error: 'unauthorized' }, 403);
  const type = clean(body.type);
  if (!['wait1_ready', 'court_assignment'].includes(type)) return json({ ok: false, error: 'invalid_type' }, 400);
  const members = Array.isArray(body.members) ? body.members.map(m => ({ id: clean(m?.id), name: clean(m?.name, 80) })).filter(m => m.id) : [];
  if (!members.length || members.length > 4) return json({ ok: false, error: 'invalid_members' }, 400);
  const event = {
    type,
    assignmentId: clean(body.assignmentId, 500) || `${type}-${Date.now()}`,
    courtNo: Number(body.courtNo || 0),
    expectedCourtNo: Number(body.expectedCourtNo || 0),
  };
  const credentials = JSON.parse(env.FIREBASE_SERVICE_ACCOUNT_JSON || '{}');
  const accessToken = await googleAccessToken(env);
  const seen = new Set();
  const targets = [];
  for (const member of members) {
    for (const record of await memberRecords(env, member.id)) {
      if (!seen.has(record.token)) {
        seen.add(record.token);
        targets.push({ member, record });
      }
    }
  }
  if (!targets.length) return json({ ok: true, assignmentId: event.assignmentId, sent: 0, failed: 0, noRegisteredToken: members.length });
  const results = await Promise.all(targets.map(t => sendFcm(env, accessToken, credentials.project_id, event, t.member, t.record)));
  const sent = results.filter(Boolean).length;
  return json({ ok: sent === results.length, assignmentId: event.assignmentId, sent, failed: results.length - sent });
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return json({ ok: true }, 204);
    const url = new URL(request.url);
    try {
      if (request.method === 'GET' && (url.pathname === '/' || url.pathname === '/health')) {
        const page = await env.PUSH_TOKENS.list({ prefix: 't:', limit: 1 });
        return json({ ok: true, service: 'jayuminton-cloudflare-user-push', mappingPresent: page.keys.length > 0 });
      }
      if (request.method !== 'POST') return json({ ok: false, error: 'method_not_allowed' }, 405);
      const body = await readBody(request);
      const action = clean(body.action);
      if (url.pathname === '/api/push/register' || action === 'register_web_token' || action === 'register_token') return register(env, body);
      if (url.pathname === '/api/push/unregister' || action === 'unregister_web_token' || action === 'unregister_token') return unregister(env, body);
      if (url.pathname === '/api/push/status' || action === 'token_status') return tokenStatus(env, body);
      if (url.pathname === '/api/push/event' || action === 'main_state_event' || ['wait1_ready', 'court_assignment'].includes(action)) return sendEvent(request, env, body, url);
      return json({ ok: false, error: 'unknown_action' }, 400);
    } catch (error) {
      return json({ ok: false, error: String(error?.message || error || 'unknown_error') }, 500);
    }
  },
};
