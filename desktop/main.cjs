'use strict';

const path = require('node:path');
const fs = require('node:fs');
const { pathToFileURL } = require('node:url');
const { app, BrowserWindow, WebContentsView, ipcMain, Menu, Tray, nativeImage, screen, session, shell } = require('electron');
const {
  TOOLBAR_HEIGHT, MIN_WINDOW, normalizeOpacity, validateSettingsUpdate,
  miniUrl, browserUrl, isAllowedRemoteUrl, sessionPartition, isTrustedSender, restoreBounds,
} = require('./lib/policy.cjs');
const { readState, writeState } = require('./lib/store.cjs');
const theme = require('./lib/theme.cjs');

// Explicit isolation hook for desktop smoke tests and separate local instances.
if (process.env.NBLANE_STICKER_USER_DATA) {
  const isolatedData = path.resolve(process.env.NBLANE_STICKER_USER_DATA);
  fs.mkdirSync(isolatedData, { recursive: true, mode: 0o700 });
  app.setPath('userData', isolatedData);
}

const entryPath = path.join(__dirname, 'renderer', 'index.html');
const entryUrl = pathToFileURL(entryPath).href;
let window = null;
let remote = null;
let tray = null;
let preferences;
let preferencesPath;
let screenMode = 'settings';
let loading = false;
let error = null;
let quitting = false;
let persistTimer;
let remoteGeneration = 0;
let clearRemoteLoad = () => {};
const REMOTE_LOAD_TIMEOUT_MS = 20_000;

const canLaunchAtLogin = () => process.platform === 'darwin' && app.isPackaged;
const configured = () => Boolean(preferences?.settings.profile);

function state() {
  return {
    settings: { ...preferences.settings },
    configured: configured(),
    loading,
    error,
    screen: screenMode,
    canLaunchAtLogin: canLaunchAtLogin(),
    version: app.getVersion(),
  };
}

function persistNow() {
  clearTimeout(persistTimer);
  persistTimer = undefined;
  writeState(preferencesPath, preferences);
}

function persistSoon() {
  clearTimeout(persistTimer);
  persistTimer = setTimeout(() => {
    try { persistNow(); } catch { /* Preferences can be retried by the next explicit setting change. */ }
  }, 200);
}

function publish() {
  if (window && !window.isDestroyed() && !window.webContents.isDestroyed()) {
    window.webContents.send('sticker:state', state());
  }
  refreshTray();
}

function layoutRemote() {
  if (!remote || !window || window.isDestroyed()) return;
  const [width, height] = window.getContentSize();
  remote.setBounds({ x: 0, y: TOOLBAR_HEIGHT, width, height: Math.max(0, height - TOOLBAR_HEIGHT) });
  remote.setVisible(screenMode === 'content' && !error && !loading);
}

function showWindow() {
  if (!window || window.isDestroyed()) return;
  if (window.isMinimized()) window.restore();
  window.show();
  window.focus();
  refreshTray();
}

function hideWindow() {
  if (!window || window.isDestroyed()) return;
  // A failed tray must not leave an invisible process with no recovery entry.
  if (tray) window.hide();
  else window.minimize();
  refreshTray();
}

function setOpacity(value) {
  const opacity = normalizeOpacity(value);
  preferences.settings.opacity = opacity;
  if (process.platform === 'darwin' || process.platform === 'win32') window?.setOpacity(opacity);
  persistSoon();
  publish();
}

function setPin(enabled) {
  if (typeof enabled !== 'boolean') throw new Error('置顶设置无效。');
  window?.setAlwaysOnTop(enabled, 'floating');
  preferences.settings.alwaysOnTop = enabled;
  persistSoon();
  publish();
}

function togglePin() {
  setPin(!preferences.settings.alwaysOnTop);
}

function showSettings() {
  if (window && !window.isDestroyed() && screenMode === 'content') preferences.bounds = window.getBounds();
  screenMode = 'settings';
  if (window && !window.isDestroyed()) {
    const bounds = window.getBounds();
    window.setBounds(availableBounds({ ...bounds, height: Math.max(420, bounds.height) }));
  }
  layoutRemote();
  publish();
}

function showContent() {
  screenMode = 'content';
  if (window && !window.isDestroyed()) {
    const currentBounds = window.getBounds();
    window.setBounds(availableBounds(preferences.bounds ?? { ...currentBounds, height: 300 }));
    preferences.bounds = window.getBounds();
    persistSoon();
  }
  layoutRemote();
  publish();
}

function setLaunchAtLogin(enabled) {
  if (!canLaunchAtLogin()) throw new Error('请将打包后的 macOS 应用放入“应用程序”后再设置开机启动。');
  app.setLoginItemSettings({ openAtLogin: enabled });
  preferences.settings.launchAtLogin = app.getLoginItemSettings().openAtLogin;
}

async function openBrowser(url = configured() ? browserUrl(preferences.settings) : null) {
  if (!url || !isAllowedRemoteUrl(url, preferences.settings.serverUrl)) return;
  await shell.openExternal(url);
}

function refreshTray() {
  if (!tray || tray.isDestroyed() || !preferences) return;
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: window?.isVisible() ? '隐藏贴纸' : '显示贴纸', click: () => window?.isVisible() ? hideWindow() : showWindow() },
    { type: 'separator' },
    { label: '始终置顶', type: 'checkbox', checked: preferences.settings.alwaysOnTop, click: (item) => setPin(item.checked) },
    { label: '不透明度', submenu: [1, 0.85, 0.7, 0.5].map((opacity) => ({
      label: opacity === 1 ? '100% · 恢复不透明' : `${Math.round(opacity * 100)}%`,
      type: 'radio', checked: preferences.settings.opacity === opacity, click: () => setOpacity(opacity),
    })) },
    { label: '开机启动', type: 'checkbox', enabled: canLaunchAtLogin(), checked: preferences.settings.launchAtLogin, click: (item) => {
      try { setLaunchAtLogin(item.checked); persistNow(); publish(); } catch { publish(); }
    } },
    { label: '连接设置…', click: () => { showSettings(); showWindow(); } },
    { label: '在浏览器打开', enabled: configured(), click: () => { void openBrowser().catch(() => {}); } },
    { type: 'separator' },
    { label: '退出 nblane 贴纸', accelerator: 'CommandOrControl+Q', click: () => app.quit() },
  ]));
}

function createTray() {
  try {
    const icon = nativeImage.createFromPath(path.join(__dirname, 'renderer', 'trayTemplate.png'));
    if (icon.isEmpty()) return;
    const sized = icon.resize({ width: 18, height: 18 });
    sized.setTemplateImage(true);
    tray = new Tray(sized);
    tray.setToolTip('nblane 贴纸');
    tray.on('double-click', showWindow);
    refreshTray();
    if (process.platform === 'darwin') app.dock.hide();
  } catch {
    tray = null;
  }
}

function destroyRemote() {
  remoteGeneration += 1;
  clearRemoteLoad();
  clearRemoteLoad = () => {};
  if (!remote) return;
  const previous = remote;
  remote = null;
  if (window && !window.isDestroyed()) window.contentView.removeChildView(previous);
  if (!previous.webContents.isDestroyed()) previous.webContents.close({ waitForBeforeUnload: false });
}

function navigationUrl(details) {
  return typeof details === 'string' ? details : details?.url;
}

function connectionError(code, description) {
  const label = typeof description === 'string' && /^ERR_[A-Z0-9_]+$/.test(description) ? description : '';
  const reason = code === -105 ? '找不到网站，请检查服务地址和网络。'
    : code === -106 ? '网络已断开，请连接网络后重试。'
    : code === -102 ? '网站拒绝了连接，请确认服务正在运行。'
    : code === -118 || code === -7 ? '连接超时，请检查网络后重试。'
    : code <= -200 && code >= -299 ? '网站证书验证失败，请检查服务地址和系统时间。'
    : code === -3 ? '页面连接已取消，请重新连接。'
    : '暂时无法连接网站，请检查网络和服务地址后重试。';
  const detail = label || (Number.isInteger(code) ? String(code) : '');
  return detail ? `${reason}（${detail}）` : reason;
}

function loadRemote() {
  if (!configured() || !window || window.isDestroyed()) return;
  destroyRemote();
  const generation = remoteGeneration;
  const serverUrl = preferences.settings.serverUrl;
  const partition = session.fromPartition(sessionPartition(serverUrl));
  partition.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
  partition.setPermissionCheckHandler(() => false);
  const view = new WebContentsView({ webPreferences: {
    session: partition,
    contextIsolation: true,
    sandbox: true,
    nodeIntegration: false,
    webSecurity: true,
    allowRunningInsecureContent: false,
  } });
  remote = view;
  view.setBackgroundColor(theme.pageBg);
  window.contentView.addChildView(view);
  loading = true;
  error = null;
  let failed = false;
  let documentReady = false;
  let loadTimer;
  let activeUrl = miniUrl(preferences.settings);
  let navigation = 0;
  let initialNavigation;
  const current = () => remote === view && remoteGeneration === generation && !view.webContents.isDestroyed();
  const clearLoadTimer = () => {
    clearTimeout(loadTimer);
    loadTimer = undefined;
  };
  clearRemoteLoad = clearLoadTimer;
  const fail = (message) => {
    if (!current() || failed) return;
    clearLoadTimer();
    failed = true;
    loading = false;
    error = message;
    layoutRemote();
    publish();
  };
  const beginLoad = (url) => {
    if (!current()) return;
    clearLoadTimer();
    navigation += 1;
    activeUrl = url;
    documentReady = false;
    failed = false;
    loading = true;
    error = null;
    const attempt = navigation;
    loadTimer = setTimeout(() => {
      if (!current() || attempt !== navigation || !loading) return;
      fail('连接超过 20 秒，请检查网络或网站地址后重试。（ERR_TIMED_OUT）');
      view.webContents.stop();
    }, REMOTE_LOAD_TIMEOUT_MS);
    layoutRemote();
    publish();
  };
  const showReadyDocument = () => {
    if (!current() || failed || !isAllowedRemoteUrl(view.webContents.getURL(), serverUrl)) return;
    clearLoadTimer();
    documentReady = true;
    loading = false;
    error = null;
    layoutRemote();
    publish();
  };
  const denyOtherOrigin = (event, details, _isInPlace, legacyIsMainFrame) => {
    const url = navigationUrl(details) || event.url;
    if (!isAllowedRemoteUrl(url, serverUrl)) {
      event.preventDefault();
      if (event.isMainFrame ?? legacyIsMainFrame ?? true) {
        fail('页面试图跳转到其他网站，已停止连接。请检查网站地址。');
      }
    }
  };
  view.webContents.on('will-navigate', denyOtherOrigin);
  view.webContents.on('will-redirect', denyOtherOrigin);
  view.webContents.on('will-frame-navigate', denyOtherOrigin);
  view.webContents.on('will-attach-webview', (event) => event.preventDefault());
  view.webContents.setWindowOpenHandler(({ url }) => {
    if (isAllowedRemoteUrl(url, serverUrl)) void openBrowser(url).catch(() => {});
    return { action: 'deny' };
  });
  // SPA history changes and subframes can spin Chromium's loading indicator
  // without a new top-level document or a matching did-finish-load event.
  view.webContents.on('did-start-navigation', (details, url, isInPlace, isMainFrame) => {
    if (!(details.isMainFrame ?? isMainFrame) || (details.isSameDocument ?? isInPlace)) return;
    beginLoad(details.url || url);
    initialNavigation ??= navigation;
  });
  view.webContents.on('did-redirect-navigation', (details, url, _isInPlace, isMainFrame) => {
    if (current() && (details.isMainFrame ?? isMainFrame)) activeUrl = details.url || url;
  });
  view.webContents.on('dom-ready', showReadyDocument);
  view.webContents.on('did-finish-load', showReadyDocument);
  view.webContents.on('did-stop-loading', () => {
    if (!current() || !loading || failed) return;
    const attempt = navigation;
    setImmediate(() => {
      if (!current() || attempt !== navigation || !loading || failed || view.webContents.isLoadingMainFrame()) return;
      if (documentReady) showReadyDocument();
      else fail(connectionError(-3, 'ERR_ABORTED'));
    });
  });
  const failLoad = (_event, code, description, url, isMainFrame) => {
    if (!current() || !isMainFrame || (url && url !== activeUrl)) return;
    if (code === -3) {
      // Cancellation can belong to a superseded request, even for the same URL.
      // The replacement request owns its timer; stopped current loads are
      // finalized by did-stop-loading instead of overwriting a working page.
      return;
    }
    fail(connectionError(code, description));
  };
  view.webContents.on('did-fail-load', failLoad);
  view.webContents.on('did-fail-provisional-load', failLoad);
  view.webContents.on('render-process-gone', () => fail('任务页面已停止运行，请重新加载。'));
  beginLoad(activeUrl);
  void view.webContents.loadURL(activeUrl).catch((cause) => {
    // A newer navigation owns its own events and timeout. A rejected promise
    // from the initial request must not replace that newer page's state.
    if (!current() || !loading || (initialNavigation !== undefined && initialNavigation !== navigation)) return;
    fail(connectionError(cause.errno, cause.code));
  });
}

async function invoke(action, payload) {
  switch (action) {
    case 'get-state': return state();
    case 'save-settings': {
      const update = validateSettingsUpdate(payload);
      if (Object.hasOwn(update, 'launchAtLogin') && update.launchAtLogin !== preferences.settings.launchAtLogin) {
        setLaunchAtLogin(update.launchAtLogin);
      }
      preferences.settings = {
        ...preferences.settings,
        serverUrl: update.serverUrl,
        profile: update.profile,
      };
      persistNow();
      showContent();
      loadRemote();
      break;
    }
    case 'set-opacity': setOpacity(payload); break;
    case 'set-pin': setPin(payload); break;
    case 'toggle-pin': togglePin(); break;
    case 'hide': hideWindow(); break;
    case 'retry': if (configured()) { screenMode = 'content'; loadRemote(); } break;
    case 'show-settings': showSettings(); break;
    case 'cancel-settings':
      if (configured()) showContent();
      break;
    case 'open-browser': await openBrowser(); break;
    case 'quit': app.quit(); break;
    default: throw new Error('不支持的操作。');
  }
  return state();
}

function availableBounds(saved) {
  const displays = screen.getAllDisplays();
  const primary = screen.getPrimaryDisplay();
  return restoreBounds(saved, displays.map((display) => display.workArea), displays.findIndex((display) => display.id === primary.id));
}

function createWindow() {
  const bounds = availableBounds(preferences.bounds);
  window = new BrowserWindow({
    ...availableBounds(configured() ? bounds : { ...bounds, height: Math.max(420, bounds.height) }),
    minWidth: MIN_WINDOW.width,
    minHeight: MIN_WINDOW.height,
    frame: false,
    hasShadow: true,
    show: false,
    maximizable: false,
    fullscreenable: false,
    backgroundColor: theme.pageBg,
    title: 'nblane 贴纸',
    alwaysOnTop: preferences.settings.alwaysOnTop,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      sandbox: true,
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: true,
    },
  });
  window.setAlwaysOnTop(preferences.settings.alwaysOnTop, 'floating');
  if (process.platform === 'darwin' || process.platform === 'win32') window.setOpacity(preferences.settings.opacity);
  if (process.platform === 'darwin') window.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  window.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  window.webContents.on('will-navigate', (event) => event.preventDefault());
  window.webContents.on('will-attach-webview', (event) => event.preventDefault());
  window.webContents.on('did-finish-load', publish);
  const rememberBounds = () => {
    if (!window || window.isDestroyed() || window.isMinimized() || screenMode === 'settings') return;
    preferences.bounds = window.getBounds();
    persistSoon();
  };
  window.on('resize', () => { layoutRemote(); rememberBounds(); });
  window.on('move', rememberBounds);
  window.on('show', refreshTray);
  window.on('hide', refreshTray);
  window.on('close', (event) => {
    if (!quitting && tray) {
      event.preventDefault();
      hideWindow();
      return;
    }
    destroyRemote();
  });
  window.on('closed', () => { window = null; });
  createTray();
  window.once('ready-to-show', () => {
    const backgroundStart = canLaunchAtLogin() && app.getLoginItemSettings().wasOpenedAtLogin;
    if (!backgroundStart || !tray || !configured()) showWindow();
  });
  void window.loadFile(entryPath);
  if (configured()) loadRemote();
}

if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on('second-instance', showWindow);
  app.on('activate', showWindow);
  app.on('before-quit', () => {
    quitting = true;
    try { if (preferences) persistNow(); } catch { /* Do not block quitting on an unavailable preferences volume. */ }
  });
  app.on('window-all-closed', () => app.quit());
  void app.whenReady().then(() => {
    preferencesPath = path.join(app.getPath('userData'), 'sticker-settings.json');
    preferences = readState(preferencesPath);
    if (canLaunchAtLogin()) preferences.settings.launchAtLogin = app.getLoginItemSettings().openAtLogin;
    screenMode = configured() ? 'content' : 'settings';
    Menu.setApplicationMenu(Menu.buildFromTemplate([
      ...(process.platform === 'darwin' ? [{ role: 'appMenu' }] : []),
      { role: 'editMenu' },
      { label: '贴纸', submenu: [
        { label: '显示贴纸', click: showWindow },
        { label: '恢复不透明', click: () => setOpacity(1) },
        { label: '重新加载', accelerator: 'CommandOrControl+R', click: () => loadRemote() },
        { role: 'quit' },
      ] },
    ]));
    ipcMain.handle('sticker:invoke', (event, action, payload) => {
      if (!isTrustedSender(event, window?.webContents, entryUrl)) throw new Error('拒绝不可信页面的操作。');
      return invoke(action, payload);
    });
    createWindow();
    const recoverBounds = () => {
      if (window && !window.isDestroyed()) window.setBounds(availableBounds(window.getBounds()));
    };
    screen.on('display-removed', recoverBounds);
    screen.on('display-metrics-changed', recoverBounds);
  }).catch(() => {
    // Never print settings or authentication details in startup errors.
    console.error('The nblane sticker could not start.');
    app.quit();
  });
}
