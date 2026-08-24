import fs from 'node:fs';
import assert from 'node:assert/strict';

const src = fs.readFileSync(new URL('./worker-do.js', import.meta.url), 'utf8');

assert.ok(src.includes("if (!['wait1_ready', 'court_assignment'].includes(type))"), 'assignment push event allowlist regressed');
assert.ok(src.includes("memberIds: members.map(m => m.id)"), 'push target lookup must use only event member ids');
assert.ok(src.includes("const memberById = Object.fromEntries(members.map(m => [m.id, m]))"), 'target member map missing');
assert.ok(src.includes("repeatCount: '8'"), '8 vibration groups payload missing');
assert.ok(src.includes("pulsesPerGroup: '3'"), '3 pulses per group payload missing');
assert.ok(src.includes("stopOnConfirm: 'true'"), 'confirm-stop payload missing');
assert.ok(src.includes("restricted_package_name = 'com.jayuminton.user'"), 'current user app package restriction missing');
assert.ok(src.includes("url.pathname === '/api/push/event'"), 'push event endpoint missing');
assert.ok(src.includes("if (!members.length || members.length > 4)"), 'assignment target cardinality guard missing');
assert.equal(/script\.google\.com|googleusercontent\.com/.test(src), false, 'GAS dependency leaked into push worker');

console.log('USER_PUSH_TARGET_3X8_CONTRACT_OK');
