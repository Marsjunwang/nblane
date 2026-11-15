'use strict';

const { createHash } = require('node:crypto');

const DEFAULT_SETTINGS = Object.freeze({
  serverUrl: 'https://www.nblane.cloud',
  profile: '',
  opacity: 1,
  alwaysOnTop: true,
  launchAtLogin: false,
});
const TOOLBAR_HEIGHT = 42;
const MIN_WINDOW = Object.freeze({ width: 280, height: 200 });

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
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0.4 || value > 1) {
    throw new Error('不透明度必须在 40% 到 100% 之间。');
  }
  return Math.round(value * 100) / 100;
}

function normalizeSettings(value) {
  const input = value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  const settings = { ...DEFAULT_SETTINGS };
  try { settings.serverUrl = normalizeServerUrl(input.serverUrl); } catch { /* Use safe defaults for invalid stored values. */ }
  try { settings.profile = normalizeProfile(input.profile, true); } catch { /* Require setup again for an invalid profile. */ }
  try { settings.opacity = normalizeOpacity(input.opacity); } catch { /* Recover at full visibility. */ }
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
  return settings;
}

function miniUrl(settings) {
  return `${normalizeServerUrl(settings.serverUrl)}/p/${encodeURIComponent(normalizeProfile(settings.profile))}/mini`;
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
  const height = Math.round(Math.min(area.height, Math.max(MIN_WINDOW.height, source?.height ?? 300)));
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
  DEFAULT_SETTINGS, TOOLBAR_HEIGHT, MIN_WINDOW, normalizeServerUrl, normalizeProfile,
  normalizeOpacity, normalizeSettings, validateSettingsUpdate, miniUrl, browserUrl,
  isAllowedRemoteUrl, sessionPartition, isTrustedSender, validBounds, restoreBounds,
};
