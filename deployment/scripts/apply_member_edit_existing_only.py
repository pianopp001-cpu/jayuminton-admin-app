from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")


def replace_function(src: str, name: str, replacement: str):
    token = "function " + name + "("
    start = src.find(token)
    if start < 0:
        return src, False
    brace = src.find("{", start)
    if brace < 0:
        raise RuntimeError(f"opening brace missing for {name}")
    depth = 0
    quote = None
    escape = False
    i = brace
    while i < len(src):
        ch = src[i]
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"', "`"):
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[:start] + replacement + src[i + 1 :], True
        i += 1
    raise RuntimeError(f"unbalanced function {name}")


def function_span(src: str, name: str):
    token = "function " + name + "("
    start = src.find(token)
    if start < 0:
        return None
    brace = src.find("{", start)
    if brace < 0:
        return None
    depth = 0
    quote = None
    escape = False
    i = brace
    while i < len(src):
        ch = src[i]
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"', "`"):
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
        i += 1
    return None


# ---------------- Admin.html ----------------
p = root / "Admin.html"
a = p.read_text(encoding="utf-8")
quick = re.compile(r'<div id="quickMoveBar" class="quick-move-bar hidden"[^>]*>.*?</div>', re.S)
quick_html = '''<div id="quickMoveBar" class="quick-move-bar hidden" aria-label="길게 누른 멤버 관리">
    <button type="button" onclick="sendQuickPickToActive()">배정대기로</button>
    <button type="button" class="danger" onclick="deleteQuickPickedMembers()">삭제</button>
    <button type="button" class="ghost-button" onclick="closeMemberActionBar()">취소</button>
    <button type="button" class="primary" onclick="startMemberEdit()">편집</button>
  </div>'''
if quick.search(a):
    a = quick.sub(quick_html, a, count=1)
else:
    raise RuntimeError("quickMoveBar not found")

# If an edit modal already exists, convert it to Cancel/Edit only.
a = a.replace('id="saveMemberEditButton"', 'id="applyMemberEditButton"')
a = a.replace('onclick="saveMemberEdit()"', 'onclick="applyMemberEdit()"')
a = a.replace('>수정 저장</button>', '>수정</button>')

if 'id="memberEditModal"' not in a:
    modal = '''
  <!-- JAYUMINTON_MEMBER_EDIT_MODAL_EXISTING_ONLY -->
  <div id="memberEditModal" class="modal-backdrop hidden" onclick="if(event.target===this) closeMemberEdit()">
    <div class="modal-card member-edit-modal-card" role="dialog" aria-modal="true" aria-labelledby="memberEditTitle">
      <div class="modal-head">
        <div>
          <span class="eyebrow dark-eyebrow">MEMBER EDIT</span>
          <h2 id="memberEditTitle">멤버 편집</h2>
        </div>
        <button type="button" class="modal-close" onclick="closeMemberEdit()">×</button>
      </div>
      <div class="member-edit-form">
        <label>이름 또는 닉네임<input id="editMemberName" maxlength="20" autocomplete="off"></label>
        <label>성별<select id="editMemberGender"><option value="male">남자</option><option value="female">여자</option></select></label>
        <label>급수<input id="editMemberGrade" maxlength="12" autocomplete="off"></label>
        <label>구력<input id="editMemberExperience" maxlength="20" autocomplete="off"></label>
      </div>
      <div class="member-edit-actions">
        <button type="button" class="ghost-button" onclick="closeMemberEdit()">취소</button>
        <button id="applyMemberEditButton" type="button" class="primary" onclick="applyMemberEdit()">수정</button>
      </div>
    </div>
  </div>
'''
    m = re.search(r'<div\s+id="wholeSwapBar"|<div id="wholeSwapBar"', a)
    if not m:
        raise RuntimeError("wholeSwapBar anchor not found")
    a = a[: m.start()] + modal + a[m.start() :]

# Final hard normalization: no '수정 저장' wording in admin edit UI.
a = a.replace('수정 저장', '수정')
p.write_text(a, encoding="utf-8")


# ---------------- Style.html ----------------
p = root / "Style.html"
css = p.read_text(encoding="utf-8")
marker = "JAYUMINTON_MEMBER_EDIT_EXISTING_ONLY_STYLE"
if marker not in css:
    css += r'''

/* JAYUMINTON_MEMBER_EDIT_EXISTING_ONLY_STYLE */
#adminApp .quick-move-bar{
  display:flex!important;
  flex-wrap:nowrap!important;
  align-items:center!important;
  gap:4px!important;
  width:min(520px,calc(100% - 10px))!important;
  padding:5px!important;
  left:50%!important;
  transform:translateX(-50%)!important;
}
#adminApp .quick-move-bar.hidden{display:none!important}
#adminApp .quick-move-bar button{
  flex:1 1 0!important;
  min-width:0!important;
  width:auto!important;
  height:36px!important;
  min-height:36px!important;
  padding:0 3px!important;
  font-size:10px!important;
  line-height:1!important;
  white-space:nowrap!important;
}
.member-edit-modal-card{width:min(440px,calc(100% - 22px))!important}
.member-edit-form{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px}
.member-edit-form label{display:flex;flex-direction:column;gap:6px;font-size:12px;font-weight:900}
.member-edit-form input,.member-edit-form select{width:100%;min-width:0}
.member-edit-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:14px}
.member-edit-actions button{min-width:110px}
@media(max-width:460px){
  #adminApp .quick-move-bar{width:calc(100% - 6px)!important;gap:2px!important;padding:4px!important}
  #adminApp .quick-move-bar button{font-size:9px!important;padding:0 1px!important}
  .member-edit-form{grid-template-columns:1fr}
}
'''
p.write_text(css, encoding="utf-8")


# ---------------- Script.html ----------------
p = root / "Script.html"
s = p.read_text(encoding="utf-8")
closing = s.rfind("</script>")
if closing < 0:
    raise RuntimeError("Script.html closing tag missing")
s = s[: closing + len("</script>")] + "\n"

# User mode never receives the admin long-press handlers.
member_attrs = '''function memberLongPressAttributes(memberId) {
  if (!IS_ADMIN) return '';
  return (
    ' onpointerdown="startMemberLongPress(\\'' + memberId + '\\',event)"' +
    ' onpointermove="moveMemberLongPress(event)"' +
    ' onpointerup="finishMemberLongPress()"' +
    ' onpointercancel="finishMemberLongPress()"' +
    ' oncontextmenu="event.preventDefault()"'
  );
}'''
s, ok = replace_function(s, "memberLongPressAttributes", member_attrs)
if not ok:
    raise RuntimeError("memberLongPressAttributes missing")

sig = "function startMemberLongPress(memberId, event) {"
pos = s.find(sig)
if pos < 0:
    raise RuntimeError("startMemberLongPress missing")
after = pos + len(sig)
if "if (!IS_ADMIN) return;" not in s[after : after + 180]:
    s = s[:after] + "\n  if (!IS_ADMIN) return;" + s[after:]

if "let EDIT_MEMBER_ID" not in s:
    anchor = "let MEMBER_ACTION_IDS = [];"
    if anchor not in s:
        raise RuntimeError("MEMBER_ACTION_IDS missing")
    s = s.replace(anchor, anchor + "\nlet EDIT_MEMBER_ID = '';", 1)

start_edit = '''function startMemberEdit() {
  if (!IS_ADMIN) return;
  if (MEMBER_ACTION_IDS.length !== 1) {
    alert('편집할 멤버 한 명을 길게 눌러 주세요.');
    return;
  }
  const member = memberById(MEMBER_ACTION_IDS[0]);
  if (!member) {
    alert('멤버 정보를 찾을 수 없습니다.');
    return;
  }
  EDIT_MEMBER_ID = String(member.id || '');
  const name = document.getElementById('editMemberName');
  const gender = document.getElementById('editMemberGender');
  const grade = document.getElementById('editMemberGrade');
  const experience = document.getElementById('editMemberExperience');
  const modal = document.getElementById('memberEditModal');
  if (!name || !gender || !grade || !experience || !modal) {
    alert('편집 화면을 불러오지 못했습니다. 앱을 완전히 종료한 뒤 다시 실행해 주세요.');
    return;
  }
  name.value = String(member.name || '');
  gender.value = member.gender === 'female' ? 'female' : 'male';
  grade.value = String(member.grade || '');
  experience.value = String(member.experience || '');
  closeMemberActionBar();
  modal.classList.remove('hidden');
  setTimeout(function(){ name.focus(); name.select(); }, 80);
}'''
s, ok = replace_function(s, "startMemberEdit", start_edit)
if not ok:
    anchor = "async function addMember() {"
    if anchor not in s:
        raise RuntimeError("addMember anchor missing")
    s = s.replace(anchor, start_edit + "\n\n" + anchor, 1)

close_edit = '''function closeMemberEdit() {
  EDIT_MEMBER_ID = '';
  const modal = document.getElementById('memberEditModal');
  if (modal) modal.classList.add('hidden');
  const button = document.getElementById('applyMemberEditButton');
  if (button) {
    button.disabled = false;
    button.textContent = '수정';
  }
}'''
s, ok = replace_function(s, "closeMemberEdit", close_edit)
if not ok:
    anchor = "async function addMember() {"
    pos = s.find(anchor)
    if pos < 0:
        raise RuntimeError("addMember anchor missing for closeMemberEdit")
    s = s[:pos] + close_edit + "\n\n" + s[pos:]

apply_edit = '''async function applyMemberEdit() {
  if (!IS_ADMIN || !EDIT_MEMBER_ID || ACTION_IN_FLIGHT) return;
  const targetId = String(EDIT_MEMBER_ID);
  const name = String(document.getElementById('editMemberName')?.value || '').trim();
  const gender = String(document.getElementById('editMemberGender')?.value || '').trim();
  const grade = String(document.getElementById('editMemberGrade')?.value || '').trim();
  const experience = String(document.getElementById('editMemberExperience')?.value || '').trim();
  if (!name) {
    alert('이름 또는 닉네임을 입력하세요.');
    return;
  }
  if (gender !== 'male' && gender !== 'female') {
    alert('성별을 선택하세요.');
    return;
  }
  const button = document.getElementById('applyMemberEditButton');
  ACTION_IN_FLIGHT = true;
  if (button) {
    button.disabled = true;
    button.textContent = '수정 중…';
  }
  try {
    const state = await server('updateMemberProfile', [ADMIN_PIN_VALUE, targetId, name, gender, grade, experience]);
    const modal = document.getElementById('memberEditModal');
    if (modal) modal.classList.add('hidden');
    EDIT_MEMBER_ID = '';
    renderState(state);
  } catch (error) {
    alert(String((error && error.message) || error || '멤버 수정에 실패했습니다.'));
  } finally {
    ACTION_IN_FLIGHT = false;
    if (button) {
      button.disabled = false;
      button.textContent = '수정';
    }
  }
}'''
s, ok = replace_function(s, "applyMemberEdit", apply_edit)
if not ok:
    anchor = "async function addMember() {"
    pos = s.find(anchor)
    if pos < 0:
        raise RuntimeError("addMember anchor missing for applyMemberEdit")
    s = s[:pos] + apply_edit + "\n\n" + s[pos:]

# Any legacy edit-save entrypoint becomes an alias to the real update operation.
if "function saveMemberEdit(" in s:
    s, _ = replace_function(s, "saveMemberEdit", "function saveMemberEdit() { return applyMemberEdit(); }")

# New-member registration must never branch into edit/update logic.
span = function_span(s, "addMember")
if not span:
    raise RuntimeError("addMember function missing")
start, end = span
add_fn = s[start:end]
add_fn = re.sub(
    r"\s*if\s*\(\s*EDIT_MEMBER_ID\s*\)\s*\{\s*(?:await\s+)?(?:saveMemberEdit|applyMemberEdit)\(\)\s*;?\s*return\s*;?\s*\}",
    "",
    add_fn,
    flags=re.S,
)
add_fn = re.sub(
    r"\s*if\s*\(\s*EDIT_MEMBER_ID\s*\)\s*return\s+(?:saveMemberEdit|applyMemberEdit)\(\)\s*;?",
    "",
    add_fn,
    flags=re.S,
)
s = s[:start] + add_fn + s[end:]

p.write_text(s, encoding="utf-8")


# ---------------- Code.js ----------------
p = root / "Code.js"
c = p.read_text(encoding="utf-8")
server_fn = '''function updateMemberProfile(pin, memberId, name, gender, grade, experience) {
  auth_(pin);
  return withDocumentLock_('멤버 수정', function() {
    memberId = String(memberId == null ? '' : memberId).trim();
    name = String(name == null ? '' : name).trim();
    gender = String(gender == null ? '' : gender).trim();
    grade = String(grade == null ? '' : grade).trim();
    experience = String(experience == null ? '' : experience).trim();

    if (!memberId) throw new Error('수정할 멤버가 없습니다.');
    if (!name) throw new Error('이름 또는 닉네임을 입력하세요.');
    if (name.length > 20) throw new Error('이름은 20자 이내로 입력하세요.');
    if (gender !== 'male' && gender !== 'female') throw new Error('성별을 선택하세요.');
    if (grade.length > 12) throw new Error('급수는 12자 이내로 입력하세요.');
    if (experience.length > 20) throw new Error('구력은 20자 이내로 입력하세요.');

    const members = readMembers_();
    const index = members.findIndex(function(item) {
      return String(item.id) === memberId;
    });
    if (index < 0) throw new Error('수정할 기존 멤버를 찾을 수 없습니다.');

    const duplicate = members.some(function(item, itemIndex) {
      return itemIndex !== index && String(item.name || '').trim() === name;
    });
    if (duplicate) throw new Error('같은 이름의 멤버가 이미 있습니다.');

    // Existing-member-only update: preserve id, game count, status and placement.
    members[index].name = name;
    members[index].gender = gender;
    members[index].grade = grade;
    members[index].experience = experience;

    writeMembers_(members);
    if (typeof touch_ === 'function') touch_();
    return getPublicState();
  });
}'''
c, ok = replace_function(c, "updateMemberProfile", server_fn)
if not ok:
    pos = c.find("function addMember(")
    if pos < 0:
        raise RuntimeError("Code.js addMember anchor missing")
    c = c[:pos] + server_fn + "\n\n" + c[pos:]
p.write_text(c, encoding="utf-8")


# ---------------- hard validation ----------------
admin = (root / "Admin.html").read_text(encoding="utf-8")
script = (root / "Script.html").read_text(encoding="utf-8")
code = (root / "Code.js").read_text(encoding="utf-8")
style = (root / "Style.html").read_text(encoding="utf-8")

required_admin = [
    '>배정대기로</button>',
    '>삭제</button>',
    '>취소</button>',
    '>편집</button>',
    'id="applyMemberEditButton"',
    'onclick="applyMemberEdit()">수정</button>',
]
for item in required_admin:
    if item not in admin:
        raise RuntimeError(f"Admin validation missing: {item}")
if "수정 저장" in admin:
    raise RuntimeError("legacy edit-save wording remains")
if "function applyMemberEdit()" not in script:
    raise RuntimeError("applyMemberEdit missing")
if "server('updateMemberProfile'" not in script:
    raise RuntimeError("edit does not call updateMemberProfile")
if "if (!IS_ADMIN) return '';" not in script:
    raise RuntimeError("user long-press guard missing")
if "function updateMemberProfile(" not in code:
    raise RuntimeError("server updateMemberProfile missing")
if "members[index].name = name;" not in code:
    raise RuntimeError("existing member overwrite missing")
if marker not in style:
    raise RuntimeError("one-line action style missing")

print("Existing-member-only edit patch validated")
