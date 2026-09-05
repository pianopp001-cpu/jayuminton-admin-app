#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
html = path.read_text(encoding='utf-8')
MARKER = 'jmAdminEdgeUiV20881'

if MARKER in html:
    print('ADMIN_EDGE_UI_V20881_ALREADY_OK')
    raise SystemExit(0)

if 'jmAdminFixedQuickMenuV20880' not in html:
    raise SystemExit('v208.80 quick-menu prerequisite missing')

old_selection = "#jmAdminFixedQuickMenu .jm-q-selection{position:absolute!important;left:7px!important;top:-23px!important;display:flex!important;align-items:center!important;justify-content:center!important;width:max-content!important;min-width:66px!important;padding:3px 8px!important;border:1px solid #15803d!important;border-radius:7px!important;background:rgba(236,253,245,.96)!important;color:#14532d!important;font-size:10.5px!important;font-weight:950!important;line-height:1.1!important;box-shadow:0 1px 4px rgba(15,118,55,.18)!important;pointer-events:none!important}"
new_selection = "#jmAdminFixedQuickMenu .jm-q-selection{position:fixed!important;left:max(5px,env(safe-area-inset-left))!important;top:max(5px,env(safe-area-inset-top))!important;z-index:2147483020!important;display:flex!important;align-items:center!important;justify-content:center!important;width:max-content!important;min-width:54px!important;max-width:120px!important;padding:2px 5px!important;border:1px solid #15803d!important;border-radius:6px!important;background:rgba(236,253,245,.94)!important;color:#14532d!important;font-size:9px!important;font-weight:950!important;line-height:1.05!important;box-shadow:0 1px 3px rgba(15,118,55,.14)!important;pointer-events:none!important;white-space:nowrap!important}"
if old_selection not in html:
    raise SystemExit('selection badge CSS anchor missing')
html = html.replace(old_selection, new_selection, 1)

old_side = "#jmKokSideToggle{position:fixed!important;z-index:2147483010!important;right:0!important;top:42vh!important;width:52px!important;height:36px!important;min-width:52px!important;min-height:36px!important;padding:0 3px!important;border:2px solid #6d28d9!important;border-right:0!important;border-radius:9px 0 0 9px!important;background:#7c3aed!important;color:#fff!important;font-size:9px!important;line-height:1!important;font-weight:1000!important;white-space:nowrap!important;box-shadow:-3px 2px 8px rgba(15,23,42,.22)!important;transition:right .2s ease!important}"
new_side = "#jmKokSideToggle{position:fixed!important;z-index:2147483010!important;right:0!important;top:42vh!important;width:28px!important;height:82px!important;min-width:28px!important;min-height:82px!important;padding:4px 1px!important;border:2px solid #6d28d9!important;border-right:0!important;border-radius:9px 0 0 9px!important;background:#7c3aed!important;color:#fff!important;font-size:9px!important;line-height:1.05!important;font-weight:1000!important;white-space:normal!important;word-break:keep-all!important;text-align:center!important;box-shadow:-3px 2px 8px rgba(15,23,42,.18)!important;transition:right .2s ease!important}"
if old_side not in html:
    raise SystemExit('kok side-toggle CSS anchor missing')
html = html.replace(old_side, new_side, 1)

old_toggle = "var button=document.getElementById('jmKokSideToggle');if(button){button.textContent=opening?'콕체크 ▶':'콕체크 ◀';button.classList.toggle('jm-open',opening);button.setAttribute('aria-label',opening?'콕체크 닫기':'콕체크 열기');}"
new_toggle = "var button=document.getElementById('jmKokSideToggle');if(button){button.innerHTML=opening?'콕<br>체<br>크<br>▶':'콕<br>체<br>크<br>◀';button.classList.toggle('jm-open',opening);button.setAttribute('aria-label',opening?'콕체크 닫기':'콕체크 열기');}"
if old_toggle not in html:
    raise SystemExit('kok toggle text anchor missing')
html = html.replace(old_toggle, new_toggle, 1)

old_install = "button=make('jmKokSideToggle','콕체크 ◀',toggleKokPanel);button.setAttribute('aria-label','콕체크 열기');document.body.appendChild(button);return button;"
new_install = "button=make('jmKokSideToggle','콕체크 ◀',toggleKokPanel);button.innerHTML='콕<br>체<br>크<br>◀';button.setAttribute('aria-label','콕체크 열기');document.body.appendChild(button);return button;"
if old_install not in html:
    raise SystemExit('kok side-toggle install anchor missing')
html = html.replace(old_install, new_install, 1)

marker_style = "<style id=\"jmAdminEdgeUiV20881Style\">/* jmAdminEdgeUiV20881 */</style>"
close = html.lower().rfind('</body>')
if close < 0:
    raise SystemExit('body close not found')
html = html[:close] + marker_style + '\n' + html[close:]

for required in (
    MARKER,
    "left:max(5px,env(safe-area-inset-left))",
    "top:max(5px,env(safe-area-inset-top))",
    "width:28px!important;height:82px!important",
    "button.innerHTML=opening?'콕<br>체<br>크<br>▶':'콕<br>체<br>크<br>◀'",
    "button.innerHTML='콕<br>체<br>크<br>◀'",
):
    if required not in html:
        raise SystemExit('v208.81 requirement missing: ' + required)

path.write_text(html, encoding='utf-8')
print('ADMIN_EDGE_UI_V20881_OK')
