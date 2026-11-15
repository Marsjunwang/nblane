'use strict';

(() => {
  const api = window.nblaneSticker;
  const byId = (id) => document.getElementById(id);
  const elements = {
    toolbarDefault: byId('toolbar-default'),
    toolbarOpacity: byId('toolbar-opacity'),
    message: byId('toolbar-message'),
    pin: byId('pin-button'),
    pinLabel: byId('pin-label'),
    alwaysOnTop: byId('always-on-top'),
    opacityButton: byId('opacity-button'),
    toolbarRange: byId('toolbar-opacity-range'),
    toolbarValue: byId('toolbar-opacity-value'),
    settings: byId('settings-screen'),
    form: byId('settings-form'),
    fields: byId('settings-fields'),
    serverUrl: byId('server-url'),
    profile: byId('profile'),
    launchAtLogin: byId('launch-at-login'),
    settingsRange: byId('settings-opacity-range'),
    settingsValue: byId('settings-opacity-value'),
    formError: byId('settings-error'),
    save: byId('save-settings'),
    cancel: byId('cancel-settings'),
    contentStatus: byId('content-status'),
    statusHeading: byId('status-heading'),
    statusDescription: byId('status-description'),
    statusActions: byId('status-actions'),
    loadingMark: byId('loading-mark'),
  };

  let state = null;
  let formDirty = false;
  let settingsInitialized = false;
  let savePending = false;
  let toolbarOpacityOpen = false;
  let desiredOpacity = null;
  let opacityWorker = null;
  let opacityError = null;
  let localError = '';

  const errorMessage = (error) => error instanceof Error ? error.message : String(error);

  function showError(error) {
    localError = errorMessage(error);
    elements.message.textContent = '操作未完成';
    elements.message.title = localError;
    elements.formError.textContent = localError;
    elements.formError.hidden = false;
  }

  function clearError() {
    localError = '';
    elements.formError.textContent = '';
    elements.formError.hidden = true;
    elements.message.textContent = 'nblane';
    elements.message.removeAttribute('title');
  }

  function displayOpacity(opacity) {
    const percent = Math.round(opacity * 100);
    for (const range of [elements.toolbarRange, elements.settingsRange]) {
      range.value = String(percent);
      range.setAttribute('aria-valuetext', `${percent}% 不透明`);
    }
    elements.toolbarValue.textContent = `${percent}%`;
    elements.settingsValue.textContent = `${percent}%`;
  }

  function fillForm(settings) {
    elements.serverUrl.value = settings.serverUrl;
    elements.profile.value = settings.profile;
    elements.launchAtLogin.checked = settings.launchAtLogin;
    formDirty = false;
    settingsInitialized = true;
  }

  function applyState(next) {
    if (!next || typeof next !== 'object' || !next.settings) return;
    const enteringSettings = next.screen === 'settings' && state?.screen !== 'settings';
    state = next;
    const showingSettings = state.screen === 'settings';
    if (showingSettings && (enteringSettings || !settingsInitialized || !formDirty)) {
      fillForm(state.settings);
    }
    elements.settings.hidden = !showingSettings;
    elements.contentStatus.hidden = showingSettings || (!state.loading && !state.error);
    elements.pin.setAttribute('aria-pressed', String(state.settings.alwaysOnTop));
    elements.pinLabel.textContent = state.settings.alwaysOnTop ? '已置顶' : '置顶';
    elements.pin.title = state.settings.alwaysOnTop ? '已置顶 · 点击取消' : '始终置顶 · 点击开启';
    elements.alwaysOnTop.checked = state.settings.alwaysOnTop;
    if (!opacityWorker && desiredOpacity === null) displayOpacity(state.settings.opacity);
    elements.launchAtLogin.disabled = !state.canLaunchAtLogin;
    // The first connection stays short; opacity remains available in the
    // toolbar and joins the full settings form after a profile is configured.
    byId('settings-opacity-field').hidden = !state.configured;
    byId('login-unavailable').hidden = state.canLaunchAtLogin;
    elements.cancel.hidden = !state.configured;
    byId('settings-open-browser').hidden = !state.configured;
    byId('settings-heading').textContent = state.configured ? '贴纸设置' : '连接你的档案';
    elements.save.textContent = savePending ? '正在连接…' : state.configured ? '保存设置' : '连接档案';
    elements.fields.disabled = savePending;
    byId('version').textContent = state.version ? `v${state.version}` : '';
    elements.loadingMark.hidden = Boolean(state.error);
    elements.statusHeading.textContent = state.error ? '暂时无法连接' : '正在连接档案';
    elements.statusDescription.textContent = state.error || '首次连接需要在贴纸里登录，正在打开页面…';
    elements.statusActions.hidden = !state.error && !state.loading;
    if (enteringSettings) {
      clearError();
      if (!state.configured) elements.profile.focus();
    }
  }

  async function invoke(action, payload) {
    const next = await api.invoke(action, payload);
    applyState(next);
    return next;
  }

  function bindAction(id, action) {
    const button = byId(id);
    button.addEventListener('click', async () => {
      button.disabled = true;
      clearError();
      try {
        await invoke(action);
      } catch (error) {
        showError(error);
      } finally {
        button.disabled = false;
      }
    });
  }

  function setOpacityEditor(open) {
    toolbarOpacityOpen = open;
    elements.toolbarDefault.hidden = open;
    elements.toolbarOpacity.hidden = !open;
    elements.opacityButton.setAttribute('aria-expanded', String(open));
    if (open) elements.toolbarRange.focus();
    else elements.opacityButton.focus();
  }

  // Only one opacity write is in flight. A new slider value replaces the next
  // queued value, so a slow round trip can never restore an older position.
  function queueOpacity(opacity) {
    const normalized = Math.min(1, Math.max(0.4, opacity));
    desiredOpacity = normalized;
    opacityError = null;
    displayOpacity(normalized);
    clearError();
    if (opacityWorker) return;
    opacityWorker = (async () => {
      try {
        while (desiredOpacity !== null) {
          const value = desiredOpacity;
          desiredOpacity = null;
          await invoke('set-opacity', value);
        }
      } catch (error) {
        desiredOpacity = null;
        opacityError = error;
        showError(error);
      } finally {
        opacityWorker = null;
        if (state) displayOpacity(state.settings.opacity);
      }
    })();
  }

  function onOpacityInput(event) {
    queueOpacity(Number(event.target.value) / 100);
  }

  if (!api) {
    elements.loadingMark.hidden = true;
    elements.statusHeading.textContent = '请从 nblane 贴纸应用打开';
    elements.statusDescription.textContent = '这个页面需要在桌面应用中使用。';
    for (const button of document.querySelectorAll('.toolbar button')) button.disabled = true;
    return;
  }

  elements.opacityButton.addEventListener('click', () => setOpacityEditor(true));
  byId('opacity-close').addEventListener('click', () => setOpacityEditor(false));
  byId('opacity-restore').addEventListener('click', () => queueOpacity(1));
  elements.toolbarRange.addEventListener('input', onOpacityInput);
  elements.settingsRange.addEventListener('input', onOpacityInput);
  elements.alwaysOnTop.addEventListener('change', async () => {
    const enabled = elements.alwaysOnTop.checked;
    elements.alwaysOnTop.disabled = true;
    elements.pin.disabled = true;
    clearError();
    try {
      await invoke('set-pin', enabled);
    } catch (error) {
      if (state) elements.alwaysOnTop.checked = state.settings.alwaysOnTop;
      showError(error);
    } finally {
      elements.alwaysOnTop.disabled = false;
      elements.pin.disabled = false;
    }
  });

  bindAction('pin-button', 'toggle-pin');
  bindAction('hide-button', 'hide');
  bindAction('settings-button', 'show-settings');
  bindAction('status-settings-button', 'show-settings');
  bindAction('cancel-settings', 'cancel-settings');
  bindAction('retry-button', 'retry');
  bindAction('settings-open-browser', 'open-browser');

  for (const input of [elements.serverUrl, elements.profile, elements.launchAtLogin]) {
    input.addEventListener('input', () => {
      formDirty = true;
      if (localError) clearError();
    });
  }

  elements.form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (savePending) return;
    savePending = true;
    elements.fields.disabled = true;
    elements.save.textContent = '正在连接…';
    clearError();
    const draft = {
      serverUrl: elements.serverUrl.value.trim(),
      profile: elements.profile.value.trim(),
      launchAtLogin: elements.launchAtLogin.checked,
    };
    try {
      if (opacityWorker) await opacityWorker;
      if (opacityError) throw opacityError;
      await invoke('save-settings', draft);
      formDirty = false;
    } catch (error) {
      showError(error);
    } finally {
      savePending = false;
      if (state) applyState(state);
    }
  });

  document.addEventListener('keydown', async (event) => {
    if (event.key === 'Escape' && toolbarOpacityOpen) {
      event.preventDefault();
      setOpacityEditor(false);
      return;
    }
    const openSettings = (event.metaKey || event.ctrlKey) && event.key === ',';
    const closeSettings = event.key === 'Escape' && state?.configured && state.screen === 'settings';
    if (!openSettings && !closeSettings) return;
    event.preventDefault();
    try {
      await invoke(openSettings ? 'show-settings' : 'cancel-settings');
    } catch (error) {
      showError(error);
    }
  });

  const unsubscribe = api.onState(applyState);
  window.addEventListener('unload', unsubscribe, { once: true });
  invoke('get-state').catch((error) => {
    elements.loadingMark.hidden = true;
    elements.statusHeading.textContent = '贴纸暂时无法启动';
    elements.statusDescription.textContent = errorMessage(error);
    showError(error);
  });
})();
