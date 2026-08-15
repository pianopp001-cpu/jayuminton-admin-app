#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v3_member_badges_patch.py WORKDIR')

work = Path(sys.argv[1])
script = work / 'Script.html'
s = script.read_text(encoding='utf-8')
marker = 'JAYUMINTON_MEMBER_BADGES_V1'
if marker in s:
    raise SystemExit('member badges patch already present')

addon = r'''

/* JAYUMINTON_MEMBER_BADGES_V1
   - self badge: cute yellow star + small neutral "나", never over the name
   - NEW badge: members registered today (createdAt), tiny and outside the name line
*/
(function installMemberBadges(){
  if (typeof IS_ADMIN !== 'undefined' && IS_ADMIN) return;
  if (window.__JAYUMINTON_MEMBER_BADGES_V1__) return;
  window.__JAYUMINTON_MEMBER_BADGES_V1__ = true;

  function localDay(value){
    var d = value instanceof Date ? value : new Date(value);
    if (!d || isNaN(d.getTime())) return '';
    return [d.getFullYear(), String(d.getMonth()+1).padStart(2,'0'), String(d.getDate()).padStart(2,'0')].join('-');
  }

  function decorateBadges(){
    var today = localDay(new Date());
    document.querySelectorAll('#memberApp [data-member-id]').forEach(function(card){
      var id = String(card.getAttribute('data-member-id') || '');
      if (!id) return;
      var member = null;
      try { member = typeof memberById === 'function' ? memberById(id) : null; } catch (e) {}
      var isToday = !!(member && member.createdAt && localDay(member.createdAt) === today);
      var badge = card.querySelector(':scope > .member-new-badge');
      if (isToday && !badge) {
        badge = document.createElement('span');
        badge.className = 'member-new-badge';
        badge.textContent = 'NEW';
        badge.setAttribute('aria-label','오늘 신규 등록');
        card.appendChild(badge);
      } else if (!isToday && badge) {
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
    '#memberApp .member-new-badge{position:absolute!important;top:-7px!important;left:3px!important;right:auto!important;bottom:auto!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;height:12px!important;min-height:12px!important;padding:0 3px!important;border:1px solid #bfdbfe!important;border-radius:5px!important;background:#eff6ff!important;color:#3b82f6!important;font-size:6.5px!important;font-weight:900!important;line-height:10px!important;letter-spacing:.15px!important;white-space:nowrap!important;pointer-events:none!important;z-index:11!important;box-shadow:0 1px 2px rgba(15,23,42,.08)!important}',
    '#memberApp .person[data-member-id]>.name,#memberApp .person[data-member-id] .name{position:relative!important;z-index:1!important}'
  ].join('');
  document.head.appendChild(style);

  decorateBadges();
  new MutationObserver(function(){
    window.clearTimeout(window.__jmMemberBadgesTimer);
    window.__jmMemberBadgesTimer = window.setTimeout(decorateBadges, 0);
  }).observe(document.getElementById('memberApp') || document.documentElement,{childList:true,subtree:true});
})();
'''

pos = s.rfind('</script>')
if pos < 0:
    raise SystemExit('Script.html closing script tag missing')
s = s[:pos] + addon + '\n' + s[pos:]
script.write_text(s, encoding='utf-8')

text = script.read_text(encoding='utf-8')
for needle in [marker, 'member-new-badge', 'member.createdAt', 'content:"⭐"!important', "badge.textContent = 'NEW'", 'color:#4b5563!important']:
    if needle not in text:
        raise SystemExit(f'missing member badges patch {needle!r}')
