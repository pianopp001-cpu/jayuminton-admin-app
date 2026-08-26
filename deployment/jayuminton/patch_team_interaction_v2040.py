from pathlib import Path

BRIDGE=Path('deployment/jayuminton/cloudflare_v6_frontend_bridge.js')
LAYOUT=Path('deployment/jayuminton/admin_team_layout_v2038.js')

b=BRIDGE.read_text()
a=LAYOUT.read_text()

# 1) Shared temporary pair rendering: only the two explicitly selected members get the one-game line.
old="""    loadTempPairs().forEach(function(group,index){\n      [[group.pairA,TEMP_PAIR_COLORS[(index*2)%TEMP_PAIR_COLORS.length]],[group.pairB,TEMP_PAIR_COLORS[(index*2+1)%TEMP_PAIR_COLORS.length]]].forEach(function(side){\n        Array.prototype.forEach.call(document.querySelectorAll(selector),function(card){var id=idOf(card);if(side[0].indexOf(id)>=0){card.classList.add('jm-temp-pair');if(card.style&&card.style.setProperty)card.style.setProperty('--jm-temp-pair-color',side[1]);}});\n      });\n    });"""
new="""    loadTempPairs().forEach(function(group,index){\n      var side=[group.pairA,TEMP_PAIR_COLORS[index%TEMP_PAIR_COLORS.length]];\n      Array.prototype.forEach.call(document.querySelectorAll(selector),function(card){var id=idOf(card);if(side[0].indexOf(id)>=0){card.classList.add('jm-temp-pair');if(card.style&&card.style.setProperty)card.style.setProperty('--jm-temp-pair-color',side[1]);}});\n    });"""
if old not in b: raise SystemExit('shared render anchor changed')
b=b.replace(old,new,1)

# 2) Shared style: keep official Team1/Team2 as a small bottom label instead of hiding it.
b=b.replace(".jm-team-bottom-label{display:none!important}", ".jm-team-bottom-label{display:block!important;visibility:visible!important;position:static!important;width:100%!important;margin:3px 0 0!important;padding:0!important;text-align:left!important;font-size:9px!important;font-weight:900!important;line-height:1.1!important;white-space:nowrap!important;pointer-events:none!important}")

# 3) Admin safety CSS: bottom official label visible, permanent team stays double-line, temporary pair overlays with solid outer line.
b=b.replace("#adminApp .jm-team-bottom-label{display:none!important;visibility:hidden!important;", "#adminApp .jm-team-bottom-label{display:block!important;visibility:visible!important;")

# 4) Move old official team text to one small bottom label (no right-side badge).
old="""          Array.prototype.forEach.call(card.querySelectorAll('.jm-team-bottom-label'),function(bottom){bottom.remove();});\n"""
new="""          var bottom=card.querySelector('.jm-team-bottom-label');\n          if(!bottom){bottom=document.createElement('small');bottom.className='jm-team-bottom-label';card.appendChild(bottom);}\n          bottom.textContent=teamText;\n          if(bottom.parentElement!==card||card.lastElementChild!==bottom)card.appendChild(bottom);\n"""
if old not in b: raise SystemExit('admin bottom-label anchor changed')
b=b.replace(old,new,1)

# 5) Admin temporary pair render: only pairA gets the one-game line; pairB is retained only for ordering/server validation.
old="""      loadTempPairs().forEach(function(group,index){\n        [[group.pairA,TEMP_PAIR_COLORS[(index*2)%TEMP_PAIR_COLORS.length]],[group.pairB,TEMP_PAIR_COLORS[(index*2+1)%TEMP_PAIR_COLORS.length]]].forEach(function(side){\n          side[0].forEach(function(id){\n            Array.prototype.forEach.call(app.querySelectorAll(cardSelector),function(el){var card=memberCard(el)||el;if(cardMemberId(card)===String(id)){card.classList.add('jm-temp-pair');card.style.setProperty('--jm-temp-pair-color',side[1]);}});\n          });\n        });\n      });"""
new="""      loadTempPairs().forEach(function(group,index){\n        var side=[group.pairA,TEMP_PAIR_COLORS[index%TEMP_PAIR_COLORS.length]];\n        side[0].forEach(function(id){\n          Array.prototype.forEach.call(app.querySelectorAll(cardSelector),function(el){var card=memberCard(el)||el;if(cardMemberId(card)===String(id)){card.classList.add('jm-temp-pair');card.style.setProperty('--jm-temp-pair-color',side[1]);}});\n        });\n      });"""
if old not in b: raise SystemExit('admin render anchor changed')
b=b.replace(old,new,1)

# 6) Same wait/court: second click asks whether this is one-game team setting or normal move/swap.
old="""      var first={id:pendingPair.id,card:pendingPair.card};recordTempPair(first,{id:id,card:card},group);\n"""
new="""      var first={id:pendingPair.id,card:pendingPair.card};\n      var makePair=window.confirm('같은 '+(group.zone==='court'?'코트':'대기번호')+' 안의 두 명입니다.\\n\\n확인 = 1회성 팀설정\\n취소 = 이동·교환');\n      if(makePair){\n        event.preventDefault();event.stopPropagation();if(event.stopImmediatePropagation)event.stopImmediatePropagation();\n        recordTempPair(first,{id:id,card:card},group);\n      }else{\n        pendingPair=null;renderTempPairs();\n      }\n"""
if old not in b: raise SystemExit('pair click anchor changed')
b=b.replace(old,new,1)

# 7) Admin layout: preserve/recreate small official label, never remove it.
a=a.replace(".team-label,.jm-team-bottom-label,span,small,label,b,strong,em,i", ".team-label,span,label,b,strong,em,i")
a=a.replace(".team-label,.jm-team-bottom-label,span,small,label,b,strong,em,i", ".team-label,span,label,b,strong,em,i")
old="""      for(var j=0;j<nodes.length;j++){\n        var node=nodes[j];\n        if(normalizeTeam((node.getAttribute&&node.getAttribute('data-team-label'))||node.textContent))node.remove();\n      }\n"""
new="""      for(var j=0;j<nodes.length;j++){\n        var node=nodes[j];\n        if(normalizeTeam((node.getAttribute&&node.getAttribute('data-team-label'))||node.textContent))node.remove();\n      }\n      if(team){\n        var bottom=card.querySelector('.jm-team-bottom-label');\n        if(!bottom){bottom=document.createElement('small');bottom.className='jm-team-bottom-label';card.appendChild(bottom);}\n        bottom.textContent=team;if(card.lastElementChild!==bottom)card.appendChild(bottom);\n      }\n"""
if old not in a: raise SystemExit('layout label preservation anchor changed')
a=a.replace(old,new,1)
a=a.replace("#adminApp .member-team-badge,#adminApp .jm-team-badge,#adminApp .team-badge,#adminApp .team-label,#adminApp .jm-team-bottom-label,#adminApp [data-team-label]{display:none!important;", "#adminApp .member-team-badge,#adminApp .jm-team-badge,#adminApp .team-badge,#adminApp .team-label,#adminApp [data-team-label]{display:none!important;")
# Add explicit bottom-label style before permanent team style.
a=a.replace("#adminApp .has-member-team{position:relative!important;", "#adminApp .jm-team-bottom-label{display:block!important;visibility:visible!important;position:static!important;width:100%!important;height:auto!important;margin:3px 0 0!important;padding:0!important;text-align:left!important;font-size:9px!important;font-weight:900!important;line-height:1.1!important;white-space:nowrap!important;color:var(--member-team-color)!important;pointer-events:none!important}#adminApp .has-member-team{position:relative!important;")

BRIDGE.write_text(b)
LAYOUT.write_text(a)
print('TEAM_INTERACTION_V2040_OK')
