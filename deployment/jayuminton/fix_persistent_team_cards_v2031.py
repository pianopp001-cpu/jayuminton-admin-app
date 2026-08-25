from pathlib import Path

path = Path('deployment/jayuminton/cloudflare_v6_frontend_bridge.js')
source = path.read_text(encoding='utf-8')
old = "var cards=scope.querySelectorAll('#adminApp .has-member-team');"
new = "var cards=scope.querySelectorAll('#adminApp '+cardSelector.split(',').join(',#adminApp '));"
if old not in source:
    raise SystemExit('team card selector anchor not found')
source = source.replace(old, new, 1)
old2 = "if(teamText){\n          card.setAttribute('data-jm-team-text',teamText);"
new2 = "if(teamText){\n          card.classList.add('has-member-team');\n          card.setAttribute('data-jm-team-text',teamText);"
if old2 not in source:
    raise SystemExit('team label restore anchor not found')
source = source.replace(old2, new2, 1)
source = source.replace("jayuminton-admin-team-safety-v2036", "jayuminton-admin-team-safety-v2037")
path.write_text(source, encoding='utf-8')
print('PERSISTENT_TEAM_CARDS_V2031_OK')
