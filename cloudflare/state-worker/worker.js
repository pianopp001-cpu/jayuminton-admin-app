const jsonHeaders = {
  'content-type': 'application/json; charset=utf-8',
  'access-control-allow-origin': '*',
  'access-control-allow-methods': 'GET,POST,OPTIONS',
  'access-control-allow-headers': 'content-type,x-jayuminton-key',
  'cache-control': 'no-store',
};

function reply(body, status = 200) { return new Response(JSON.stringify(body), { status, headers: jsonHeaders }); }

export function emptyState() {
  return {
    schemaVersion: 2, revision: 0, members: [],
    courts: { '1': [], '2': [], '3': [], '4': [] },
    courtStartedAt: { '1': '', '2': '', '3': '', '4': '' },
    waitGroups: [[], [], [], [], []],
    settings: { memberPassword: '', memberPasswordVersion: 1, courtOrientation: 'door-right' },
    swapRequests: [], actionHistory: [], updatedAt: new Date(0).toISOString(),
  };
}

function uniqueIds(value, limit = 4) { return [...new Set((Array.isArray(value) ? value : []).map(String).filter(Boolean))].slice(0, limit); }

export function normalizeState(input) {
  const base = emptyState();
  const state = input && typeof input === 'object' ? structuredClone(input) : {};
  state.schemaVersion = 2;
  state.members = Array.isArray(state.members) ? state.members : [];
  state.courts = state.courts && typeof state.courts === 'object' ? state.courts : base.courts;
  state.waitGroups = Array.isArray(state.waitGroups) ? state.waitGroups.slice(0, 5) : [];
  while (state.waitGroups.length < 5) state.waitGroups.push([]);
  const occupied = new Set();
  for (const no of ['1', '2', '3', '4']) {
    state.courts[no] = uniqueIds(state.courts[no]).filter(id => !occupied.has(id));
    state.courts[no].forEach(id => occupied.add(id));
  }
  state.waitGroups = state.waitGroups.map(group => uniqueIds(group).filter(id => {
    if (occupied.has(id)) return false;
    occupied.add(id); return true;
  }));
  state.courtStartedAt = Object.assign(base.courtStartedAt, state.courtStartedAt || {});
  state.settings = Object.assign(base.settings, state.settings || {});
  state.swapRequests = Array.isArray(state.swapRequests) ? state.swapRequests.slice(-100) : [];
  state.actionHistory = Array.isArray(state.actionHistory) ? state.actionHistory.slice(-50) : [];
  state.revision = Math.max(0, Number(state.revision) || 0);
  state.updatedAt = String(state.updatedAt || new Date().toISOString());
  return syncMemberStatuses(state);
}

function locationOf(state, memberId) {
  const id = String(memberId);
  for (const no of ['1', '2', '3', '4']) if (state.courts[no].includes(id)) return { type: 'court', key: no };
  for (let i = 0; i < 5; i += 1) if (state.waitGroups[i].includes(id)) return { type: 'wait', key: String(i + 1) };
  return null;
}

function removeEverywhere(state, memberIds) {
  const ids = new Set(memberIds.map(String));
  for (const no of ['1', '2', '3', '4']) state.courts[no] = state.courts[no].filter(id => !ids.has(id));
  state.waitGroups = state.waitGroups.map(group => group.filter(id => !ids.has(id)));
}

function container(state, location) {
  if (location?.type === 'court' && ['1', '2', '3', '4'].includes(String(location.key))) return state.courts[String(location.key)];
  const index = Number(location?.key) - 1;
  if (location?.type === 'wait' && index >= 0 && index < 5) return state.waitGroups[index];
  throw new Error('invalid_location');
}

function syncMemberStatuses(state) {
  const courtIds = new Set(Object.values(state.courts).flat());
  const waitIds = new Set(state.waitGroups.flat());
  state.members = state.members.map(member => {
    const next = { ...member };
    if (courtIds.has(String(member.id))) next.status = 'playing';
    else if (waitIds.has(String(member.id))) next.status = 'waiting';
    else if (!['before', 'rest', 'home'].includes(String(member.status))) next.status = 'active';
    return next;
  });
  return state;
}

function memberSummaries(state, ids) {
  const wanted = new Set(ids.map(String));
  return state.members.filter(m => wanted.has(String(m.id))).map(m => ({ id: String(m.id), name: String(m.name || '') }));
}

function addGames(state, ids, delta = 1) {
  const wanted = new Set(ids.map(String));
  state.members = state.members.map(m => wanted.has(String(m.id)) ? { ...m, games: Math.max(0, (Number(m.games) || 0) + delta) } : m);
}

export function finishCourtMutation(input, courtNo, now = new Date().toISOString()) {
  const state = normalizeState(input);
  const no = String(courtNo);
  if (!['1', '2', '3', '4'].includes(no)) throw new Error('invalid_court');
  const finished = [...state.courts[no]];
  const entrants = [...state.waitGroups[0]];
  const newlyReady = [...state.waitGroups[1]];
  state.courts[no] = entrants;
  state.courtStartedAt[no] = entrants.length ? now : '';
  state.waitGroups = [[...state.waitGroups[1]], [...state.waitGroups[2]], [...state.waitGroups[3]], [...state.waitGroups[4]], []];
  removeEverywhere(state, finished);
  addGames(state, entrants, 1);
  syncMemberStatuses(state);
  return { state, event: { type: 'court_finished', courtNo: Number(no), finished, courtEntrants: memberSummaries(state, entrants), wait1Entrants: memberSummaries(state, newlyReady) } };
}

export function moveMutation(input, memberIds, destination) {
  const state = normalizeState(input);
  const ids = uniqueIds(memberIds);
  if (!ids.length) throw new Error('members_required');
  const target = container(state, destination);
  const existing = target.filter(id => !ids.includes(id));
  if (existing.length + ids.length > 4) throw new Error('location_full');
  const enteringCourt = destination.type === 'court' ? ids.filter(id => locationOf(state, id)?.type !== 'court') : [];
  removeEverywhere(state, ids);
  container(state, destination).push(...ids);
  if (destination.type === 'court') {
    const no = String(destination.key);
    if (!state.courtStartedAt[no]) state.courtStartedAt[no] = new Date().toISOString();
    addGames(state, enteringCourt, 1);
  }
  syncMemberStatuses(state);
  return { state, event: { type: 'members_moved', memberIds: ids, destination } };
}

export function swapMutation(input, leftIds, rightIds) {
  const state = normalizeState(input);
  const a = uniqueIds(leftIds); const b = uniqueIds(rightIds);
  if (!a.length || a.length !== b.length) throw new Error('equal_swap_groups_required');
  const aLoc = locationOf(state, a[0]); const bLoc = locationOf(state, b[0]);
  if (!aLoc || !bLoc || a.some(id => JSON.stringify(locationOf(state, id)) !== JSON.stringify(aLoc)) || b.some(id => JSON.stringify(locationOf(state, id)) !== JSON.stringify(bLoc))) throw new Error('invalid_swap_groups');
  if (JSON.stringify(aLoc) === JSON.stringify(bLoc)) throw new Error('same_location');
  const aTarget = container(state, aLoc); const bTarget = container(state, bLoc);
  a.forEach((id, i) => { aTarget[aTarget.indexOf(id)] = b[i]; });
  b.forEach((id, i) => { bTarget[bTarget.indexOf(id)] = a[i]; });
  const enteringCourt = [];
  if (aLoc.type === 'court' && bLoc.type !== 'court') enteringCourt.push(...b);
  if (bLoc.type === 'court' && aLoc.type !== 'court') enteringCourt.push(...a);
  addGames(state, enteringCourt, 1);
  syncMemberStatuses(state);
  return { state, event: { type: 'members_swapped', leftIds: a, rightIds: b } };
}

async function digest(value) {
  const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
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
  await db.prepare('INSERT INTO app_state(id,revision,state_json,updated_at) VALUES(1,?,?,?) ON CONFLICT(id) DO UPDATE SET revision=excluded.revision,state_json=excluded.state_json,updated_at=excluded.updated_at').bind(state.revision, JSON.stringify(state), state.updatedAt).run();
  return state;
}

function assertInternal(request, env) {
  const expected = String(env.INTERNAL_KEY || '');
  const actual = String(request.headers.get('x-jayuminton-key') || '');
  if (!expected || actual !== expected) throw new Error('unauthorized');
}

function findPrior(state, operationId) { return operationId && state.actionHistory.find(item => item.operationId === operationId); }
function recordAction(state, operationId, action, event) {
  state.actionHistory.push({ operationId, action, event, at: new Date().toISOString() });
  state.actionHistory = state.actionHistory.slice(-50);
}

async function sendPush(env, type, event, members) {
  if (!members.length || !env.PUSH_URL || !env.INTERNAL_KEY) return { ok: true, skipped: true };
  const body = { type, assignmentId: `${type}-${event.courtNo || 0}-${Date.now()}-${members.map(m => m.id).join('-')}`, courtNo: event.courtNo || 0, members };
  try {
    const response = await fetch(env.PUSH_URL, { method: 'POST', headers: { 'content-type': 'application/json', 'x-jayuminton-key': env.INTERNAL_KEY }, body: JSON.stringify(body) });
    return await response.json();
  } catch (error) { return { ok: false, error: String(error?.message || error) }; }
}

export class StateCoordinator {
  constructor(state, env) { this.state = state; this.env = env; }
  async fetch(request) {
    try {
      assertInternal(request, this.env);
      const body = await request.json();
      const action = String(body.action || '');
      if (action === 'import') {
        const incoming = normalizeState(body.state); const existing = await readState(this.env.DB);
        if (existing.revision > 0 && !body.replace) return reply({ ok: false, error: 'state_exists' }, 409);
        const sourceDigest = await digest(JSON.stringify(incoming)); const saved = await writeState(this.env.DB, incoming);
        await this.env.DB.prepare('INSERT INTO migration_audit(source,source_digest,member_count,imported_at) VALUES(?,?,?,?)').bind(String(body.source || 'manual'), sourceDigest, saved.members.length, saved.updatedAt).run();
        return reply({ ok: true, revision: saved.revision, memberCount: saved.members.length, sourceDigest });
      }
      if (action === 'backup') {
        const current = await readState(this.env.DB);
        await this.env.DB.prepare('DELETE FROM state_backups').run();
        await this.env.DB.prepare('INSERT INTO state_backups(revision,state_json,created_at) VALUES(?,?,?)').bind(current.revision, JSON.stringify(current), new Date().toISOString()).run();
        return reply({ ok: true, revision: current.revision });
      }
      if (action === 'restoreBackup') {
        const row = await this.env.DB.prepare('SELECT state_json FROM state_backups ORDER BY id DESC LIMIT 1').first();
        if (!row) return reply({ ok: false, error: 'backup_not_found' }, 404);
        return reply({ ok: true, state: await writeState(this.env.DB, JSON.parse(row.state_json)) });
      }
      const current = await readState(this.env.DB); const operationId = String(body.operationId || ''); const prior = findPrior(current, operationId);
      if (prior) return reply({ ok: true, duplicate: true, state: current, event: prior.event });
      let result;
      if (action === 'finishCourt') result = finishCourtMutation(current, body.courtNo);
      else if (action === 'moveMembers') result = moveMutation(current, body.memberIds, body.destination);
      else if (action === 'swapMembers') result = swapMutation(current, body.leftIds, body.rightIds);
      else return reply({ ok: false, error: 'unsupported_action' }, 400);
      recordAction(result.state, operationId, action, result.event);
      const saved = await writeState(this.env.DB, result.state); const notifications = [];
      if (action === 'finishCourt') {
        notifications.push(await sendPush(this.env, 'court_assignment', result.event, result.event.courtEntrants));
        notifications.push(await sendPush(this.env, 'wait1_ready', result.event, result.event.wait1Entrants));
      }
      return reply({ ok: true, state: saved, event: result.event, notifications });
    } catch (error) {
      const message = String(error?.message || error);
      return reply({ ok: false, error: message }, message === 'unauthorized' ? 401 : 400);
    }
  }
}

async function coordinator(request, env, action, body = {}) {
  const id = env.STATE_COORDINATOR.idFromName('global-state');
  return env.STATE_COORDINATOR.get(id).fetch(new Request(request.url, { method: 'POST', headers: request.headers, body: JSON.stringify({ ...body, action }) }));
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: jsonHeaders });
    const url = new URL(request.url);
    if (url.pathname === '/health') {
      let database = false; try { await env.DB.prepare('SELECT 1 AS ok').first(); database = true; } catch (_) {}
      return reply({ ok: database, backend: 'cloudflare-only', database: 'd1', concurrency: 'durable-object', gas: false, rpcVersion: 2 });
    }
    if (url.pathname === '/api/internal/state' && request.method === 'GET') {
      try { assertInternal(request, env); } catch (_) { return reply({ ok: false, error: 'unauthorized' }, 401); }
      return reply({ ok: true, state: await readState(env.DB) });
    }
    if (url.pathname === '/api/internal/import' && request.method === 'POST') return coordinator(request, env, 'import', await request.json());
    if (url.pathname === '/api/internal/backup' && request.method === 'POST') return coordinator(request, env, 'backup');
    if (url.pathname === '/api/internal/rpc' && request.method === 'POST') { const body = await request.json(); return coordinator(request, env, String(body.action || ''), body); }
    return reply({ ok: false, error: 'not_found' }, 404);
  },
};
