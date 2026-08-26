from pathlib import Path
import runpy

# Apply the complete v2 server-authoritative temp-pair patch first.
runpy.run_path('deployment/jayuminton/patch_shared_temp_pairs_v2.py', run_name='__main__')

# Keep mutation-side reconciliation and frontend outline protection deterministic/idempotent.
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
    w = w.replace(
        "  reconcileTempPairs(state);\n  reconcileTempPairs(state);\n",
        "  reconcileTempPairs(state);\n",
        1,
    )
wp.write_text(w)

bp = Path('deployment/jayuminton/cloudflare_v6_frontend_bridge.js')
b = bp.read_text()

# Do not let permanent-team styling wipe the temporary pair outline.
old_shadow = "card.style.setProperty('box-shadow','none','important');\n          card.style.setProperty('border'"
new_shadow = "if(card.classList.contains('jm-temp-pair'))card.style.removeProperty('box-shadow');else card.style.setProperty('box-shadow','none','important');\n          card.style.setProperty('border'"
if new_shadow not in b and old_shadow in b:
    b = b.replace(old_shadow, new_shadow, 1)

# Add a high-specificity temp-pair outline once so both admin and member cards retain it.
outline = "#adminApp .member.jm-team-card.has-member-team.jm-temp-pair,#adminApp .member.jm-team-card.jm-temp-pair,#adminApp .has-member-team.jm-temp-pair,#adminApp .jm-temp-pair{box-shadow:0 0 0 3px var(--jm-temp-pair-color)!important}"
if outline not in b:
    marker = ".jm-temp-pair{box-shadow:0 0 0 3px var(--jm-temp-pair-color)!important}.jm-team-bottom-label{display:none!important}"
    if marker in b:
        b = b.replace(marker, marker + outline, 1)

# Remove accidental duplicate copies if older failed patch attempts left them behind.
while outline + outline in b:
    b = b.replace(outline + outline, outline, 1)

duplicate = "#adminApp .member.jm-team-card.has-member-team.jm-temp-pair{box-shadow:0 0 0 3px var(--jm-temp-pair-color)!important}#adminApp .member.jm-team-card.jm-temp-pair{box-shadow:0 0 0 3px var(--jm-temp-pair-color)!important}"
while duplicate + duplicate in b:
    b = b.replace(duplicate + duplicate, duplicate, 1)

bp.write_text(b)
print('SHARED_TEMP_PAIRS_V3_OK')
