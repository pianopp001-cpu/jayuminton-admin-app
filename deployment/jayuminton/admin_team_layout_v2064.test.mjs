import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

function classList() {
  const values = new Set();
  return {
    add(...names) { names.forEach(name => values.add(name)); },
    remove(...names) { names.forEach(name => values.delete(name)); },
    toggle(name, force) {
      if (force === undefined) force = !values.has(name);
      if (force) values.add(name); else values.delete(name);
      return force;
    },
    contains(name) { return values.has(name); },
  };
}

function card(id) {
  const attributes = { 'data-member-id': id };
  const properties = {};
  return {
    classList: classList(),
    style: {
      setProperty(name, value) { properties[name] = value; },
      removeProperty(name) { delete properties[name]; },
      getPropertyValue(name) { return properties[name] || ''; },
    },
    getAttribute(name) { return attributes[name] || ''; },
    setAttribute(name, value) { attributes[name] = String(value); },
    removeAttribute(name) { delete attributes[name]; },
    querySelector() { return null; },
    querySelectorAll() { return []; },
    matches() { return false; },
  };
}

const cards = ['1', '2', '3', '4', '5', '6'].map(card);
const members = [
  { id: '1', bundleId: 'legacy-shared-bundle', teamLabel: '팀 1', teamColor: '#6d28d9' },
  { id: '2', bundleId: 'legacy-shared-bundle', teamLabel: '팀 1', teamColor: '#6d28d9' },
  { id: '3', bundleId: 'legacy-shared-bundle', teamLabel: '팀 2', teamColor: '#6d28d9' },
  { id: '4', bundleId: 'legacy-shared-bundle', teamLabel: '팀 2', teamColor: '#6d28d9' },
  { id: '5', bundleId: 'legacy-shared-bundle', teamLabel: '팀 3', teamColor: '#6d28d9' },
  { id: '6', bundleId: 'legacy-shared-bundle', teamLabel: '팀 3', teamColor: '#6d28d9' },
];

const elements = new Map();
const app = {
  querySelectorAll(selector) {
    return selector === '.wait-card,.wait-item' ? [] : cards;
  },
};
elements.set('adminApp', app);

let domReady;
const document = {
  readyState: 'loading',
  head: {
    appendChild(node) {
      node.remove = () => elements.delete(node.id);
      elements.set(node.id, node);
    },
  },
  documentElement: { appendChild(node) { document.head.appendChild(node); } },
  getElementById(id) { return elements.get(id) || null; },
  createElement() { return { id: '', textContent: '', remove() {} }; },
  addEventListener(type, handler) { if (type === 'DOMContentLoaded') domReady = handler; },
};

class MutationObserver {
  constructor(handler) { this.handler = handler; }
  observe() {}
}

const context = {
  document,
  STATE: { members },
  MutationObserver,
  requestAnimationFrame(handler) { handler(); },
  setTimeout(handler) { handler(); return 1; },
};
context.window = context;

const source = await readFile(new URL('./admin_team_layout_v2038.js', import.meta.url), 'utf8');
vm.runInNewContext(source, context, { filename: 'admin_team_layout_v2038.js' });
assert.equal(typeof domReady, 'function');
domReady();

const colors = cards.map(item => item.style.getPropertyValue('--member-team-color'));
assert.equal(colors[0], colors[1]);
assert.equal(colors[2], colors[3]);
assert.equal(colors[4], colors[5]);
assert.equal(new Set([colors[0], colors[2], colors[4]]).size, 3, 'every permanent team must have a distinct color');

const css = elements.get('jm-team-v2066').textContent;
assert.match(css, /border:2px solid var\(--member-team-color/);
assert.match(css, /0 0 0 2px rgba\(255,255,255/);
assert.match(css, /0 0 0 4px var\(--member-team-color/);
assert.doesNotMatch(css, /inset 0 0 0/);
assert.doesNotMatch(css, /inset\s+5px\s+0/);
assert.doesNotMatch(css, /padding-left/);
assert.doesNotMatch(css, /border-left/);
assert.doesNotMatch(css, /min-height:88px/);
assert.doesNotMatch(css, /padding-bottom:28px/);

const interactionSource = await readFile(new URL('./admin_card_interaction_v2042.js', import.meta.url), 'utf8');
assert.match(interactionSource, /function clearMessageSelection\(\)/);
assert.match(interactionSource, /SELECTED\.clear\(\)/);
assert.match(interactionSource, /__JAYUMINTON_RESET_MULTI_SELECTION_V2057__/);
assert.match(interactionSource, /if\(!selected\.length\)clearMessageSelection\(\)/);
// The active button is dynamically disabled only when the current selection is not from one place.
assert.match(interactionSource, /class=\"jm-do-active\"/);
assert.match(interactionSource, />코트배정 대기<\/button>/);
assert.match(interactionSource, /canActive=samePlace\(selected\)/);
assert.match(interactionSource, /function moveSelectedToActive\(ids\)/);
assert.match(interactionSource, /ids\.length<2\|\|ids\.length>4\|\|!samePlace\(ids\)/);
assert.match(interactionSource, /rpc\('setMemberStatus',\[null,ids,'active'\]\)/);
assert.match(interactionSource, /grid-template-columns:repeat\(2,minmax\(0,1fr\)\)/);

const injectorSource = await readFile(new URL('./inject_cloudflare_v6_frontend_bridge.py', import.meta.url), 'utf8');
assert.match(injectorSource, /__JAYUMINTON_ADMIN_SELECTION_SCOPE_V2057__/);
assert.match(injectorSource, /id=\"quickClearSelectionButton\"/);
assert.match(injectorSource, /class=\"jm-quick-member-actions\"/);
assert.match(injectorSource, /#adminApp #quickMoveBar\.quick-move-bar\{display:grid!important;grid-template-columns:repeat\(4,minmax\(0,1fr\)\)!important/);
assert.match(injectorSource, /overflow-x:hidden!important/);
assert.match(injectorSource, /onclick=\"startMemberEdit\(\)\">편집<\/button>/);
assert.match(injectorSource, /id=\"cancelMemberEditButton\"/);
assert.match(injectorSource, /closeQuickMemberMessage\(true\)/);
assert.match(injectorSource, /await window\.server\('addMember'/);
assert.match(injectorSource, /__JAYUMINTON_ADMIN_MEMBER_SAVE_V2065__/);
assert.match(injectorSource, /window\.addMember=function\(\)\{return save\('add'\);\}/);
assert.match(injectorSource, /window\.applyMemberEdit=function\(\)\{return save\('edit'\);\}/);
assert.match(injectorSource, /window\.server\(editing\?'updateMemberProfile':'addMember',args\)/);
assert.match(injectorSource, /saveButton&&!saveBusy/);
assert.match(injectorSource, /ADD_MEMBER_IN_FLIGHT\|\|!!ACTION_IN_FLIGHT/);
assert.match(injectorSource, /legacy google\.script\.run member registration survived/);

const userVisualSource = await readFile(new URL('./patch_team_visuals_v6.py', import.meta.url), 'utf8');
assert.match(userVisualSource, /JAYUMINTON_TEAM_VISUALS_V8/);
assert.match(userVisualSource, /border:2px solid var\(--jm-team-color/);
assert.match(userVisualSource, /0 0 0 2px rgba\(255,255,255/);
assert.match(userVisualSource, /0 0 0 4px var\(--jm-team-color/);
assert.match(userVisualSource, /'#7c3aed','#0891b2','#ea580c','#059669'/);

console.log('ADMIN_TEAM_LAYOUT_V2066_OK distinct=true vivid-double=true size-stable=true user-admin-consistent=true');
