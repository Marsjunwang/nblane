'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { DEFAULT_SETTINGS } = require('../lib/policy.cjs');
const { readState, writeState } = require('../lib/store.cjs');

function temporary(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'nblane-sticker-test-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return path.join(root, 'preferences', 'sticker-settings.json');
}

test('missing and corrupted preferences recover with a visible unconfigured window', (t) => {
  const filename = temporary(t);
  assert.deepEqual(readState(filename), { settings: DEFAULT_SETTINGS, bounds: null });
  fs.mkdirSync(path.dirname(filename));
  for (const content of ['{broken', 'null', '[]', '"text"']) {
    fs.writeFileSync(filename, content);
    assert.deepEqual(readState(filename), { settings: DEFAULT_SETTINGS, bounds: null });
  }
});

test('preferences round-trip without retaining arbitrary fields or authentication data', (t) => {
  const filename = temporary(t);
  const settings = { ...DEFAULT_SETTINGS, profile: '测试用户', opacity: 0.7, alwaysOnTop: false, launchAtLogin: true };
  const bounds = { x: -1000, y: 50, width: 360, height: 300 };
  writeState(filename, { settings: { ...settings, cookie: 'fixture-only' }, bounds: { ...bounds, token: 'fixture-only' }, password: 'fixture-only' });
  assert.deepEqual(readState(filename), { settings, bounds });
  assert.doesNotMatch(fs.readFileSync(filename, 'utf8'), /fixture-only|password|cookie|token/);
  writeState(filename, { settings: { ...settings, opacity: 1 }, bounds });
  assert.equal(readState(filename).settings.opacity, 1);
  assert.deepEqual(fs.readdirSync(path.dirname(filename)), ['sticker-settings.json']);
  if (process.platform !== 'win32') assert.equal(fs.statSync(filename).mode & 0o777, 0o600);
});
