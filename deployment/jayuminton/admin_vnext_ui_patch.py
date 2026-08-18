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

# Rename all visible smart-assignment labels; behavior stays on smartAssignSelected().
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
    <button class="primary mobile-assign-button" onclick="smartAssignSelected()">위치 자동배정</button>
  </div>''','''  <div class="mobile-quick-bar admin-vnext-bottom-bar">
    <span id="mobileSelectedCount">0명 선택</span>
    <button id="mobileUndoButton" class="ghost-button undo-button mobile-undo-button" onclick="undoLastAction()" disabled>↶ 실행 취소</button>
    <button class="ghost-button mobile-refresh-button" type="button" onclick="loadState()">↻ 새로고침</button>
    <button class="primary mobile-assign-button" onclick="smartAssignSelected()">자동배정</button>
  </div>''','bottom bar')

p.write_text(s,encoding='utf-8')
print('admin vNext UI patch prepared')
