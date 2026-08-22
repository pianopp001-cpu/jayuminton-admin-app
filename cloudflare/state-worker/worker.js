const jsonHeaders = {
  'content-type': 'application/json; charset=utf-8',
  'access-control-allow-origin': '*',
  'access-control-allow-methods': 'GET,POST,OPTIONS',
  'access-control-allow-headers': 'content-type,x-jayuminton-key,authorization',
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

export function autoAssignMutation(input, candidateIds, destinations) {
  let state = normalizeState(input);
  const memberById = new Map(state.members.map(m => [String(m.id), m]));
  const available = uniqueIds(candidateIds, 200).filter(id => memberById.has(id) && !locationOf(state, id));
  const ordered = [];
  const men = available.filter(id => String(memberById.get(id).gender || '').toLowerCase().startsWith('m') || memberById.get(id).gender === '남');
  const women = available.filter(id => !men.includes(id));
  while (men.length || women.length) { if (men.length) ordered.push(men.shift()); if (women.length) ordered.push(women.shift()); }
  const assigned = [];
  for (const destination of Array.isArray(destinations) ? destinations : []) {
    const free = Math.max(0, 4 - container(state, destination).length); const ids = ordered.splice(0, free);
    if (!ids.length) continue;
    state = moveMutation(state, ids, destination).state; assigned.push({ destination, memberIds: ids });
  }
  return { state, event: { type: 'auto_assigned', assigned } };
}

export function upsertMemberMutation(input, member) {
  const state = normalizeState(input); const id = String(member?.id || crypto.randomUUID()); const name = String(member?.name || '').trim();
  if (!name || name.length > 20) throw new Error('invalid_member_name');
  const clean = { id, name, gender: member.gender === '여' ? '여' : '남', grade: String(member.grade || ''), career: String(member.career || member.experience || ''), publicMemo: String(member.publicMemo || member.memo || ''), isNew: Boolean(member.isNew), isSponsor: Boolean(member.isSponsor), games: Math.max(0, Number(member.games) || 0), status: String(member.status || 'active'), createdAt: String(member.createdAt || new Date().toISOString()) };
  const index = state.members.findIndex(m => String(m.id) === id);
  if (index >= 0) state.members[index] = { ...state.members[index], ...clean }; else state.members.push(clean);
  return { state, event: { type: index >= 0 ? 'member_updated' : 'member_created', memberId: id } };
}

export function setMemberStatusMutation(input, memberIds, status) {
  const state = normalizeState(input); const ids = uniqueIds(memberIds, 200);
  if (!['active', 'before', 'rest', 'home'].includes(String(status))) throw new Error('invalid_member_status');
  removeEverywhere(state, ids); const wanted = new Set(ids);
  state.members = state.members.map(m => wanted.has(String(m.id)) ? { ...m, status: String(status) } : m);
  return { state, event: { type: 'member_status_changed', memberIds: ids, status: String(status) } };
}

export function adjustGamesMutation(input, memberIds, delta, reset = false) {
  const state = normalizeState(input); const ids = uniqueIds(memberIds, 200); const wanted = new Set(ids);
  if (!ids.length) throw new Error('members_required');
  if (!reset && ![-1, 1].includes(Number(delta))) throw new Error('invalid_game_delta');
  state.members = state.members.map(m => wanted.has(String(m.id)) ? { ...m, games: reset ? 0 : Math.max(0, (Number(m.games) || 0) + Number(delta)) } : m);
  return { state, event: { type: 'games_adjusted', memberIds: ids, delta: reset ? 'reset' : Number(delta) } };
}

export function requestSwapMutation(input, requesterId, targetId, nowMs = Date.now()) {
  const state = normalizeState(input); const requester = String(requesterId); const target = String(targetId);
  if (requester === target || !locationOf(state, requester) || !locationOf(state, target)) throw new Error('invalid_swap_request');
  state.swapRequests = state.swapRequests.filter(r => r.status !== 'pending' || Number(r.expiresAt) > nowMs);
  const request = { id: crypto.randomUUID(), requesterId: requester, targetId: target, status: 'pending', createdAt: nowMs, expiresAt: nowMs + 300000 };
  state.swapRequests.push(request); return { state, event: { type: 'swap_requested', request } };
}

export function respondSwapMutation(input, requestId, responderId, accept, nowMs = Date.now()) {
  let state = normalizeState(input); const request = state.swapRequests.find(r => r.id === String(requestId));
  if (!request || request.status !== 'pending' || request.targetId !== String(responderId)) throw new Error('swap_request_not_found');
  if (Number(request.expiresAt) <= nowMs) { request.status = 'expired'; return { state, event: { type: 'swap_expired', requestId: request.id } }; }
  request.status = accept ? 'accepted' : 'rejected'; request.respondedAt = nowMs;
  if (accept) state = swapMutation(state, [request.requesterId], [request.targetId]).state;
  const saved = state.swapRequests.find(r => r.id === request.id); if (saved) Object.assign(saved, request);
  return { state, event: { type: accept ? 'swap_accepted' : 'swap_rejected', requestId: request.id } };
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

function bytesToBase64Url(bytes) {
  let binary = ''; for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/g, '');
}
function stringToBase64Url(value) { return bytesToBase64Url(new TextEncoder().encode(value)); }
function base64UrlToString(value) {
  const base64 = String(value).replaceAll('-', '+').replaceAll('_', '/').padEnd(Math.ceil(String(value).length / 4) * 4, '=');
  return new TextDecoder().decode(Uint8Array.from(atob(base64), c => c.charCodeAt(0)));
}
async function hmac(value, secret) {
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  return bytesToBase64Url(new Uint8Array(await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(value))));
}
async function issueMemberSession(env, state, memberId) {
  const payload = stringToBase64Url(JSON.stringify({ memberId: String(memberId || ''), passwordVersion: Number(state.settings.memberPasswordVersion || 1), expiresAt: Date.now() + 30 * 86400000 }));
  return `${payload}.${await hmac(payload, String(env.INTERNAL_KEY || ''))}`;
}
async function verifyMemberSession(request, env, state) {
  const auth = String(request.headers.get('authorization') || ''); const token = auth.toLowerCase().startsWith('bearer ') ? auth.slice(7) : '';
  const [payload, signature] = token.split('.');
  if (!payload || !signature || signature !== await hmac(payload, String(env.INTERNAL_KEY || ''))) throw new Error('unauthorized');
  const session = JSON.parse(base64UrlToString(payload));
  if (Number(session.expiresAt) <= Date.now() || Number(session.passwordVersion) !== Number(state.settings.memberPasswordVersion || 1)) throw new Error('session_expired');
  if (session.memberId && !state.members.some(m => String(m.id) === String(session.memberId))) throw new Error('member_not_found');
  return session;
}

export function publicState(state, memberId = '') {
  const safe = normalizeState(state); const me = String(memberId || '');
  safe.settings = { memberPasswordVersion: Number(safe.settings.memberPasswordVersion || 1), courtOrientation: safe.settings.courtOrientation };
  safe.swapRequests = safe.swapRequests.filter(r => r.status === 'pending' && (r.requesterId === me || r.targetId === me));
  delete safe.actionHistory; return safe;
}

function findPrior(state, operationId) { return operationId && state.actionHistory.find(item => item.operationId === operationId); }
function recordAction(state, operationId, action, event, beforeState) {
  const undoState = normalizeState(beforeState); undoState.actionHistory = [];
  state.actionHistory.push({ operationId, action, event, undoState, at: new Date().toISOString() });
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
      if (action === 'undoLast') {
        const last = current.actionHistory[current.actionHistory.length - 1];
        if (!last?.undoState) return reply({ ok: false, error: 'nothing_to_undo' }, 409);
        const restored = normalizeState(last.undoState); restored.actionHistory = current.actionHistory.slice(0, -1);
        return reply({ ok: true, state: await writeState(this.env.DB, restored), event: { type: 'action_undone', action: last.action } });
      }
      let result;
      if (action === 'finishCourt') result = finishCourtMutation(current, body.courtNo);
      else if (action === 'moveMembers') result = moveMutation(current, body.memberIds, body.destination);
      else if (action === 'swapMembers') result = swapMutation(current, body.leftIds, body.rightIds);
      else if (action === 'autoAssign') result = autoAssignMutation(current, body.candidateIds, body.destinations);
      else if (action === 'upsertMember') result = upsertMemberMutation(current, body.member);
      else if (action === 'setMemberStatus') result = setMemberStatusMutation(current, body.memberIds, body.status);
      else if (action === 'adjustGames') result = adjustGamesMutation(current, body.memberIds, body.delta, body.reset);
      else if (action === 'requestSwap') result = requestSwapMutation(current, body.requesterId, body.targetId);
      else if (action === 'respondSwap') result = respondSwapMutation(current, body.requestId, body.responderId, body.accept);
      else if (action === 'setSettings') {
        result = { state: normalizeState(current), event: { type: 'settings_updated' } };
        if (body.memberPassword !== undefined) { result.state.settings.memberPassword = String(body.memberPassword); result.state.settings.memberPasswordVersion = Number(result.state.settings.memberPasswordVersion || 0) + 1; }
        if (['door-left', 'door-right'].includes(body.courtOrientation)) result.state.settings.courtOrientation = body.courtOrientation;
      }
      else if (action === 'deleteMembers') {
        result = setMemberStatusMutation(current, body.memberIds, 'home'); const ids = new Set(uniqueIds(body.memberIds, 200));
        result.state.members = result.state.members.filter(m => !ids.has(String(m.id))); result.event.type = 'members_deleted';
      }
      else if (action === 'resetAll') {
        result = { state: emptyState(), event: { type: 'all_reset' } };
        result.state.settings = { ...current.settings };
      }
      else return reply({ ok: false, error: 'unsupported_action' }, 400);
      recordAction(result.state, operationId, action, result.event, current);
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

async function coordinatorAsInternal(request, env, action, body = {}) {
  const headers = new Headers(request.headers); headers.set('x-jayuminton-key', String(env.INTERNAL_KEY || ''));
  const id = env.STATE_COORDINATOR.idFromName('global-state');
  return env.STATE_COORDINATOR.get(id).fetch(new Request(request.url, { method: 'POST', headers, body: JSON.stringify({ ...body, action }) }));
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: jsonHeaders });
    const url = new URL(request.url);
    if (url.pathname === '/health') {
      let database = false; try { await env.DB.prepare('SELECT 1 AS ok').first(); database = true; } catch (_) {}
      return reply({ ok: database, backend: 'cloudflare-only', database: 'd1', concurrency: 'durable-object', gas: false, rpcVersion: 3 });
    }
    if (url.pathname === '/api/internal/state' && request.method === 'GET') {
      try { assertInternal(request, env); } catch (_) { return reply({ ok: false, error: 'unauthorized' }, 401); }
      return reply({ ok: true, state: await readState(env.DB) });
    }
    if (url.pathname === '/api/internal/import' && request.method === 'POST') return coordinator(request, env, 'import', await request.json());
    if (url.pathname === '/api/internal/backup' && request.method === 'POST') return coordinator(request, env, 'backup');
    if (url.pathname === '/api/internal/rpc' && request.method === 'POST') { const body = await request.json(); return coordinator(request, env, String(body.action || ''), body); }
    if (url.pathname === '/api/member/login' && request.method === 'POST') {
      const body = await request.json(); const state = await readState(env.DB);
      if (!state.settings.memberPassword || String(body.password || '') !== String(state.settings.memberPassword)) return reply({ ok: false, error: 'invalid_password' }, 401);
      const memberId = String(body.memberId || '');
      if (memberId && !state.members.some(m => String(m.id) === memberId)) return reply({ ok: false, error: 'member_not_found' }, 404);
      return reply({ ok: true, token: await issueMemberSession(env, state, memberId), state: publicState(state, memberId) });
    }
    if (url.pathname === '/api/member/state' && request.method === 'GET') {
      try { const state = await readState(env.DB); const session = await verifyMemberSession(request, env, state); return reply({ ok: true, state: publicState(state, session.memberId), memberId: session.memberId }); }
      catch (error) { return reply({ ok: false, error: String(error?.message || error) }, 401); }
    }
    if (url.pathname === '/api/member/identity' && request.method === 'POST') {
      try {
        const state = await readState(env.DB); await verifyMemberSession(request, env, state); const body = await request.json(); const memberId = String(body.memberId || '');
        if (!state.members.some(m => String(m.id) === memberId)) return reply({ ok: false, error: 'member_not_found' }, 404);
        return reply({ ok: true, token: await issueMemberSession(env, state, memberId), memberId });
      } catch (error) { return reply({ ok: false, error: String(error?.message || error) }, 401); }
    }
    if (url.pathname === '/api/member/rpc' && request.method === 'POST') {
      try {
        const state = await readState(env.DB); const session = await verifyMemberSession(request, env, state); const body = await request.json();
        if (!session.memberId) return reply({ ok: false, error: 'member_identity_required' }, 403);
        if (body.action === 'selfMove') {
          if (container(state, body.destination).length >= 4) return reply({ ok: false, error: 'location_full' }, 409);
          return coordinatorAsInternal(request, env, 'moveMembers', { operationId: body.operationId, memberIds: [session.memberId], destination: body.destination });
        }
        if (body.action === 'requestSwap') return coordinatorAsInternal(request, env, 'requestSwap', { operationId: body.operationId, requesterId: session.memberId, targetId: body.targetId });
        if (body.action === 'respondSwap') return coordinatorAsInternal(request, env, 'respondSwap', { operationId: body.operationId, requestId: body.requestId, responderId: session.memberId, accept: Boolean(body.accept) });
        return reply({ ok: false, error: 'unsupported_member_action' }, 400);
      } catch (error) { return reply({ ok: false, error: String(error?.message || error) }, 401); }
    }
    return reply({ ok: false, error: 'not_found' }, 404);
  },
};
