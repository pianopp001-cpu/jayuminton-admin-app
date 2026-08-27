from pathlib import Path
import sys

html = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
s = html.read_text(encoding='utf-8')

# This patch is intentionally limited to the exact v203.0 baseline interaction UI.
# Keep every other v203.0 behavior/layout intact.
required = [
    '__JAYUMINTON_ADMIN_MULTI_ACTION_V2053__',
    '__JAYUMINTON_ADMIN_CONTINUE_SELECTION_V2067__',
    "if(selected.length!==2){if(p)p.remove();return;}",
    "if(same){if(selected.length<4){selected.push(id);renderGreen();renderPanel();return;}",
    "if(selected.length>=2&&selected.length<=4){beginAutoTarget({kind:'member',id:id});return;}",
]
for marker in required:
    if marker not in s:
        raise SystemExit('v203 baseline marker missing: ' + marker)

# The baseline already supports selecting a 3rd/4th person in code. The actual problem is
# the large 2-person action panel covering cards. Keep team setup available only for exactly
# two selected people, but collapse that panel to one small pass-through team button.
style_anchor = ".jm-do-team:disabled{opacity:.38}"
style_patch = style_anchor + ".jm-multi-action.jm-v203-two-team-only{width:auto!important;max-width:140px!important;left:8px!important;right:auto!important;bottom:8px!important;transform:none!important;padding:4px!important;border-radius:12px!important}.jm-multi-action.jm-v203-two-team-only .jm-multi-head,.jm-multi-action.jm-v203-two-team-only .jm-multi-help,.jm-multi-action.jm-v203-two-team-only .jm-do-move,.jm-multi-action.jm-v203-two-team-only .jm-do-active,.jm-multi-action.jm-v203-two-team-only .jm-do-cancel{display:none!important}.jm-multi-action.jm-v203-two-team-only .jm-multi-actions{display:block!important}.jm-multi-action.jm-v203-two-team-only .jm-do-team{display:block!important;min-height:36px!important;padding:0 10px!important;font-size:12px!important}"
if style_anchor not in s:
    raise SystemExit('v203 baseline style anchor missing')
s = s.replace(style_anchor, style_patch, 1)

render_anchor = "function renderPanel(){var p=document.getElementById('jm-admin-multi-action');"
render_patch = render_anchor + "if(p)p.classList.remove('jm-v203-two-team-only');"
if render_anchor not in s:
    raise SystemExit('v203 baseline renderPanel anchor missing')
s = s.replace(render_anchor, render_patch, 1)

two_anchor = "var canTeam=samePlace(selected);p=panel();p.innerHTML="
two_patch = "var canTeam=samePlace(selected);p=panel();p.classList.add('jm-v203-two-team-only');p.innerHTML="
if two_anchor not in s:
    raise SystemExit('v203 baseline two-person panel anchor missing')
s = s.replace(two_anchor, two_patch, 1)

marker = '<!-- JAYUMINTON_V203_BASELINE_CONTINUOUS_3_4_MINIMAL -->'
if marker not in s:
    s = s.replace('</body>', marker + '\n</body>', 1)

html.write_text(s, encoding='utf-8')
print('V203_BASELINE_CONTINUOUS_3_4_MINIMAL_OK')
