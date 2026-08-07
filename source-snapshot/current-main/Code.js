const ADMIN_PIN = '1006';
const DEFAULT_MEMBER_PASSWORD = '0000';
const MAX_MEMBERS = 500;
const GROUP_SIZE = 4;
const WAIT_GROUP_COUNT = 5;

const SHEET_MEMBERS = 'Members';
const SHEET_COURTS = 'Courts';
const SHEET_WAIT = 'WaitGroups';
const SHEET_SETTINGS = 'Settings';
const SHEET_LOGS = 'ActionLogs';
const BACKUP_PREFIX = 'JayuBackup_';
let SETUP_READY_ = false;

function doGet(e) {
  ensureSetup_();

  const isAdmin =
    e &&
    e.parameter &&
    e.parameter.mode === 'admin';

  const template =
    HtmlService.createTemplateFromFile(
      isAdmin ? 'Admin' : 'Index'
    );

  if (!isAdmin) {
    template.memberPageUrl = ScriptApp.getService().getUrl() || '';
    template.pushReturn = JSON.stringify({
      connected: Boolean(e && e.parameter && e.parameter.push === 'on'),
      memberId: String(e && e.parameter && e.parameter.pushMemberId || ''),
      memberName: String(e && e.parameter && e.parameter.pushMemberName || '')
    });
  }

  return template
    .evaluate()
    .setTitle(
      isAdmin
        ? '자유민턴 코트배정 관리자'
        : '자유민턴 코트배정 현황'
    )
    .addMetaTag(
      'viewport',
      'width=device-width,initial-scale=1'
    )
    .setXFrameOptionsMode(
      HtmlService.XFrameOptionsMode.ALLOWALL
    );
}

function include(filename) {
  return HtmlService
    .createHtmlOutputFromFile(filename)
    .getContent();
}

function ensureSetup_() {
  if (SETUP_READY_) {
    return;
  }

  const ss = SpreadsheetApp.getActiveSpreadsheet();

  if (!ss) {
    throw new Error(
      'Google 스프레드시트의 확장 프로그램 → Apps Script에서 실행하세요.'
    );
  }

  const setupCache = CacheService.getDocumentCache();
  const setupKey = 'JAYUMINTON_SETUP_V11_' + ss.getId();

  if (setupCache.get(setupKey) === '1') {
    SETUP_READY_ = true;
    return;
  }

  ensureMembersSheet_(ss);
  ensureCourtsSheet_(ss);
  ensureWaitSheet_(ss);
  ensureSettingsSheet_(ss);
  ensureLogsSheet_(ss);
  migrateLegacyDataIfNeeded_(ss);
  trimLogs_();
  cleanupLegacyCourtData_();
  setupCache.put(setupKey, '1', 21600);
  SETUP_READY_ = true;
}

function ensureMembersSheet_(ss) {
  let sheet = ss.getSheetByName(SHEET_MEMBERS);

  if (!sheet) {
    sheet = ss.insertSheet(SHEET_MEMBERS);
  }

  sheet.getRange(1, 1, 1, 8).setValues([[
    'ID',
    'NAME',
    'GENDER',
    'GAMES',
    'STATUS',
    'CREATED_AT',
    'GRADE',
    'EXPERIENCE'
  ]]);
  sheet.setFrozenRows(1);
}

function ensureCourtsSheet_(ss) {
  let sheet = ss.getSheetByName(SHEET_COURTS);

  if (!sheet) {
    sheet = ss.insertSheet(SHEET_COURTS);
    sheet.getRange(1, 1, 1, 6).setValues([[
      'COURT_NO',
      'SLOT_1',
      'SLOT_2',
      'SLOT_3',
      'SLOT_4',
      'STARTED_AT'
    ]]);

    sheet.getRange(2, 1, 4, 6).setValues([
      [1, '', '', '', '', ''],
      [2, '', '', '', '', ''],
      [3, '', '', '', '', ''],
      [4, '', '', '', '', '']
    ]);

    sheet.setFrozenRows(1);
    return;
  }

  sheet.getRange(1, 6).setValue('STARTED_AT');
}

function ensureWaitSheet_(ss) {
  let sheet = ss.getSheetByName(SHEET_WAIT);

  if (!sheet) {
    sheet = ss.insertSheet(SHEET_WAIT);
    sheet.getRange(1, 1, 1, 5).setValues([[
      'GROUP_NO',
      'SLOT_1',
      'SLOT_2',
      'SLOT_3',
      'SLOT_4'
    ]]);

    sheet.getRange(2, 1, 5, 5).setValues([
      [1, '', '', '', ''],
      [2, '', '', '', ''],
      [3, '', '', '', ''],
      [4, '', '', '', ''],
      [5, '', '', '', '']
    ]);

    sheet.setFrozenRows(1);
  }
}

function ensureSettingsSheet_(ss) {
  let sheet = ss.getSheetByName(SHEET_SETTINGS);

  if (!sheet) {
    sheet = ss.insertSheet(SHEET_SETTINGS);
    sheet.getRange(1, 1, 1, 2).setValues([[
      'KEY',
      'VALUE'
    ]]);

    sheet.getRange(2, 1, 4, 2).setValues([
      ['MEMBER_PASSWORD', DEFAULT_MEMBER_PASSWORD],
      ['MEMBER_PASSWORD_VERSION', '1'],
      ['UPDATED_AT', new Date().toISOString()],
      ['LEGACY_MIGRATED', '0']
    ]);

    sheet.getRange(2, 2).setNumberFormat('@');
    sheet.setFrozenRows(1);
  }

  ensureSetting_('MEMBER_PASSWORD', DEFAULT_MEMBER_PASSWORD);
  ensureSetting_('MEMBER_PASSWORD_VERSION', '1');
  ensureSetting_('MEMBER_SESSION_TOKEN', Utilities.getUuid() + Utilities.getUuid());
  ensureSetting_('UPDATED_AT', new Date().toISOString());
  ensureSetting_('LEGACY_MIGRATED', '0');
  ensureSetting_('LAST_BACKUP_AT', '');
  ensureSetting_('OPERATION_COUNT', '0');
}


function ensureLogsSheet_(ss) {
  let sheet = ss.getSheetByName(SHEET_LOGS);

  if (!sheet) {
    sheet = ss.insertSheet(SHEET_LOGS);
    sheet.getRange(1, 1, 1, 4).setValues([[
      'TIME',
      'ACTION',
      'DETAIL',
      'USER'
    ]]);
    sheet.setFrozenRows(1);
  }
}

function withDocumentLock_(actionName, callback) {
  const lock = LockService.getDocumentLock();

  if (!lock.tryLock(15000)) {
    throw new Error(
      '다른 작업을 처리 중입니다. 잠시 후 다시 눌러주세요.'
    );
  }

  try {
    ensureSetup_();

    const result = callback();

    if (shouldLogSuccess_(actionName)) {
      logAction_(
        actionName,
        '정상 처리'
      );
    }

    return result;
  } catch (error) {
    logAction_(
      actionName,
      '오류: ' + String(error.message || error)
    );

    throw error;
  } finally {
    lock.releaseLock();
  }
}

function logAction_(action, detail) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName(SHEET_LOGS);

    if (!sheet) {
      return;
    }

    sheet.appendRow([
      new Date(),
      String(action || ''),
      String(detail || '').slice(0, 300),
      Session.getActiveUser().getEmail() || ''
    ]);

    trimLogs_();
  } catch (error) {
    // 로그 실패가 실제 배정 작업을 막지 않게 함
  }
}

function shouldLogSuccess_(actionName) {
  return [
    '경기 종료 자동 순환',
    '코트 교환',
    '코트 일부 인원 이동·교환',
    '수동 백업',
    '백업 복원',
    '전체 데이터 초기화',
    '멤버 비밀번호 변경'
  ].indexOf(String(actionName)) >= 0;
}

function trimLogs_() {
  try {
    const sheet =
      SpreadsheetApp
        .getActiveSpreadsheet()
        .getSheetByName(SHEET_LOGS);

    if (!sheet) {
      return;
    }

    const maxRows = 300;
    const trimAt = 350;
    const logRows =
      Math.max(0, sheet.getLastRow() - 1);

    if (logRows > trimAt) {
      sheet.deleteRows(
        2,
        logRows - maxRows
      );
    }
  } catch (error) {
    // 정리 실패가 운영을 막지 않게 함
  }
}

function incrementOperationCount_() {
  const current =
    Number(
      getSetting_('OPERATION_COUNT') || 0
    ) + 1;

  setSetting_(
    'OPERATION_COUNT',
    String(current)
  );
}

function maybeRunMaintenance_() {
  const count =
    Number(
      getSetting_('OPERATION_COUNT') || 0
    );

  if (
    count > 0 &&
    count % 100 === 0
  ) {
    repairData_();
    trimLogs_();
    cleanupLegacyCourtData_();
  }
}

function cleanupLegacyCourtData_() {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const legacy = ss.getSheetByName('CourtData');

    if (!legacy) {
      return;
    }

    if (
      getSetting_('LEGACY_MIGRATED') !== '1'
    ) {
      return;
    }

    const values =
      legacy
        .getRange('A:B')
        .getDisplayValues();

    const keysToClear = {
      MEMBERS: '[]',
      COURTS: '{"1":[],"2":[],"3":[],"4":[]}',
      WAIT_GROUPS: '[[],[],[],[],[]]',
      HISTORY: '[]'
    };

    for (
      let index = 1;
      index < values.length;
      index++
    ) {
      const key =
        String(values[index][0]);

      if (
        Object.prototype.hasOwnProperty.call(
          keysToClear,
          key
        )
      ) {
        const newValue =
          keysToClear[key];

        if (
          String(values[index][1]) !== newValue
        ) {
          legacy
            .getRange(index + 1, 2)
            .setValue(newValue);
        }
      }
    }
  } catch (error) {
    // 구버전 정리 실패가 현재 운영을 막지 않게 함
  }
}

function repairData_() {
  const members = readMembers_();
  const courts = readCourts_();
  const startedAt = readCourtStartedAt_();
  const waitGroups = readWaitGroups_();

  const validIds = {};
  const occupiedIds = {};

  members.forEach(function(member) {
    validIds[member.id] = true;
    member.games = Math.max(
      0,
      Number(member.games) || 0
    );
  });

  Object.keys(courts).forEach(function(key) {
    const clean = [];

    (courts[key] || []).forEach(function(id) {
      if (
        validIds[id] &&
        !occupiedIds[id] &&
        clean.length < GROUP_SIZE
      ) {
        clean.push(id);
        occupiedIds[id] = 'court';
      }
    });

    courts[key] = clean;
  });

  for (
    let groupIndex = 0;
    groupIndex < WAIT_GROUP_COUNT;
    groupIndex++
  ) {
    const clean = [];

    (waitGroups[groupIndex] || [])
      .forEach(function(id) {
        if (
          validIds[id] &&
          !occupiedIds[id] &&
          clean.length < GROUP_SIZE
        ) {
          clean.push(id);
          occupiedIds[id] = 'wait';
        }
      });

    waitGroups[groupIndex] = clean;
  }

  const courtIds = {};
  const waitIds = {};

  Object.keys(courts).forEach(function(key) {
    courts[key].forEach(function(id) {
      courtIds[id] = true;
    });
  });

  waitGroups.forEach(function(group) {
    group.forEach(function(id) {
      waitIds[id] = true;
    });
  });

  members.forEach(function(member) {
    if (courtIds[member.id]) {
      member.status = 'playing';
    } else if (waitIds[member.id]) {
      member.status = 'waiting';
    } else if (
      member.status === 'playing' ||
      member.status === 'waiting'
    ) {
      member.status = 'active';
    } else {
      member.status = normalizeStatus_(
        member.status
      );
    }
  });

  Object.keys(courts).forEach(function(key) {
    markCourtStartedIfFull_(courts, startedAt, key);
  });

  writeMembers_(members);
  writeCourts_(courts, startedAt);
  writeWaitGroups_(waitGroups);
}


/*
 * 백업은 누적하지 않습니다.
 * 같은 이름의 기존 백업 4개를 삭제하고 최근 1세트만 다시 만듭니다.
 */
function createBackupSnapshot_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  [
    SHEET_MEMBERS,
    SHEET_COURTS,
    SHEET_WAIT,
    SHEET_SETTINGS
  ].forEach(function(sourceName) {
    const source = ss.getSheetByName(sourceName);
    const backupName =
      BACKUP_PREFIX + sourceName;

    const existing =
      ss.getSheetByName(backupName);

    if (existing) {
      ss.deleteSheet(existing);
    }

    const copy = source.copyTo(ss);
    copy.setName(backupName);
    copy.hideSheet();
  });

  setSetting_(
    'LAST_BACKUP_AT',
    new Date().toISOString()
  );
}

function createManualBackup(pin) {
  auth_(pin);

  return withDocumentLock_(
    '수동 백업',
    function() {
      createBackupSnapshot_();

      return {
        ok: true,
        backedUpAt:
          getSetting_('LAST_BACKUP_AT')
      };
    }
  );
}

function restoreManualBackup(pin) {
  auth_(pin);

  return withDocumentLock_(
    '백업 복원',
    function() {
      const ss = SpreadsheetApp.getActiveSpreadsheet();

      [
        SHEET_MEMBERS,
        SHEET_COURTS,
        SHEET_WAIT,
        SHEET_SETTINGS
      ].forEach(function(targetName) {
        const backup =
          ss.getSheetByName(
            BACKUP_PREFIX + targetName
          );

        const target =
          ss.getSheetByName(targetName);

        if (!backup || !target) {
          throw new Error(
            '복원할 백업이 없습니다.'
          );
        }

        target.clearContents();

        const range =
          backup.getDataRange();

        if (
          range.getNumRows() > 0 &&
          range.getNumColumns() > 0
        ) {
          target
            .getRange(
              1,
              1,
              range.getNumRows(),
              range.getNumColumns()
            )
            .setValues(
              range.getValues()
            );
        }
      });

      repairData_();
      touch_();

      return getPublicState();
    }
  );
}

function getSystemStatus(pin) {
  auth_(pin);

  ensureSetup_();

  return {
    lastBackupAt:
      getSetting_('LAST_BACKUP_AT') || '',
    updatedAt:
      getSetting_('UPDATED_AT') || '',
    memberCount:
      readMembers_().length,
    logCount:
      SpreadsheetApp
        .getActiveSpreadsheet()
        .getSheetByName(SHEET_LOGS)
        .getLastRow() > 1
          ? SpreadsheetApp
              .getActiveSpreadsheet()
              .getSheetByName(SHEET_LOGS)
              .getLastRow() - 1
          : 0
  };
}

function migrateLegacyDataIfNeeded_(ss) {
  if (getSetting_('LEGACY_MIGRATED') === '1') {
    return;
  }

  const oldSheet = ss.getSheetByName('CourtData');

  if (!oldSheet) {
    setSetting_('LEGACY_MIGRATED', '1');
    return;
  }

  const values =
    oldSheet.getRange('A:B').getDisplayValues();

  const legacy = {};

  for (let i = 1; i < values.length; i++) {
    legacy[String(values[i][0])] = values[i][1];
  }

  const currentMembers = readMembers_();

  if (
    currentMembers.length === 0 &&
    legacy.MEMBERS
  ) {
    try {
      const members = JSON.parse(legacy.MEMBERS);

      members.forEach(function(member) {
        if (!member || !member.id || !member.name) {
          return;
        }

        appendMember_({
          id: String(member.id),
          name: String(member.name),
          gender:
            member.gender === 'female'
              ? 'female'
              : 'male',
          games: Number(member.games) || 0,
          status: normalizeStatus_(member.status),
          createdAt: new Date().toISOString(),
          grade: String(member.grade || ''),
          experience: String(member.experience || '')
        });
      });
    } catch (error) {}
  }

  if (legacy.COURTS) {
    try {
      const courts = JSON.parse(legacy.COURTS);
      writeCourts_(courts);
    } catch (error) {}
  }

  if (legacy.WAIT_GROUPS) {
    try {
      const waitGroups =
        JSON.parse(legacy.WAIT_GROUPS);
      writeWaitGroups_(waitGroups);
    } catch (error) {}
  }

  if (legacy.MEMBER_PASSWORD) {
    setSetting_(
      'MEMBER_PASSWORD',
      String(legacy.MEMBER_PASSWORD)
    );
  }

  if (legacy.MEMBER_PASSWORD_VERSION) {
    setSetting_(
      'MEMBER_PASSWORD_VERSION',
      String(legacy.MEMBER_PASSWORD_VERSION)
    );
  }

  setSetting_('LEGACY_MIGRATED', '1');
}

function normalizeStatus_(status) {
  if (
    ['before', 'active', 'rest', 'away', 'playing', 'waiting']
      .indexOf(status) >= 0
  ) {
    return status;
  }

  if (
    status === 'unassigned'
  ) {
    return 'active';
  }

  return 'active';
}

function adminLogin(pin) {
  return String(pin == null ? '' : pin).trim() ===
    String(ADMIN_PIN).trim();
}

function adminSessionToken_() {
  const spreadsheet =
    SpreadsheetApp.getActiveSpreadsheet();

  const source = [
    String(ADMIN_PIN).trim(),
    spreadsheet ? spreadsheet.getId() : '',
    'JAYUMINTON_ADMIN_SESSION_V1'
  ].join('|');

  return Utilities
    .base64EncodeWebSafe(
      Utilities.computeDigest(
        Utilities.DigestAlgorithm.SHA_256,
        source
      )
    )
    .replace(/=+$/g, '');
}

function createAdminSession(pin) {
  ensureSetup_();

  if (!adminLogin(pin)) {
    return {
      ok: false,
      token: ''
    };
  }

  return {
    ok: true,
    token: adminSessionToken_()
  };
}

function resumeAdminSession(token) {
  ensureSetup_();

  return (
    String(token == null ? '' : token) !== '' &&
    String(token) === adminSessionToken_()
  );
}

function auth_(credential) {
  if (
    !adminLogin(credential) &&
    !resumeAdminSession(credential)
  ) {
    throw new Error('관리자 PIN이 틀렸습니다.');
  }
}

function memberSessionToken_() {
  let token = String(getSetting_('MEMBER_SESSION_TOKEN') || '').trim();
  if (!token) {
    token = Utilities.getUuid() + Utilities.getUuid();
    setSetting_('MEMBER_SESSION_TOKEN', token);
  }
  return token;
}

function verifyMemberPassword(password) {
  ensureSetup_();

  const current =
    String(
      getSetting_('MEMBER_PASSWORD') ||
      DEFAULT_MEMBER_PASSWORD
    ).trim();

  const entered =
    String(password == null ? '' : password).trim();

  const ok = current === entered;
  const version = ok
    ? String(getSetting_('MEMBER_PASSWORD_VERSION') || '1')
    : '';

  return {
    ok: ok,
    version: version,
    sessionToken: ok ? memberSessionToken_() : ''
  };
}

function resumeMemberSession(token) {
  ensureSetup_();
  const entered = String(token == null ? '' : token).trim();
  const ok = entered !== '' && entered === memberSessionToken_();
  return {
    ok: ok,
    version: ok ? String(getSetting_('MEMBER_PASSWORD_VERSION') || '1') : ''
  };
}

function getMemberPasswordVersion() {
  ensureSetup_();

  return String(
    getSetting_('MEMBER_PASSWORD_VERSION') ||
    '1'
  );
}

function getCurrentMemberPassword(pin) {
  auth_(pin);

  return String(
    getSetting_('MEMBER_PASSWORD') ||
    DEFAULT_MEMBER_PASSWORD
  ).trim();
}

function changeMemberPasswordUnlocked_(pin, newPassword) {
  auth_(pin);

  const value =
    String(newPassword == null ? '' : newPassword).trim();

  if (
    value.length < 4 ||
    value.length > 20 ||
    /\s/.test(value)
  ) {
    throw new Error(
      '멤버 비밀번호는 공백 없이 4~20자로 입력하세요.'
    );
  }

  const nextVersion =
    Number(
      getSetting_('MEMBER_PASSWORD_VERSION') ||
      1
    ) + 1;

  setSetting_('MEMBER_PASSWORD', value);
  setSetting_(
    'MEMBER_PASSWORD_VERSION',
    String(nextVersion)
  );
  setSetting_(
    'MEMBER_SESSION_TOKEN',
    Utilities.getUuid() + Utilities.getUuid()
  );
  touch_();

  return {
    ok: true,
    version: String(nextVersion),
    password: value
  };
}

function getPublicState() {
  ensureSetup_();

  const members = readMembers_();
  const courts = readCourts_();
  const waitGroups = readWaitGroups_();
  const courtStartedAt = readCourtStartedAt_();

  const validIds = {};
  members.forEach(function(member) {
    validIds[member.id] = true;
  });

  Object.keys(courts).forEach(function(key) {
    courts[key] =
      (courts[key] || []).filter(function(id) {
        return validIds[id];
      });
  });

  const cleanWait =
    waitGroups.map(function(group) {
      return (group || []).filter(function(id) {
        return validIds[id];
      });
    });

  return {
    members: members,
    courts: courts,
    waitGroups: cleanWait,
    courtStartedAt: courtStartedAt,
    updatedAt:
      getSetting_('UPDATED_AT') ||
      new Date().toISOString(),
    maxMembers: MAX_MEMBERS
  };
}

function makeState_(members, courts, waitGroups, courtStartedAt) {
  return {
    members: members,
    courts: courts,
    waitGroups: waitGroups,
    courtStartedAt: courtStartedAt,
    updatedAt: new Date().toISOString(),
    maxMembers: MAX_MEMBERS
  };
}

function smartAssignSelected(pin, ids, preferredCourt) {
  return withDocumentLock_(
    '4명 빠른 자동 배정',
    function() {
      auth_(pin);
      ids = normalizeIds_(ids);
      preferredCourt = String(preferredCourt || '');

      if (ids.length !== GROUP_SIZE) {
        throw new Error('빠른 자동 배정은 정확히 4명을 선택하세요.');
      }

      const members = readMembers_();
      const courts = readCourts_();
      const waitGroups = readWaitGroups_();
      const startedAt = readCourtStartedAt_();
      const memberMap = {};
      let courtsChanged = false;
      let waitChanged = false;

      members.forEach(function(member) {
        memberMap[member.id] = member;
      });

      ids.forEach(function(id) {
        if (!memberMap[id] || memberMap[id].status !== 'active') {
          throw new Error('코트배정 대기 상태인 인원만 선택하세요.');
        }
      });

      const maleCount = ids.filter(function(id) {
        return memberMap[id].gender === 'male';
      }).length;
      const femaleCount = ids.length - maleCount;

      if (
        !(
          maleCount === 4 ||
          femaleCount === 4 ||
          (maleCount === 2 && femaleCount === 2)
        )
      ) {
        throw new Error(
          '복식은 남자 4명, 여자 4명 또는 남자 2명·여자 2명만 가능합니다.'
        );
      }

      let emptyCourts = ['1', '2', '3', '4'].filter(function(courtNo) {
        return (courts[courtNo] || []).length === 0;
      });

      while (emptyCourts.length) {
        const firstQueuedIndex = waitGroups.findIndex(function(group) {
          return (group || []).length === GROUP_SIZE;
        });

        if (firstQueuedIndex < 0) break;

        const promoted = waitGroups[firstQueuedIndex].slice();
        const promotedCourt = emptyCourts[0];

        courts[promotedCourt] = promoted;
        courtsChanged = true;
        waitChanged = true;
        startedAt[promotedCourt] = new Date().toISOString();
        promoted.forEach(function(id) {
          memberMap[id].status = 'playing';
        });

        waitGroups.splice(firstQueuedIndex, 1);
        waitGroups.push([]);
        emptyCourts.shift();
      }

      let targetCourt = '';

      if (emptyCourts.length === 1) {
        targetCourt = emptyCourts[0];
      } else if (emptyCourts.length > 1) {
        if (emptyCourts.indexOf(preferredCourt) < 0) {
          throw new Error('빈 코트가 2개 이상입니다. 배정할 코트를 선택하세요.');
        }
        targetCourt = preferredCourt;
      }

      if (targetCourt) {
        courts[targetCourt] = ids.slice();
        courtsChanged = true;
        startedAt[targetCourt] = new Date().toISOString();
        ids.forEach(function(id) {
          memberMap[id].status = 'playing';
        });
      } else {
        let lastOccupiedWait = -1;
        waitGroups.forEach(function(group, index) {
          if ((group || []).length > 0) {
            lastOccupiedWait = index;
          }
        });

        let targetWait =
          lastOccupiedWait + 1 < WAIT_GROUP_COUNT &&
          (waitGroups[lastOccupiedWait + 1] || []).length === 0
            ? lastOccupiedWait + 1
            : waitGroups.findIndex(function(group) {
                return (group || []).length === 0;
              });

        if (targetWait < 0) {
          throw new Error('대기 1~5조가 모두 차 있습니다.');
        }

        waitGroups[targetWait] = ids.slice();
        waitChanged = true;
        ids.forEach(function(id) {
          memberMap[id].status = 'waiting';
        });
      }

      if (courtsChanged) writeCourts_(courts, startedAt);
      if (waitChanged) writeWaitGroups_(waitGroups);
      writeMembers_(members);

      return makeState_(members, courts, waitGroups, startedAt);
    }
  );
}

function addMemberUnlocked_(pin, name, gender, grade, experience) {
  auth_(pin);

  name = String(name == null ? '' : name).trim();
  gender = String(gender == null ? '' : gender).trim();
  grade = String(grade == null ? '' : grade).trim();
  experience = String(experience == null ? '' : experience).trim();

  if (!name || name.length > 20) {
    throw new Error(
      '이름 또는 닉네임은 1자 이상 20자 이하로 입력하세요.'
    );
  }

  if (
    ['male', 'female'].indexOf(gender) < 0
  ) {
    throw new Error('성별을 선택하세요.');
  }

  if (grade.length > 12) {
    throw new Error('급수는 12자 이내로 입력하세요.');
  }

  if (experience.length > 20) {
    throw new Error('구력은 20자 이내로 입력하세요.');
  }

  const members = readMembers_();

  if (members.length >= MAX_MEMBERS) {
    throw new Error('멤버는 최대 500명입니다.');
  }

  const member = {
    id: Utilities.getUuid(),
    name: name,
    gender: gender,
    games: 0,
    status: 'active',
    createdAt: new Date().toISOString(),
    grade: grade,
    experience: experience,
    level: grade,
    career: experience
  };

  appendMember_(member);
  members.push(member);
  touch_();

  /*
   * 멤버 한 명 저장 뒤 코트·대기조 전체를 다시 읽으면 체감 지연이 커진다.
   * 현재 웹/앱 화면은 result.member를 STATE에 합칠 수 있으므로 가벼운 응답만 반환한다.
   */
  return {
    ok: true,
    member: member,
    updatedAt: new Date().toISOString(),
    maxMembers: MAX_MEMBERS
  };
}

function setMemberStatusUnlocked_(pin, ids, status) {
  auth_(pin);

  ids = normalizeIds_(ids);

  if (!ids.length) {
    throw new Error('멤버를 선택하세요.');
  }

  if (
    ['before', 'active', 'rest', 'away']
      .indexOf(status) < 0
  ) {
    throw new Error('잘못된 상태입니다.');
  }

  removeEverywhere_(ids);

  const members = readMembers_();

  members.forEach(function(member) {
    if (ids.indexOf(member.id) >= 0) {
      member.status = status;
    }
  });

  writeMembers_(members);
  touch_();

  return getPublicState();
}

function assignMembersToCourtUnlocked_(
  pin,
  courtNo,
  ids
) {
  auth_(pin);

  courtNo = String(courtNo);
  ids = normalizeIds_(ids);

  if (
    ['1', '2', '3', '4'].indexOf(courtNo) < 0
  ) {
    throw new Error('잘못된 코트 번호입니다.');
  }

  if (!ids.length) {
    throw new Error('멤버를 선택하세요.');
  }

  const courts = readCourts_();
  const startedAt = readCourtStartedAt_();

  if (
    (courts[courtNo] || []).length +
    ids.length >
    GROUP_SIZE
  ) {
    throw new Error(
      '한 코트에는 최대 4명만 들어갈 수 있습니다.'
    );
  }

  removeEverywhere_(ids);

  const refreshedCourts = readCourts_();

  refreshedCourts[courtNo] =
    (refreshedCourts[courtNo] || []).concat(ids);

  markCourtStartedIfFull_(refreshedCourts, startedAt, courtNo);
  writeCourts_(refreshedCourts, startedAt);
  updateMemberStatuses_(ids, 'playing');
  touch_();

  return getPublicState();
}

function autoFillCourtUnlocked_(pin, courtNo, ids) {
  auth_(pin);

  courtNo = String(courtNo);
  ids = normalizeIds_(ids);

  if (['1', '2', '3', '4'].indexOf(courtNo) < 0) {
    throw new Error('잘못된 코트 번호입니다.');
  }

  const courts = readCourts_();
  const existingIds = (courts[courtNo] || []).slice();
  const needed = GROUP_SIZE - existingIds.length;

  if (needed <= 0 || ids.length !== needed) {
    throw new Error(
      '선택한 코트의 빈자리 수와 배정 인원이 맞지 않습니다.'
    );
  }

  const members = readMembers_();
  const memberMap = {};
  members.forEach(function(member) {
    memberMap[member.id] = member;
  });

  ids.forEach(function(id) {
    if (!memberMap[id] || memberMap[id].status !== 'active') {
      throw new Error('코트배정 대기 상태인 인원만 자동배정할 수 있습니다.');
    }
  });

  const finalIds = existingIds.concat(ids);
  let maleCount = 0;
  let femaleCount = 0;

  finalIds.forEach(function(id) {
    const member = memberMap[id];
    if (!member) {
      throw new Error('코트 인원 정보를 확인할 수 없습니다.');
    }
    if (member.gender === 'female') femaleCount++;
    else maleCount++;
  });

  if (
    !(
      maleCount === 4 ||
      femaleCount === 4 ||
      (maleCount === 2 && femaleCount === 2)
    )
  ) {
    throw new Error(
      '자동배정은 남복·여복·혼복 조합만 가능합니다.'
    );
  }

  return assignMembersToCourtUnlocked_(
    pin,
    courtNo,
    ids
  );
}

function assignMembersToWaitGroupUnlocked_(
  pin,
  groupIndex,
  ids
) {
  auth_(pin);

  groupIndex = Number(groupIndex);
  ids = normalizeIds_(ids);

  if (
    groupIndex < 0 ||
    groupIndex >= WAIT_GROUP_COUNT
  ) {
    throw new Error('잘못된 대기조 번호입니다.');
  }

  if (!ids.length) {
    throw new Error('멤버를 선택하세요.');
  }

  const waitGroups = readWaitGroups_();

  if (
    waitGroups[groupIndex].length +
    ids.length >
    GROUP_SIZE
  ) {
    throw new Error(
      '한 대기조에는 최대 4명만 들어갈 수 있습니다.'
    );
  }

  removeEverywhere_(ids);

  const refreshedWait = readWaitGroups_();

  refreshedWait[groupIndex] =
    refreshedWait[groupIndex].concat(ids);

  writeWaitGroups_(refreshedWait);
  updateMemberStatuses_(ids, 'waiting');
  touch_();

  return getPublicState();
}

function autoFillWaitGroupUnlocked_(
  pin,
  groupIndex,
  ids
) {
  auth_(pin);

  groupIndex = Number(groupIndex);
  ids = normalizeIds_(ids);

  if (
    groupIndex < 0 ||
    groupIndex >= WAIT_GROUP_COUNT
  ) {
    throw new Error('잘못된 대기조 번호입니다.');
  }

  const waitGroups = readWaitGroups_();
  const existingIds =
    (waitGroups[groupIndex] || []).slice();
  const needed = GROUP_SIZE - existingIds.length;

  if (needed <= 0 || ids.length !== needed) {
    throw new Error(
      '선택한 대기조의 빈자리 수와 배정 인원이 맞지 않습니다.'
    );
  }

  const members = readMembers_();
  const memberMap = {};
  members.forEach(function(member) {
    memberMap[member.id] = member;
  });

  ids.forEach(function(id) {
    if (!memberMap[id] || memberMap[id].status !== 'active') {
      throw new Error('코트배정 대기 상태인 인원만 자동배정할 수 있습니다.');
    }
  });

  const finalIds = existingIds.concat(ids);
  let maleCount = 0;
  let femaleCount = 0;

  finalIds.forEach(function(id) {
    const member = memberMap[id];
    if (!member) {
      throw new Error('대기조 인원 정보를 확인할 수 없습니다.');
    }
    if (member.gender === 'female') femaleCount++;
    else maleCount++;
  });

  if (
    !(
      maleCount === 4 ||
      femaleCount === 4 ||
      (maleCount === 2 && femaleCount === 2)
    )
  ) {
    throw new Error(
      '자동배정은 남복·여복·혼복 조합만 가능합니다.'
    );
  }

  return assignMembersToWaitGroupUnlocked_(
    pin,
    groupIndex,
    ids
  );
}

function assignWaitGroupToCourtUnlocked_(
  pin,
  groupIndex,
  courtNo
) {
  auth_(pin);

  groupIndex = Number(groupIndex);
  courtNo = String(courtNo);

  const waitGroups = readWaitGroups_();
  const courts = readCourts_();
  const startedAt = readCourtStartedAt_();
  const group = waitGroups[groupIndex] || [];

  if (group.length !== GROUP_SIZE) {
    throw new Error(
      '4명이 모두 채워진 대기조만 코트에 배정할 수 있습니다.'
    );
  }

  if ((courts[courtNo] || []).length) {
    throw new Error(
      '비어 있는 코트에만 배정할 수 있습니다.'
    );
  }

  courts[courtNo] = group.slice();
  waitGroups[groupIndex] = [];

  startedAt[courtNo] = new Date().toISOString();
  writeCourts_(courts, startedAt);
  writeWaitGroups_(waitGroups);
  updateMemberStatuses_(group, 'playing');
  touch_();

  return getPublicState();
}

function finishCourtUnlocked_(pin, courtNo) {
  auth_(pin);

  courtNo = String(courtNo);

  if (
    ['1', '2', '3', '4'].indexOf(courtNo) < 0
  ) {
    throw new Error('잘못된 코트 번호입니다.');
  }

  const courts = readCourts_();
  const startedAt = readCourtStartedAt_();
  const waitGroups = readWaitGroups_();
  const finished = courts[courtNo] || [];

  if (finished.length !== GROUP_SIZE) {
    throw new Error(
      '4명이 모두 배정된 코트만 경기 종료할 수 있습니다.'
    );
  }

  const members = readMembers_();

  members.forEach(function(member) {
    if (finished.indexOf(member.id) >= 0) {
      member.games =
        (Number(member.games) || 0) + 1;
      member.status = 'active';
    }
  });

  const waitOne = waitGroups[0] || [];

  if (waitOne.length === GROUP_SIZE) {
    courts[courtNo] = waitOne.slice();
    startedAt[courtNo] = new Date().toISOString();

    members.forEach(function(member) {
      if (waitOne.indexOf(member.id) >= 0) {
        member.status = 'playing';
      }
    });

    const shifted = [
      (waitGroups[1] || []).slice(),
      (waitGroups[2] || []).slice(),
      (waitGroups[3] || []).slice(),
      (waitGroups[4] || []).slice(),
      []
    ];

    writeWaitGroups_(shifted);
  } else {
    courts[courtNo] = [];
    startedAt[courtNo] = '';
  }

  writeCourts_(courts, startedAt);
  writeMembers_(members);
  touch_();

  return getPublicState();
}

function removeFromCourtUnlocked_(pin, courtNo, id) {
  auth_(pin);

  courtNo = String(courtNo);
  id = String(id);

  const courts = readCourts_();
  const startedAt = readCourtStartedAt_();

  courts[courtNo] =
    (courts[courtNo] || [])
      .filter(function(memberId) {
        return memberId !== id;
      });

  startedAt[courtNo] = '';
  writeCourts_(courts, startedAt);
  updateMemberStatuses_([id], 'active');
  touch_();

  return getPublicState();
}

function removeFromWaitGroupUnlocked_(
  pin,
  groupIndex,
  id
) {
  auth_(pin);

  groupIndex = Number(groupIndex);
  id = String(id);

  const waitGroups = readWaitGroups_();

  waitGroups[groupIndex] =
    waitGroups[groupIndex]
      .filter(function(memberId) {
        return memberId !== id;
      });

  writeWaitGroups_(waitGroups);
  updateMemberStatuses_([id], 'active');
  touch_();

  return getPublicState();
}

function decreaseSelectedGameCountsUnlocked_(
  pin,
  ids
) {
  auth_(pin);

  ids = normalizeIds_(ids);

  if (!ids.length) {
    throw new Error('멤버를 선택하세요.');
  }

  const members = readMembers_();

  members.forEach(function(member) {
    if (ids.indexOf(member.id) >= 0) {
      member.games = Math.max(
        0,
        (Number(member.games) || 0) - 1
      );
    }
  });

  writeMembers_(members);
  touch_();

  return getPublicState();
}

function resetSelectedGameCountsUnlocked_(
  pin,
  ids
) {
  auth_(pin);

  ids = normalizeIds_(ids);

  if (!ids.length) {
    throw new Error('멤버를 선택하세요.');
  }

  const members = readMembers_();

  members.forEach(function(member) {
    if (ids.indexOf(member.id) >= 0) {
      member.games = 0;
    }
  });

  writeMembers_(members);
  touch_();

  return getPublicState();
}

function deleteMembersUnlocked_(pin, ids) {
  auth_(pin);

  ids = normalizeIds_(ids);

  if (!ids.length) {
    throw new Error('멤버를 선택하세요.');
  }

  removeEverywhere_(ids);

  const members =
    readMembers_().filter(function(member) {
      return ids.indexOf(member.id) < 0;
    });

  writeMembers_(members);
  touch_();

  return getPublicState();
}

function resetAllOperationDataUnlocked_(pin) {
  auth_(pin);

  writeMembers_([]);
  writeCourts_(
    {
      '1': [],
      '2': [],
      '3': [],
      '4': []
    },
    {
      '1': '',
      '2': '',
      '3': '',
      '4': ''
    }
  );

  writeWaitGroups_([
    [],
    [],
    [],
    [],
    []
  ]);

  touch_();

  return getPublicState();
}


function changeMemberPassword(pin, newPassword) {
  return withDocumentLock_(
    '멤버 비밀번호 변경',
    function() {
      return changeMemberPasswordUnlocked_(
        pin,
        newPassword
      );
    }
  );
}

function addMember(pin, name, gender, grade, experience) {
  return withDocumentLock_(
    '멤버 등록',
    function() {
      return addMemberUnlocked_(
        pin,
        name,
        gender,
        grade,
        experience
      );
    }
  );
}

function setMemberStatus(pin, ids, status) {
  return withDocumentLock_(
    '멤버 상태 변경',
    function() {
      return setMemberStatusUnlocked_(
        pin,
        ids,
        status
      );
    }
  );
}

function assignMembersToCourt(pin, courtNo, ids) {
  return withDocumentLock_(
    '코트 직접 배정',
    function() {
      return assignMembersToCourtUnlocked_(
        pin,
        courtNo,
        ids
      );
    }
  );
}

function autoFillCourt(pin, courtNo, ids) {
  return withDocumentLock_(
    '코트 복식 자동 채우기',
    function() {
      return autoFillCourtUnlocked_(
        pin,
        courtNo,
        ids
      );
    }
  );
}

function autoFillWaitGroup(pin, groupIndex, ids) {
  return withDocumentLock_(
    '대기조 복식 자동 채우기',
    function() {
      return autoFillWaitGroupUnlocked_(
        pin,
        groupIndex,
        ids
      );
    }
  );
}

function assignMembersToWaitGroup(
  pin,
  groupIndex,
  ids
) {
  return withDocumentLock_(
    '대기조 배정',
    function() {
      return assignMembersToWaitGroupUnlocked_(
        pin,
        groupIndex,
        ids
      );
    }
  );
}

function assignWaitGroupToCourt(
  pin,
  groupIndex,
  courtNo
) {
  return withDocumentLock_(
    '대기조 코트 배정',
    function() {
      return assignWaitGroupToCourtUnlocked_(
        pin,
        groupIndex,
        courtNo
      );
    }
  );
}



function adjustCourtMembers(
  pin,
  courtA,
  courtB,
  selectedA,
  selectedB
) {
  return withDocumentLock_(
    '코트 일부 인원 이동·교환',
    function() {
      auth_(pin);

      courtA = String(courtA);
      courtB = String(courtB);
      selectedA = normalizeIds_(selectedA);
      selectedB = normalizeIds_(selectedB);

      if (
        ['1', '2', '3', '4'].indexOf(courtA) < 0 ||
        ['1', '2', '3', '4'].indexOf(courtB) < 0
      ) {
        throw new Error('잘못된 코트 번호입니다.');
      }

      if (courtA === courtB) {
        throw new Error('서로 다른 코트를 선택하세요.');
      }

      if (!selectedA.length && !selectedB.length) {
        throw new Error('이동하거나 교환할 인원을 선택하세요.');
      }

      const courts = readCourts_();
      const startedAt = readCourtStartedAt_();
      const groupA = (courts[courtA] || []).slice();
      const groupB = (courts[courtB] || []).slice();

      selectedA.forEach(function(id) {
        if (groupA.indexOf(id) < 0) {
          throw new Error(
            '첫 번째 코트에 없는 인원이 선택되었습니다.'
          );
        }
      });

      selectedB.forEach(function(id) {
        if (groupB.indexOf(id) < 0) {
          throw new Error(
            '두 번째 코트에 없는 인원이 선택되었습니다.'
          );
        }
      });

      const remainA =
        groupA.filter(function(id) {
          return selectedA.indexOf(id) < 0;
        });

      const remainB =
        groupB.filter(function(id) {
          return selectedB.indexOf(id) < 0;
        });

      const nextA =
        remainA.concat(selectedB);

      const nextB =
        remainB.concat(selectedA);

      if (
        nextA.length > GROUP_SIZE ||
        nextB.length > GROUP_SIZE
      ) {
        throw new Error(
          '이동 후 한 코트가 4명을 초과합니다. 선택 인원을 조정하세요.'
        );
      }

      courts[courtA] = nextA;
      courts[courtB] = nextB;

      markCourtStartedIfFull_(courts, startedAt, courtA);
      markCourtStartedIfFull_(courts, startedAt, courtB);
      writeCourts_(courts, startedAt);
      repairData_();
      touch_();

      return getPublicState();
    }
  );
}

function swapCourts(pin, courtA, courtB) {
  return withDocumentLock_(
    '코트 교환',
    function() {
      auth_(pin);

      courtA = String(courtA);
      courtB = String(courtB);

      if (
        ['1', '2', '3', '4'].indexOf(courtA) < 0 ||
        ['1', '2', '3', '4'].indexOf(courtB) < 0
      ) {
        throw new Error('잘못된 코트 번호입니다.');
      }

      if (courtA === courtB) {
        throw new Error('서로 다른 코트를 선택하세요.');
      }

      const courts = readCourts_();
      const startedAt = readCourtStartedAt_();
      const temp = (courts[courtA] || []).slice();

      courts[courtA] = (courts[courtB] || []).slice();
      courts[courtB] = temp;

      const timeTemp = startedAt[courtA];
      startedAt[courtA] = startedAt[courtB];
      startedAt[courtB] = timeTemp;

      writeCourts_(courts, startedAt);
      repairData_();
      touch_();

      return getPublicState();
    }
  );
}

function swapWaitGroups(pin, groupA, groupB) {
  return withDocumentLock_(
    '대기조 전체 교환',
    function() {
      auth_(pin);

      groupA = Number(groupA);
      groupB = Number(groupB);

      if (
        groupA < 0 ||
        groupA >= WAIT_GROUP_COUNT ||
        groupB < 0 ||
        groupB >= WAIT_GROUP_COUNT
      ) {
        throw new Error('잘못된 대기조 번호입니다.');
      }

      if (groupA === groupB) {
        throw new Error('서로 다른 대기조를 선택하세요.');
      }

      const waitGroups = readWaitGroups_();
      const temp = (waitGroups[groupA] || []).slice();

      waitGroups[groupA] =
        (waitGroups[groupB] || []).slice();
      waitGroups[groupB] = temp;

      writeWaitGroups_(waitGroups);
      touch_();

      return getPublicState();
    }
  );
}

function adjustWaitGroupMembers(
  pin,
  groupA,
  groupB,
  selectedA,
  selectedB
) {
  return withDocumentLock_(
    '대기조 일부 인원 이동·교환',
    function() {
      auth_(pin);

      groupA = Number(groupA);
      groupB = Number(groupB);
      selectedA = normalizeIds_(selectedA);
      selectedB = normalizeIds_(selectedB);

      if (
        groupA < 0 || groupA >= WAIT_GROUP_COUNT ||
        groupB < 0 || groupB >= WAIT_GROUP_COUNT
      ) {
        throw new Error('잘못된 대기조 번호입니다.');
      }

      if (groupA === groupB) {
        throw new Error('서로 다른 대기조를 선택하세요.');
      }

      if (!selectedA.length && !selectedB.length) {
        throw new Error('이동하거나 교환할 인원을 선택하세요.');
      }

      const waitGroups = readWaitGroups_();
      const idsA = (waitGroups[groupA] || []).slice();
      const idsB = (waitGroups[groupB] || []).slice();

      selectedA.forEach(function(id) {
        if (idsA.indexOf(id) < 0) {
          throw new Error('첫 번째 대기조에 없는 인원이 선택되었습니다.');
        }
      });

      selectedB.forEach(function(id) {
        if (idsB.indexOf(id) < 0) {
          throw new Error('두 번째 대기조에 없는 인원이 선택되었습니다.');
        }
      });

      const nextA = idsA.filter(function(id) {
        return selectedA.indexOf(id) < 0;
      }).concat(selectedB);

      const nextB = idsB.filter(function(id) {
        return selectedB.indexOf(id) < 0;
      }).concat(selectedA);

      if (nextA.length > GROUP_SIZE || nextB.length > GROUP_SIZE) {
        throw new Error(
          '이동 후 한 대기조가 4명을 초과합니다. 선택 인원을 조정하세요.'
        );
      }

      waitGroups[groupA] = nextA;
      waitGroups[groupB] = nextB;
      writeWaitGroups_(waitGroups);
      touch_();

      return getPublicState();
    }
  );
}

function moveOrSwapMember(
  pin,
  memberId,
  targetType,
  targetIndex,
  targetMemberId
) {
  return withDocumentLock_(
    '빠른 드래그 이동·교환',
    function() {
      auth_(pin);

      memberId = String(memberId || '');
      targetType = String(targetType || '');
      targetIndex = String(targetIndex == null ? '' : targetIndex);
      targetMemberId = String(targetMemberId || '');

      if (!memberId || memberId === targetMemberId) {
        throw new Error('이동할 다른 인원을 선택하세요.');
      }

      if (['court', 'wait', 'active'].indexOf(targetType) < 0) {
        throw new Error('잘못된 이동 위치입니다.');
      }

      const members = readMembers_();
      const courts = readCourts_();
      const waitGroups = readWaitGroups_();
      const startedAt = readCourtStartedAt_();
      const validIds = {};

      members.forEach(function(member) {
        validIds[member.id] = true;
      });

      if (!validIds[memberId] || (targetMemberId && !validIds[targetMemberId])) {
        throw new Error('멤버 정보를 찾을 수 없습니다.');
      }

      function locate(id) {
        let result = { type: 'active', index: '', position: -1 };

        Object.keys(courts).some(function(key) {
          const position = (courts[key] || []).indexOf(id);
          if (position >= 0) {
            result = { type: 'court', index: key, position: position };
            return true;
          }
          return false;
        });

        if (result.type !== 'active') return result;

        waitGroups.some(function(group, index) {
          const position = (group || []).indexOf(id);
          if (position >= 0) {
            result = { type: 'wait', index: String(index), position: position };
            return true;
          }
          return false;
        });

        return result;
      }

      function groupOf(location) {
        if (location.type === 'court') return courts[location.index];
        if (location.type === 'wait') return waitGroups[Number(location.index)];
        return null;
      }

      const source = locate(memberId);
      const targetLocation = {
        type: targetType,
        index: targetIndex,
        position: -1
      };

      if (
        targetType === 'court' &&
        ['1', '2', '3', '4'].indexOf(targetIndex) < 0
      ) {
        throw new Error('잘못된 코트 번호입니다.');
      }

      if (
        targetType === 'wait' &&
        (Number(targetIndex) < 0 || Number(targetIndex) >= WAIT_GROUP_COUNT)
      ) {
        throw new Error('잘못된 대기조 번호입니다.');
      }

      if (targetMemberId) {
        const other = locate(targetMemberId);
        const sourceGroup = groupOf(source);
        const otherGroup = groupOf(other);

        if (sourceGroup) sourceGroup[source.position] = targetMemberId;
        if (otherGroup) otherGroup[other.position] = memberId;

        if (!sourceGroup && otherGroup) {
          otherGroup[other.position] = memberId;
        }

        if (sourceGroup && !otherGroup) {
          sourceGroup[source.position] = targetMemberId;
        }
      } else {
        const destination = groupOf(targetLocation);

        if (destination && destination.length >= GROUP_SIZE) {
          throw new Error('선택한 위치는 이미 4명이 모두 찼습니다.');
        }

        const sourceGroup = groupOf(source);
        if (sourceGroup) sourceGroup.splice(source.position, 1);
        if (destination) destination.push(memberId);
      }

      Object.keys(courts).forEach(function(key) {
        markCourtStartedIfFull_(courts, startedAt, key);
      });

      const playing = {};
      const waiting = {};
      Object.keys(courts).forEach(function(key) {
        (courts[key] || []).forEach(function(id) { playing[id] = true; });
      });
      waitGroups.forEach(function(group) {
        (group || []).forEach(function(id) { waiting[id] = true; });
      });

      members.forEach(function(member) {
        if (playing[member.id]) member.status = 'playing';
        else if (waiting[member.id]) member.status = 'waiting';
        else if (
          member.id === memberId ||
          member.id === targetMemberId
        ) member.status = 'active';
      });

      writeCourts_(courts, startedAt);
      writeWaitGroups_(waitGroups);
      writeMembers_(members);
      touch_();

      return makeState_(members, courts, waitGroups, startedAt);
    }
  );
}

function undoLastAction(pin, state) {
  return withDocumentLock_(
    '직전 작업 실행 취소',
    function() {
      auth_(pin);

      if (!state || !Array.isArray(state.members)) {
        throw new Error('되돌릴 상태 정보가 없습니다.');
      }

      if (state.members.length > MAX_MEMBERS) {
        throw new Error('멤버 데이터가 허용 범위를 초과했습니다.');
      }

      const members = state.members.map(function(member) {
        return {
          id: String(member.id || ''),
          name: String(member.name || '').slice(0, 20),
          gender: member.gender === 'female' ? 'female' : 'male',
          games: Math.max(0, Number(member.games) || 0),
          status: normalizeStatus_(String(member.status || 'active')),
          createdAt: String(member.createdAt || ''),
          grade: String(member.grade || '').slice(0, 12),
          experience: String(member.experience || '').slice(0, 20)
        };
      }).filter(function(member) {
        return member.id && member.name;
      });

      const courts = { '1': [], '2': [], '3': [], '4': [] };
      ['1', '2', '3', '4'].forEach(function(key) {
        courts[key] = normalizeIds_(
          state.courts && (state.courts[key] || state.courts[Number(key)])
        ).slice(0, GROUP_SIZE);
      });

      const waitGroups = [];
      for (let i = 0; i < WAIT_GROUP_COUNT; i++) {
        waitGroups.push(
          normalizeIds_(
            state.waitGroups && state.waitGroups[i]
          ).slice(0, GROUP_SIZE)
        );
      }

      const startedAt = {
        '1': '', '2': '', '3': '', '4': ''
      };
      ['1', '2', '3', '4'].forEach(function(key) {
        startedAt[key] = String(
          state.courtStartedAt &&
          (state.courtStartedAt[key] || state.courtStartedAt[Number(key)]) ||
          ''
        );
      });

      writeMembers_(members);
      writeCourts_(courts, startedAt);
      writeWaitGroups_(waitGroups);
      touch_();

      return makeState_(members, courts, waitGroups, startedAt);
    }
  );
}

function finishCourt(pin, courtNo) {
  return withDocumentLock_(
    '경기 종료 자동 순환',
    function() {
      return finishCourtUnlocked_(
        pin,
        courtNo
      );
    }
  );
}

function removeFromCourt(pin, courtNo, id) {
  return withDocumentLock_(
    '코트에서 빼기',
    function() {
      return removeFromCourtUnlocked_(
        pin,
        courtNo,
        id
      );
    }
  );
}

function removeFromWaitGroup(
  pin,
  groupIndex,
  id
) {
  return withDocumentLock_(
    '대기조에서 빼기',
    function() {
      return removeFromWaitGroupUnlocked_(
        pin,
        groupIndex,
        id
      );
    }
  );
}

function decreaseSelectedGameCounts(pin, ids) {
  return withDocumentLock_(
    '선택 게임 -1',
    function() {
      return decreaseSelectedGameCountsUnlocked_(
        pin,
        ids
      );
    }
  );
}

function resetSelectedGameCounts(pin, ids) {
  return withDocumentLock_(
    '선택 게임 초기화',
    function() {
      return resetSelectedGameCountsUnlocked_(
        pin,
        ids
      );
    }
  );
}

function deleteMembers(pin, ids) {
  return withDocumentLock_(
    '멤버 삭제',
    function() {
      return deleteMembersUnlocked_(
        pin,
        ids
      );
    }
  );
}

function resetAllOperationData(pin) {
  return withDocumentLock_(
    '전체 데이터 초기화',
    function() {
      createBackupSnapshot_();

      return resetAllOperationDataUnlocked_(
        pin
      );
    }
  );
}

function updateMemberStatuses_(ids, status) {
  const members = readMembers_();

  members.forEach(function(member) {
    if (ids.indexOf(member.id) >= 0) {
      member.status = status;
    }
  });

  writeMembers_(members);
}

function removeEverywhere_(ids) {
  const courts = readCourts_();

  Object.keys(courts).forEach(function(key) {
    courts[key] =
      courts[key].filter(function(id) {
        return ids.indexOf(id) < 0;
      });
  });

  writeCourts_(courts);

  const waitGroups = readWaitGroups_();

  for (
    let i = 0;
    i < waitGroups.length;
    i++
  ) {
    waitGroups[i] =
      waitGroups[i].filter(function(id) {
        return ids.indexOf(id) < 0;
      });
  }

  writeWaitGroups_(waitGroups);
}

function normalizeIds_(ids) {
  if (!Array.isArray(ids)) {
    return [];
  }

  const result = [];

  ids.forEach(function(id) {
    id = String(id);

    if (
      id &&
      result.indexOf(id) < 0
    ) {
      result.push(id);
    }
  });

  return result;
}

function readMembers_() {
  const sheet =
    SpreadsheetApp
      .getActiveSpreadsheet()
      .getSheetByName(SHEET_MEMBERS);

  const lastRow = sheet.getLastRow();

  if (lastRow < 2) {
    return [];
  }

  const values =
    sheet
      .getRange(2, 1, lastRow - 1, 8)
      .getValues();

  return values
    .filter(function(row) {
      return String(row[0]).trim() !== '';
    })
    .map(function(row) {
      return {
        id: String(row[0]),
        name: String(row[1]),
        gender:
          String(row[2]) === 'female'
            ? 'female'
            : 'male',
        games: Number(row[3]) || 0,
        status: normalizeStatus_(
          String(row[4])
        ),
        createdAt: String(row[5] || ''),
        grade: String(row[6] || ''),
        experience: String(row[7] || ''),
        /* Legacy APK/client aliases retained for compatibility. */
        level: String(row[6] || ''),
        career: String(row[7] || '')
      };
    });
}

function appendMember_(member) {
  const sheet =
    SpreadsheetApp
      .getActiveSpreadsheet()
      .getSheetByName(SHEET_MEMBERS);

  sheet
    .getRange(sheet.getLastRow() + 1, 1, 1, 8)
    .setValues([[
      member.id,
      member.name,
      member.gender,
      member.games,
      member.status,
      member.createdAt,
      member.grade || '',
      member.experience || ''
    ]]);
}

function writeMembers_(members) {
  const sheet =
    SpreadsheetApp
      .getActiveSpreadsheet()
      .getSheetByName(SHEET_MEMBERS);

  const lastRow = sheet.getLastRow();

  if (lastRow > 1) {
    sheet
      .getRange(2, 1, lastRow - 1, 8)
      .clearContent();
  }

  if (!members.length) {
    return;
  }

  const rows =
    members.map(function(member) {
      return [
        member.id,
        member.name,
        member.gender,
        Number(member.games) || 0,
        member.status,
        member.createdAt || '',
        member.grade || '',
        member.experience || ''
      ];
    });

  sheet
    .getRange(2, 1, rows.length, 8)
    .setValues(rows);
}

function readCourts_() {
  const sheet =
    SpreadsheetApp
      .getActiveSpreadsheet()
      .getSheetByName(SHEET_COURTS);

  const values =
    sheet.getRange(2, 1, 4, 5).getValues();

  const result = {
    '1': [],
    '2': [],
    '3': [],
    '4': []
  };

  values.forEach(function(row) {
    const key = String(row[0]);

    result[key] =
      row
        .slice(1, 5)
        .map(String)
        .filter(function(value) {
          return value !== '';
        });
  });

  return result;
}

function readCourtStartedAt_() {
  const sheet =
    SpreadsheetApp
      .getActiveSpreadsheet()
      .getSheetByName(SHEET_COURTS);

  const values =
    sheet.getRange(2, 1, 4, 6).getDisplayValues();

  const result = {
    '1': '',
    '2': '',
    '3': '',
    '4': ''
  };

  values.forEach(function(row) {
    const key = String(row[0]);

    if (Object.prototype.hasOwnProperty.call(result, key)) {
      result[key] = String(row[5] || '');
    }
  });

  return result;
}

function writeCourts_(courts, startedAt) {
  const sheet =
    SpreadsheetApp
      .getActiveSpreadsheet()
      .getSheetByName(SHEET_COURTS);

  const times = startedAt || readCourtStartedAt_();
  const rows = [];

  for (let i = 1; i <= 4; i++) {
    const key = String(i);
    const group = (courts[key] || []).slice(0, 4);

    while (group.length < 4) {
      group.push('');
    }

    const actualCount = group.filter(function(id) {
      return id !== '';
    }).length;

    const started = actualCount === GROUP_SIZE
      ? String(times[key] || '')
      : '';

    rows.push([
      i,
      group[0],
      group[1],
      group[2],
      group[3],
      started
    ]);
  }

  sheet
    .getRange(2, 1, 4, 6)
    .setValues(rows);
}

function markCourtStartedIfFull_(courts, startedAt, courtNo) {
  const key = String(courtNo);
  const full = (courts[key] || []).length === GROUP_SIZE;

  if (full && !startedAt[key]) {
    startedAt[key] = new Date().toISOString();
  }

  if (!full) {
    startedAt[key] = '';
  }
}

function readWaitGroups_() {
  const sheet =
    SpreadsheetApp
      .getActiveSpreadsheet()
      .getSheetByName(SHEET_WAIT);

  const values =
    sheet.getRange(2, 1, 5, 5).getValues();

  return values.map(function(row) {
    return row
      .slice(1, 5)
      .map(String)
      .filter(function(value) {
        return value !== '';
      });
  });
}

function writeWaitGroups_(waitGroups) {
  const sheet =
    SpreadsheetApp
      .getActiveSpreadsheet()
      .getSheetByName(SHEET_WAIT);

  const rows = [];

  for (let i = 0; i < 5; i++) {
    const group =
      (waitGroups[i] || []).slice(0, 4);

    while (group.length < 4) {
      group.push('');
    }

    rows.push([
      i + 1,
      group[0],
      group[1],
      group[2],
      group[3]
    ]);
  }

  sheet
    .getRange(2, 1, 5, 5)
    .setValues(rows);
}

function ensureSetting_(key, defaultValue) {
  const sheet =
    SpreadsheetApp
      .getActiveSpreadsheet()
      .getSheetByName(SHEET_SETTINGS);

  const lastRow = Math.max(1, sheet.getLastRow());
  const values =
    sheet.getRange(1, 1, lastRow, 2).getDisplayValues();

  for (let i = 1; i < values.length; i++) {
    if (String(values[i][0]) === key) {
      return;
    }
  }

  sheet.appendRow([key, String(defaultValue)]);
}

function getSetting_(key) {
  const sheet =
    SpreadsheetApp
      .getActiveSpreadsheet()
      .getSheetByName(SHEET_SETTINGS);

  const lastRow = Math.max(1, sheet.getLastRow());
  const values =
    sheet.getRange(1, 1, lastRow, 2).getDisplayValues();

  for (let i = 1; i < values.length; i++) {
    if (String(values[i][0]) === key) {
      return String(values[i][1]);
    }
  }

  return '';
}

function setSetting_(key, value) {
  const sheet =
    SpreadsheetApp
      .getActiveSpreadsheet()
      .getSheetByName(SHEET_SETTINGS);

  const lastRow = Math.max(1, sheet.getLastRow());
  const values =
    sheet.getRange(1, 1, lastRow, 2).getDisplayValues();

  for (let i = 1; i < values.length; i++) {
    if (String(values[i][0]) === key) {
      sheet
        .getRange(i + 1, 2)
        .setNumberFormat('@')
        .setValue(String(value));

      return;
    }
  }

  sheet.appendRow([key, String(value)]);
}

function touch_() {
  setSetting_(
    'UPDATED_AT',
    new Date().toISOString()
  );
}
