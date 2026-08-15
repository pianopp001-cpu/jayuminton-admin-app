#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v3_member_badges_patch.py WORKDIR')

work = Path(sys.argv[1])
script = work / 'Script.html'
s = script.read_text(encoding='utf-8')
marker = 'JAYUMINTON_MEMBER_BADGES_V5'
if marker in s:
    raise SystemExit('member badges patch already present')

addon = r'''

/* JAYUMINTON_MEMBER_BADGES_V5
   - self: bright yellow star with red outline + coral "나" pill, one line
   - no white bubble; marker sits just above/right of card border and never covers the name
   - NEW: only when backend member.isNew === true (explicit admin checkbox)
*/
(function installMemberBadges(){
  if (typeof IS_ADMIN !== 'undefined' && IS_ADMIN) return;
  if (window.__JAYUMINTON_MEMBER_BADGES_V5__) return;
  window.__JAYUMINTON_MEMBER_BADGES_V5__ = true;

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
    '#memberApp .member-self-star{position:absolute!important;top:-9px!important;right:-3px!important;left:auto!important;bottom:auto!important;display:inline-flex!important;flex-direction:row!important;flex-wrap:nowrap!important;align-items:center!important;justify-content:flex-start!important;gap:3px!important;width:max-content!important;min-width:max-content!important;max-width:none!important;height:15px!important;min-height:15px!important;padding:0!important;margin:0!important;border:0!important;border-radius:0!important;background:transparent!important;box-shadow:none!important;color:#ff5b72!important;font-size:8px!important;font-weight:950!important;line-height:15px!important;letter-spacing:-.25px!important;white-space:nowrap!important;word-break:keep-all!important;overflow:visible!important;pointer-events:none!important;z-index:20!important;text-shadow:none!important}',
    '#memberApp .member-self-star::before{content:"★"!important;display:inline-block!important;flex:0 0 auto!important;color:#ffd84d!important;font-size:12px!important;font-weight:900!important;line-height:15px!important;filter:drop-shadow(0 1px 1px rgba(15,23,42,.18))!important;text-shadow:-.8px 0 #d62828,.8px 0 #d62828,0 -.8px #d62828,0 .8px #d62828,-.6px -.6px #d62828,.6px -.6px #d62828,-.6px .6px #d62828,.6px .6px #d62828!important}',
    '#memberApp .member-self-star{padding-right:1px!important}',
    '#memberApp .member-self-star::after{content:""!important;position:absolute!important;right:-3px!important;top:2px!important;width:15px!important;height:11px!important;border-radius:6px!important;background:rgba(255,235,239,.92)!important;border:1px solid rgba(255,91,114,.28)!important;z-index:-1!important}',
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

for old in ('JAYUMINTON_MEMBER_BADGES_V1','JAYUMINTON_MEMBER_BADGES_V2','JAYUMINTON_MEMBER_BADGES_V3','JAYUMINTON_MEMBER_BADGES_V4','JAYUMINTON_MEMBER_BADGES_V5'):
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
for needle in [marker, 'member.isNew===true', 'content:"★"!important', 'color:#ffd84d!important', '#d62828', 'color:#ff5b72!important', 'rgba(255,235,239,.92)', 'flex-wrap:nowrap!important', 'width:max-content!important', "badge.textContent='NEW'", 'font-size:5.5px!important']:
    if needle not in text:
        raise SystemExit(f'missing member badges patch {needle!r}')
if 'localDay(' in text and 'member.createdAt' in text:
    raise SystemExit('legacy automatic NEW-by-date logic still present')
