import core, { StateCoordinator } from './worker.js';

export { StateCoordinator };

const JSON_HEADERS = { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' };
const reply = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: JSON_HEADERS });
const uniq = (xs) => [...new Set((Array.isArray(xs) ? xs : []).map(String).filter(Boolean))];
const isMale = (m) => {
  const g = String(m?.gender || '').toLowerCase();
  return g === '남' || g === 'male' || g.startsWith('m');
};

function occupiedIds(state) {
  return new Set([
    ...Object.values(state?.courts || {}).flat().map(String),
    ...(state?.waitGroups || []).flat().map(String),
  ]);
}

function targetArray(state, destination) {
  if (destination?.type !== 'court') return [];
  return (state?.courts?.[String(destination.key)] || []).map(String);
}

function selectValidFill(state, pool, destination, membersById) {
  const target = targetArray(state, destination);
  const free = Math.max(0, 4 - target.length);
  if (!free || !pool.length) return [];

  const existingMen = target.filter(id => isMale(membersById.get(id))).length;
  const existingWomen = target.length - existingMen;
  const patterns = [[2,2], [4,0], [0,4]];

  for (const [finalMen, finalWomen] of patterns) {
    const needMen = finalMen - existingMen;
    const needWomen = finalWomen - existingWomen;
    if (needMen < 0 || needWomen < 0 || needMen + needWomen !== free) continue;
    const men = pool.filter(id => isMale(membersById.get(id)));
    const women = pool.filter(id => !isMale(membersById.get(id)));
    if (men.length < needMen || women.length < needWomen) continue;
    return [...men.slice(0, needMen), ...women.slice(0, needWomen)];
  }

  // MD remainder rule: only relax composition when these are the final remaining candidates.
  if (pool.length <= free) return pool.slice(0, free);
  return [];
}

async function callCore(request, path, body, method = 'POST') {
  const url = new URL(request.url);
  url.pathname = path;
  const headers = new Headers(request.headers);
  headers.set('content-type', 'application/json');
  return core.fetch(new Request(url.toString(), {
    method,
    headers,
    body: method === 'GET' ? undefined : JSON.stringify(body || {}),
  }), request.__env);
}

async function getAdminState(request, env) {
  const url = new URL(request.url);
  url.pathname = '/api/admin/state';
  const res = await core.fetch(new Request(url.toString(), { method: 'GET', headers: request.headers }), env);
  const packet = await res.json();
  if (!packet.ok) throw new Error(packet.error || 'admin_state_failed');
  return packet.state;
}

async function moveOne(request, env, memberIds, destination) {
  const url = new URL(request.url);
  url.pathname = '/api/admin/rpc';
  const headers = new Headers(request.headers);
  headers.set('content-type', 'application/json');
  const res = await core.fetch(new Request(url.toString(), {
    method: 'POST', headers,
    body: JSON.stringify({
      action: 'moveMembers',
      operationId: `md-auto-${Date.now()}-${crypto.randomUUID()}`,
      memberIds,
      destination,
    }),
  }), env);
  const packet = await res.json();
  if (!packet.ok) throw new Error(packet.error || 'autoassign_move_failed');
  return packet.state;
}

async function mdAutoAssign(request, env, candidateIds, destinations) {
  let state = await getAdminState(request, env);
  const membersById = new Map((state.members || []).map(m => [String(m.id), m]));
  const occupied = occupiedIds(state);
  const pool = uniq(candidateIds).filter(id => membersById.has(id) && !occupied.has(id));
  const assigned = [];

  for (const destination of Array.isArray(destinations) ? destinations : []) {
    const ids = selectValidFill(state, pool, destination, membersById);
    if (!ids.length) continue;
    state = await moveOne(request, env, ids, destination);
    const chosen = new Set(ids);
    for (let i = pool.length - 1; i >= 0; i -= 1) if (chosen.has(pool[i])) pool.splice(i, 1);
    assigned.push({ destination, memberIds: ids });
  }
  return { state, event: { type: 'auto_assigned', assigned } };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === 'POST' && url.pathname === '/api/admin/rpc') {
      const body = await request.clone().json().catch(() => ({}));
      if (body.action === 'autoAssign') {
        try {
          const out = await mdAutoAssign(request, env, body.candidateIds, body.destinations);
          return reply({ ok: true, state: out.state, event: out.event });
        } catch (error) {
          return reply({ ok: false, error: String(error?.message || error) }, 400);
        }
      }
    }
    if (request.method === 'POST' && url.pathname === '/api/compat/rpc') {
      const body = await request.clone().json().catch(() => ({}));
      if (body.name === 'smartAssignSelected') {
        try {
          const args = Array.isArray(body.args) ? body.args : [];
          const out = await mdAutoAssign(request, env, args[1], [{ type: 'court', key: String(args[2]) }]);
          return reply({ ok: true, result: out.state });
        } catch (error) {
          return reply({ ok: false, error: String(error?.message || error) });
        }
      }
    }
    return core.fetch(request, env);
  },
};
