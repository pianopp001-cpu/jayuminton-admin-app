#!/usr/bin/env python3
"""1) Relabel + enlarge the per-court 경기종료(finish game) button: instead of a separate
"N번코트 경기종료" line stacked above a button that just says "경기 종료" (redundant --
"경기종료" appeared twice), fold the court number directly into the button's own label
("1코트 종료", "3코트 종료", ...) and make the button itself much bigger/easier to tap.
2) Make finishCourt() apply its (fully deterministic) state change to the court/wait
groups optimistically, the same way manual assign/move/swap already do, instead of
waiting for the full server round trip before the court visually clears.

Operates on the fully-built admin index.html (same file build-admin-native-session-fix.yml
extracts from the latest release APK)."""
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
html = path.read_text(encoding='utf-8')

MARKER = 'jmFinishCourtBigButtonAndOptimisticV2'
if MARKER in html:
    print('ADMIN_FINISH_COURT_SPEED_ALREADY_OK')
    raise SystemExit(0)

OLD_MARKER = 'jmFinishCourtBigButtonAndOptimisticV1'
if OLD_MARKER in html:
    raise SystemExit('old jmFinishCourtBigButtonAndOptimisticV1 marker present -- base HTML already has the V1 button, refusing to double-patch')

# 1) Court card buttons: split "선택 인원 넣기" and "경기 종료" into their own rows, and
# fold the court number straight into the (now much bigger) finish button's own text --
# "1코트 종료" instead of a separate "1번코트 경기종료" label sitting above a button that
# repeats "경기 종료" again.
OLD_BUTTONS = (
    "const buttons =\n"
    "          IS_ADMIN\n"
    "            ? (\n"
    "              '<div class=\"toolbar section\">' +\n"
    "              '<button class=\"primary\" ' +\n"
    "              'onclick=\"putSelectedIntoCourt(' +\n"
    "              courtNo +\n"
    "              ')\">' +\n"
    "              '선택 인원 넣기' +\n"
    "              '</button>' +\n"
    "              '<button onclick=\"finishCourt(' +\n"
    "              courtNo +\n"
    "              ')\">' +\n"
    "              '경기 종료' +\n"
    "              '</button>' +\n"
    "              '</div>'\n"
    "            )\n"
    "            : '';"
)
NEW_BUTTONS = (
    "const buttons =\n"
    "          IS_ADMIN\n"
    "            ? (\n"
    "              '<div class=\"toolbar section\">' +\n"
    "              '<button class=\"primary\" ' +\n"
    "              'onclick=\"putSelectedIntoCourt(' +\n"
    "              courtNo +\n"
    "              ')\">' +\n"
    "              '선택 인원 넣기' +\n"
    "              '</button>' +\n"
    "              '</div>' +\n"
    "              '<div class=\"finish-court-block\">' +\n"
    "              '<button class=\"finish-court-button\" onclick=\"finishCourt(' +\n"
    "              courtNo +\n"
    "              ')\">' +\n"
    "              courtNo +\n"
    "              '코트 종료' +\n"
    "              '</button>' +\n"
    "              '</div>'\n"
    "            )\n"
    "            : '';"
)
if html.count(OLD_BUTTONS) != 1:
    raise SystemExit(f'expected exactly one court buttons match, found {html.count(OLD_BUTTONS)}')
html = html.replace(OLD_BUTTONS, NEW_BUTTONS, 1)

# 2) CSS for the big button, injected before </head>.
STYLE = (
    '\n<style id="jmFinishCourtBigButtonStyle">\n'
    '/* ' + MARKER + ' */\n'
    '.finish-court-block{margin-top:8px}\n'
    '.finish-court-button{display:block!important;width:100%!important;min-height:56px!important;'
    'font-size:18px!important;font-weight:900!important;border-radius:12px!important;'
    'padding:10px 12px!important;white-space:nowrap!important;overflow:hidden!important;'
    'text-overflow:ellipsis!important;box-sizing:border-box!important;text-align:center!important}\n'
    '</style>\n'
)
if html.count('</head>') != 1:
    raise SystemExit('</head> anchor not found or not unique')
html = html.replace('</head>', STYLE + '</head>', 1)

# 3) Optimistic finishCourt(): apply the (deterministic) court/wait promotion locally
# first, same pattern as quickWholeGroupSwap/batchAssignToTarget/quickMoveOrSwap, and
# roll back on failure like those do.
OLD_FINISH = """async function finishCourt(courtNo) {
  const previousState =
    JSON.parse(JSON.stringify(STATE));
  const waitingMembers =
    (STATE.waitGroups[0] || [])
      .map(memberById)
      .filter(Boolean);
  let voiceStarted = false;

  if (
    VOICE_GUIDE_ENABLED &&
    'speechSynthesis' in window &&
    Array.isArray(STATE.courts[courtNo])
  ) {
    playCourtFinishVoice(
      Number(courtNo),
      waitingMembers
    );
    voiceStarted = true;
  }

  try {
    const state = await server(
      'finishCourt',
      [
        ADMIN_PIN_VALUE,
        courtNo
      ]
    );

    SELECTED.clear();
    renderState(state);
    setUndoState(previousState);
    rememberVoiceAnnouncement(
      Number(courtNo),
      waitingMembers
    );
  } catch (error) {
    if (voiceStarted) {
      window.speechSynthesis.cancel();
      VOICE_UTTERANCES = [];
      restorePageMediaVolume();
    }
    alert(error.message || error);
  }
}"""

if html.count(OLD_FINISH) != 1:
    raise SystemExit('finishCourt() anchor not found or not unique -- source has drifted')

NEW_FINISH = OLD_FINISH.replace(
    "async function finishCourt(courtNo) {",
    "/* %s: mirrors the server's finishCourtMutation exactly (wait1 -> court,\n"
    "   wait2..5 shift up, new empty wait5, +1 game for entrants) so the court can\n"
    "   clear the instant the button is tapped instead of after a full round trip. */\n"
    "function applyFinishCourtLocally(courtNo) {\n"
    "  const no = String(courtNo);\n"
    "  const entrants = (STATE.waitGroups[0] || []).slice();\n"
    "  STATE.courts[no] = entrants;\n"
    "  STATE.courtStartedAt[no] = entrants.length ? new Date().toISOString() : '';\n"
    "  STATE.waitGroups = [\n"
    "    (STATE.waitGroups[1] || []).slice(),\n"
    "    (STATE.waitGroups[2] || []).slice(),\n"
    "    (STATE.waitGroups[3] || []).slice(),\n"
    "    (STATE.waitGroups[4] || []).slice(),\n"
    "    []\n"
    "  ];\n"
    "\n"
    "  const entering = new Set(entrants);\n"
    "  const playing = new Set();\n"
    "  const waiting = new Set();\n"
    "  Object.keys(STATE.courts).forEach(function(key) {\n"
    "    (STATE.courts[key] || []).forEach(function(id) { playing.add(id); });\n"
    "  });\n"
    "  STATE.waitGroups.forEach(function(group) {\n"
    "    (group || []).forEach(function(id) { waiting.add(id); });\n"
    "  });\n"
    "  STATE.members.forEach(function(member) {\n"
    "    if (entering.has(member.id)) {\n"
    "      member.games = Math.max(0, (Number(member.games) || 0) + 1);\n"
    "    }\n"
    "    if (playing.has(member.id)) member.status = 'playing';\n"
    "    else if (waiting.has(member.id)) member.status = 'waiting';\n"
    "    else if (['before', 'rest', 'away'].indexOf(String(member.status)) < 0) member.status = 'active';\n"
    "  });\n"
    "}\n"
    "\n"
    "async function finishCourt(courtNo) {" % MARKER,
    1,
).replace(
    "  try {\n"
    "    const state = await server(\n"
    "      'finishCourt',\n"
    "      [\n"
    "        ADMIN_PIN_VALUE,\n"
    "        courtNo\n"
    "      ]\n"
    "    );\n"
    "\n"
    "    SELECTED.clear();\n"
    "    renderState(state);\n"
    "    setUndoState(previousState);\n"
    "    rememberVoiceAnnouncement(\n"
    "      Number(courtNo),\n"
    "      waitingMembers\n"
    "    );\n"
    "  } catch (error) {\n"
    "    if (voiceStarted) {\n"
    "      window.speechSynthesis.cancel();\n"
    "      VOICE_UTTERANCES = [];\n"
    "      restorePageMediaVolume();\n"
    "    }\n"
    "    alert(error.message || error);\n"
    "  }\n"
    "}",
    "  try {\n"
    "    applyFinishCourtLocally(courtNo);\n"
    "    renderState();\n"
    "\n"
    "    const state = await server(\n"
    "      'finishCourt',\n"
    "      [\n"
    "        ADMIN_PIN_VALUE,\n"
    "        courtNo\n"
    "      ]\n"
    "    );\n"
    "\n"
    "    SELECTED.clear();\n"
    "    renderState(state);\n"
    "    setUndoState(previousState);\n"
    "    rememberVoiceAnnouncement(\n"
    "      Number(courtNo),\n"
    "      waitingMembers\n"
    "    );\n"
    "  } catch (error) {\n"
    "    STATE = previousState;\n"
    "    renderState();\n"
    "    if (voiceStarted) {\n"
    "      window.speechSynthesis.cancel();\n"
    "      VOICE_UTTERANCES = [];\n"
    "      restorePageMediaVolume();\n"
    "    }\n"
    "    alert(error.message || error);\n"
    "  }\n"
    "}",
    1,
)

if OLD_FINISH == NEW_FINISH:
    raise SystemExit('finishCourt() replacement did not change anything -- patch logic bug')

html = html.replace(OLD_FINISH, NEW_FINISH, 1)

if MARKER not in html:
    raise SystemExit('marker missing after patch (should be unreachable)')
if html.count('function applyFinishCourtLocally(') != 1:
    raise SystemExit('applyFinishCourtLocally must exist exactly once')
if html.count('class="finish-court-button"') != 1:
    raise SystemExit('finish-court-button template must exist exactly once (it renders per court at runtime)')

path.write_text(html, encoding='utf-8')
print('ADMIN_FINISH_COURT_SPEED_OK')
