from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
worker_path = ROOT / 'cloudflare/state-worker/worker.js'
script_path = ROOT / 'source-snapshot/current-main/Script.html'

worker = worker_path.read_text(encoding='utf-8')
script = script_path.read_text(encoding='utf-8')

# 1) MD(4): court-assignment-wait(active) is a real swappable location.
old_location = """function locationOf(state, memberId) {\n  const id = String(memberId);\n  for (const no of ['1', '2', '3', '4']) if (state.courts[no].includes(id)) return { type: 'court', key: no };\n  for (let i = 0; i < 5; i += 1) if (state.waitGroups[i].includes(id)) return { type: 'wait', key: String(i + 1) };\n  return null;\n}\n"""
new_location = """function locationOf(state, memberId) {\n  const id = String(memberId);\n  for (const no of ['1', '2', '3', '4']) if (state.courts[no].includes(id)) return { type: 'court', key: no };\n  for (let i = 0; i < 5; i += 1) if (state.waitGroups[i].includes(id)) return { type: 'wait', key: String(i + 1) };\n  const member = state.members.find(m => String(m.id) === id);\n  if (member && String(member.status) === 'active') return { type: 'active', key: 'active' };\n  return null;\n}\n"""
if old_location not in worker:
    raise SystemExit('locationOf anchor not found')
worker = worker.replace(old_location, new_location, 1)

old_swap = """  if (JSON.stringify(aLoc) === JSON.stringify(bLoc)) throw new Error('same_location');\n  const aTarget = container(state, aLoc); const bTarget = container(state, bLoc);\n  a.forEach((id, i) => { aTarget[aTarget.indexOf(id)] = b[i]; });\n  b.forEach((id, i) => { bTarget[bTarget.indexOf(id)] = a[i]; });\n  const enteringCourt = [];\n  if (aLoc.type === 'court' && bLoc.type !== 'court') enteringCourt.push(...b);\n  if (bLoc.type === 'court' && aLoc.type !== 'court') enteringCourt.push(...a);\n  addGames(state, enteringCourt, 1);\n  syncMemberStatuses(state);\n"""
new_swap = """  if (JSON.stringify(aLoc) === JSON.stringify(bLoc)) throw new Error('same_location');\n  const enteringCourt = [];\n  if (aLoc.type === 'active' || bLoc.type === 'active') {\n    if (aLoc.type === 'active' && bLoc.type === 'active') throw new Error('same_location');\n    const activeIds = aLoc.type === 'active' ? a : b;\n    const placedIds = aLoc.type === 'active' ? b : a;\n    const placedLoc = aLoc.type === 'active' ? bLoc : aLoc;\n    const placedTarget = container(state, placedLoc);\n    placedIds.forEach((id, i) => { placedTarget[placedTarget.indexOf(id)] = activeIds[i]; });\n    if (placedLoc.type === 'court') enteringCourt.push(...activeIds);\n  } else {\n    const aTarget = container(state, aLoc); const bTarget = container(state, bLoc);\n    a.forEach((id, i) => { aTarget[aTarget.indexOf(id)] = b[i]; });\n    b.forEach((id, i) => { bTarget[bTarget.indexOf(id)] = a[i]; });\n    if (aLoc.type === 'court' && bLoc.type !== 'court') enteringCourt.push(...b);\n    if (bLoc.type === 'court' && aLoc.type !== 'court') enteringCourt.push(...a);\n  }\n  addGames(state, enteringCourt, 1);\n  syncMemberStatuses(state);\n"""
if old_swap not in worker:
    raise SystemExit('swap anchor not found')
worker = worker.replace(old_swap, new_swap, 1)

# 2) MD(4): one backup = all member input preserved, everyone restored to court-assignment waiting.
old_backup = """      if (action === 'backup') {\n        const current = await readState(this.env.DB);\n        await this.env.DB.prepare('DELETE FROM state_backups').run();\n        await this.env.DB.prepare('INSERT INTO state_backups(revision,state_json,created_at) VALUES(?,?,?)').bind(current.revision, JSON.stringify(current), new Date().toISOString()).run();\n        return reply({ ok: true, revision: current.revision });\n      }\n"""
new_backup = """      if (action === 'backup') {\n        const current = await readState(this.env.DB);\n        const backupState = normalizeState(structuredClone(current));\n        backupState.courts = { '1': [], '2': [], '3': [], '4': [] };\n        backupState.courtStartedAt = { '1': '', '2': '', '3': '', '4': '' };\n        backupState.waitGroups = [[], [], [], [], []];\n        backupState.swapRequests = [];\n        backupState.actionHistory = [];\n        backupState.members = backupState.members.map(member => ({ ...member, status: 'active' }));\n        await this.env.DB.prepare('DELETE FROM state_backups').run();\n        await this.env.DB.prepare('INSERT INTO state_backups(revision,state_json,created_at) VALUES(?,?,?)').bind(current.revision, JSON.stringify(backupState), new Date().toISOString()).run();\n        return reply({ ok: true, revision: current.revision });\n      }\n"""
if old_backup not in worker:
    raise SystemExit('backup anchor not found')
worker = worker.replace(old_backup, new_backup, 1)

# 3) MD(4): web foreground vibration is 3 pulses x 8 groups for both wait1 and court assignment.
old_repeat = """function memberAlertRepeatCount(type) {\n  if (type === 'court_assignment') return 4;\n  if (type === 'wait1_ready') return 2;\n  return 1;\n}\n"""
new_repeat = """function memberAlertRepeatCount(type) {\n  if (type === 'court_assignment') return 8;\n  if (type === 'wait1_ready') return 8;\n  return 1;\n}\n"""
if old_repeat not in script:
    raise SystemExit('memberAlertRepeatCount anchor not found')
script = script.replace(old_repeat, new_repeat, 1)

# 4) MD(4): self card needs a visible star plus small '나' marker.
script = script.replace('class=\\"member-self-star\\" aria-label=\\"내 이름\\">나</span>', 'class=\\"member-self-star\\" aria-label=\\"내 이름\\">★ 나</span>')
script = script.replace('class="member-self-star" aria-label="내 이름">나</span>', 'class="member-self-star" aria-label="내 이름">★ 나</span>')
if '★ 나</span>' not in script:
    raise SystemExit('self star patch did not apply')

worker_path.write_text(worker, encoding='utf-8')
script_path.write_text(script, encoding='utf-8')
print('MD4 core v3 patch applied')
