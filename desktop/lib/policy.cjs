'use strict';

const { createHash } = require('node:crypto');

const DEFAULT_SETTINGS = Object.freeze({
  serverUrl: 'https://www.nblane.cloud',
  profile: '',
  opacity: 0.86,
  backgroundBlur: false,
  refreshIntervalSeconds: 60,
  alwaysOnTop: true,
  launchAtLogin: false,
});
const TOOLBAR_HEIGHT = 44;
const CONTROLS_WIDTH = 216;
const MAX_CONTENT_HEIGHT = 560;
const MIN_WINDOW = Object.freeze({ width: 280, height: 156 });

function normalizeServerUrl(value) {
  if (typeof value !== 'string' || value.length > 2048) {
    throw new Error('请输入有效的服务地址。');
  }
  let url;
  try {
    url = new URL(value.trim());
  } catch {
    throw new Error('请输入完整地址，例如 https://www.nblane.cloud。');
  }
  const loopback = ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
  if (url.protocol !== 'https:' && !(url.protocol === 'http:' && loopback)) {
    throw new Error('服务地址必须使用 HTTPS；本机开发可使用 localhost 的 HTTP 地址。');
  }
  if (url.username || url.password || url.search || url.hash || url.pathname !== '/') {
    throw new Error('只填写服务域名，不要包含账号、路径、查询参数或片段。');
  }
  return url.origin;
}

function normalizeProfile(value, allowEmpty = false) {
  if (typeof value !== 'string') throw new Error('请输入档案名称。');
  const profile = value.trim();
  if ((!profile && !allowEmpty) || profile === '.' || profile === '..' || /[/\\\p{Cc}]/u.test(profile)) {
    throw new Error('档案名称不能为空，也不能包含斜线或控制字符。');
  }
  return profile;
}

function normalizeOpacity(value) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0.1 || value > 1) {
    throw new Error('不透明度必须在 10% 到 100% 之间。');
  }
  return Math.round(value * 100) / 100;
}

function normalizeRefreshInterval(value) {
  if (![15, 30, 60, 120, 300].includes(value)) {
    throw new Error('自动刷新间隔必须为 15、30、60、120 或 300 秒。');
  }
  return value;
}

function normalizeSettings(value) {
  const input = value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  const settings = { ...DEFAULT_SETTINGS };
  try { settings.serverUrl = normalizeServerUrl(input.serverUrl); } catch { /* Use safe defaults for invalid stored values. */ }
  try { settings.profile = normalizeProfile(input.profile, true); } catch { /* Require setup again for an invalid profile. */ }
  try { settings.opacity = normalizeOpacity(input.opacity); } catch { /* Recover the default surface. */ }
  try { settings.refreshIntervalSeconds = normalizeRefreshInterval(input.refreshIntervalSeconds); } catch { /* Preserve the default polling interval for old or invalid preferences. */ }
  if (typeof input.backgroundBlur === 'boolean') settings.backgroundBlur = input.backgroundBlur;
  if (typeof input.alwaysOnTop === 'boolean') settings.alwaysOnTop = input.alwaysOnTop;
  if (typeof input.launchAtLogin === 'boolean') settings.launchAtLogin = input.launchAtLogin;
  return settings;
}

function validateSettingsUpdate(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw new Error('设置格式无效。');
  const settings = {
    serverUrl: normalizeServerUrl(input.serverUrl),
    profile: normalizeProfile(input.profile),
  };
  if (Object.hasOwn(input, 'launchAtLogin')) {
    if (typeof input.launchAtLogin !== 'boolean') throw new Error('开机启动设置无效。');
    settings.launchAtLogin = input.launchAtLogin;
  }
  if (Object.hasOwn(input, 'refreshIntervalSeconds')) {
    settings.refreshIntervalSeconds = normalizeRefreshInterval(input.refreshIntervalSeconds);
  }
  return settings;
}

function miniUrl(settings) {
  const refresh = normalizeRefreshInterval(settings.refreshIntervalSeconds ?? 60);
  return `${normalizeServerUrl(settings.serverUrl)}/p/${encodeURIComponent(normalizeProfile(settings.profile))}/mini?sticker=1&toolbar=full&refresh=${refresh}`;
}

/** Only the configured mini route may supply layout metadata. */
function isIntegratedMiniUrl(value, settings) {
  try {
    const url = new URL(value);
    const expected = new URL(miniUrl(settings));
    return !url.username && !url.password && url.origin === expected.origin
      && url.pathname === expected.pathname && url.searchParams.get('sticker') === '1';
  } catch {
    return false;
  }
}

/** Renderer measurements are untrusted, even on the configured website. */
function contentMetrics(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)
      || !Number.isInteger(value.height) || value.height < 1 || value.height > 100_000
      || typeof value.overlay !== 'boolean') return null;
  return { height: value.height, overlay: value.overlay };
}

function contentHeight(metrics) {
  const value = contentMetrics(metrics);
  if (!value) throw new Error('Invalid sticker content measurement');
  return Math.min(MAX_CONTENT_HEIGHT, Math.max(MIN_WINDOW.height, value.height, value.overlay ? 420 : 0));
}

function browserUrl(settings) {
  return `${normalizeServerUrl(settings.serverUrl)}/p/${encodeURIComponent(normalizeProfile(settings.profile))}/projects`;
}

function isAllowedRemoteUrl(value, serverUrl) {
  try {
    const url = new URL(value);
    return !url.username && !url.password && url.origin === normalizeServerUrl(serverUrl)
      && (url.protocol === 'https:' || url.protocol === 'http:');
  } catch {
    return false;
  }
}

function sessionPartition(serverUrl) {
  return `persist:nblane-sticker-${createHash('sha256').update(normalizeServerUrl(serverUrl)).digest('hex').slice(0, 24)}`;
}

function isTrustedSender(event, owner, entryUrl) {
  try {
    return Boolean(owner && event.sender === owner && event.senderFrame === owner.mainFrame
      && event.senderFrame.url === entryUrl);
  } catch {
    return false;
  }
}

function validBounds(value) {
  return value && typeof value === 'object'
    && ['x', 'y', 'width', 'height'].every((key) => Number.isFinite(value[key]))
    && value.width > 0 && value.height > 0;
}

function intersectionArea(a, b) {
  return Math.max(0, Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x))
    * Math.max(0, Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y));
}

/** Restore only inside an available work area, including negative-coordinate displays. */
function restoreBounds(saved, workAreas, primaryIndex = 0) {
  const areas = workAreas.filter(validBounds);
  if (!areas.length) throw new Error('找不到可用的显示器。');
  let area = areas[Math.min(Math.max(primaryIndex, 0), areas.length - 1)];
  const source = validBounds(saved) ? saved : null;
  if (source) {
    let largest = 0;
    for (const candidate of areas) {
      const overlap = intersectionArea(source, candidate);
      if (overlap > largest) {
        area = candidate;
        largest = overlap;
      }
    }
  }
  const width = Math.round(Math.min(area.width, Math.max(MIN_WINDOW.width, source?.width ?? 360)));
  const height = Math.round(Math.min(area.height, Math.max(MIN_WINDOW.height, source?.height ?? 240)));
  const x = source?.x ?? area.x + area.width - width - 24;
  const y = source?.y ?? area.y + 48;
  return {
    x: Math.round(Math.max(area.x, Math.min(x, area.x + area.width - width))),
    y: Math.round(Math.max(area.y, Math.min(y, area.y + area.height - height))),
    width,
    height,
  };
}

module.exports = {
  DEFAULT_SETTINGS, TOOLBAR_HEIGHT, CONTROLS_WIDTH, MIN_WINDOW, normalizeServerUrl, normalizeProfile,
  normalizeOpacity, normalizeRefreshInterval, normalizeSettings, validateSettingsUpdate, miniUrl, isIntegratedMiniUrl, contentMetrics, contentHeight, browserUrl,
  isAllowedRemoteUrl, sessionPartition, isTrustedSender, validBounds, restoreBounds,
};
