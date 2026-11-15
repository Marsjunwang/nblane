'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const {
  DEFAULT_SETTINGS, normalizeServerUrl, normalizeProfile, normalizeOpacity, normalizeSettings,
  validateSettingsUpdate, miniUrl, isAllowedRemoteUrl, sessionPartition, isTrustedSender, restoreBounds,
} = require('../lib/policy.cjs');

test('server configuration accepts secure origins and explicit local development only', () => {
  assert.equal(normalizeServerUrl(' https://example.test:8443/ '), 'https://example.test:8443');
  for (const address of ['http://localhost:18504', 'http://127.0.0.1:18504', 'http://[::1]:18504']) {
    assert.equal(normalizeServerUrl(address), address);
  }
  for (const address of [
    'http://example.test', 'http://localhost.attacker.test', 'http://192.168.1.1',
    'file:///tmp/page.html', 'javascript:alert(1)', 'data:text/html,hello',
    'https://name:password@example.test', 'https://example.test/p/alice/mini',
    'https://example.test/?token=example', 'https://example.test/#access', 'not a URL',
  ]) {
    assert.throws(() => normalizeServerUrl(address), { name: 'Error' }, address);
  }
});

test('profile URLs encode display text and reject path or control characters', () => {
  assert.equal(normalizeProfile('  测试 用户  '), '测试 用户');
  assert.equal(miniUrl({ serverUrl: 'https://example.test', profile: '测试 #? 用户' }),
    'https://example.test/p/%E6%B5%8B%E8%AF%95%20%23%3F%20%E7%94%A8%E6%88%B7/mini');
  for (const name of ['', ' ', '.', '..', '../alice', 'alice/bob', 'alice\\bob', 'a\u0000b', 'a\u0085b']) {
    assert.throws(() => normalizeProfile(name), { name: 'Error' });
  }
});

test('remote navigation cannot escape its configured origin or launch privileged URLs', () => {
  const server = 'https://example.test';
  assert.equal(isAllowedRemoteUrl('https://example.test/login?next=%2Fp%2Ftest%2Fmini', server), true);
  assert.equal(isAllowedRemoteUrl('https://example.test:443/p/test/projects', server), true);
  for (const destination of [
    'https://example.test.evil.test/p/test', 'https://evil.test/?next=https://example.test',
    'https://example.test@evil.test', 'https://evil@example.test', 'http://example.test',
    'https://example.test:444', 'file:///tmp/a', 'javascript:alert(1)', 'mailto:a@example.test',
  ]) {
    assert.equal(isAllowedRemoteUrl(destination, server), false, destination);
  }
  assert.equal(isAllowedRemoteUrl('http://localhost:18504/login', 'http://localhost:18504'), true);
  assert.equal(isAllowedRemoteUrl('http://localhost:8504/login', 'http://localhost:18504'), false);
});

test('session identity follows normalized server origin and stays separate between deployments', () => {
  assert.equal(sessionPartition('https://example.test/'), sessionPartition('https://example.test:443'));
  assert.notEqual(sessionPartition('https://example.test'), sessionPartition('https://other.test'));
  assert.notEqual(sessionPartition('https://example.test'), sessionPartition('https://example.test:8443'));
  assert.match(sessionPartition('https://example.test'), /^persist:nblane-sticker-[a-f0-9]{24}$/);
});

test('IPC requires both the actual local WebContents and its exact main frame', () => {
  const entry = 'file:///app/renderer/index.html';
  const frame = { url: entry };
  const owner = { mainFrame: frame };
  assert.equal(isTrustedSender({ sender: owner, senderFrame: frame }, owner, entry), true);
  assert.equal(isTrustedSender({ sender: { mainFrame: frame }, senderFrame: frame }, owner, entry), false);
  assert.equal(isTrustedSender({ sender: owner, senderFrame: { url: entry } }, owner, entry), false);
  frame.url = `${entry}?remote=true`;
  assert.equal(isTrustedSender({ sender: owner, senderFrame: frame }, owner, entry), false);
  frame.url = 'https://example.test';
  assert.equal(isTrustedSender({ sender: owner, senderFrame: frame }, owner, entry), false);
  assert.equal(isTrustedSender({ sender: owner, senderFrame: null }, owner, entry), false);
});

test('opacity never permits an invisible or invalid window', () => {
  for (const value of [0, 0.39, 1.01, NaN, Infinity, '0.5', null]) {
    assert.throws(() => normalizeOpacity(value), { name: 'Error' });
  }
  assert.equal(normalizeOpacity(0.4), 0.4);
  assert.equal(normalizeOpacity(0.855), 0.86);
  assert.equal(normalizeOpacity(1), 1);
});

test('stored preferences recover unsafe values and discard undeclared fields', () => {
  assert.deepEqual(normalizeSettings({
    serverUrl: 'file:///tmp/x', profile: '../x', opacity: 0, alwaysOnTop: 'false',
    launchAtLogin: 'yes', password: 'fixture-only', preload: '/tmp/evil.cjs',
  }), DEFAULT_SETTINGS);
  assert.deepEqual(validateSettingsUpdate({
    serverUrl: 'https://example.test', profile: 'demo', launchAtLogin: false,
    opacity: 0, alwaysOnTop: false, executable: '/tmp/ignored',
  }), { serverUrl: 'https://example.test', profile: 'demo', launchAtLogin: false });
  assert.throws(() => validateSettingsUpdate({ serverUrl: 'https://example.test', profile: 'demo', launchAtLogin: 'true' }));
});

test('window restoration recovers unplugged displays and keeps negative-coordinate displays', () => {
  const primary = { x: 0, y: 25, width: 1440, height: 875 };
  const left = { x: -1920, y: 0, width: 1920, height: 1080 };
  assert.deepEqual(restoreBounds({ x: -1500, y: 40, width: 360, height: 300 }, [primary, left]),
    { x: -1500, y: 40, width: 360, height: 300 });
  assert.deepEqual(restoreBounds({ x: -1500, y: 40, width: 360, height: 300 }, [primary]),
    { x: 0, y: 40, width: 360, height: 300 });
  assert.deepEqual(restoreBounds({ x: 1400, y: 880, width: 500, height: 500 }, [primary]),
    { x: 940, y: 400, width: 500, height: 500 });
  const huge = restoreBounds({ x: 0, y: 0, width: 10000, height: 10000 }, [primary]);
  assert.deepEqual(huge, primary);
  assert.deepEqual(restoreBounds(null, [primary]), { x: 1056, y: 73, width: 360, height: 300 });
  assert.equal(restoreBounds({ x: NaN, y: 0, width: 500, height: 500 }, [primary]).width, 360);
});
