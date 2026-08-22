const jsonHeaders = {
  'content-type': 'application/json; charset=utf-8',
  'access-control-allow-origin': '*',
  'access-control-allow-methods': 'GET,POST,OPTIONS',
  'access-control-allow-headers': 'content-type,x-jayuminton-key',
  'cache-control': 'no-store',
};

function reply(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: jsonHeaders });
}

function emptyState() {
  return {
    schemaVersion: 1,
    revision: 0,
    members: [],
    courts: { '1': [], '2': [], '3': [], '4': [] },
    courtStartedAt: { '1': '', '2': '', '3': '', '4': '' },
    waitGroups: [[], [], [], [], []],
    settings: { memberPassword: '', memberPasswordVersion: 1, courtOrientation: 'door-right' },
    swapRequests: [],
    actionHistory: [],
    updatedAt: new Date(0).toISOString(),
  };
}

function normalizeState(input) {
  const base = emptyState();
  const state = input && typeof input === 'object' ? structuredClone(input) : {};
  state.schemaVersion = 1;
  state.members = Array.isArray(state.members) ? state.members : [];
  state.courts = state.courts && typeof state.courts === 'object' ? state.courts : base.courts;
  for (const no of ['1', '2', '3', '4']) state.courts[no] = Array.isArray(state.courts[no]) ? state.courts[no].map(String).slice(0, 4) : [];
  state.waitGroups = Array.isArray(state.waitGroups) ? state.waitGroups.slice(0, 5) : [];
  while (state.waitGroups.length < 5) state.waitGroups.push([]);
  state.waitGroups = state.waitGroups.map(group => Array.isArray(group) ? group.map(String).slice(0, 4) : []);
  state.courtStartedAt = Object.assign(base.courtStartedAt, state.courtStartedAt || {});
  state.settings = Object.assign(base.settings, state.settings || {});
  state.swapRequests = Array.isArray(state.swapRequests) ? state.swapRequests : [];
  state.actionHistory = Array.isArray(state.actionHistory) ? state.actionHistory.slice(-30) : [];
  state.revision = Math.max(0, Number(state.revision) || 0);
  state.updatedAt = String(state.updatedAt || new Date().toISOString());
  return state;
}

async function digest(value) {
  const bytes = new TextEncoder().encode(value);
  const hash = await crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(hash)].map(v => v.toString(16).padStart(2, '0')).join('');
}

async function readState(db) {
  const row = await db.prepare('SELECT revision,state_json,updated_at FROM app_state WHERE id=1').first();
  if (!row) return emptyState();
  const state = normalizeState(JSON.parse(row.state_json));
  state.revision = Number(row.revision) || 0;
  state.updatedAt = String(row.updated_at || state.updatedAt);
  return state;
}

async function writeState(db, state) {
  state = normalizeState(state);
  state.revision = Math.max(0, Number(state.revision) || 0) + 1;
  state.updatedAt = new Date().toISOString();
  await db.prepare('INSERT INTO app_state(id,revision,state_json,updated_at) VALUES(1,?,?,?) ON CONFLICT(id) DO UPDATE SET revision=excluded.revision,state_json=excluded.state_json,updated_at=excluded.updated_at')
    .bind(state.revision, JSON.stringify(state), state.updatedAt).run();
  return state;
}

function assertInternal(request, env) {
  const expected = String(env.INTERNAL_KEY || '');
  const actual = String(request.headers.get('x-jayuminton-key') || '');
  if (!expected || actual !== expected) throw new Error('unauthorized');
}

export class StateCoordinator {
  constructor(state, env) { this.state = state; this.env = env; }

  async fetch(request) {
    try {
      const body = await request.json();
      const action = String(body.action || '');
      if (action === 'import') {
        assertInternal(request, this.env);
        const incoming = normalizeState(body.state);
        const existing = await readState(this.env.DB);
        if (existing.revision > 0 && !body.replace) return reply({ ok: false, error: 'state_exists' }, 409);
        const canonical = JSON.stringify(incoming);
        const sourceDigest = await digest(canonical);
        const saved = await writeState(this.env.DB, incoming);
        await this.env.DB.prepare('INSERT INTO migration_audit(source,source_digest,member_count,imported_at) VALUES(?,?,?,?)')
          .bind(String(body.source || 'manual'), sourceDigest, saved.members.length, saved.updatedAt).run();
        return reply({ ok: true, revision: saved.revision, memberCount: saved.members.length, sourceDigest });
      }
      if (action === 'backup') {
        assertInternal(request, this.env);
        const current = await readState(this.env.DB);
        await this.env.DB.prepare('DELETE FROM state_backups').run();
        await this.env.DB.prepare('INSERT INTO state_backups(revision,state_json,created_at) VALUES(?,?,?)')
          .bind(current.revision, JSON.stringify(current), new Date().toISOString()).run();
        return reply({ ok: true, revision: current.revision });
      }
      return reply({ ok: false, error: 'unsupported_action' }, 400);
    } catch (error) {
      const message = String(error && error.message || error);
      return reply({ ok: false, error: message }, message === 'unauthorized' ? 401 : 500);
    }
  }
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: jsonHeaders });
    const url = new URL(request.url);
    if (url.pathname === '/health') {
      let database = false;
      try { await env.DB.prepare('SELECT 1 AS ok').first(); database = true; } catch (_) {}
      return reply({ ok: database, backend: 'cloudflare-only', database: 'd1', concurrency: 'durable-object', gas: false });
    }
    if (url.pathname === '/api/internal/state' && request.method === 'GET') {
      try { assertInternal(request, env); }
      catch (_) { return reply({ ok: false, error: 'unauthorized' }, 401); }
      return reply({ ok: true, state: await readState(env.DB) });
    }
    if (url.pathname === '/api/internal/import' && request.method === 'POST') {
      const id = env.STATE_COORDINATOR.idFromName('global-state');
      const body = Object.assign(await request.json(), { action: 'import' });
      return env.STATE_COORDINATOR.get(id).fetch(new Request(url, { method: 'POST', headers: request.headers, body: JSON.stringify(body) }));
    }
    if (url.pathname === '/api/internal/backup' && request.method === 'POST') {
      const id = env.STATE_COORDINATOR.idFromName('global-state');
      return env.STATE_COORDINATOR.get(id).fetch(new Request(url, { method: 'POST', headers: request.headers, body: JSON.stringify({ action: 'backup' }) }));
    }
    return reply({ ok: false, error: 'not_found' }, 404);
  },
};
