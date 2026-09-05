import core, { StateCoordinator } from './worker.js';

export { StateCoordinator };

const JSON_HEADERS = {
  'content-type': 'application/json; charset=utf-8',
  'cache-control': 'no-store',
  'access-control-allow-origin': '*',
  'access-control-allow-methods': 'GET,POST,OPTIONS',
  'access-control-allow-headers': 'content-type,x-jayuminton-key,authorization',
};
const reply = (body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: JSON_HEADERS });
const uniq = (xs) =>
  [...new Set((Array.isArray(xs) ? xs : []).map(String).filter(Boolean))];

const MUTATING_COMPAT = new Set([
  'addMember','updateMemberProfile','setMemberStatus','deleteMembers',
  'assignMembersToCourt','assignMembersToWaitGroup','smartAssignSelected',
  'finishCourt','undoLastAction','adjustMemberGames',
  'decreaseSelectedGameCounts','resetSelectedGameCounts',
  'resetAllOperationData','restoreManualBackup','changeMemberPassword',
  'memberMoveSelf','memberReturnSelfToWait','memberMoveToWaitGroup',
  'memberLeaveWaitGroup','memberAcceptAnywhereSwap','memberRejectAnywhereSwap',
]);

const isMale = (m) => {
  const g = String(m?.gender || '').toLowerCase();
  return g === '남' || g === 'male' || g.startsWith('m');
};

function stateLocation(state, memberId) {
  const id = String(memberId);
  for (const no of ['1','2','3','4']) {
    if ((state?.courts?.[no] || []).map(String).includes(id)) {
      return { type: 'court', key: no };
    }
  }
  const groups = Array.isArray(state?.waitGroups) ? state.waitGroups : [];
  for (let i = 0; i < groups.length; i += 1) {
    if ((groups[i] || []).map(String).includes(id)) {
      return { type: 'wait', key: String(i + 1) };
    }
  }
  const member = (state?.members || []).find(m => String(m?.id) === id);
  if (member && String(member.status) === 'active') {
    return { type: 'active', key: 'active' };
  }
  return null;
}

function occupiedIds(state) {
  return new Set([
    ...Object.values(state?.courts || {}).flat().map(String),
    ...(state?.waitGroups || []).flat().map(String),
  ]);
}

export function targetArray(state, destination) {
  if (destination?.type === 'court') {
    return (state?.courts?.[String(destination.key)] || []).map(String);
  }
  if (destination?.type === 'wait') {
    const index = Math.max(0, Number(destination.key || 1) - 1);
    return (state?.waitGroups?.[index] || []).map(String);
  }
  return [];
}

export function selectValidFill(state, pool, destination, membersById) {
  const target = targetArray(state, destination);
  const free = Math.max(0, 4 - target.length);
  if (!free || !pool.length) return [];

  const existingMen = target.filter(id => isMale(membersById.get(id))).length;
  const existingWomen = target.length - existingMen;
  const patterns = [[2, 2], [4, 0], [0, 4]];

  for (const [finalMen, finalWomen] of patterns) {
    const needMen = finalMen - existingMen;
    const needWomen = finalWomen - existingWomen;
    if (needMen < 0 || needWomen < 0 || needMen + needWomen !== free) continue;
    const men = pool.filter(id => isMale(membersById.get(id)));
    const women = pool.filter(id => !isMale(membersById.get(id)));
    if (men.length < needMen || women.length < needWomen) continue;
    return [...men.slice(0, needMen), ...women.slice(0, needWomen)];
  }

  if (pool.length <= free) return pool.slice(0, free);
  return [];
}

export function eligibleAutoAssignPool(state, candidateIds = []) {
  const members = Array.isArray(state?.members) ? state.members : [];
  const membersById = new Map(members.map(m => [String(m?.id || ''), m]));
  const occupied = occupiedIds(state);
  const requested = uniq(candidateIds);
  const source = requested.length ? requested : members.map(m => String(m?.id || '')).filter(Boolean);
  return uniq(source).filter(id => {
    const member = membersById.get(id);
    return member && String(member.status || 'active') === 'active' && !occupied.has(id);
  });
}

async function getAdminState(request, env) {
  const url = new URL(request.url);
  url.pathname = '/api/admin/state';
  const res = await core.fetch(new Request(url.toString(), { method: 'GET', headers: request.headers }), env);
  const packet = await res.json();
  if (!packet.ok) throw new Error(packet.error || 'admin_state_failed');
  return packet.state;
}

async function getVisibleState(request, env) {
  try { return await getAdminState(request, env); } catch (_) {}
  const url = new URL(request.url);
  url.pathname = '/api/member/state';
  const res = await core.fetch(new Request(url.toString(), { method: 'GET', headers: request.headers }), env);
  const packet = await res.json();
  if (!packet.ok) throw new Error(packet.error || 'member_state_failed');
  return packet.state;
}

async function moveOne(request, env, memberIds, destination) {
  const url = new URL(request.url);
  url.pathname = '/api/admin/rpc';
  const headers = new Headers(request.headers);
  headers.set('content-type', 'application/json');
  const res = await core.fetch(new Request(url.toString(), {
    method: 'POST', headers,
    body: JSON.stringify({ action: 'moveMembers', operationId: `md-auto-${Date.now()}-${crypto.randomUUID()}`, memberIds, destination }),
  }), env);
  const packet = await res.json();
  if (!packet.ok) throw new Error(packet.error || 'autoassign_move_failed');
  return packet;
}

async function mdAutoAssign(request, env, candidateIds, destinations) {
  let state = await getAdminState(request, env);
  const membersById = new Map((state.members || []).map(m => [String(m.id), m]));
  const pool = eligibleAutoAssignPool(state, candidateIds);
  const assigned = []; const courtEntrantIds = [];
  for (const destination of Array.isArray(destinations) ? destinations : []) {
    const ids = selectValidFill(state, pool, destination, membersById);
    if (!ids.length) continue;
    const moved = await moveOne(request, env, ids, destination);
    state = moved.state;
    courtEntrantIds.push(...(moved.event?.courtEntrantIds || []));
    const chosen = new Set(ids);
    for (let i = pool.length - 1; i >= 0; i -= 1) if (chosen.has(pool[i])) pool.splice(i, 1);
    assigned.push({ destination, memberIds: ids });
  }
  return { state, event: { type: 'auto_assigned', assigned, courtEntrantIds: [...new Set(courtEntrantIds.map(String))] } };
}

async function ensurePairTable(env) {
  await env.DB.prepare(`CREATE TABLE IF NOT EXISTS pair_stats (
    member_a TEXT NOT NULL,
    member_b TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (member_a, member_b)
  )`).run();
  await env.DB.prepare(`CREATE TABLE IF NOT EXISTS pair_stat_events (
    revision TEXT PRIMARY KEY,
    recorded_at TEXT NOT NULL
  )`).run();
}

async function clearPairStatistics(env) {
  await ensurePairTable(env);
  await env.DB.batch([
    env.DB.prepare('DELETE FROM pair_stats'),
    env.DB.prepare('DELETE FROM pair_stat_events'),
  ]);
}

async function incrementPair(env, a, b) {
  const ids = [String(a), String(b)].sort();
  if (!ids[0] || !ids[1] || ids[0] === ids[1]) return;
  await env.DB.prepare(`INSERT INTO pair_stats(member_a,member_b,count) VALUES(?,?,1)
    ON CONFLICT(member_a,member_b) DO UPDATE SET count=count+1`).bind(ids[0], ids[1]).run();
}

async function recordPairTransitions(env, after, event) {
  if (!after || !event) return;
  const revision = String(after.revision || '');
  const entered = [...new Set((event.courtEntrantIds || []).map(String).filter(Boolean))];
  if (!revision || !entered.length) return;
  await ensurePairTable(env);
  const pairs = new Set();
  for (const id of entered) {
    const loc = stateLocation(after, id);
    if (!loc || loc.type !== 'court') continue;
    const occupants = (after.courts?.[loc.key] || []).map(String);
    for (const other of occupants) {
      if (!other || other === id) continue;
      pairs.add([id, other].sort().join('::'));
    }
  }
  if (!pairs.size) return;
  const rows = [...pairs].map(key => key.split('::'));
  // One atomic D1 batch: a committed state revision can contribute its pairs
  // only once. Concurrent admin/member requests may obtain stale outer
  // snapshots, but the entrant list comes from the exact serialized DO event.
  await env.DB.batch([
    env.DB.prepare(`INSERT INTO pair_stats(member_a,member_b,count)
      SELECT json_extract(value,'$[0]'),json_extract(value,'$[1]'),1
      FROM json_each(?)
      WHERE NOT EXISTS (SELECT 1 FROM pair_stat_events WHERE revision=?)
      ON CONFLICT(member_a,member_b) DO UPDATE SET count=count+1`).bind(JSON.stringify(rows), revision),
    env.DB.prepare('INSERT OR IGNORE INTO pair_stat_events(revision,recorded_at) VALUES(?,?)')
      .bind(revision, new Date().toISOString()),
  ]);
}

function extractStateFromCompat(packet) {
  if (!packet || !packet.ok) return null;
  const result = packet.result;
  if (result?.state?.members) return result.state;
  if (result?.members && result?.courts) return result;
  return null;
}

async function pairStatistics(request, env) {
  const state = await getAdminState(request, env);
  await ensurePairTable(env);
  const rows = await env.DB.prepare('SELECT member_a,member_b,count FROM pair_stats WHERE count>0 ORDER BY count DESC').all();
  const names = new Map((state.members || []).map(m => [String(m.id), String(m.name || '')]));
  const partners = new Map((state.members || []).map(m => [String(m.id), []]));
  for (const row of rows.results || []) {
    const a = String(row.member_a || ''); const b = String(row.member_b || ''); const count = Math.max(0, Number(row.count) || 0);
    if (!names.has(a) || !names.has(b) || !count) continue;
    partners.get(a).push({ id: b, name: names.get(b), count });
    partners.get(b).push({ id: a, name: names.get(a), count });
  }
  return (state.members || []).map(m => ({
    id: String(m.id), name: String(m.name || ''), games: Math.max(0, Number(m.games) || 0),
    partners: (partners.get(String(m.id)) || []).sort((x, y) => y.count - x.count || x.name.localeCompare(y.name, 'ko')),
  })).sort((a, b) => b.games - a.games || a.name.localeCompare(b.name, 'ko'));
}

async function forwardAndRecord(request, env, before, options = {}) {
  const response = await core.fetch(request, env);
  const clone = response.clone();
  const packet = await clone.json().catch(() => null);
  if (packet?.ok && options.clearPairStats) await clearPairStatistics(env);
  const after = packet?.state?.members ? packet.state : extractStateFromCompat(packet);
  const exactEvent = packet?.event || after?.actionHistory?.[after.actionHistory.length - 1]?.event || null;
  if (after && exactEvent) await recordPairTransitions(env, after, exactEvent);
  return response;
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: JSON_HEADERS });
    const url = new URL(request.url);
    if (request.method === 'POST' && url.pathname === '/api/admin/rpc') {
      const body = await request.clone().json().catch(() => ({}));
      if (body.action === 'autoAssign') {
        try {
          const before = await getAdminState(request, env).catch(() => null);
          const out = await mdAutoAssign(request, env, body.candidateIds, body.destinations);
          if (out?.state) await recordPairTransitions(env, out.state, out.event);
          return reply({ ok: true, state: out.state, event: out.event });
        } catch (error) { return reply({ ok: false, error: String(error?.message || error) }, 400); }
      }
      const before = await getAdminState(request, env).catch(() => null);
      return forwardAndRecord(request, env, before, { clearPairStats: body.action === 'resetAll' });
    }
    if (request.method === 'POST' && url.pathname === '/api/member/rpc') {
      const before = await getVisibleState(request, env).catch(() => null);
      return forwardAndRecord(request, env, before);
    }
    if (request.method === 'POST' && url.pathname === '/api/compat/rpc') {
      const body = await request.clone().json().catch(() => ({}));
      if (body.name === 'getPairStatistics') {
        try { return reply({ ok: true, result: await pairStatistics(request, env) }); }
        catch (error) { return reply({ ok: false, error: String(error?.message || error) }); }
      }
      if (body.name === 'smartAssignSelected') {
        try {
          const args = Array.isArray(body.args) ? body.args : [];
          const before = await getVisibleState(request, env).catch(() => null);
          const out = await mdAutoAssign(request, env, args[1], [{ type: 'court', key: String(args[2]) }]);
          if (out?.state) await recordPairTransitions(env, out.state, out.event);
          return reply({ ok: true, result: out.state });
        } catch (error) { return reply({ ok: false, error: String(error?.message || error) }); }
      }
      if (MUTATING_COMPAT.has(String(body.name || ''))) {
        const before = await getVisibleState(request, env).catch(() => null);
        const isRestore = body.name === 'restoreManualBackup';
        return forwardAndRecord(request, env, isRestore ? null : before, { clearPairStats: body.name === 'resetAllOperationData' || isRestore });
      }
    }
    return core.fetch(request, env);
  },
};