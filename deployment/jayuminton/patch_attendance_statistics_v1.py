#!/usr/bin/env python3
"""Patch the Cloudflare state worker with administrator attendance timestamps.

V2 contract:
- 콕제출체크의 완료(kokInactive false -> true) records arrivedAt.
- before -> active does NOT record arrival anymore.
- active assignment-pool -> away records departedAt.
- pair statistics returns games/partners plus arrivedAt/departedAt.

The timestamps live on each member inside the canonical D1 state JSON, so they
participate in the same Durable Object serialization, backup, undo and reset
behavior as the rest of the member state.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('cloudflare/state-worker')
worker_path = root / 'worker.js'
entry_path = root / 'worker-md-entry.js'

worker = worker_path.read_text(encoding='utf-8')
marker = 'JAYUMINTON_ATTENDANCE_TIMES_V2'

old_status = """export function setMemberStatusMutation(input, memberIds, status) {
  const state = normalizeState(input); const ids = uniqueIds(memberIds, 200);
  if (!['active', 'before', 'rest', 'away'].includes(String(status))) throw new Error('invalid_member_status');
  removeEverywhere(state, ids); const wanted = new Set(ids);
  state.members = state.members.map(m => wanted.has(String(m.id)) ? { ...m, status: String(status) } : m);
  return { state, event: { type: 'member_status_changed', memberIds: ids, status: String(status) } };
}
"""
new_status = """export function setMemberStatusMutation(input, memberIds, status, now = new Date().toISOString()) {
  /* JAYUMINTON_ATTENDANCE_TIMES_V2
     Arrival is NOT tied to before -> active. It is recorded only when the administrator
     completes 콕 제출. Departure remains active assignment-pool -> away. */
  const state = normalizeState(input); const ids = uniqueIds(memberIds, 200);
  const nextStatus = String(status);
  if (!['active', 'before', 'rest', 'away'].includes(nextStatus)) throw new Error('invalid_member_status');
  const timestamp = String(now || new Date().toISOString());
  const previous = new Map(ids.map(id => {
    const member = state.members.find(m => String(m.id) === String(id));
    return [String(id), {
      status: String(member?.status || 'active'),
      location: locationOf(state, id),
    }];
  }));
  removeEverywhere(state, ids); const wanted = new Set(ids);
  const departedMemberIds = [];
  state.members = state.members.map(m => {
    const id = String(m.id);
    if (!wanted.has(id)) return m;
    const before = previous.get(id) || { status: String(m.status || 'active'), location: null };
    const next = { ...m, status: nextStatus };
    if (nextStatus === 'away' && before.status === 'active' && before.location?.type === 'active') {
      next.departedAt = timestamp;
      departedMemberIds.push(id);
    }
    return next;
  });
  return { state, event: {
    type: 'member_status_changed', memberIds: ids, status: nextStatus,
    arrivedMemberIds: [], departedMemberIds,
  } };
}
"""

old_kok = """export function setMemberKokInactiveMutation(input, memberIds, inactive) {
  const state = normalizeState(input); const ids = uniqueIds(memberIds, 200); const wanted = new Set(ids);
  if (!ids.length) throw new Error('members_required');
  const flag = Boolean(inactive);
  state.members = state.members.map(m => wanted.has(String(m.id)) ? { ...m, kokInactive: flag } : m);
  return { state, event: { type: 'kok_inactive_changed', memberIds: ids, inactive: flag } };
}
"""
new_kok = """export function setMemberKokInactiveMutation(input, memberIds, inactive, now = new Date().toISOString()) {
  /* JAYUMINTON_KOK_ARRIVAL_TIME_V2
     The administrator's 콕제출체크 완료 button is the attendance clock-in action.
     Only false -> true records arrival. Repeated true calls are idempotent. A deliberate
     복귀 -> 완료 records the new completion time and starts a fresh attendance session. */
  const state = normalizeState(input); const ids = uniqueIds(memberIds, 200); const wanted = new Set(ids);
  if (!ids.length) throw new Error('members_required');
  const flag = Boolean(inactive);
  const timestamp = String(now || new Date().toISOString());
  const previous = new Map(state.members.map(m => [String(m.id), Boolean(m.kokInactive)]));
  const arrivedMemberIds = [];
  state.members = state.members.map(m => {
    const id = String(m.id);
    if (!wanted.has(id)) return m;
    const next = { ...m, kokInactive: flag };
    if (flag && !previous.get(id)) {
      next.arrivedAt = timestamp;
      next.departedAt = '';
      arrivedMemberIds.push(id);
    }
    return next;
  });
  return { state, event: {
    type: 'kok_inactive_changed', memberIds: ids, inactive: flag, arrivedMemberIds,
  } };
}
"""

if marker not in worker:
    if worker.count(old_status) != 1:
        raise SystemExit('setMemberStatusMutation attendance anchor mismatch')
    if worker.count(old_kok) != 1:
        raise SystemExit('setMemberKokInactiveMutation attendance anchor mismatch')
    worker = worker.replace(old_status, new_status, 1)
    worker = worker.replace(old_kok, new_kok, 1)
worker_path.write_text(worker, encoding='utf-8')

entry = entry_path.read_text(encoding='utf-8')
entry_marker = 'JAYUMINTON_ATTENDANCE_STATS_RESPONSE_V2'
old_entry = """  return (state.members || []).map(m => ({
    id: String(m.id), name: String(m.name || ''), games: Math.max(0, Number(m.games) || 0),
    partners: (partners.get(String(m.id)) || []).sort((x, y) => y.count - x.count || x.name.localeCompare(y.name, 'ko')),
  })).sort((a, b) => b.games - a.games || a.name.localeCompare(b.name, 'ko'));
"""
new_entry = """  return (state.members || []).map(m => ({
    /* JAYUMINTON_ATTENDANCE_STATS_RESPONSE_V2 */
    id: String(m.id), name: String(m.name || ''), games: Math.max(0, Number(m.games) || 0),
    arrivedAt: String(m.arrivedAt || ''), departedAt: String(m.departedAt || ''),
    partners: (partners.get(String(m.id)) || []).sort((x, y) => y.count - x.count || x.name.localeCompare(y.name, 'ko')),
  })).sort((a, b) => b.games - a.games || a.name.localeCompare(b.name, 'ko'));
"""
if entry_marker not in entry:
    if entry.count(old_entry) != 1:
        raise SystemExit('pairStatistics attendance response anchor mismatch')
    entry = entry.replace(old_entry, new_entry, 1)
entry_path.write_text(entry, encoding='utf-8')

print('ATTENDANCE_STATISTICS_V2_KOK_ARRIVAL_PATCHED')
