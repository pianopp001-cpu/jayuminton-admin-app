from pathlib import Path

SCRIPT = Path('source-snapshot/current-main/Script.html')
STYLE = Path('source-snapshot/current-main/Style.html')

script = SCRIPT.read_text(encoding='utf-8')
style = STYLE.read_text(encoding='utf-8')

old_click = """document.addEventListener('click', function(event) {\n  if (!ACTION_IN_FLIGHT) return;\n  const control = event.target.closest('button,summary');\n  if (!control) return;\n  event.preventDefault();\n  event.stopImmediatePropagation();\n}, true);"""
new_click = """document.addEventListener('click', function(event) {\n  if (!ACTION_IN_FLIGHT) return;\n  const control = event.target.closest('button,summary');\n  if (!control) return;\n\n  // 저장 중에도 경기 종료 음성은 즉시 제어할 수 있어야 한다.\n  // 재생/반복/멈춤/소리 켜기는 저장 요청과 무관한 로컬 음성 제어이므로 예외 처리한다.\n  const voiceControl =\n    control.closest('.court-voice-controls') ||\n    control.id === 'soundUnlockButton' ||\n    control.id === 'replayVoiceButton' ||\n    control.id === 'repeatVoiceButton';\n  if (voiceControl) return;\n\n  event.preventDefault();\n  event.stopImmediatePropagation();\n}, true);"""
if old_click not in script:
    raise SystemExit('Script target not found: busy click guard')
script = script.replace(old_click, new_click, 1)

old_css = """/* Saving still prevents conflicting writes, but the page no longer looks frozen. */\nbody.action-busy{\n  cursor:progress!important;\n}\nbody.action-busy::after{\n  content:\"저장 중\";\n  position:fixed;\n  right:10px;\n  bottom:calc(10px + env(safe-area-inset-bottom));\n  z-index:10050;\n  padding:5px 9px;\n  border-radius:999px;\n  background:rgba(24,39,75,.92);\n  color:#fff;\n  font-size:10px;\n  font-weight:900;\n  box-shadow:0 4px 12px rgba(0,0,0,.18);\n  pointer-events:none;\n}"""
new_css = """/* Saving lock: all operation controls are blocked while a write is pending.\n   Voice controls stay above the lock so an announcement can always be stopped/replayed. */\nbody.action-busy{\n  cursor:progress!important;\n}\nbody.action-busy::before{\n  content:\"\";\n  position:fixed;\n  inset:0;\n  z-index:10040;\n  background:rgba(15,23,42,.22);\n  backdrop-filter:blur(1px);\n  pointer-events:auto;\n}\nbody.action-busy::after{\n  content:\"저장 중 · 잠시만 기다려 주세요\";\n  position:fixed;\n  left:50%;\n  top:50%;\n  transform:translate(-50%,-50%);\n  z-index:10050;\n  min-width:210px;\n  padding:13px 18px;\n  border-radius:14px;\n  background:rgba(24,39,75,.96);\n  color:#fff;\n  text-align:center;\n  font-size:13px;\n  font-weight:950;\n  box-shadow:0 12px 34px rgba(0,0,0,.3);\n  pointer-events:none;\n}\nbody.action-busy .court-voice-controls{\n  position:relative!important;\n  z-index:10060!important;\n  pointer-events:auto!important;\n}\nbody.action-busy .court-voice-controls button{\n  position:relative!important;\n  z-index:10061!important;\n  pointer-events:auto!important;\n}\nbody.action-busy .court-voice-controls::before{\n  content:\"음성 제어는 저장 중에도 사용 가능\";\n  position:absolute;\n  left:0;\n  bottom:calc(100% + 4px);\n  padding:3px 7px;\n  border-radius:999px;\n  background:#fff;\n  color:#334155;\n  border:1px solid #cbd5e1;\n  font-size:9px;\n  font-weight:900;\n  white-space:nowrap;\n  box-shadow:0 2px 8px rgba(0,0,0,.12);\n}"""
if old_css not in style:
    raise SystemExit('Style target not found: saving indicator block')
style = style.replace(old_css, new_css, 1)

# Earlier generic rule disables every button during action-busy; override only voice controls.
append_css = """\n\n/* v1.6.32 saving lock exception: only voice playback controls remain clickable. */\nbody.action-busy .court-voice-controls,\nbody.action-busy .court-voice-controls button{\n  pointer-events:auto!important;\n}\n"""
if 'v1.6.32 saving lock exception' not in style:
    style += append_css

SCRIPT.write_text(script, encoding='utf-8')
STYLE.write_text(style, encoding='utf-8')
print('patched Script.html and Style.html')
