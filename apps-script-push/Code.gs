const JAYUMINTON_PUSH_CONFIG = Object.freeze({
  projectId: 'jayuminton-push',
  tokenUrl: 'https://oauth2.googleapis.com/token',
  fcmUrl: 'https://fcm.googleapis.com/v1/projects/jayuminton-push/messages:send',
  tokenScope: 'https://www.googleapis.com/auth/firebase.messaging',
  tokenCacheKey: 'jayuminton_fcm_access_token',
  webTokenProperty: 'JAYUMINTON_WEB_PUSH_TOKENS_V1',
  memberPageUrl: 'https://script.google.com/macros/s/AKfycbwVgdQG-DXbgxCgd8L11WA57-DCVaOwF4Sc_lktAZZ0yPJSCIosOOKkmKe3oU8a5pfJ7Q/exec',
  maxTokensPerMember: 5,
  maxTotalTokens: 1200,
  tokenMaxAgeMs: 120 * 24 * 60 * 60 * 1000
});

function doGet() {
  return jsonOutput_({
    ok: true,
    service: 'jayuminton-free-web-push-relay',
    projectId: JAYUMINTON_PUSH_CONFIG.projectId,
    registeredTokens: countWebPushTokens_()
  });
}

function doPost(e) {
  try {
    const rawBody = e && e.parameter && e.parameter.payload
      ? String(e.parameter.payload || '')
      : String(e && e.postData ? (e.postData.contents || '') : '');
    const body = JSON.parse(rawBody || '{}');
    const action = String(body.action || '').trim();

    if (action === 'register_web_token') {
      return jsonOutput_(registerWebToken_(body));
    }
    if (action === 'unregister_web_token') {
      return jsonOutput_(unregisterWebToken_(body));
    }

    verifyAdminSecret_(e);
    return jsonOutput_(sendAssignmentEvent_(cleanEvent_(body)));
  } catch (error) {
    console.error(error && error.stack ? error.stack : String(error));
    return jsonOutput_({
      ok: false,
      error: String(error && error.message ? error.message : error)
    });
  }
}

function verifyPushConfiguration() {
  const properties = PropertiesService.getScriptProperties();
  const sharedSecret = String(
    properties.getProperty('JAYUMINTON_PUSH_SHARED_SECRET') || ''
  );
  const serviceAccountJson = String(
    properties.getProperty('FCM_SERVICE_ACCOUNT_JSON') || ''
  );
  if (!sharedSecret) {
    throw new Error('JAYUMINTON_PUSH_SHARED_SECRET Script Property is missing.');
  }
  if (!serviceAccountJson) {
    throw new Error('FCM_SERVICE_ACCOUNT_JSON Script Property is missing.');
  }
  const credentials = JSON.parse(serviceAccountJson);
  if (credentials.project_id !== JAYUMINTON_PUSH_CONFIG.projectId) {
    throw new Error('Service-account project_id must be jayuminton-push.');
  }
  const token = getFcmAccessToken_(true);
  return {
    ok: Boolean(token),
    projectId: credentials.project_id,
    clientEmail: credentials.client_email,
    registeredTokens: countWebPushTokens_()
  };
}

function registerWebToken_(body) {
  const memberId = cleanText_(body.memberId, 200);
  const memberName = cleanText_(body.memberName, 80);
  const token = cleanToken_(body.token);
  const userAgent = cleanText_(body.userAgent, 300);
  if (!memberId || !memberName || !token) {
    throw new Error('memberId, memberName and token are required.');
  }

  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const records = loadWebPushTokens_();
    const now = Date.now();
    const active = records.filter(function(record) {
      return record && record.token &&
        now - Number(record.updatedAt || 0) <=
          JAYUMINTON_PUSH_CONFIG.tokenMaxAgeMs &&
        record.token !== token;
    });
    active.push({
      memberId: memberId,
      memberName: memberName,
      token: token,
      userAgent: userAgent,
      updatedAt: now
    });
    const limited = limitWebPushTokens_(active);
    saveWebPushTokens_(limited);
    return {
      ok: true,
      action: 'registered',
      memberId: memberId,
      memberName: memberName,
      registeredTokens: limited.length
    };
  } finally {
    lock.releaseLock();
  }
}

function unregisterWebToken_(body) {
  const token = cleanToken_(body.token);
  if (!token) throw new Error('token is required.');

  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const records = loadWebPushTokens_();
    const next = records.filter(function(record) {
      return record && record.token !== token;
    });
    saveWebPushTokens_(next);
    return {
      ok: true,
      action: 'unregistered',
      removed: records.length - next.length
    };
  } finally {
    lock.releaseLock();
  }
}

function sendAssignmentEvent_(event) {
  const records = loadWebPushTokens_();
  const now = Date.now();
  const memberIds = {};
  event.members.forEach(function(member) {
    memberIds[member.id] = member;
  });

  const targets = [];
  const seenTokens = {};
  records.forEach(function(record) {
    if (!record || !record.token || seenTokens[record.token]) return;
    if (now - Number(record.updatedAt || 0) >
        JAYUMINTON_PUSH_CONFIG.tokenMaxAgeMs) return;
    const member = memberIds[String(record.memberId || '')];
    if (!member) return;
    seenTokens[record.token] = true;
    targets.push({token: record.token, member: member});
  });

  if (!targets.length) {
    return {
      ok: true,
      assignmentId: event.assignmentId,
      sent: 0,
      failed: 0,
      noRegisteredBrowser: event.members.length
    };
  }

  const accessToken = getFcmAccessToken_();
  const requests = targets.map(function(target) {
    return makeWebFcmRequest_(event, target.member, target.token, accessToken);
  });
  const responses = UrlFetchApp.fetchAll(requests);
  const failedTokens = [];
  let sent = 0;

  responses.forEach(function(response, index) {
    const status = response.getResponseCode();
    if (status >= 200 && status < 300) {
      sent += 1;
      return;
    }
    const text = response.getContentText();
    const target = targets[index];
    console.error(JSON.stringify({
      message: 'FCM web send failed',
      assignmentId: event.assignmentId,
      memberId: target.member.id,
      status: status,
      response: text
    }));
    if (status === 404 || status === 410 ||
        /UNREGISTERED|registration-token-not-registered/i.test(text)) {
      failedTokens.push(target.token);
    }
  });

  if (failedTokens.length) removeInvalidTokens_(failedTokens);
  return {
    ok: sent === targets.length,
    assignmentId: event.assignmentId,
    sent: sent,
    failed: targets.length - sent
  };
}

function makeWebFcmRequest_(event, member, token, accessToken) {
  const isWait = event.type === 'wait1_ready';
  const courtNo = isWait ? event.expectedCourtNo : event.courtNo;
  const title = isWait ? '대기 1순위 안내' : '코트 입장 안내';
  const body = isWait
    ? member.name + '님, 대기 1순위입니다. ' + courtNo +
      '번 코트가 다음으로 나올 예정이니 준비해 주세요.'
    : member.name + '님, ' + courtNo + '번 코트로 들어가 주세요.';

  const payload = {
    message: {
      token: token,
      data: {
        type: event.type,
        assignmentId: event.assignmentId,
        memberId: member.id,
        memberName: member.name,
        title: title,
        body: body,
        link: JAYUMINTON_PUSH_CONFIG.memberPageUrl,
        courtNo: String(event.courtNo || ''),
        expectedCourtNo: String(event.expectedCourtNo || '')
      },
      webpush: {
        headers: {Urgency: 'high', TTL: '600'},
        fcm_options: {link: JAYUMINTON_PUSH_CONFIG.memberPageUrl}
      }
    }
  };

  return {
    url: JAYUMINTON_PUSH_CONFIG.fcmUrl,
    method: 'post',
    contentType: 'application/json; charset=utf-8',
    headers: {Authorization: 'Bearer ' + accessToken},
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };
}

function cleanEvent_(body) {
  const type = String(body && body.type || 'court_assignment').trim();
  const assignmentId = String(body && body.assignmentId || '').trim();
  const sourceMembers = Array.isArray(body && body.members) ? body.members : [];
  if (!/^[A-Za-z0-9_.-]{8,500}$/.test(assignmentId)) {
    throw new Error('Invalid assignmentId.');
  }
  if (type !== 'court_assignment' && type !== 'wait1_ready') {
    throw new Error('Invalid notification type.');
  }

  const uniqueMembers = {};
  sourceMembers.forEach(function(member) {
    const id = cleanText_(member && member.id, 200);
    const name = cleanText_(member && member.name, 80);
    if (id && name) uniqueMembers[id] = {id: id, name: name};
  });
  const members = Object.keys(uniqueMembers).map(function(id) {
    return uniqueMembers[id];
  });

  if (type === 'court_assignment') {
    const courtNo = Number(body.courtNo);
    if ([1, 2, 3, 4].indexOf(courtNo) === -1 || members.length !== 4) {
      throw new Error('Court assignment requires one valid court and four members.');
    }
    return {
      type: type,
      assignmentId: assignmentId,
      courtNo: courtNo,
      expectedCourtNo: 0,
      members: members
    };
  }

  const expectedCourtNo = Number(body.expectedCourtNo);
  if ([1, 2, 3, 4].indexOf(expectedCourtNo) === -1 ||
      members.length < 1 || members.length > 4) {
    throw new Error('Wait-1 notification requires one expected court and one to four members.');
  }
  return {
    type: type,
    assignmentId: assignmentId,
    courtNo: 0,
    expectedCourtNo: expectedCourtNo,
    members: members
  };
}

function verifyAdminSecret_(e) {
  const expected = String(
    PropertiesService.getScriptProperties()
      .getProperty('JAYUMINTON_PUSH_SHARED_SECRET') || ''
  );
  const supplied = String(e && e.parameter ? (e.parameter.key || '') : '');
  if (!secureEquals_(supplied, expected)) throw new Error('unauthorized');
}

function loadWebPushTokens_() {
  const raw = PropertiesService.getScriptProperties()
    .getProperty(JAYUMINTON_PUSH_CONFIG.webTokenProperty);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    return [];
  }
}

function saveWebPushTokens_(records) {
  PropertiesService.getScriptProperties().setProperty(
    JAYUMINTON_PUSH_CONFIG.webTokenProperty,
    JSON.stringify(records || [])
  );
}

function limitWebPushTokens_(records) {
  const sorted = (records || []).slice().sort(function(left, right) {
    return Number(right.updatedAt || 0) - Number(left.updatedAt || 0);
  });
  const perMember = {};
  const result = [];
  sorted.forEach(function(record) {
    if (result.length >= JAYUMINTON_PUSH_CONFIG.maxTotalTokens) return;
    const memberId = String(record.memberId || '');
    perMember[memberId] = Number(perMember[memberId] || 0);
    if (perMember[memberId] >= JAYUMINTON_PUSH_CONFIG.maxTokensPerMember) return;
    perMember[memberId] += 1;
    result.push(record);
  });
  return result;
}

function removeInvalidTokens_(tokens) {
  const invalid = {};
  tokens.forEach(function(token) { invalid[token] = true; });
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    saveWebPushTokens_(loadWebPushTokens_().filter(function(record) {
      return record && !invalid[record.token];
    }));
  } finally {
    lock.releaseLock();
  }
}

function countWebPushTokens_() {
  return loadWebPushTokens_().length;
}

function cleanText_(value, maxLength) {
  return String(value == null ? '' : value).trim().slice(0, maxLength);
}

function cleanToken_(value) {
  const token = String(value == null ? '' : value).trim();
  return !token || token.length < 40 || token.length > 4096 ? '' : token;
}

function getFcmAccessToken_(forceRefresh) {
  const cache = CacheService.getScriptCache();
  if (!forceRefresh) {
    const cached = cache.get(JAYUMINTON_PUSH_CONFIG.tokenCacheKey);
    if (cached) return cached;
  }

  const rawCredentials = PropertiesService.getScriptProperties()
    .getProperty('FCM_SERVICE_ACCOUNT_JSON');
  if (!rawCredentials) {
    throw new Error('FCM_SERVICE_ACCOUNT_JSON Script Property is missing.');
  }
  const credentials = JSON.parse(rawCredentials);
  if (!credentials.client_email || !credentials.private_key) {
    throw new Error('Service-account JSON is missing client_email or private_key.');
  }

  const now = Math.floor(Date.now() / 1000);
  const header = base64Url_(JSON.stringify({alg: 'RS256', typ: 'JWT'}));
  const claim = base64Url_(JSON.stringify({
    iss: credentials.client_email,
    scope: JAYUMINTON_PUSH_CONFIG.tokenScope,
    aud: JAYUMINTON_PUSH_CONFIG.tokenUrl,
    iat: now,
    exp: now + 3600
  }));
  const unsignedJwt = header + '.' + claim;
  const signature = Utilities.computeRsaSha256Signature(
    unsignedJwt,
    credentials.private_key
  );
  const assertion = unsignedJwt + '.' + base64UrlBytes_(signature);

  const response = UrlFetchApp.fetch(JAYUMINTON_PUSH_CONFIG.tokenUrl, {
    method: 'post',
    payload: {
      grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
      assertion: assertion
    },
    muteHttpExceptions: true
  });
  const status = response.getResponseCode();
  const text = response.getContentText();
  if (status < 200 || status >= 300) {
    throw new Error('OAuth token request failed (' + status + '): ' + text);
  }

  const tokenResponse = JSON.parse(text);
  if (!tokenResponse.access_token) {
    throw new Error('OAuth response did not contain access_token.');
  }
  const expiresIn = Math.max(60, Number(tokenResponse.expires_in || 3600) - 300);
  cache.put(
    JAYUMINTON_PUSH_CONFIG.tokenCacheKey,
    tokenResponse.access_token,
    Math.min(21600, expiresIn)
  );
  return tokenResponse.access_token;
}

function base64Url_(text) {
  return base64UrlBytes_(Utilities.newBlob(text).getBytes());
}

function base64UrlBytes_(bytes) {
  return Utilities.base64EncodeWebSafe(bytes).replace(/=+$/g, '');
}

function secureEquals_(left, right) {
  if (!left || !right || left.length !== right.length) return false;
  let difference = 0;
  for (let index = 0; index < left.length; index += 1) {
    difference |= left.charCodeAt(index) ^ right.charCodeAt(index);
  }
  return difference === 0;
}

function jsonOutput_(value) {
  return ContentService
    .createTextOutput(JSON.stringify(value))
    .setMimeType(ContentService.MimeType.JSON);
}
