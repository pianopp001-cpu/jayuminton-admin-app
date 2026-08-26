from pathlib import Path
import runpy

# Apply the complete server-authoritative temp-pair patch first.
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
# Never render permanent team text. Permanent team = two-line border only.
b = b.replace(".jm-team-bottom-label{display:block!important;visibility:visible!important;position:static!important;width:100%!important;margin:3px 0 0!important;padding:0!important;text-align:left!important;font-size:9px!important;font-weight:900!important;line-height:1.1!important;white-space:nowrap!important;pointer-events:none!important}", ".jm-team-bottom-label{display:none!important;visibility:hidden!important;width:0!important;height:0!important;overflow:hidden!important}")
b = b.replace("#adminApp .jm-team-bottom-label{display:block!important;visibility:visible!important;width:100%!important;height:auto!important;min-width:0!important;max-width:none!important;margin:3px 0 0!important;padding:0!important;border:0!important;overflow:visible!important;position:static!important;float:none!important;clear:both!important;text-align:left!important;font-size:9px!important;font-weight:900!important;line-height:1.15!important;white-space:nowrap!important;color:var(--member-team-color)!important;pointer-events:none!important}", "#adminApp .jm-team-bottom-label{display:none!important;visibility:hidden!important;width:0!important;height:0!important;overflow:hidden!important}")
# Remove the legacy creator itself, not just its CSS.
old_creator = "          var bottom=card.querySelector('.jm-team-bottom-label');\n          if(!bottom){bottom=document.createElement('small');bottom.className='jm-team-bottom-label';card.appendChild(bottom);}\n          bottom.textContent=teamText;\n          if(bottom.parentElement!==card||card.lastElementChild!==bottom)card.appendChild(bottom);"
new_creator = "          Array.prototype.forEach.call(card.querySelectorAll('.jm-team-bottom-label'),function(bottom){bottom.remove();});"
if old_creator in b:
    b = b.replace(old_creator, new_creator, 1)
# Temporary pair is an overlay; never erase permanent border/outline.
b = b.replace("if(card.classList.contains('jm-temp-pair'))card.style.removeProperty('box-shadow');else card.style.setProperty('box-shadow','none','important');", "if(card.classList.contains('jm-temp-pair'))card.style.removeProperty('box-shadow');else card.style.setProperty('box-shadow','none','important');")
# Re-pairing is intentionally replaceable: selecting any two people in the same 4-person
# wait/court group removes the previous temporary grouping involving those four and saves the new pair.
if "old=loadTempPairs().filter(function(saved){var all=saved.pairA.concat(saved.pairB);return !ids.some(function(id){return all.indexOf(id)>=0;});});" not in b:
    raise SystemExit('replaceable temporary-pair contract missing')
# Only clicked pairA gets the temporary solid overlay; pairB stays visually unpainted.
if "var side=[group.pairA,TEMP_PAIR_COLORS[index%TEMP_PAIR_COLORS.length]];" not in b:
    raise SystemExit('pairA-only overlay contract missing')
# Remove any surviving visible bottom-label assignment.
if 'bottom.textContent=teamText' in b:
    raise SystemExit('visible team label creator survived')
bp.write_text(b)
print('SHARED_TEMP_PAIRS_V3_OK replaceable=true labels=false pairAOnly=true')
