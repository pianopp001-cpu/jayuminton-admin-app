from pathlib import Path
import runpy

# Keep server-authoritative temporary-pair state and deterministic ordering.
runpy.run_path('deployment/jayuminton/patch_shared_temp_pairs_v2.py', run_name='__main__')

wp = Path('cloudflare/state-worker/worker.js')
w = wp.read_text()
targets = [
    ("  syncMemberStatuses(state);\n  return { state, event: { type: 'court_finished'",
     "  syncMemberStatuses(state);\n  reconcileTempPairs(state);\n  return { state, event: { type: 'court_finished'"),
    ("  syncMemberStatuses(state);\n  return { state, event: { type: 'members_moved'",
     "  syncMemberStatuses(state);\n  reconcileTempPairs(state);\n  return { state, event: { type: 'members_moved'"),
    ("  syncMemberStatuses(state);\n  return { state, event: { type: 'members_swapped'",
     "  syncMemberStatuses(state);\n  reconcileTempPairs(state);\n  return { state, event: { type: 'members_swapped'"),
    ("  return { state, event: { type: 'locations_swapped'",
     "  reconcileTempPairs(state);\n  return { state, event: { type: 'locations_swapped'"),
]
for old, new in targets:
    if new not in w and old in w:
        w = w.replace(old, new, 1)
while "  reconcileTempPairs(state);\n  reconcileTempPairs(state);\n" in w:
    w = w.replace("  reconcileTempPairs(state);\n  reconcileTempPairs(state);\n", "  reconcileTempPairs(state);\n", 1)
wp.write_text(w)

bp = Path('deployment/jayuminton/cloudflare_v6_frontend_bridge.js')
b = bp.read_text()

# Latest official-team contract: permanent team keeps a double line and a tiny bottom Team1/Team2 label.
hidden_shared = ".jm-team-bottom-label{display:none!important;visibility:hidden!important;width:0!important;height:0!important;overflow:hidden!important}"
visible_shared = ".jm-team-bottom-label{display:block!important;visibility:visible!important;position:static!important;width:100%!important;margin:3px 0 0!important;padding:0!important;text-align:left!important;font-size:9px!important;font-weight:900!important;line-height:1.1!important;white-space:nowrap!important;pointer-events:none!important}"
b = b.replace(hidden_shared, visible_shared)
hidden_admin = "#adminApp .jm-team-bottom-label{display:none!important;visibility:hidden!important;width:0!important;height:0!important;overflow:hidden!important}"
visible_admin = "#adminApp .jm-team-bottom-label{display:block!important;visibility:visible!important;width:100%!important;height:auto!important;min-width:0!important;max-width:none!important;margin:3px 0 0!important;padding:0!important;border:0!important;overflow:visible!important;position:static!important;float:none!important;clear:both!important;text-align:left!important;font-size:9px!important;font-weight:900!important;line-height:1.15!important;white-space:nowrap!important;color:var(--member-team-color)!important;pointer-events:none!important}"
b = b.replace(hidden_admin, visible_admin)

remove_creator = "          Array.prototype.forEach.call(card.querySelectorAll('.jm-team-bottom-label'),function(bottom){bottom.remove();});"
creator = "          var bottom=card.querySelector('.jm-team-bottom-label');\n          if(!bottom){bottom=document.createElement('small');bottom.className='jm-team-bottom-label';card.appendChild(bottom);}\n          bottom.textContent=teamText;\n          if(bottom.parentElement!==card||card.lastElementChild!==bottom)card.appendChild(bottom);"
if remove_creator in b:
    b = b.replace(remove_creator, creator, 1)

# Only explicitly clicked pairA receives the one-game solid overlay. pairB is unpainted.
if "var side=[group.pairA,TEMP_PAIR_COLORS[index%TEMP_PAIR_COLORS.length]];" not in b:
    raise SystemExit('pairA-only overlay contract missing')
# Re-pairing the same four is allowed by replacing their previous temp pair state.
if "old=loadTempPairs().filter(function(saved){var all=saved.pairA.concat(saved.pairB);return !ids.some(function(id){return all.indexOf(id)>=0;});});" not in b:
    raise SystemExit('replaceable temporary-pair contract missing')
# Same wait/court second click must ask which action is intended.
if "확인 = 1회성 팀설정" not in b or "취소 = 이동·교환" not in b:
    raise SystemExit('same-group choice prompt missing')
if 'bottom.textContent=teamText' not in b:
    raise SystemExit('official tiny bottom team label missing')

bp.write_text(b)
print('SHARED_TEMP_PAIRS_V3_OK replaceable=true labels=bottom-small pairAOnly=true prompt=true')
