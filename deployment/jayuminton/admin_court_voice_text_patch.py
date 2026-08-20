#!/usr/bin/env python3
"""Keep admin court voice concise and natural; member-device alerts remain voice-free."""
from pathlib import Path
import sys

path=Path(sys.argv[1])
html=path.read_text(encoding='utf-8')
old="function finishText(courtNo,members){var calls=(members||[]).map(cleanName).filter(Boolean).map(function(n){return n+'님';});var base=Number(courtNo)+'번 코트 경기가 종료되었습니다.';return calls.length?base+'\\n대기 1번 '+calls.join(', ')+'\\n'+Number(courtNo)+'번 코트로 들어가 주세요.':base+'\\n대기 1번에 입장할 인원이 없습니다.';}"
new="function finishText(courtNo,members){var calls=(members||[]).map(cleanName).filter(Boolean).map(function(n){return n+' 님';});var base=Number(courtNo)+'번 코트 나왔습니다.';return calls.length?base+'\\n'+calls.join(', '):base+'\\n입장할 대기 1번 인원이 없습니다.';}"
if old in html:
    html=html.replace(old,new,1)
elif new not in html:
    raise SystemExit('finishText anchor missing')
html=html.replace("window.NativeVoice.speak('court_finish_'+Date.now(),text,.88,1,'')","window.NativeVoice.speak('court_finish_'+Date.now(),text,.82,1,'')",1)
html=html.replace("heldUtterance.rate=.88","heldUtterance.rate=.82",1)
for required in ("번 코트 나왔습니다.","return n+' 님'","text,.82,1", "heldUtterance.rate=.82"):
    if required not in html:
        raise SystemExit('court voice contract missing: '+required)
path.write_text(html,encoding='utf-8')
print('ADMIN_COURT_VOICE_TEXT_PATCH_OK')