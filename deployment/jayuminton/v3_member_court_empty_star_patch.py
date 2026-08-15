#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v3_member_court_empty_star_patch.py WORKDIR')

work = Path(sys.argv[1])
script = work / 'Script.html'
s = script.read_text(encoding='utf-8')
marker = 'JAYUMINTON_MEMBER_COURT_EMPTY_STAR_V1'
if marker in s:
    raise SystemExit('court empty/star patch already present')

addon = r'''

/* JAYUMINTON_MEMBER_COURT_EMPTY_STAR_V1
   Member UX production patch:
   - registered self is implicit source
   - one tap on an empty court slot moves there immediately
   - destination is highlighted before save
   - self marker is a tiny red star, never a name-covering badge
*/
(function installMemberCourtEmptyStarPatch(){
  if (typeof IS_ADMIN !== 'undefined' && IS_ADMIN) return;
  if (window.__JAYUMINTON_MEMBER_COURT_EMPTY_STAR_V1__) return;
  window.__JAYUMINTON_MEMBER_COURT_EMPTY_STAR_V1__ = true;

  function selfId(){
    try { return String(typeof storedSelfMemberId === 'function' ? (storedSelfMemberId() || '') : ''); }
    catch (e) { return ''; }
  }

  function courtDestination(card){
    if (!card || !card.closest) return null;
    var courtCard = card.closest('#memberCourts .v4-court-card');
    if (!courtCard) return null;
    var match = String(courtCard.className || '').match(/(?:^|\\s)court-(\\d+)(?:\\s|$)/);
    var players = card.closest('.players');
    if (!match || !players) return null;
    var slotIndex = Array.prototype.indexOf.call(players.children, card);
    if (slotIndex < 0) return null;
    return {type:'court', courtNo:String(match[1]), slotIndex:Number(slotIndex)};
  }

  document.addEventListener('click', function(event){
    var card = event.target && event.target.closest
      ? event.target.closest('#memberCourts .v4-court-card .person.empty')
      : null;
    if (!card) return;
    var destination = courtDestination(card);
    if (!destination) return;

    event.preventDefault();
    event.stopImmediatePropagation();

    if (!selfId()) {
      if (window.memberAnywhereModal && typeof window.memberAnywhereModal.show === 'function') {
        window.memberAnywhereModal.show('본인 설정 필요','먼저 본인 이름을 설정해 주세요.');
      }
      return;
    }

    document.querySelectorAll('.member-anywhere-destination-selected').forEach(function(el){
      el.classList.remove('member-anywhere-destination-selected');
    });
    card.classList.add('member-anywhere-destination-selected');

    if (typeof window.memberAnywhereMoveSelf === 'function') {
      window.memberAnywhereMoveSelf(destination);
    }
  }, true);

  var style = document.createElement('style');
  style.id = 'jayuminton-member-court-empty-star-style';
  style.textContent = [
    '#memberApp .is-self-member{position:relative!important;overflow:visible!important}',
    '#memberApp .member-self-star{position:absolute!important;top:-5px!important;right:-2px!important;left:auto!important;bottom:auto!important;width:11px!important;min-width:11px!important;height:11px!important;min-height:11px!important;padding:0!important;margin:0!important;border:0!important;border-radius:0!important;background:transparent!important;box-shadow:none!important;color:transparent!important;font-size:0!important;line-height:1!important;overflow:visible!important;pointer-events:none!important;z-index:9!important}',
    '#memberApp .member-self-star::before{content:"★"!important;display:block!important;color:#e11d48!important;font-size:10px!important;font-weight:900!important;line-height:11px!important;text-shadow:0 1px 1px rgba(255,255,255,.9)!important}',
    '#memberApp .member-self-star b,#memberApp .member-self-star small{display:none!important}',
    '#memberApp #memberCourts .person.empty{cursor:pointer!important}',
    '#memberApp .member-anywhere-destination-selected{outline:4px solid #111!important;outline-offset:-4px!important;box-shadow:0 0 0 4px rgba(255,215,0,.95),0 5px 14px rgba(0,0,0,.24)!important}'
  ].join('');
  document.head.appendChild(style);
})();
'''

pos = s.rfind('</script>')
if pos < 0:
    raise SystemExit('Script.html closing script tag missing')
s = s[:pos] + addon + '\n' + s[pos:]
script.write_text(s, encoding='utf-8')

text = script.read_text(encoding='utf-8')
for needle in [
    marker,
    "event.target.closest('#memberCourts .v4-court-card .person.empty')",
    "return {type:'court', courtNo:String(match[1]), slotIndex:Number(slotIndex)}",
    'window.memberAnywhereMoveSelf(destination)',
    'content:"★"!important',
    'color:#e11d48!important'
]:
    if needle not in text:
        raise SystemExit(f'missing court empty/star patch {needle!r}')
