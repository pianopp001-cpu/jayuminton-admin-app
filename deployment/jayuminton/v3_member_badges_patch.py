#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v3_member_badges_patch.py WORKDIR')

work = Path(sys.argv[1])
script = work / 'Script.html'
s = script.read_text(encoding='utf-8')
marker = 'JAYUMINTON_MEMBER_BADGES_V2'
if marker in s:
    raise SystemExit('member badges patch already present')

addon = r'''

/* JAYUMINTON_MEMBER_BADGES_V2
   Self badge only.
   Automatic NEW-by-createdAt behavior was intentionally removed.
   NEW will only be reintroduced from an explicit admin registration flag.
*/
(function installMemberBadges(){
  if (typeof IS_ADMIN !== 'undefined' && IS_ADMIN) return;
  if (window.__JAYUMINTON_MEMBER_BADGES_V2__) return;
  window.__JAYUMINTON_MEMBER_BADGES_V2__ = true;

  var style = document.createElement('style');
  style.id = 'jayuminton-member-badges-style';
  style.textContent = [
    '#memberApp .person[data-member-id],#memberApp .member[data-member-id]{position:relative!important;overflow:visible!important}',
    '#memberApp .member-self-star{position:absolute!important;top:-8px!important;right:3px!important;left:auto!important;bottom:auto!important;display:inline-flex!important;align-items:center!important;gap:1px!important;width:auto!important;min-width:0!important;height:13px!important;min-height:13px!important;padding:0 2px!important;margin:0!important;border:0!important;border-radius:0!important;background:transparent!important;box-shadow:none!important;color:#4b5563!important;font-size:7px!important;font-weight:800!important;line-height:13px!important;letter-spacing:-.25px!important;white-space:nowrap!important;overflow:visible!important;pointer-events:none!important;z-index:12!important;text-shadow:0 1px 1px rgba(255,255,255,.98)!important}',
    '#memberApp .member-self-star::before{content:"⭐"!important;display:inline-block!important;color:initial!important;font-size:9px!important;line-height:13px!important}',
    '#memberApp .member-self-star b,#memberApp .member-self-star small{display:none!important}',
    '#memberApp .member-new-badge{display:none!important}',
    '#memberApp .person[data-member-id]>.name,#memberApp .person[data-member-id] .name{position:relative!important;z-index:1!important}'
  ].join('');
  document.head.appendChild(style);

  document.querySelectorAll('#memberApp .member-new-badge').forEach(function(node){ node.remove(); });
})();
'''

pos = s.rfind('</script>')
if pos < 0:
    raise SystemExit('Script.html closing script tag missing')
s = s[:pos] + addon + '\n' + s[pos:]
script.write_text(s, encoding='utf-8')

text = script.read_text(encoding='utf-8')
for needle in [marker, 'content:"⭐"!important', '#memberApp .member-new-badge{display:none!important}', 'color:#4b5563!important']:
    if needle not in text:
        raise SystemExit(f'missing member badges patch {needle!r}')
if 'member.createdAt' in text and 'JAYUMINTON_MEMBER_BADGES_V1' in text:
    raise SystemExit('legacy automatic NEW logic still present')
