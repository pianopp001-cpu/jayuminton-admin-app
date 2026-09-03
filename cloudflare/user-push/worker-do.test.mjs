import assert from 'node:assert/strict';
import worker, { PushRegistry } from './worker-do.js';

const originalFetch = globalThis.fetch;
const sentPayloads = [];
globalThis.fetch = async (url, init = {}) => {
  const target = String(url);
  if (target === 'https://oauth2.googleapis.com/token') return new Response(JSON.stringify({ access_token: 'test-token', expires_in: 3600 }), { status: 200 });
  if (target.includes('fcm.googleapis.com/')) {
    sentPayloads.push(JSON.parse(init.body));
    return new Response(JSON.stringify({ name: 'projects/test/messages/1' }), { status: 200 });
  }
  return originalFetch(url, init);
};

const records = new Map();
const storage = {
  async get(key) { return records.get(key); },
  async put(values) { for (const [key, value] of Object.entries(values)) records.set(key, value); },
  async delete(keys) { for (const key of Array.isArray(keys) ? keys : [keys]) records.delete(key); },
  async list({ prefix = '', limit = Infinity } = {}) { return new Map([...records].filter(([key]) => key.startsWith(prefix)).slice(0, limit)); },
};
const registry = new PushRegistry({ storage }, {});
const registryStub = { fetch: request => registry.fetch(request) };
const env = {
  INTERNAL_KEY: 'internal',
  FIREBASE_SERVICE_ACCOUNT_JSON: JSON.stringify({ client_email: 'test@example.com', private_key: '-----BEGIN PRIVATE KEY-----\nAA==\n-----END PRIVATE KEY-----', project_id: 'test-project' }),
  PUSH_REGISTRY: { idFromName: () => 'global-v1', get: () => registryStub },
};

// Avoid exercising RSA signing while preserving and inspecting the exact final FCM payload.
const cryptoOriginal = globalThis.crypto;
Object.defineProperty(globalThis, 'crypto', { configurable: true, value: {
  ...cryptoOriginal,
  subtle: { ...cryptoOriginal.subtle, importKey: async () => ({}), sign: async () => new Uint8Array([1]).buffer, digest: cryptoOriginal.subtle.digest.bind(cryptoOriginal.subtle) },
} });

await registry.fetch(new Request('https://registry/register', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ memberId: '7', memberName: '회원7', token: 'x'.repeat(80), userAgent: 'JayumintonNativeAndroid/1' }) }));

for (const scenario of [
  ['swap_request', '자리 교환 요청', '회원1님이 자리 교환을 요청했습니다.'],
  ['swap_result', '자리 교환 결과', '회원7님이 자리 교환 요청을 수락했습니다.'],
  ['pair_request', '짝 요청', '회원14님이 함께 경기할 짝을 요청했습니다.'],
  ['pair_result', '짝 요청 결과', '회원15님이 짝 요청을 거절했습니다.'],
]) {
  const [type, title, body] = scenario;
  const response = await worker.fetch(new Request('https://push/api/push/event', { method: 'POST', headers: { 'content-type': 'application/json', 'x-jayuminton-key': 'internal' }, body: JSON.stringify({ type, members: [{ id: '7', name: '회원7' }], messageText: body }) }), env);
  assert.equal(response.status, 200);
  const payload = sentPayloads.at(-1).message;
  assert.equal(payload.data.type, type);
  assert.equal(payload.data.title, title);
  assert.equal(payload.data.body, body);
  assert.equal(payload.android.priority, 'high');
  assert.equal(payload.android.restricted_package_name, 'com.jayuminton.user');
}

console.log('user-push worker-do tests passed');
