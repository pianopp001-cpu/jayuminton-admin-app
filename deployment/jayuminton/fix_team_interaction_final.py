from pathlib import Path
p=Path('deployment/jayuminton/cloudflare_v6_frontend_bridge.js')
s=p.read_text()
visible='.jm-team-bottom-label{display:block!important;visibility:visible!important;position:static!important;width:100%!important;margin:3px 0 0!important;padding:0!important;text-align:left!important;font-size:9px!important;font-weight:900!important;line-height:1.1!important;white-space:nowrap!important;pointer-events:none!important}'
hidden='.jm-team-bottom-label{display:none!important;visibility:hidden!important;width:0!important;height:0!important;overflow:hidden!important}'
s=s.replace(visible,hidden)
old="""          var bottom=card.querySelector('.jm-team-bottom-label');
          if(!bottom){bottom=document.createElement('small');bottom.className='jm-team-bottom-label';card.appendChild(bottom);}
          bottom.textContent=teamText;
          if(bottom.parentElement!==card||card.lastElementChild!==bottom)card.appendChild(bottom);"""
new="""          Array.prototype.forEach.call(card.querySelectorAll('.jm-team-bottom-label'),function(bottom){bottom.remove();});"""
if old in s:s=s.replace(old,new)
if 'bottom.textContent=teamText' in s:raise SystemExit('team label creation remains')
if 'var pairA=[first.id,second.id],pairB=ids.filter' not in s:raise SystemExit('pair logic missing')
if '확인 = 1회성 팀설정' not in s or '취소 = 이동·교환' not in s:raise SystemExit('same-group choice missing')
if "var side=[group.pairA" not in s:raise SystemExit('selected-pair-only rendering missing')
# Always remove legacy visible team labels without touching the persistent two-line border.
anchor="    if(document.getElementById&&!document.getElementById('jayuminton-shared-temp-pair-style')){"
cleanup="""    Array.prototype.forEach.call(document.querySelectorAll('.jm-team-bottom-label,.member-team-badge,.jm-team-badge,.team-badge,.team-label,[data-team-label]'),function(node){
      var txt=String(node.textContent||((node.getAttribute&&node.getAttribute('data-team-label'))||'')).replace(/\\s+/g,'');
      if(/^팀\\d+$/.test(txt)||/^TEAM\\d+$/i.test(txt)){node.textContent='';if(node.style)node.style.setProperty('display','none','important');}
    });
"""
if cleanup not in s:
    if anchor not in s:raise SystemExit('renderer anchor missing')
    s=s.replace(anchor,cleanup+anchor,1)
p.write_text(s)
print('patched final team interaction')
