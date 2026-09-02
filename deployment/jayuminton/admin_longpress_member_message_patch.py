#!/usr/bin/env python3
"""Add a "메시지 보내기" (send message) button to the long-press member action bar
(#quickMoveBar), which pops up when long-pressing ANY member card anywhere in the
admin screen (active roster, quick roster, excluded roster, court/wait cards, ...) --
they all already share the same memberLongPressAttributes()/MEMBER_ACTION_IDS wiring.

Operates on the fully-built admin index.html (same file build-admin-native-session-fix.yml
extracts from the latest release APK)."""
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
html = path.read_text(encoding='utf-8')

MARKER = 'jmLongPressMemberMessageV1'
if MARKER in html:
    print('ADMIN_LONGPRESS_MEMBER_MESSAGE_ALREADY_OK')
    raise SystemExit(0)

OLD_BAR = (
    '  <div id="quickMoveBar" class="quick-move-bar hidden" aria-label="길게 누른 멤버 관리">\n'
    '    <button type="button" onclick="setLongPressedMemberStatus(\'active\')">코트배정</button>\n'
    '    <button type="button" onclick="setLongPressedMemberStatus(\'before\')">도착전</button>\n'
    '    <button type="button" onclick="setLongPressedMemberStatus(\'rest\')">휴식</button>\n'
    '    <button type="button" onclick="setLongPressedMemberStatus(\'away\')">귀가</button>\n'
    '    <button type="button" onclick="startMemberEdit()">편집</button>\n'
    '    <button type="button" class="danger" onclick="deleteLongPressedMembers()">삭제</button>\n'
    '    <button type="button" class="ghost-button" onclick="closeMemberActionBar()">취소</button>\n'
    '  </div>'
)
NEW_BAR = (
    '  <div id="quickMoveBar" class="quick-move-bar hidden" aria-label="길게 누른 멤버 관리">\n'
    '    <button type="button" onclick="setLongPressedMemberStatus(\'active\')">코트배정</button>\n'
    '    <button type="button" onclick="setLongPressedMemberStatus(\'before\')">도착전</button>\n'
    '    <button type="button" onclick="setLongPressedMemberStatus(\'rest\')">휴식</button>\n'
    '    <button type="button" onclick="setLongPressedMemberStatus(\'away\')">귀가</button>\n'
    '    <button type="button" onclick="openMemberActionMessage()">메시지 보내기</button>\n'
    '    <button type="button" onclick="startMemberEdit()">편집</button>\n'
    '    <button type="button" class="danger" onclick="deleteLongPressedMembers()">삭제</button>\n'
    '    <button type="button" class="ghost-button" onclick="closeMemberActionBar()">취소</button>\n'
    '  </div>'
)
if html.count(OLD_BAR) != 1:
    raise SystemExit(f'expected exactly one quickMoveBar match, found {html.count(OLD_BAR)}')
html = html.replace(OLD_BAR, NEW_BAR, 1)

OLD_FN = '''function deleteLongPressedMembers() {
  const ids = (typeof MEMBER_ACTION_IDS !== 'undefined' ? MEMBER_ACTION_IDS : []).map(String).filter(Boolean);
  if (!ids.length) return;
  if (!window.confirm('선택한 멤버를 삭제하시겠습니까?')) return;
  closeMemberActionBar();
  return runAction('deleteMembers', [ADMIN_PIN_VALUE, ids]);
}'''
if html.count(OLD_FN) != 1:
    raise SystemExit('deleteLongPressedMembers anchor not found or not unique')

NEW_FN = OLD_FN + '''

/* %s: 길게 눌러 뜨는 멤버 액션바에서 바로 메시지를 보낸다. 이미 있는
   회원카드 선택(SELECTED) 기반 메시지 모달(openQuickMemberMessage)을 그대로
   재사용하기 위해, 길게 누른 멤버 id로 SELECTED를 채운 뒤 그 모달을 연다. */
function openMemberActionMessage() {
  const ids = (typeof MEMBER_ACTION_IDS !== 'undefined' ? MEMBER_ACTION_IDS : []).map(String).filter(Boolean);
  if (!ids.length) {
    alert('메시지를 보낼 멤버를 길게 눌러 주세요.');
    return;
  }
  closeMemberActionBar();
  try {
    SELECTED.clear();
    ids.forEach(function(id) { SELECTED.add(String(id)); });
  } catch (error) {}
  if (typeof window.openQuickMemberMessage === 'function') {
    window.openQuickMemberMessage();
  } else {
    alert('메시지 기능을 찾을 수 없습니다.');
  }
}''' % MARKER

html = html.replace(OLD_FN, NEW_FN, 1)

if MARKER not in html:
    raise SystemExit('marker missing after patch (should be unreachable)')
if html.count('onclick="openMemberActionMessage()"') != 1:
    raise SystemExit('new button wiring must exist exactly once')

path.write_text(html, encoding='utf-8')
print('ADMIN_LONGPRESS_MEMBER_MESSAGE_OK')
