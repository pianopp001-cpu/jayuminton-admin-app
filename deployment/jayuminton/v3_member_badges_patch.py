#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v3_member_badges_patch.py WORKDIR')

work = Path(sys.argv[1])
script = work / 'Script.html'
s = script.read_text(encoding='utf-8')
marker = 'JAYUMINTON_MEMBER_BADGES_V3'
if marker in s:
    raise SystemExit('member badges patch already present')

addon = r'''

/* JAYUMINTON_MEMBER_BADGES_V3
   - self: cute yellow star + tiny neutral "나"
   - NEW: only when backend member.isNew === true (explicit admin checkbox)
   - both markers stay tiny and never cover the member name
*/
(function installMemberBadges(){
  if (typeof IS_ADMIN !== 'undefined' && IS_ADMIN) return;
  if (window.__JAYUMINTON_MEMBER_BADGES_V3__) return;
  window.__JAYUMINTON_MEMBER_BADGES_V3__ = true;

  function decorateNew(){
    document.querySelectorAll('#memberApp [data-member-id]').forEach(function(card){
      var id=String(card.getAttribute('data-member-id')||'');
      if(!id)return;
      var member=null;
      try{member=typeof memberById==='function'?memberById(id):null;}catch(e){}
      var badge=card.querySelector(':scope > .member-new-badge');
      if(member&&member.isNew===true){
        if(!badge){
          badge=document.createElement('span');
          badge.className='member-new-badge';
          badge.textContent='NEW';
          badge.setAttribute('aria-label','신규 회원');
          card.appendChild(badge);
        }
      }else if(badge){
        badge.remove();
      }
    });
  }

  var style = document.createElement('style');
  style.id = 'jayuminton-member-badges-style';
  style.textContent = [
    '#memberApp .person[data-member-id],#memberApp .member[data-member-id]{position:relative!important;overflow:visible!important}',
    '#memberApp .member-self-star{position:absolute!important;top:-8px!important;right:3px!important;left:auto!important;bottom:auto!important;display:inline-flex!important;align-items:center!important;gap:1px!important;width:auto!important;min-width:0!important;height:13px!important;min-height:13px!important;padding:0 2px!important;margin:0!important;border:0!important;border-radius:0!important;background:transparent!important;box-shadow:none!important;color:#4b5563!important;font-size:7px!important;font-weight:800!important;line-height:13px!important;letter-spacing:-.25px!important;white-space:nowrap!important;overflow:visible!important;pointer-events:none!important;z-index:12!important;text-shadow:0 1px 1px rgba(255,255,255,.98)!important}',
    '#memberApp .member-self-star::before{content:"⭐"!important;display:inline-block!important;color:initial!important;font-size:9px!important;line-height:13px!important}',
    '#memberApp .member-self-star b,#memberApp .member-self-star small{display:none!important}',
    '#memberApp .member-new-badge{position:absolute!important;top:-5px!important;left:4px!important;display:inline-block!important;padding:0 2px!important;border:0!important;border-radius:3px!important;background:#f5f3ff!important;color:#7c3aed!important;font-size:5.5px!important;font-weight:900!important;line-height:9px!important;height:9px!important;white-space:nowrap!important;pointer-events:none!important;z-index:10!important;box-shadow:none!important}',
    '#memberApp .person[data-member-id]>.name,#memberApp .person[data-member-id] .name{position:relative!important;z-index:1!important}'
  ].join('');
  document.head.appendChild(style);

  decorateNew();
  new MutationObserver(function(){
    clearTimeout(window.__jmNewDecorTimer);
    window.__jmNewDecorTimer=setTimeout(decorateNew,0);
  }).observe(document.getElementById('memberApp')||document.documentElement,{childList:true,subtree:true});
})();
'''

# Strip earlier badge addons if the source already carries one.
for old in ('JAYUMINTON_MEMBER_BADGES_V1','JAYUMINTON_MEMBER_BADGES_V2','JAYUMINTON_MEMBER_BADGES_V3'):
    if old in s:
        start=s.find('/* '+old)
        if start>=0:
            end=s.find('\n})();\n',start)
            if end>=0:
                s=s[:start]+s[end+len('\n})();\n'):]
                break
pos = s.rfind('</script>')
if pos < 0:
    raise SystemExit('Script.html closing script tag missing')
s = s[:pos] + addon + '\n' + s[pos:]
script.write_text(s, encoding='utf-8')

text = script.read_text(encoding='utf-8')
for needle in [marker, 'member.isNew===true', 'content:"⭐"!important', "badge.textContent='NEW'", 'font-size:5.5px!important']:
    if needle not in text:
        raise SystemExit(f'missing member badges patch {needle!r}')
if 'localDay(' in text and 'member.createdAt' in text:
    raise SystemExit('legacy automatic NEW-by-date logic still present')
