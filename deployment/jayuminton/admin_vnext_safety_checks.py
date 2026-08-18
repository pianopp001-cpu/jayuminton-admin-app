#!/usr/bin/env python3
"""Static guardrails for admin-vNext patch files. Does not deploy or edit production."""
from pathlib import Path
root=Path(__file__).resolve().parent
files=list(root.glob('admin_vnext_*_patch.py'))+[root/'apply_admin_vnext_patches.py']
errors=[]
for p in files:
    text=p.read_text(encoding='utf-8')
    forbidden=["root/'Index.html'", "root / 'Index.html'", 'Index.html\'; s=', 'firebase deploy', 'firebase hosting', 'clasp deploy', 'clasp push', 'flutter build', 'gradlew', 'play.google.com', 'google-services.json', 'AndroidManifest.xml', 'MainActivity', 'WebView']
    for token in forbidden:
        if token in text: errors.append(f'{p.name}: forbidden user/app/deploy token: {token}')

apply=(root/'apply_admin_vnext_patches.py').read_text(encoding='utf-8')
expected=['admin_vnext_backend_patch.py','admin_vnext_assignment_guard_patch.py','admin_vnext_member_fields_patch.py','admin_vnext_ui_patch.py','admin_vnext_script_patch.py','admin_vnext_multiselect_patch.py','admin_vnext_partial_court_ui_patch.py']
for name in expected:
    if name not in apply: errors.append('apply chain missing '+name)

backend=(root/'admin_vnext_backend_patch.py').read_text(encoding='utf-8')
for needle in ["incrementGamesForCourtEntrants_(members, entrants)","if (!finished.length) throw new Error('비어 있는 코트는 경기 종료할 수 없습니다.')","if (waitOne.length > 0)"]:
    if needle not in backend: errors.append('backend invariant missing '+needle)

# Every browser-side patch must target only Admin.html or Script.html.
admin_targets={
 'admin_vnext_ui_patch.py':"root/'Admin.html'",
 'admin_vnext_script_patch.py':"root/'Script.html'",
 'admin_vnext_multiselect_patch.py':"root/'Script.html'",
 'admin_vnext_partial_court_ui_patch.py':"root/'Script.html'",
}
for name,target in admin_targets.items():
    text=(root/name).read_text(encoding='utf-8')
    if target not in text: errors.append(f'{name}: expected admin-only target missing')

if errors: raise SystemExit('\n'.join(errors))
print('admin-vNext production isolation checks passed: all current admin patches covered; user web/app/deploy paths untouched')
