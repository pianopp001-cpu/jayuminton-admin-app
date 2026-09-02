#!/usr/bin/env python3
"""Allow whole-group swap between a court and a wait group (not just court<->court
or wait<->wait). Operates on the fully-built admin index.html."""
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
html = path.read_text(encoding='utf-8')

MARKER = 'jmCourtWaitCrossSwapV1'
if MARKER in html:
    print('ADMIN_COURT_WAIT_CROSS_SWAP_ALREADY_OK')
    raise SystemExit(0)

OLD = """function handleGroupHeaderClick(type, index, event) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }

  if (QUICK_PICK) {
    assignToQuickTarget(type, index);
    return;
  }

  if (SELECTED.size) {
    alert(
      '선택한 인원은 빈자리를 두 번 눌러 배치하세요. ' +
      '전체 교환은 인원 선택을 해제한 뒤 사용하세요.'
    );
    return;
  }

  index = String(index);

  if (!WHOLE_SWAP_PICK) {
    WHOLE_SWAP_PICK = {
      type: type,
      index: index
    };
    refreshWholeSwapVisuals();
    return;
  }

  const first = WHOLE_SWAP_PICK;

  if (
    first.type === type &&
    first.index === index
  ) {
    cancelWholeSwap();
    return;
  }

  if (first.type !== type) {
    alert(
      type === 'court'
        ? '코트끼리만 전체 교환할 수 있습니다.'
        : '대기조끼리만 전체 교환할 수 있습니다.'
    );
    WHOLE_SWAP_PICK = {
      type: type,
      index: index
    };
    refreshWholeSwapVisuals();
    return;
  }

  WHOLE_SWAP_PICK = null;
  quickWholeGroupSwap(
    type,
    first.index,
    index
  );
}

function applyWholeGroupSwapLocally(type, indexA, indexB) {
  if (type === 'court') {
    const courtA = Number(indexA);
    const courtB = Number(indexB);
    const players = STATE.courts[courtA];
    const startedAt = STATE.courtStartedAt[courtA];

    STATE.courts[courtA] = STATE.courts[courtB];
    STATE.courts[courtB] = players;
    STATE.courtStartedAt[courtA] =
      STATE.courtStartedAt[courtB];
    STATE.courtStartedAt[courtB] = startedAt;
    return;
  }

  const groupA = Number(indexA);
  const groupB = Number(indexB);
  const players = STATE.waitGroups[groupA];

  STATE.waitGroups[groupA] =
    STATE.waitGroups[groupB];
  STATE.waitGroups[groupB] = players;
}

async function quickWholeGroupSwap(type, indexA, indexB) {
  const previousState =
    JSON.parse(JSON.stringify(STATE));

  try {
    applyWholeGroupSwapLocally(
      type,
      indexA,
      indexB
    );
    renderState();

    const method =
      type === 'court'
        ? 'swapCourts'
        : 'swapWaitGroups';

    const state = await server(method, [
      ADMIN_PIN_VALUE,
      Number(indexA),
      Number(indexB)
    ]);

    renderState(state);
    setUndoState(previousState);
  } catch (error) {
    STATE = previousState;
    renderState();
    alert(error.message || error);
  }
}"""

NEW = """function handleGroupHeaderClick(type, index, event) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }

  if (QUICK_PICK) {
    assignToQuickTarget(type, index);
    return;
  }

  if (SELECTED.size) {
    alert(
      '선택한 인원은 빈자리를 두 번 눌러 배치하세요. ' +
      '전체 교환은 인원 선택을 해제한 뒤 사용하세요.'
    );
    return;
  }

  index = String(index);

  if (!WHOLE_SWAP_PICK) {
    WHOLE_SWAP_PICK = {
      type: type,
      index: index
    };
    refreshWholeSwapVisuals();
    return;
  }

  const first = WHOLE_SWAP_PICK;

  if (
    first.type === type &&
    first.index === index
  ) {
    cancelWholeSwap();
    return;
  }

  /* jmCourtWaitCrossSwapV1: 코트<->대기조 조합도 전체 교환이 되어야 하므로
     서로 다른 type이어도 막지 않고 바로 교환한다. */
  WHOLE_SWAP_PICK = null;
  quickWholeGroupSwap(
    first.type,
    first.index,
    type,
    index
  );
}

function applyWholeGroupSwapLocally(typeA, indexA, typeB, indexB) {
  if (typeA === 'court' && typeB === 'court') {
    const courtA = Number(indexA);
    const courtB = Number(indexB);
    const players = STATE.courts[courtA];
    const startedAt = STATE.courtStartedAt[courtA];

    STATE.courts[courtA] = STATE.courts[courtB];
    STATE.courts[courtB] = players;
    STATE.courtStartedAt[courtA] =
      STATE.courtStartedAt[courtB];
    STATE.courtStartedAt[courtB] = startedAt;
    return;
  }

  if (typeA === 'wait' && typeB === 'wait') {
    const groupA = Number(indexA);
    const groupB = Number(indexB);
    const players = STATE.waitGroups[groupA];

    STATE.waitGroups[groupA] =
      STATE.waitGroups[groupB];
    STATE.waitGroups[groupB] = players;
    return;
  }

  /* jmCourtWaitCrossSwapV1: 코트 하나와 대기조 하나를 통째로 맞바꾼다. */
  const courtIndex = Number(typeA === 'court' ? indexA : indexB);
  const waitIndex = Number(typeA === 'court' ? indexB : indexA);
  const courtPlayers = STATE.courts[courtIndex];
  const waitPlayers = STATE.waitGroups[waitIndex];

  STATE.courts[courtIndex] = waitPlayers;
  STATE.waitGroups[waitIndex] = courtPlayers;
  STATE.courtStartedAt[courtIndex] =
    (waitPlayers && waitPlayers.length) ? new Date().toISOString() : '';
}

async function quickWholeGroupSwap(typeA, indexA, typeB, indexB) {
  const previousState =
    JSON.parse(JSON.stringify(STATE));

  try {
    applyWholeGroupSwapLocally(
      typeA,
      indexA,
      typeB,
      indexB
    );
    renderState();

    let method;
    let args;

    if (typeA === typeB) {
      method = typeA === 'court' ? 'swapCourts' : 'swapWaitGroups';
      args = [ADMIN_PIN_VALUE, Number(indexA), Number(indexB)];
    } else {
      /* jmCourtWaitCrossSwapV1 */
      method = 'swapCourtAndWaitGroup';
      const courtIndex = Number(typeA === 'court' ? indexA : indexB);
      const waitIndex = Number(typeA === 'court' ? indexB : indexA);
      args = [ADMIN_PIN_VALUE, courtIndex, waitIndex];
    }

    const state = await server(method, args);

    renderState(state);
    setUndoState(previousState);
  } catch (error) {
    STATE = previousState;
    renderState();
    alert(error.message || error);
  }
}"""

count = html.count(OLD)
if count != 1:
    raise SystemExit(f'expected exactly one match for whole-group swap block, found {count}')

html = html.replace(OLD, NEW, 1)

import re as _re
mutations_match = _re.search(r"var MUTATIONS=new Set\(\[(?P<items>.*?)\]\);", html)
if not mutations_match:
    raise SystemExit('MUTATIONS set anchor not found')
if "'swapCourtAndWaitGroup'" not in mutations_match.group('items'):
    insertion = mutations_match.group(0).replace("]);", ",'swapCourtAndWaitGroup']);", 1)
    html = html[:mutations_match.start()] + insertion + html[mutations_match.end():]

if MARKER not in html:
    raise SystemExit('marker missing after patch (should be unreachable)')

path.write_text(html, encoding='utf-8')
print('ADMIN_COURT_WAIT_CROSS_SWAP_OK')
