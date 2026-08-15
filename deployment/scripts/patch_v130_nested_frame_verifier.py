from pathlib import Path

p = Path('deployment/scripts/hotfix_v130_white_screen.sh')
s = p.read_text(encoding='utf-8')
old = """const frames = page.frames();\nconst target = frames.find(f => f !== page.mainFrame() && f.url().includes('script.google.com')) || frames.find(f => f !== page.mainFrame() && !f.url().startsWith('about:blank'));\nlet inner = '';\nif (target) inner = (await target.locator('body').innerText({timeout:6000}).catch(()=>'' )).replace(/\\s+/g,' ').trim();\nconst proof = { frameUrls: frames.map(f=>f.url()), inner: inner.slice(0,2000), errors };\nfs.writeFileSync('proof.json', JSON.stringify(proof,null,2));\nconsole.log(JSON.stringify(proof,null,2));\nif (!target) throw new Error('court iframe did not load');\nif (inner.length < 20) throw new Error('court iframe body is blank');\n"""
new = """const frames = page.frames();\nconst inspected = [];\nfor (const frame of frames) {\n  if (frame === page.mainFrame()) continue;\n  const inner = (await frame.locator('body').innerText({timeout:6000}).catch(()=>'' )).replace(/\\s+/g,' ').trim();\n  inspected.push({url:frame.url(), inner:inner.slice(0,4000)});\n}\nconst target = inspected.find(x => /멤버 열람 비밀번호|자유민턴 코트배정 현황/.test(x.inner)) || inspected.sort((a,b)=>b.inner.length-a.inner.length)[0] || null;\nconst inner = target ? target.inner : '';\nconst proof = { frameUrls: frames.map(f=>f.url()), inspected, selected: target, errors };\nfs.writeFileSync('proof.json', JSON.stringify(proof,null,2));\nconsole.log(JSON.stringify(proof,null,2));\nif (!target) throw new Error('court iframe did not load');\nif (!/멤버 열람 비밀번호|자유민턴 코트배정 현황/.test(inner)) throw new Error('member UI not found in nested Apps Script frames');\n"""
if old not in s:
    raise SystemExit('nested verifier anchor missing')
p.write_text(s.replace(old, new, 1), encoding='utf-8')
print('V130_NESTED_FRAME_VERIFIER_PATCHED')
