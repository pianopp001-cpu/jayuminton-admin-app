#!/usr/bin/env python3
"""Patch the Cloudflare state worker with administrator attendance timestamps.

Contract:
- before -> active records arrivedAt
- active assignment-pool -> away records departedAt
- pair statistics returns games/partners plus arrivedAt/departedAt

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
marker = 'JAYUMINTON_ATTENDANCE_TIMES_V1'
old = """export function setMemberStatusMutation(input, memberIds, status) {
  const state = normalizeState(input); const ids = uniqueIds(memberIds, 200);
  if (!['active', 'before', 'rest', 'away'].includes(String(status))) throw new Error('invalid_member_status');
  removeEverywhere(state, ids); const wanted = new Set(ids);
  state.members = state.members.map(m => wanted.has(String(m.id)) ? { ...m, status: String(status) } : m);
  return { state, event: { type: 'member_status_changed', memberIds: ids, status: String(status) } };
}
"""
new = """export function setMemberStatusMutation(input, memberIds, status, now = new Date().toISOString()) {
  /* JAYUMINTON_ATTENDANCE_TIMES_V1
     Administrator attendance contract:
     before -> active records arrival, and active assignment-pool -> away records departure.
     A fresh arrival clears the previous departure so today's row cannot show stale leave time. */
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
  const arrivedMemberIds = []; const departedMemberIds = [];
  state.members = state.members.map(m => {
    const id = String(m.id);
    if (!wanted.has(id)) return m;
    const before = previous.get(id) || { status: String(m.status || 'active'), location: null };
    const next = { ...m, status: nextStatus };
    if (nextStatus === 'active' && before.status === 'before') {
      next.arrivedAt = timestamp;
      next.departedAt = '';
      arrivedMemberIds.push(id);
    }
    if (nextStatus === 'away' && before.status === 'active' && before.location?.type === 'active') {
      next.departedAt = timestamp;
      departedMemberIds.push(id);
    }
    return next;
  });
  return { state, event: {
    type: 'member_status_changed', memberIds: ids, status: nextStatus,
    arrivedMemberIds, departedMemberIds,
  } };
}
"""
if marker not in worker:
    if worker.count(old) != 1:
        raise SystemExit('setMemberStatusMutation attendance anchor mismatch')
    worker = worker.replace(old, new, 1)
worker_path.write_text(worker, encoding='utf-8')

entry = entry_path.read_text(encoding='utf-8')
entry_marker = 'JAYUMINTON_ATTENDANCE_STATS_RESPONSE_V1'
old_entry = """  return (state.members || []).map(m => ({
    id: String(m.id), name: String(m.name || ''), games: Math.max(0, Number(m.games) || 0),
    partners: (partners.get(String(m.id)) || []).sort((x, y) => y.count - x.count || x.name.localeCompare(y.name, 'ko')),
  })).sort((a, b) => b.games - a.games || a.name.localeCompare(b.name, 'ko'));
"""
new_entry = """  return (state.members || []).map(m => ({
    /* JAYUMINTON_ATTENDANCE_STATS_RESPONSE_V1 */
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

print('ATTENDANCE_STATISTICS_V1_PATCHED')
