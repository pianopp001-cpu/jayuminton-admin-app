const JAYUMINTON_PUSH_CONFIG = Object.freeze({
  projectId: 'jayuminton-push',
  packageName: 'com.jayuminton.member',
  tokenUrl: 'https://oauth2.googleapis.com/token',
  fcmUrl: 'https://fcm.googleapis.com/v1/projects/jayuminton-push/messages:send',
  tokenScope: 'https://www.googleapis.com/auth/firebase.messaging',
  tokenCacheKey: 'jayuminton_fcm_access_token'
});

/**
 * Health check. Opening the deployed web-app URL in a browser should return ok:true.
 */
function doGet() {
  return jsonOutput_({
    ok: true,
    service: 'jayuminton-free-fcm-relay',
    projectId: JAYUMINTON_PUSH_CONFIG.projectId
  });
}

/**
 * Free Google Apps Script relay used by the v1.5 admin APK.
 *
 * Security:
 * - The shared secret is received as the URL query parameter `key`.
 * - The Firebase service-account JSON is stored only in Apps Script Properties.
 * - No private key is committed to GitHub or embedded in either APK.
 */
function doPost(e) {
  try {
    const properties = PropertiesService.getScriptProperties();
    const expectedSecret = String(
      properties.getProperty('JAYUMINTON_PUSH_SHARED_SECRET') || ''
    );
    const suppliedSecret = String(
      e && e.parameter ? (e.parameter.key || '') : ''
    );

    if (!secureEquals_(suppliedSecret, expectedSecret)) {
      return jsonOutput_({ok: false, error: 'unauthorized'});
    }

    const rawBody = e && e.postData ? e.postData.contents : '';
    const event = cleanEvent_(JSON.parse(rawBody || '{}'));
    const accessToken = getFcmAccessToken_();
    const requests = event.members.map(function(member) {
      return makeFcmRequest_(event, member, accessToken);
    });

    const responses = UrlFetchApp.fetchAll(requests);
    const results = responses.map(function(response, index) {
      const code = response.getResponseCode();
      const member = event.members[index];
      return {
        memberId: member.id,
        ok: code >= 200 && code < 300,
        status: code,
        response: response.getContentText()
      };
    });

    const failures = results.filter(function(result) {
      return !result.ok;
    });
    if (failures.length) {
      console.error(JSON.stringify({
        message: 'FCM send failed',
        assignmentId: event.assignmentId,
        failures: failures
      }));
    }

    return jsonOutput_({
      ok: failures.length === 0,
      assignmentId: event.assignmentId,
      sent: results.length - failures.length,
      failed: failures.length
    });
  } catch (error) {
    console.error(error && error.stack ? error.stack : String(error));
    return jsonOutput_({
      ok: false,
      error: String(error && error.message ? error.message : error)
    });
  }
}

/**
 * Run once in the Apps Script editor after adding the two Script Properties.
 * A successful return proves the service account can mint an FCM access token.
 */
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
    clientEmail: credentials.client_email
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
    const id = String(member && member.id || '').trim();
    const name = String(member && member.name || '').trim();
    if (!id || !name || id.length > 200 || name.length > 80) return;
    uniqueMembers[id] = {id: id, name: name};
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

function makeFcmRequest_(event, member, accessToken) {
  const data = {
    type: event.type,
    assignmentId: event.assignmentId,
    memberId: member.id,
    memberName: member.name
  };
  if (event.type === 'court_assignment') {
    data.courtNo = String(event.courtNo);
  } else {
    data.expectedCourtNo = String(event.expectedCourtNo);
  }

  const payload = {
    message: {
      topic: topicForMemberId_(member.id),
      data: data,
      android: {
        priority: 'high',
        ttl: '600s',
        restricted_package_name: JAYUMINTON_PUSH_CONFIG.packageName
      }
    }
  };

  return {
    url: JAYUMINTON_PUSH_CONFIG.fcmUrl,
    method: 'post',
    contentType: 'application/json; charset=utf-8',
    headers: {
      Authorization: 'Bearer ' + accessToken
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };
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

function topicForMemberId_(memberId) {
  const bytes = Utilities.computeDigest(
    Utilities.DigestAlgorithm.SHA_256,
    String(memberId || '').trim(),
    Utilities.Charset.UTF_8
  );
  const hex = bytes.map(function(value) {
    const unsigned = value < 0 ? value + 256 : value;
    return ('0' + unsigned.toString(16)).slice(-2);
  }).join('');
  return 'jm_' + hex;
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
