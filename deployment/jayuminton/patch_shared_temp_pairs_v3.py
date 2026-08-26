from pathlib import Path
import runpy

# Server-authoritative temporary-pair state. Permanent teams are visual only as double borders.
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

# Never show Team1/Team2 text. Permanent team remains double-line only.
visible_shared = ".jm-team-bottom-label{display:block!important;visibility:visible!important;position:static!important;width:100%!important;margin:3px 0 0!important;padding:0!important;text-align:left!important;font-size:9px!important;font-weight:900!important;line-height:1.1!important;white-space:nowrap!important;pointer-events:none!important}"
hidden_shared = ".jm-team-bottom-label{display:none!important;visibility:hidden!important;width:0!important;height:0!important;overflow:hidden!important}"
b = b.replace(visible_shared, hidden_shared)
visible_admin = "#adminApp .jm-team-bottom-label{display:block!important;visibility:visible!important;width:100%!important;height:auto!important;min-width:0!important;max-width:none!important;margin:3px 0 0!important;padding:0!important;border:0!important;overflow:visible!important;position:static!important;float:none!important;clear:both!important;text-align:left!important;font-size:9px!important;font-weight:900!important;line-height:1.15!important;white-space:nowrap!important;color:var(--member-team-color)!important;pointer-events:none!important}"
hidden_admin = "#adminApp .jm-team-bottom-label{display:none!important;visibility:hidden!important;width:0!important;height:0!important;overflow:hidden!important}"
b = b.replace(visible_admin, hidden_admin)

# Remove any creator left by an older patch. This also prevents flicker from periodic rerenders.
creator = "          var bottom=card.querySelector('.jm-team-bottom-label');\n          if(!bottom){bottom=document.createElement('small');bottom.className='jm-team-bottom-label';card.appendChild(bottom);}\n          bottom.textContent=teamText;\n          if(bottom.parentElement!==card||card.lastElementChild!==bottom)card.appendChild(bottom);"
remove_creator = "          Array.prototype.forEach.call(card.querySelectorAll('.jm-team-bottom-label'),function(bottom){bottom.remove();});"
b = b.replace(creator, remove_creator)

# Pair overlay: only the two explicitly selected players get a single solid overlay.
# Do not reorder seats when a pair is created; multi-select move/swap remains separate.
old_side = "var side=[group.pairA,TEMP_PAIR_COLORS[index%TEMP_PAIR_COLORS.length]];"
if old_side not in b:
    # v2 may still contain pairA+pairB renderer; collapse it to pairA only.
    old_both = "[[group.pairA,TEMP_PAIR_COLORS[(index*2)%TEMP_PAIR_COLORS.length]],[group.pairB,TEMP_PAIR_COLORS[(index*2+1)%TEMP_PAIR_COLORS.length]]].forEach(function(side){"
    if old_both in b:
        b = b.replace(old_both, "[ [group.pairA,TEMP_PAIR_COLORS[index%TEMP_PAIR_COLORS.length]] ].forEach(function(side){", 1)

# Ensure the same-group ambiguity is explicit: confirm creates one-game pair, cancel leaves normal move/swap flow.
if "확인 = 1회성 팀설정" not in b or "취소 = 이동·교환" not in b:
    raise SystemExit('same-group choice prompt missing')
if 'bottom.textContent=teamText' in b:
    raise SystemExit('team label creator still present')

bp.write_text(b)
print('SHARED_TEMP_PAIRS_V3_OK labels=none pairAOnly=true prompt=true stable=true')
