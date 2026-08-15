#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v3_admin_compact_fast_v3.py WORKDIR')

work = Path(sys.argv[1])
script = work / 'Script.html'
style = work / 'Style.html'

s = script.read_text(encoding='utf-8')
marker = 'JAYUMINTON_ADMIN_COMPACT_FAST_V4'

# Direct render contract: wherever admin compact cards previously used
# compactMemberName(member.name), explicit NEW members render the complete
# stored name. This avoids relying only on post-render DOM decoration.
direct_expr = "(member && member.isNew === true ? escapeMemberInfo(member.name) : compactMemberName(member.name))"
if direct_expr not in s:
    s = s.replace('compactMemberName(member.name)', direct_expr)

addon = r'''

/* JAYUMINTON_ADMIN_COMPACT_FAST_V4
   Final admin presentation contract:
   - normal member cards: compact two-character display name
   - explicit NEW members: full stored name including nickname parentheses
   - game count is always visible on every admin member card
   - saving indicator is non-blocking; optimistic card updates remain visible immediately
*/
(function installAdminCompactFastV4(){
  if (typeof IS_ADMIN !== 'undefined' && !IS_ADMIN) return;
  if (window.__JAYUMINTON_ADMIN_COMPACT_FAST_V4__) return;
  window.__JAYUMINTON_ADMIN_COMPACT_FAST_V4__ = true;

  function compactTwo(name){
    var base=String(name||'').split('(')[0].split('（')[0].trim();
    return Array.from(base || String(name||'').trim()).slice(0,2).join('');
  }

  function decorateCard(card){
    if(!card || !card.getAttribute) return;
    var id=String(card.getAttribute('data-member-id')||'');
    if(!id) return;
    var member=null;
    try{member=typeof memberById==='function'?memberById(id):null;}catch(e){}
    if(!member) return;

    var nameEl=card.querySelector('.name');
    if(nameEl){
      nameEl.textContent = member.isNew === true
        ? String(member.name||'')
        : compactTwo(member.name);
      if(member.isNew === true){
        var newTag=document.createElement('span');
        newTag.className='member-new-inline';
        newTag.textContent='NEW';
        nameEl.appendChild(newTag);
      }
    }

    var gameText=(Number(member.games)||0)+'게임';
    var gameEl=null;
    card.querySelectorAll('.meta,.member-game-count,[data-role="games"]').forEach(function(el){
      if(!gameEl && /게임/.test(String(el.textContent||''))) gameEl=el;
    });
    if(gameEl){
      gameEl.textContent=gameText;
      gameEl.classList.add('member-game-count');
    }else{
      gameEl=document.createElement('span');
      gameEl.className='meta member-game-count';
      gameEl.textContent=gameText;
      if(nameEl && nameEl.parentNode){
        if(nameEl.nextSibling) nameEl.parentNode.insertBefore(gameEl,nameEl.nextSibling);
        else nameEl.parentNode.appendChild(gameEl);
      }else{
        card.appendChild(gameEl);
      }
    }
  }

  function decorateAll(){
    document.querySelectorAll('#adminApp [data-member-id]').forEach(decorateCard);
  }

  var oldRenderState=window.renderState;
  if(typeof oldRenderState==='function'){
    window.renderState=function(state){
      var out=oldRenderState(state);
      requestAnimationFrame(decorateAll);
      return out;
    };
  }

  decorateAll();
  new MutationObserver(function(){
    clearTimeout(window.__jmAdminCardDecorTimer);
    window.__jmAdminCardDecorTimer=setTimeout(decorateAll,0);
  }).observe(document.getElementById('adminApp')||document.documentElement,{childList:true,subtree:true});
})();
'''

# Remove previous V3/V4 presentation addon before inserting the newest one.
for old in ('JAYUMINTON_ADMIN_COMPACT_FAST_V3','JAYUMINTON_ADMIN_COMPACT_FAST_V4'):
    start=s.find('/* '+old)
    if start>=0:
        end=s.find('\n})();\n',start)
        if end>=0:
            s=s[:start]+s[end+len('\n})();\n'):]
            break

pos=s.rfind('</script>')
if pos<0: raise SystemExit('Script.html closing script tag missing')
s=s[:pos]+addon+'\n'+s[pos:]
script.write_text(s,encoding='utf-8')

css=style.read_text(encoding='utf-8')
css_patch=r'''

/* JAYUMINTON_ADMIN_COMPACT_FAST_V4 */
.admin-saving-overlay{position:fixed!important;inset:auto 10px auto auto!important;top:62px!important;width:auto!important;height:auto!important;background:transparent!important;display:none!important;align-items:flex-start!important;justify-content:flex-end!important;pointer-events:none!important;z-index:99999!important}
.admin-saving-overlay.show{display:flex!important}
.admin-saving-card{min-width:0!important;width:auto!important;padding:7px 10px!important;border:1px solid #dbe3ef!important;border-radius:10px!important;background:rgba(255,255,255,.96)!important;box-shadow:0 4px 14px rgba(15,23,42,.14)!important;display:flex!important;flex-direction:row!important;align-items:center!important;gap:6px!important}
.admin-saving-card strong{font-size:11px!important;line-height:1!important;font-weight:900!important;white-space:nowrap!important}
.admin-saving-card small{display:none!important}
.admin-saving-spinner{width:14px!important;height:14px!important;border-width:2px!important;flex:0 0 14px!important}
#adminApp>header .wrap{flex-wrap:nowrap!important;gap:5px!important}
.header-undo-button,.header-refresh-button{flex:0 0 auto!important;width:auto!important;min-width:0!important;min-height:32px!important;height:32px!important;padding:0 7px!important;font-size:9px!important;line-height:1!important;white-space:nowrap!important}
.mobile-quick-bar{gap:5px!important}.mobile-assign-button{flex:0 0 auto!important;width:auto!important;min-width:0!important;padding:0 9px!important;font-size:10px!important;white-space:nowrap!important}.mobile-undo-button,.mobile-refresh-button{flex:0 0 auto!important;width:auto!important;min-width:0!important;padding:0 7px!important;font-size:9px!important;white-space:nowrap!important}
#adminApp [data-member-id] .member-game-count{display:inline-flex!important;flex:0 0 auto!important;opacity:1!important;visibility:visible!important;white-space:nowrap!important;font-size:10px!important;line-height:1.1!important;margin-left:4px!important}
#adminApp [data-member-id] .name{min-width:0!important;overflow:hidden!important;text-overflow:ellipsis!important;white-space:nowrap!important}
#adminApp [data-member-id] .name:has(.member-new-inline){overflow:visible!important;text-overflow:clip!important;white-space:normal!important}
#adminApp .member-new-inline{display:inline-block!important;margin-left:3px!important;padding:0 2px!important;border-radius:3px!important;background:#f5f3ff!important;color:#7c3aed!important;font-size:6px!important;font-weight:900!important;line-height:9px!important;height:9px!important;vertical-align:middle!important;white-space:nowrap!important}
'''
# Remove prior V3 css marker block only by appending V4 later; later CSS wins.
if marker not in css:
    css=css.rstrip()+css_patch
style.write_text(css,encoding='utf-8')

script_text=script.read_text(encoding='utf-8')
for needle in [marker,'member.isNew === true','member-game-count','requestAnimationFrame(decorateAll)',direct_expr]:
    if needle not in script_text: raise SystemExit(f'missing {needle!r} in Script.html')
for needle in [marker,'.mobile-assign-button','.member-game-count','.admin-saving-overlay.show']:
    if needle not in style.read_text(encoding='utf-8'): raise SystemExit(f'missing {needle!r} in Style.html')
print('ADMIN_COMPACT_FAST_V4_OK')
