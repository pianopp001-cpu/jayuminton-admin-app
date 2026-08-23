#!/usr/bin/env python3
"""Final post-contract hardening for admin Cloudflare HTML, aligned to MD(4)."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
html = path.read_text(encoding='utf-8')
marker = '</body>'
if marker not in html:
    raise SystemExit('body end marker missing')

def matching_brace(text, open_pos):
    depth = 0
    quote = ''
    escape = False
    for i in range(open_pos, len(text)):
        ch = text[i]
        if quote:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == quote:
                quote = ''
            continue
        if ch in ('\"', "'", '`'):
            quote = ch
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i
    return -1

# MD(4): a finish action must remain available even when a court currently has 0 people.
# Remove old UI-only occupancy gates. Cloudflare finishCourtMutation is authoritative.
for old, new in (
    ('(STATE.courts[courtNo] || []).length === 4', 'Array.isArray(STATE.courts[courtNo])'),
    ('(STATE.courts[courtNo] || []).length > 0', 'Array.isArray(STATE.courts[courtNo])'),
    ('state.courts[no].length === 4', 'Array.isArray(state.courts[no])'),
    ('state.courts[no].length > 0', 'Array.isArray(state.courts[no])'),
):
    html = html.replace(old, new)

# MD(4) wording: court number first, then the wait-1 roster, then enter that court.
md_finish = "function finishText(courtNo,members){var calls=(members||[]).map(cleanName).filter(Boolean).map(function(n){return n+' 님';});var base=Number(courtNo)+'번 코트 나왔습니다.';return calls.length?base+'\\n'+calls.join(', ')+'\\n'+Number(courtNo)+'번 코트로 들어가 주세요.':base+'\\n대기 1번에 입장할 인원이 없습니다.';}"
finish_start = html.find('function finishText(courtNo,members)')
if finish_start < 0:
    finish_start = html.find('function finishText(courtNo, members)')
if finish_start < 0:
    raise SystemExit('admin finishText function missing')
open_brace = html.find('{', finish_start)
close_brace = matching_brace(html, open_brace)
if open_brace < 0 or close_brace < 0:
    raise SystemExit('admin finishText function boundary missing')
html = html[:finish_start] + md_finish + html[close_brace + 1:]
if md_finish not in html:
    raise SystemExit('admin finishText replacement failed')

# Also align the older browser-TTS path if it is still present in the rendered page.
html = html.replace("courtNo + '번 코트 경기가 종료되었습니다. '", "courtNo + '번 코트 나왔습니다. '")
html = html.replace("courtNo + '번 코트 경기가 종료되었습니다.'", "courtNo + '번 코트 나왔습니다.'")
html = html.replace("window.NativeVoice.speak('court_finish_'+Date.now(),text,.88,1,'')", "window.NativeVoice.speak('court_finish_'+Date.now(),text,.82,1,'')", 1)
html = html.replace('heldUtterance.rate=.88', 'heldUtterance.rate=.82', 1)

addon = r'''
<style id="jayuminton-admin-post-contract-v23">
#pairStatisticsModal .pair-statistics-modal{overflow-y:auto!important;padding-bottom:max(32px,env(safe-area-inset-bottom))!important}
#pairStatisticsModal .pair-statistics-list{max-height:none!important;height:auto!important;overflow:visible!important;padding-bottom:max(56px,calc(env(safe-area-inset-bottom) + 40px))!important}
#pairStatisticsModal .pair-statistics-row{height:auto!important;max-height:none!important;overflow:visible!important}
#pairStatisticsModal .pair-statistics-row:last-child{margin-bottom:32px!important;padding-bottom:16px!important}
#pairStatisticsModal .pair-statistics-partners{height:auto!important;max-height:none!important;overflow:visible!important;white-space:normal!important}
</style>
<script id="jayuminton-admin-alert-role-v23">
(function(){
  window.__JAYUMINTON_ADMIN_POST_CONTRACT_V23__=true;
  window.__JAYUMINTON_ADMIN_EMPTY_COURT_FINISH_MD4__=true;
  window.__JAYUMINTON_ADMIN_STATISTICS_NO_CLIP_FINAL__=true;
  window.__JAYUMINTON_ADMIN_ALERT_ROLE_V23__={
    memberWaitAlert:'member-device-only',
    memberCourtAlert:'member-device-only',
    adminWaitVoice:false,
    adminTransitionVibration:false,
    adminCourtVoice:true,
    voiceRepeatCount:3,
    vibrationSets:8,
    vibrationsPerSet:3,
    fullCourtVoiceSet:true,
    finishWording:'court-number-roster-enter',
    voiceRate:.82
  };
  window.__JAYUMINTON_TRANSITION_ALERT__=function(){ return; };
})();
</script>
'''
# Remove previous final post-contract addons before installing v23.
for old_id in ('jayuminton-admin-post-contract-v21', 'jayuminton-admin-post-contract-v22', 'jayuminton-admin-post-contract-v23'):
    start = html.find('<style id="' + old_id + '">')
    if start >= 0:
        end = html.find('</script>', start)
        if end >= 0:
            html = html[:start] + html[end + len('</script>'):]
if 'jayuminton-admin-post-contract-v23' not in html:
    html = html.replace(marker, addon + '\n' + marker, 1)

for required in (
    'jayuminton-admin-post-contract-v23',
    '__JAYUMINTON_ADMIN_EMPTY_COURT_FINISH_MD4__',
    '__JAYUMINTON_ADMIN_STATISTICS_NO_CLIP_FINAL__',
    '__JAYUMINTON_ADMIN_ALERT_ROLE_V23__',
    "memberWaitAlert:'member-device-only'",
    "memberCourtAlert:'member-device-only'",
    'adminWaitVoice:false',
    'adminTransitionVibration:false',
    'adminCourtVoice:true',
    'voiceRepeatCount:3',
    'vibrationSets:8',
    'vibrationsPerSet:3',
    'fullCourtVoiceSet:true',
    "번 코트 나왔습니다.",
    "return n+' 님'",
    "번 코트로 들어가 주세요.",
    'text,.82,1',
    'heldUtterance.rate=.82',
    'max-height:none!important',
    'overflow:visible!important'
):
    if required not in html:
        raise SystemExit('post-contract marker missing: '+required)

# A rendered admin page must no longer gate finish/voice on exactly four occupants.
for forbidden in (
    '(STATE.courts[courtNo] || []).length === 4',
    '(STATE.courts[courtNo] || []).length > 0',
):
    if forbidden in html:
        raise SystemExit('MD4 empty-court finish gate survived: '+forbidden)

path.write_text(html, encoding='utf-8')
print('ADMIN_POST_CONTRACT_V23_MD4_OK')
