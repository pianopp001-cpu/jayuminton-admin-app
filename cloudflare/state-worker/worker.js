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
    settings: { memberPassword: '', memberPasswordVersion: 1, adminPin: '', adminPinVersion: 1, courtOrientation: 'door-right' },
    swapRequests: [], memberMessages: [], tempPairs: [], actionHistory: [], updatedAt: new Date(0).toISOString(),
  };
}

function uniqueIds(value, limit = 4) { return [...new Set((Array.isArray(value) ? value : []).map(String).filter(Boolean))].slice(0, limit); }

export function normalizeTempPairs(value) {
  const used = new Set();
  const out = [];
  for (const raw of (Array.isArray(value) ? value : []).slice(-100)) {
    if (!raw || !['wait', 'court'].includes(String(raw.zone))) continue;
    const legacyIds = [...uniqueIds(raw.pairA, 2), ...uniqueIds(raw.pairB, 2)];
    const members = uniqueIds(Array.isArray(raw.members) && raw.members.length ? raw.members : legacyIds, 4);
    if (members.length < 2 || members.length > 4) continue;
    if (members.some(id => used.has(id))) continue;
    members.forEach(id => used.add(id));
    out.push({
      members,
      pairA: members.slice(0, 2),
      pairB: members.slice(2, 4),
      zone: String(raw.zone),
      createdAt: Math.max(0, Number(raw.createdAt) || Date.now()),
    });
  }
  return out;
}

export function reconcileTempPairs(state) {
  state.tempPairs = normalizeTempPairs(state.tempPairs).filter(group => {
    const ids = uniqueIds(group.members?.length ? group.members : [...(group.pairA || []), ...(group.pairB || [])], 4);
    if (ids.length < 2) return false;
    const first = locationOf(state, ids[0]);
    if (!first || first.type !== group.zone || !['wait', 'court'].includes(first.type)) return false;
    return ids.every(id => {
      const loc = locationOf(state, id);
      return loc && loc.type === first.type && loc.key === first.key;
    });
  }).map(group => {
    const members = uniqueIds(group.members?.length ? group.members : [...(group.pairA || []), ...(group.pairB || [])], 4);
    return { ...group, members, pairA: members.slice(0, 2), pairB: members.slice(2, 4) };
  });
  return state;
}

export function normalizeState(input) {
  const base = emptyState();
  const state = input && typeof input === 'object' ? structuredClone(input) : {};
  state.schemaVersion = 2;
  state.members = Array.isArray(state.members) ? state.members : [];
  state.courts = state.courts && typeof state.courts === 'object' ? state.courts : base.courts;
  state.waitGroups = Array.isArray(state.waitGroups) ? state.waitGroups.slice(0, 5) : [];
  while (state.waitGroups.length < 5) state.waitGroups.push([]);
  // Physical slots may only contain IDs that still exist in members.
  // This removes stale/ghost IDs that made a visible empty wait slot return location_full.
  const validMemberIds = new Set(state.members.map(member => String(member?.id || '')).filter(Boolean));
  const occupied = new Set();
  for (const no of ['1', '2', '3', '4']) {
    state.courts[no] = uniqueIds(state.courts[no]).filter(id => validMemberIds.has(id) && !occupied.has(id));
    state.courts[no].forEach(id => occupied.add(id));
  }
  state.waitGroups = state.waitGroups.map(group => uniqueIds(group).filter(id => {
    if (!validMemberIds.has(id) || occupied.has(id)) return false;
    occupied.add(id); return true;
  }));
  state.courtStartedAt = Object.assign(base.courtStartedAt, state.courtStartedAt || {});
  state.settings = Object.assign(base.settings, state.settings || {});
  state.swapRequests = Array.isArray(state.swapRequests) ? state.swapRequests.slice(-100) : [];
  state.memberMessages = Array.isArray(state.memberMessages) ? state.memberMessages.slice(-50) : [];
  state.tempPairs = normalizeTempPairs(state.tempPairs);
  state.actionHistory = Array.isArray(state.actionHistory) ? state.actionHistory.slice(-50) : [];
  state.revision = Math.max(0, Number(state.revision) || 0);
  state.updatedAt = String(state.updatedAt || new Date().toISOString());
  syncMemberStatuses(state);
  return reconcileTempPairs(state);
}

function locationOf(state, memberId) {
  const id = String(memberId);
  for (const no of ['1', '2', '3', '4']) if (state.courts[no].includes(id)) return { type: 'court', key: no };
  for (let i = 0; i < 5; i += 1) if (state.waitGroups[i].includes(id)) return { type: 'wait', key: String(i + 1) };
  const member = state.members.find(m => String(m.id) === id);
  if (member && String(member.status) === 'active') return { type: 'active', key: 'active' };
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
    else if (!['before', 'rest', 'away'].includes(String(member.status))) next.status = 'active';
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
  reconcileTempPairs(state);
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
  reconcileTempPairs(state);
  return { state, event: { type: 'members_moved', memberIds: ids, destination } };
}

export function swapMutation(input, leftIds, rightIds) {
  const state = normalizeState(input);
  const a = uniqueIds(leftIds); const b = uniqueIds(rightIds);
  if (!a.length || a.length !== b.length) throw new Error('equal_swap_groups_required');
  const aLoc = locationOf(state, a[0]); const bLoc = locationOf(state, b[0]);
  if (!aLoc || !bLoc || a.some(id => JSON.stringify(locationOf(state, id)) !== JSON.stringify(aLoc)) || b.some(id => JSON.stringify(locationOf(state, id)) !== JSON.stringify(bLoc))) throw new Error('invalid_swap_groups');
  if (JSON.stringify(aLoc) === JSON.stringify(bLoc)) throw new Error('same_location');
  const enteringCourt = [];
  if (aLoc.type === 'active' || bLoc.type === 'active') {
    if (aLoc.type === 'active' && bLoc.type === 'active') throw new Error('same_location');
    const activeIds = aLoc.type === 'active' ? a : b;
    const placedIds = aLoc.type === 'active' ? b : a;
    const placedLoc = aLoc.type === 'active' ? bLoc : aLoc;
    const placedTarget = container(state, placedLoc);
    placedIds.forEach((id, i) => { placedTarget[placedTarget.indexOf(id)] = activeIds[i]; });
    if (placedLoc.type === 'court') enteringCourt.push(...activeIds);
  } else {
    const aTarget = container(state, aLoc); const bTarget = container(state, bLoc);
    a.forEach((id, i) => { aTarget[aTarget.indexOf(id)] = b[i]; });
    b.forEach((id, i) => { bTarget[bTarget.indexOf(id)] = a[i]; });
    if (aLoc.type === 'court' && bLoc.type !== 'court') enteringCourt.push(...b);
    if (bLoc.type === 'court' && aLoc.type !== 'court') enteringCourt.push(...a);
  }
  addGames(state, enteringCourt, 1);
  syncMemberStatuses(state);
  reconcileTempPairs(state);
  return { state, event: { type: 'members_swapped', leftIds: a, rightIds: b } };
}

export function swapLocationsMutation(input, left, right) {
  const state = normalizeState(input);
  const a = { type: String(left?.type || ''), key: String(left?.key || '') };
  const b = { type: String(right?.type || ''), key: String(right?.key || '') };
  if (a.type !== b.type || !['court', 'wait'].includes(a.type) || a.key === b.key) throw new Error('invalid_location_swap');
  if (a.type === 'court') {
    if (!['1', '2', '3', '4'].includes(a.key) || !['1', '2', '3', '4'].includes(b.key)) throw new Error('invalid_court');
    [state.courts[a.key], state.courts[b.key]] = [state.courts[b.key], state.courts[a.key]];
    [state.courtStartedAt[a.key], state.courtStartedAt[b.key]] = [state.courtStartedAt[b.key], state.courtStartedAt[a.key]];
  } else {
    const ai = Number(a.key) - 1, bi = Number(b.key) - 1;
    if (ai < 0 || ai > 4 || bi < 0 || bi > 4) throw new Error('invalid_wait_group');
    [state.waitGroups[ai], state.waitGroups[bi]] = [state.waitGroups[bi], state.waitGroups[ai]];
  }
  reconcileTempPairs(state);
  return { state, event: { type: 'locations_swapped', left: a, right: b } };
}

export function autoAssignMutation(input, candidateIds, destinations) {
  let state = normalizeState(input);
  const memberById = new Map(state.members.map(m => [String(m.id), m]));
  const available = uniqueIds(candidateIds, 200).filter(id => {
    const location = locationOf(state, id);
    return memberById.has(id) && (!location || location.type === 'active');
  });
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
  const index = state.members.findIndex(m => String(m.id) === id);
  const previous = index >= 0 ? state.members[index] : null;
  const clean = { id, name, gender: ['여', 'female'].includes(String(member.gender)) ? 'female' : 'male', grade: String(member.grade || ''), experience: String(member.experience || member.career || ''), career: String(member.career || member.experience || ''), publicMemo: String(member.publicMemo || member.memo || ''), isNew: Boolean(member.isNew), isDuplicate: Boolean(member.isDuplicate), isSponsor: Boolean(member.isSponsor), bundleId: member.bundleId === undefined ? String(previous?.bundleId || '') : String(member.bundleId || ''), teamLabel: member.teamLabel === undefined ? String(previous?.teamLabel || '') : String(member.teamLabel || ''), games: member.games === undefined ? Math.max(0, Number(previous?.games) || 0) : Math.max(0, Number(member.games) || 0), status: String(member.status || previous?.status || 'active'), createdAt: String(member.createdAt || previous?.createdAt || new Date().toISOString()) };
  if (index >= 0) state.members[index] = { ...state.members[index], ...clean }; else state.members.push(clean);
  return { state, event: { type: index >= 0 ? 'member_updated' : 'member_created', memberId: id } };
}

export function setBundleMutation(input, memberIds) {
  const state = normalizeState(input); const ids = uniqueIds(memberIds, 200);
  if (ids.length < 2) throw new Error('team_requires_two_members');
  if (ids.some(id => locationOf(state, id)?.type !== 'active')) throw new Error('team_requires_assignment_wait');
  const existing = new Set(state.members.map(m => String(m.teamLabel || '')).filter(Boolean));
  let number = 1; while (existing.has(`팀 ${number}`)) number += 1;
  const bundleId = `team-${crypto.randomUUID()}`; const teamLabel = `팀 ${number}`;
  const wanted = new Set(ids);
  state.members = state.members.map(m => wanted.has(String(m.id)) ? { ...m, bundleId, teamLabel } : m);
  return { state, event: { type: 'team_set', memberIds: ids, bundleId, teamLabel } };
}

export function clearBundleMutation(input, memberIds) {
  const state = normalizeState(input); const ids = uniqueIds(memberIds, 200);
  if (!ids.length) throw new Error('members_required');
  const selectedTeams = new Set();
  state.members.forEach(m => { if (ids.includes(String(m.id)) && m.bundleId) selectedTeams.add(String(m.bundleId)); });
  state.members = state.members.map(m => selectedTeams.has(String(m.bundleId || '')) ? { ...m, bundleId: '', teamLabel: '' } : m);
  return { state, event: { type: 'team_cleared', memberIds: ids } };
}

export function setTempPairsMutation(input, tempPairs) {
  const state = normalizeState(input);
  state.tempPairs = normalizeTempPairs(tempPairs);
  reconcileTempPairs(state);
  return { state, event: { type: 'temp_pairs_set', tempPairs: state.tempPairs } };
}

export function sendMemberMessageMutation(input, memberIds, message) {
  const state = normalizeState(input); const ids = uniqueIds(memberIds, 200);
  const text = String(message || '').trim().slice(0, 300);
  if (!ids.length) throw new Error('members_required');
  if (!text) throw new Error('message_required');
  const known = new Set(state.members.map(m => String(m.id)));
  const recipients = ids.filter(id => known.has(id));
  if (!recipients.length) throw new Error('members_not_found');
  const item = { id: `msg-${crypto.randomUUID()}`, memberIds: recipients, text, createdAt: new Date().toISOString() };
  state.memberMessages = [...state.memberMessages, item].slice(-50);
  return { state, event: { type: 'member_message_sent', messageId: item.id, memberIds: recipients, text } };
}

export function deleteMemberReplyMutation(input, messageId, replyId) {
  const state = normalizeState(input);
  const mid = String(messageId || ''); const rid = String(replyId || '');
  if (!mid || !rid) throw new Error('reply_required');
  const message = state.memberMessages.find(m => m && String(m.id) === mid);
  if (!message) throw new Error('message_not_found');
  const before = Array.isArray(message.replies) ? message.replies.length : 0;
  message.replies = (Array.isArray(message.replies) ? message.replies : []).filter(r => r && String(r.id) !== rid);
  if (message.replies.length === before) throw new Error('reply_not_found');
  return { state, event: { type: 'member_reply_deleted', messageId: mid, replyId: rid } };
}

export function setMemberStatusMutation(input, memberIds, status) {
  const state = normalizeState(input); const ids = uniqueIds(memberIds, 200);
  if (!['active', 'before', 'rest', 'away'].includes(String(status))) throw new Error('invalid_member_status');
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

export function cancelSwapMutation(input, requesterId) {
  const state = normalizeState(input); const request = [...state.swapRequests].reverse().find(r => r.status === 'pending' && r.requesterId === String(requesterId));
  if (!request) throw new Error('swap_request_not_found');
  request.status = 'cancelled'; request.respondedAt = Date.now();
  return { state, event: { type: 'swap_cancelled', requestId: request.id } };
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
  // Member access remains valid until the administrator changes the member
  // password.  The password version is the revocation boundary; never retain
  // or re-send the raw password on the client.
  const payload = stringToBase64Url(JSON.stringify({ memberId: String(memberId || ''), passwordVersion: Number(state.settings.memberPasswordVersion || 1), issuedAt: Date.now() }));
  return `${payload}.${await hmac(payload, String(env.INTERNAL_KEY || ''))}`;
}
async function issueAdminSession(env, state) {
  // Reuse the verified session across app restarts without storing the raw PIN.
  // PIN changes invalidate it immediately; normal sessions expire after 30 days.
  const payload = stringToBase64Url(JSON.stringify({ scope: 'admin', adminPinVersion: Number(state.settings.adminPinVersion || 1), expiresAt: Date.now() + 30 * 86400000 }));
  return `${payload}.${await hmac(payload, String(env.INTERNAL_KEY || ''))}`;
}
async function verifyMemberSession(request, env, state) {
  const auth = String(request.headers.get('authorization') || ''); const token = auth.toLowerCase().startsWith('bearer ') ? auth.slice(7) : '';
  const [payload, signature] = token.split('.');
  if (!payload || !signature || signature !== await hmac(payload, String(env.INTERNAL_KEY || ''))) throw new Error('unauthorized');
  const session = JSON.parse(base64UrlToString(payload));
  if (Number(session.passwordVersion) !== Number(state.settings.memberPasswordVersion || 1)) throw new Error('session_expired');
  if (session.memberId && !state.members.some(m => String(m.id) === String(session.memberId))) throw new Error('member_not_found');
  return session;
}
async function verifyAdminSession(request, env, state) {
  const auth = String(request.headers.get('authorization') || ''); const token = auth.toLowerCase().startsWith('bearer ') ? auth.slice(7) : '';
  const [payload, signature] = token.split('.');
  if (!payload || !signature || signature !== await hmac(payload, String(env.INTERNAL_KEY || ''))) throw new Error('unauthorized');
  const session = JSON.parse(base64UrlToString(payload));
  if (session.scope !== 'admin' || Number(session.expiresAt) <= Date.now() || Number(session.adminPinVersion) !== Number(state.settings.adminPinVersion || 1)) throw new Error('session_expired');
  return session;
}

export function publicState(state, memberId = '') {
  const safe = normalizeState(state); const me = String(memberId || '');
  safe.settings = { memberPasswordVersion: Number(safe.settings.memberPasswordVersion || 1), courtOrientation: safe.settings.courtOrientation };
  safe.swapRequests = safe.swapRequests.filter(r => r.status === 'pending' && (r.requesterId === me || r.targetId === me));
  safe.memberMessages = safe.memberMessages.filter(item => Array.isArray(item.memberIds) && item.memberIds.map(String).includes(me)).slice(-10);
  delete safe.actionHistory; return safe;
}

export function adminState(state) {
  const safe = normalizeState(state); delete safe.settings.adminPin; delete safe.actionHistory; return safe;
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
  if (event.messageText) body.messageText = String(event.messageText).slice(0, 300);
  try {
    const response = await fetch(env.PUSH_URL, { method: 'POST', headers: { 'content-type': 'application/json', 'x-jayuminton-key': env.INTERNAL_KEY }, body: JSON.stringify(body) });
    return await response.json();
  } catch (error) { return { ok: false, error: String(error?.message || error) }; }
}

export function assignmentTransitions(beforeInput, afterInput) {
  const before = normalizeState(beforeInput); const after = normalizeState(afterInput);
  const courtGroups = { '1': [], '2': [], '3': [], '4': [] }; const wait1 = [];
  for (const member of after.members) {
    const id = String(member.id); const oldLocation = locationOf(before, id); const newLocation = locationOf(after, id);
    if (!newLocation) continue;
    if (newLocation.type === 'court' && (!oldLocation || oldLocation.type !== 'court' || oldLocation.key !== newLocation.key)) courtGroups[newLocation.key].push({ id, name: String(member.name || '') });
    if (newLocation.type === 'wait' && newLocation.key === '1' && (!oldLocation || oldLocation.type !== 'wait' || oldLocation.key !== '1')) wait1.push({ id, name: String(member.name || '') });
  }
  return { courtGroups, wait1 };
}

async function publishAssignmentTransitions(env, before, after, event) {
  const transitions = assignmentTransitions(before, after); const results = [];
  for (const no of ['1', '2', '3', '4']) if (transitions.courtGroups[no].length) results.push(await sendPush(env, 'court_assignment', { ...event, courtNo: Number(no) }, transitions.courtGroups[no]));
  if (transitions.wait1.length) results.push(await sendPush(env, 'wait1_ready', event, transitions.wait1));
  if (event.type === 'member_message_sent' && Array.isArray(event.memberIds) && event.memberIds.length) {
    const wanted = new Set(event.memberIds.map(String));
    const recipients = after.members.filter(m => wanted.has(String(m.id))).map(m => ({ id: String(m.id), name: String(m.name || '') }));
    if (recipients.length) results.push(await sendPush(env, 'admin_message', { ...event, messageText: event.text }, recipients));
  }
  return results;
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
        const backupState = normalizeState(structuredClone(current));
        backupState.courts = { '1': [], '2': [], '3': [], '4': [] };
        backupState.courtStartedAt = { '1': '', '2': '', '3': '', '4': '' };
        backupState.waitGroups = [[], [], [], [], []];
        backupState.swapRequests = [];
        backupState.actionHistory = [];
        backupState.members = backupState.members.map(member => ({ ...member, status: 'active' }));
        await this.env.DB.prepare('DELETE FROM state_backups').run();
        await this.env.DB.prepare('INSERT INTO state_backups(revision,state_json,created_at) VALUES(?,?,?)').bind(current.revision, JSON.stringify(backupState), new Date().toISOString()).run();
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
      else if (action === 'swapLocations') result = swapLocationsMutation(current, body.left, body.right);
      else if (action === 'autoAssign') result = autoAssignMutation(current, body.candidateIds, body.destinations);
      else if (action === 'upsertMember') result = upsertMemberMutation(current, body.member);
      else if (action === 'setMemberStatus') result = setMemberStatusMutation(current, body.memberIds, body.status);
      else if (action === 'setBundle') result = setBundleMutation(current, body.memberIds);
      else if (action === 'clearBundle') result = clearBundleMutation(current, body.memberIds);
      else if (action === 'setTempPairs') result = setTempPairsMutation(current, body.tempPairs);
      else if (action === 'sendMemberMessage') result = sendMemberMessageMutation(current, body.memberIds, body.message);
      else if (action === 'deleteMemberReply') result = deleteMemberReplyMutation(current, body.messageId, body.replyId);
      else if (action === 'adjustGames') result = adjustGamesMutation(current, body.memberIds, body.delta, body.reset);
      else if (action === 'requestSwap') result = requestSwapMutation(current, body.requesterId, body.targetId);
      else if (action === 'respondSwap') result = respondSwapMutation(current, body.requestId, body.responderId, body.accept);
      else if (action === 'cancelSwap') result = cancelSwapMutation(current, body.requesterId);
      else if (action === 'setSettings') {
        result = { state: normalizeState(current), event: { type: 'settings_updated' } };
        if (body.memberPassword !== undefined) { result.state.settings.memberPassword = String(body.memberPassword); result.state.settings.memberPasswordVersion = Number(result.state.settings.memberPasswordVersion || 0) + 1; }
        if (body.adminPin !== undefined) { result.state.settings.adminPin = String(body.adminPin); result.state.settings.adminPinVersion = Number(result.state.settings.adminPinVersion || 0) + 1; }
        if (['door-left', 'door-right'].includes(body.courtOrientation)) result.state.settings.courtOrientation = body.courtOrientation;
      }
      else if (action === 'deleteMembers') {
        result = setMemberStatusMutation(current, body.memberIds, 'away'); const ids = new Set(uniqueIds(body.memberIds, 200));
        result.state.members = result.state.members.filter(m => !ids.has(String(m.id))); result.event.type = 'members_deleted';
      }
      else if (action === 'resetAll') {
        result = { state: emptyState(), event: { type: 'all_reset' } };
        result.state.settings = { ...current.settings };
      }
      else return reply({ ok: false, error: 'unsupported_action' }, 400);
      recordAction(result.state, operationId, action, result.event, current);
      const saved = await writeState(this.env.DB, result.state);
      const notifications = await publishAssignmentTransitions(this.env, current, saved, result.event);
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

function bearerRequest(request, token) {
  const headers = new Headers(request.headers); headers.set('authorization', `Bearer ${String(token || '')}`);
  return new Request(request.url, { method: request.method, headers });
}

async function coordinatorPacket(request, env, action, body) {
  const response = await coordinatorAsInternal(request, env, action, body); const packet = await response.json();
  if (!packet.ok) throw new Error(packet.error || 'operation_failed');
  return packet;
}

function latestSwap(state, predicate) {
  return [...state.swapRequests].reverse().find(r => r.status === 'pending' && Number(r.expiresAt) > Date.now() && predicate(r)) || null;
}

export async function legacyRpc(request, env, name, args) {
  const state = await readState(env.DB); const values = Array.isArray(args) ? args : [];
  const headerToken = String(request.headers.get('authorization') || '').replace(/^Bearer\s+/i, '');
  // v6 브리지는 기존 인수 배열을 그대로 보존하고 세션은 Authorization 헤더로 보낸다.
  // 구형 호출과의 호환을 위해 헤더가 없을 때만 첫 번째 인수를 토큰으로 사용한다.
  const token = String(headerToken || values[0] || '');
  if (name === 'createAdminSession') {
    if (!state.settings.adminPin || String(values[0] || '') !== String(state.settings.adminPin)) return { ok: false };
    return { ok: true, token: await issueAdminSession(env, state) };
  }
  if (name === 'verifyMemberPassword') {
    if (!state.settings.memberPassword || String(values[0] || '') !== String(state.settings.memberPassword)) return { ok: false };
    return { ok: true, version: String(state.settings.memberPasswordVersion || 1), sessionToken: await issueMemberSession(env, state, '') };
  }
  if (name === 'getMemberPasswordVersion') return String(state.settings.memberPasswordVersion || 1);
  if (name === 'resumeAdminSession') { await verifyAdminSession(bearerRequest(request, token), env, state); return true; }
  if (name === 'resumeMemberSession') {
    const session = await verifyMemberSession(bearerRequest(request, token), env, state);
    return { ok: true, version: String(state.settings.memberPasswordVersion || 1), memberId: String(session.memberId || ''), sessionToken: token };
  }
  if (name === 'bindMemberIdentity') {
    await verifyMemberSession(bearerRequest(request, token), env, state);
    const memberId = String(values[1] || '');
    if (!memberId || !state.members.some(member => String(member.id) === memberId)) throw new Error('member_not_found');
    return {
      ok: true,
      version: String(state.settings.memberPasswordVersion || 1),
      memberId,
      sessionToken: await issueMemberSession(env, state, memberId),
    };
  }
  if (name === 'getPublicState') {
    try { await verifyAdminSession(bearerRequest(request, token), env, state); return adminState(state); }
    catch (_) { const session = await verifyMemberSession(bearerRequest(request, token), env, state); return publicState(state, session.memberId); }
  }

  const adminNames = new Set(['getCurrentMemberPassword','getSystemStatus','addMember','updateMemberProfile','setMemberStatus','setBundle','clearBundle','setTempPairs','sendMemberMessage','deleteMemberReply','deleteMembers','assignMembersToCourt','assignMembersToWaitGroup','smartAssignSelected','finishCourt','swapMembers','swapCourts','swapWaitGroups','moveOrSwapMember','undoLastAction','adjustMemberGames','decreaseSelectedGameCounts','resetSelectedGameCounts','resetAllOperationData','createManualBackup','restoreManualBackup','changeMemberPassword']);
  if (adminNames.has(name)) {
    await verifyAdminSession(bearerRequest(request, token), env, state);
    if (name === 'getCurrentMemberPassword') return String(state.settings.memberPassword || '');
    if (name === 'getSystemStatus') return { updatedAt: state.updatedAt, revision: state.revision };
    let action; let body = { operationId: `${name}-${Date.now()}-${crypto.randomUUID()}` };
    if (name === 'addMember') { action = 'upsertMember'; body.member = { name: values[1], gender: values[2], grade: values[3], experience: values[4], ...(values[5] || {}) }; }
    else if (name === 'updateMemberProfile') { action = 'upsertMember'; body.member = { id: values[1], name: values[2], gender: values[3], grade: values[4], experience: values[5], ...(values[6] || {}) }; }
    else if (name === 'setMemberStatus') { action = 'setMemberStatus'; body.memberIds = values[1]; body.status = values[2]; }
    else if (name === 'setBundle') { action = 'setBundle'; body.memberIds = values[1]; }
    else if (name === 'clearBundle') { action = 'clearBundle'; body.memberIds = values[1]; }
    else if (name === 'setTempPairs') { action = 'setTempPairs'; body.tempPairs = values[1]; }
    else if (name === 'sendMemberMessage') { action = 'sendMemberMessage'; body.memberIds = values[1]; body.message = values[2]; }
    else if (name === 'deleteMemberReply') { action = 'deleteMemberReply'; body.messageId = values[1]; body.replyId = values[2]; }
    else if (name === 'deleteMembers') { action = 'deleteMembers'; body.memberIds = values[1]; }
    else if (name === 'assignMembersToCourt') { action = 'moveMembers'; body.memberIds = values[2]; body.destination = { type: 'court', key: String(values[1]) }; }
    else if (name === 'assignMembersToWaitGroup') { action = 'moveMembers'; body.memberIds = values[2]; body.destination = { type: 'wait', key: String(Number(values[1]) + 1) }; }
    else if (name === 'smartAssignSelected') { action = 'autoAssign'; body.candidateIds = values[1]; body.destinations = [{ type: 'court', key: String(values[2]) }]; }
    else if (name === 'finishCourt') { action = 'finishCourt'; body.courtNo = values[1]; }
    else if (name === 'swapMembers') { action = 'swapMembers'; body.leftIds = values[1]; body.rightIds = values[2]; }
    else if (name === 'swapCourts') { action = 'swapLocations'; body.left = { type: 'court', key: String(values[1]) }; body.right = { type: 'court', key: String(values[2]) }; }
    else if (name === 'swapWaitGroups') { action = 'swapLocations'; body.left = { type: 'wait', key: String(Number(values[1]) + 1) }; body.right = { type: 'wait', key: String(Number(values[2]) + 1) }; }
    else if (name === 'moveOrSwapMember') {
      const targetId = String(values[4] || '');
      if (targetId) { action = 'swapMembers'; body.leftIds = [String(values[1])]; body.rightIds = [targetId]; }
      else {
        action = 'moveMembers'; body.memberIds = [String(values[1])];
        body.destination = String(values[2]) === 'court'
          ? { type: 'court', key: String(values[3]) }
          : String(values[2]) === 'wait'
            ? { type: 'wait', key: String(Number(values[3]) + 1) }
            : { type: 'active', key: '' };
      }
    }
    else if (name === 'undoLastAction') action = 'undoLast';
    else if (name === 'adjustMemberGames') { action = 'adjustGames'; body.memberIds = [values[1]]; body.delta = values[2]; }
    else if (name === 'decreaseSelectedGameCounts') { action = 'adjustGames'; body.memberIds = values[1]; body.delta = -1; }
    else if (name === 'resetSelectedGameCounts') { action = 'adjustGames'; body.memberIds = values[1]; body.reset = true; }
    else if (name === 'resetAllOperationData') action = 'resetAll';
    else if (name === 'createManualBackup') action = 'backup';
    else if (name === 'restoreManualBackup') action = 'restoreBackup';
    else if (name === 'changeMemberPassword') { action = 'setSettings'; body.memberPassword = values[1]; }
    const packet = await coordinatorPacket(request, env, action, body);
    if (name === 'addMember' || name === 'updateMemberProfile') return { member: packet.state.members.find(m => String(m.id) === String(packet.event.memberId)), updatedAt: packet.state.updatedAt };
    if (name === 'createManualBackup') return { ok: true, revision: packet.revision };
    return packet.state || packet;
  }

  const memberNames = new Set(['updateMyProfile','memberMoveSelf','memberReturnSelfToWait','memberMoveToWaitGroup','memberLeaveWaitGroup','memberRequestAnywhereSwap','memberGetAnywhereSwapRequest','memberGetAnywhereOutgoingSwap','memberCancelAnywhereSwap','memberAcceptAnywhereSwap','memberRejectAnywhereSwap']);
  if (memberNames.has(name)) {
    const session = await verifyMemberSession(bearerRequest(request, token), env, state); const memberId = String(session.memberId || '');
    if (!memberId || (values[1] && String(values[1]) !== memberId)) throw new Error('member_identity_required');
    if (name === 'memberGetAnywhereSwapRequest') return latestSwap(state, r => r.targetId === memberId);
    if (name === 'memberGetAnywhereOutgoingSwap') return latestSwap(state, r => r.requesterId === memberId);
    let action; const body = { operationId: `${name}-${Date.now()}-${crypto.randomUUID()}` };
    if (name === 'updateMyProfile') {
      const currentMember = state.members.find(m => String(m.id) === memberId);
      if (!currentMember) throw new Error('member_not_found');
      const nextMemo = String(values[2] || '').trim().slice(0, 120);
      action = 'upsertMember'; body.member = { ...currentMember, id: memberId, publicMemo: nextMemo };
    } else if (name === 'memberMoveSelf') {
      const destination = values[2] || {};
      if (destination.type === 'status') { action = 'setMemberStatus'; body.memberIds = [memberId]; body.status = destination.status; }
      else { action = 'moveMembers'; body.memberIds = [memberId]; body.destination = destination; }
    } else if (name === 'memberReturnSelfToWait' || name === 'memberLeaveWaitGroup') { action = 'setMemberStatus'; body.memberIds = [memberId]; body.status = 'active'; }
    else if (name === 'memberMoveToWaitGroup') { action = 'moveMembers'; body.memberIds = [memberId]; body.destination = { type: 'wait', key: String(Number(values[2]) + 1) }; }
    else if (name === 'memberRequestAnywhereSwap') { action = 'requestSwap'; body.requesterId = memberId; body.targetId = String(values[2]); }
    else if (name === 'memberCancelAnywhereSwap') { action = 'cancelSwap'; body.requesterId = memberId; }
    else {
      const requesterId = String(values[2]); const createdAt = Number(values[3] || 0); const pending = latestSwap(state, r => r.targetId === memberId && r.requesterId === requesterId && (!createdAt || Number(r.createdAt) === createdAt));
      if (!pending) throw new Error('swap_request_not_found');
      action = 'respondSwap'; body.requestId = pending.id; body.responderId = memberId; body.accept = name === 'memberAcceptAnywhereSwap';
    }
    const packet = await coordinatorPacket(request, env, action, body);
    return { ok: true, state: publicState(packet.state, memberId), message: '저장되었습니다.' };
  }
  throw new Error('unsupported_legacy_rpc');
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: jsonHeaders });
    const url = new URL(request.url);
    if (url.pathname === '/health') {
      let database = false; try { await env.DB.prepare('SELECT 1 AS ok').first(); database = true; } catch (_) {}
      return reply({ ok: database, backend: 'cloudflare-only', database: 'd1', concurrency: 'durable-object', gas: false, rpcVersion: 6 });
    }
    if (url.pathname === '/api/internal/state' && request.method === 'GET') {
      try { assertInternal(request, env); } catch (_) { return reply({ ok: false, error: 'unauthorized' }, 401); }
      return reply({ ok: true, state: await readState(env.DB) });
    }
    if (url.pathname === '/api/internal/import' && request.method === 'POST') return coordinator(request, env, 'import', await request.json());
    if (url.pathname === '/api/internal/backup' && request.method === 'POST') return coordinator(request, env, 'backup');
    if (url.pathname === '/api/internal/rpc' && request.method === 'POST') { const body = await request.json(); return coordinator(request, env, String(body.action || ''), body); }
    if (url.pathname === '/api/compat/rpc' && request.method === 'POST') {
      try { const body = await request.json(); return reply({ ok: true, result: await legacyRpc(request, env, String(body.name || ''), body.args) }); }
      catch (error) { return reply({ ok: false, error: String(error?.message || error) }, 200); }
    }
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
    if (url.pathname === '/api/admin/login' && request.method === 'POST') {
      const body = await request.json(); const state = await readState(env.DB);
      if (!state.settings.adminPin || String(body.pin || '') !== String(state.settings.adminPin)) return reply({ ok: false, error: 'invalid_admin_pin' }, 401);
      return reply({ ok: true, token: await issueAdminSession(env, state), state: adminState(state) });
    }
    if (url.pathname === '/api/admin/state' && request.method === 'GET') {
      try { const state = await readState(env.DB); await verifyAdminSession(request, env, state); return reply({ ok: true, state: adminState(state) }); }
      catch (error) { return reply({ ok: false, error: String(error?.message || error) }, 401); }
    }
    if (url.pathname === '/api/admin/rpc' && request.method === 'POST') {
      try {
        const state = await readState(env.DB); await verifyAdminSession(request, env, state); const body = await request.json();
        const allowed = new Set(['finishCourt','moveMembers','swapMembers','autoAssign','upsertMember','setMemberStatus','setBundle','clearBundle','setTempPairs','sendMemberMessage','adjustGames','setSettings','deleteMembers','resetAll','backup','restoreBackup','undoLast','cancelSwap']);
        if (!allowed.has(String(body.action || ''))) return reply({ ok: false, error: 'unsupported_admin_action' }, 400);
        return coordinatorAsInternal(request, env, String(body.action), body);
      } catch (error) { return reply({ ok: false, error: String(error?.message || error) }, 401); }
    }
    return reply({ ok: false, error: 'not_found' }, 404);
  },
};
