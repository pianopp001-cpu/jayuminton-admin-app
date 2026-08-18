#!/usr/bin/env python3
"""Patch admin-only UI. Does not modify Index/user frontend."""
from pathlib import Path
import sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('source-snapshot/current-main')
p=root/'Admin.html'; s=p.read_text(encoding='utf-8')

def rep(a,b,label):
 global s
 if a not in s: raise SystemExit(label+' anchor not found')
 s=s.replace(a,b,1)

rep('''      <input
        id="newExperience"
        maxlength="20"
        placeholder="구력(선택, 예: 3년)"
      >

      <button''','''      <input
        id="newExperience"
        maxlength="20"
        placeholder="구력(선택, 예: 3년)"
      >

      <input id="newPublicMemo" maxlength="40" placeholder="메모(선택, 생일·특이사항 등)">
      <label class="member-flag-check"><input id="newIsNew" type="checkbox"> 신규</label>
      <label class="member-flag-check"><input id="newIsSponsor" type="checkbox"> 🎁 찬조</label>

      <button''','member fields')

s=s.replace('<button onclick="decreaseSelectedGames()">게임횟수 -1</button>', '<button onclick="decreaseSelectedGames()">게임횟수 -1</button>\n      <button onclick="increaseSelectedGames()">게임횟수 +1</button>')
s=s.replace('''        <button onclick="decreaseSelectedGames()">
          게임횟수 -1
        </button>''','''        <button onclick="decreaseSelectedGames()">
          게임횟수 -1
        </button>
        <button onclick="increaseSelectedGames()">
          게임횟수 +1
        </button>''')
rep('''      <button onclick="setSelectedStatus('away')">귀가</button>
      <button onclick="decreaseSelectedGames()">게임횟수 -1</button>''','''      <button onclick="setSelectedStatus('away')">귀가</button>
      <button onclick="setSelectedBundle()">🔗 묶음 지정</button>
      <button onclick="clearSelectedBundle()">묶음 해제</button>
      <button onclick="decreaseSelectedGames()">게임횟수 -1</button>''','bundle buttons')

s=s.replace('선택 위치 자동배정', '자동배정')
s=s.replace('>위치 자동배정</button>', '>자동배정</button>')

rep('''  <div class="mobile-quick-bar">
    <span id="mobileSelectedCount">0명 선택</span>
    <button
      id="mobileUndoButton"
      class="ghost-button undo-button mobile-undo-button"
      onclick="undoLastAction()"
      disabled
    >↶ 실행 취소</button>
    <button class="primary mobile-assign-button" onclick="smartAssignSelected()">자동배정</button>
  </div>''','''  <div class="mobile-quick-bar admin-vnext-bottom-bar">
    <span id="mobileSelectedCount">0명 선택</span>
    <button id="mobileUndoButton" class="ghost-button undo-button mobile-undo-button" onclick="undoLastAction()" disabled>↶ 실행 취소</button>
    <button class="ghost-button mobile-refresh-button" type="button" onclick="loadState()">↻ 새로고침</button>
    <button class="primary mobile-assign-button" onclick="smartAssignSelected()">자동배정</button>
  </div>''','bottom bar')

# Requested proportions: keep Undo large; refresh is half the width of Auto; all three stay one row.
style='''
<style id="adminVnextBottomBarStyle">
  .admin-vnext-bottom-bar{display:grid!important;grid-template-columns:minmax(112px,1.15fr) minmax(58px,.5fr) minmax(116px,1fr);gap:8px;align-items:stretch}
  .admin-vnext-bottom-bar #mobileSelectedCount{grid-column:1/-1;font-size:12px;line-height:14px;min-height:14px}
  .admin-vnext-bottom-bar button{min-height:48px!important;margin:0!important;padding:8px 6px!important;font-size:15px!important;font-weight:800!important;white-space:nowrap}
  .admin-vnext-bottom-bar .mobile-refresh-button{font-size:13px!important}
  @media (max-width:380px){.admin-vnext-bottom-bar{grid-template-columns:minmax(100px,1.1fr) minmax(52px,.5fr) minmax(104px,1fr);gap:5px}.admin-vnext-bottom-bar button{font-size:13px!important;padding:7px 3px!important}}
</style>
'''
if '</body>' not in s: raise SystemExit('body end anchor not found')
s=s.replace('</body>',style+'\n</body>',1)

p.write_text(s,encoding='utf-8')
print('admin vNext UI patch prepared')
