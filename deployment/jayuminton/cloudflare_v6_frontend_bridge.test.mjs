import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('./cloudflare_v6_frontend_bridge.js', import.meta.url), 'utf8');

async function run({ admin, stored, name, args }) {
  let request;
  const localStorage = {
    getItem(key) { return stored[key] || ''; },
    setItem(key, value) { stored[key] = String(value); },
    removeItem(key) { delete stored[key]; },
  };
  const context = {
    IS_ADMIN: admin,
    localStorage,
    window: {},
    document: { readyState: 'loading', addEventListener() {} },
    setTimeout,
    fetch: async (_url, options) => {
      request = options;
      return { json: async () => ({ ok: true, result: { ok: true } }) };
    },
    Proxy, Object, Array, String, JSON, Error, Promise,
  };
  context.window = context;
  vm.runInNewContext(source, context);
  await new Promise((resolve, reject) => {
    context.google.script.run.withSuccessHandler(resolve).withFailureHandler(reject)[name](...args);
  });
  return request;
}

const adminRequest = await run({
  admin: true,
  stored: { jayuminton_admin_session_v1: 'admin-session' },
  name: 'finishCourt',
  args: ['old-admin-pin', 2],
});
assert.equal(adminRequest.headers.authorization, 'Bearer admin-session');
assert.deepEqual(JSON.parse(adminRequest.body).args, ['old-admin-pin', 2]);

const memberRequest = await run({
  admin: false,
  stored: { jayuminton_member_session_token_v1: 'member-session' },
  name: 'memberMoveSelf',
  args: ['member-id', { type: 'wait', key: '1' }],
});
assert.equal(memberRequest.headers.authorization, 'Bearer member-session');
assert.equal(JSON.parse(memberRequest.body).args[0], 'member-id');

const loginRequest = await run({ admin: true, stored: {}, name: 'createAdminSession', args: ['entered-pin'] });
assert.equal('authorization' in loginRequest.headers, false);

console.log('CLOUDFLARE_V6_BRIDGE_AUTH_TESTS_OK');
