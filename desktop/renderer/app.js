'use strict';

(() => {
  const controlsOnly = new URLSearchParams(window.location.search).get('controls') === '1';
  document.documentElement.classList.toggle('controls-only', controlsOnly);
  document.body.classList.toggle('controls-only', controlsOnly);
  const api = window.nblaneSticker;
  const byId = (id) => document.getElementById(id);
  const elements = {
    toolbar: document.querySelector('.toolbar'),
    message: byId('toolbar-message'),
    pin: byId('pin-button'),
    refresh: byId('refresh-button'),
    openBrowser: byId('open-browser-button'),
    more: byId('more-button'),
    opacityButton: byId('opacity-button'),
    opacityPopover: byId('opacity-popover'),
    toolbarRange: byId('toolbar-opacity-range'),
    toolbarValue: byId('toolbar-opacity-value'),
    controlError: byId('control-error'),
    alwaysOnTop: byId('always-on-top'),
    settings: byId('settings-screen'),
    form: byId('settings-form'),
    fields: byId('settings-fields'),
    serverUrl: byId('server-url'),
    profile: byId('profile'),
    refreshInterval: byId('refresh-interval'),
    launchAtLogin: byId('launch-at-login'),
    settingsRange: byId('settings-opacity-range'),
    settingsValue: byId('settings-opacity-value'),
    backgroundBlur: byId('background-blur'),
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
  let previewOpacity = null;
  let desiredOpacity = null;
  let opacityWorker = null;
  let opacityError = null;
  let blurPending = false;
  let localError = '';

  const errorMessage = (error) => error instanceof Error ? error.message : String(error);

  function showError(error) {
    localError = errorMessage(error);
    elements.message.textContent = '操作未完成';
    elements.message.title = localError;
    elements.formError.textContent = localError;
    elements.formError.hidden = false;
    elements.controlError.textContent = localError;
    elements.more.title = `操作未完成：${localError}`;
    elements.more.dataset.error = 'true';
  }

  function clearError() {
    localError = '';
    elements.formError.textContent = '';
    elements.formError.hidden = true;
    elements.message.textContent = state?.settings.profile || 'nblane';
    elements.message.removeAttribute('title');
    elements.controlError.textContent = '';
    elements.more.title = '更多操作';
    delete elements.more.dataset.error;
  }

  function applySurface() {
    const effective = previewOpacity !== null && state?.nativeTransparency && !state?.reducedTransparency
      ? previewOpacity : state?.effectiveOpacity ?? 1;
    const opacity = Number.isFinite(effective) ? Math.min(1, Math.max(0.1, effective)) : 1;
    // Keep the view and every glyph fully opaque. Only the host's background
    // color receives alpha; the compact controls view contributes no second tint.
    document.documentElement.style.setProperty('--sticker-surface-alpha', String(opacity));
  }

  function displayOpacity(opacity) {
    const percent = Math.round(opacity * 100);
    for (const input of [elements.settingsRange, elements.toolbarRange]) {
      input.value = String(percent);
      input.setAttribute('aria-valuetext', `${percent}% 背景不透明`);
    }
    elements.settingsValue.textContent = `${percent}%`;
    elements.toolbarValue.textContent = `${percent}%`;
  }

  function fillForm(settings) {
    elements.serverUrl.value = settings.serverUrl;
    elements.profile.value = settings.profile;
    elements.refreshInterval.value = String(settings.refreshIntervalSeconds ?? 60);
    elements.launchAtLogin.checked = settings.launchAtLogin;
    formDirty = false;
    settingsInitialized = true;
  }

  function applyState(next) {
    if (!next || typeof next !== 'object' || !next.settings) return;
    const enteringSettings = next.screen === 'settings' && state?.screen !== 'settings';
    const enteringOpacity = Boolean(next.opacityEditor) && !state?.opacityEditor;
    state = next;
    applySurface();
    const showingSettings = state.screen === 'settings';
    elements.pin.setAttribute('aria-pressed', String(state.settings.alwaysOnTop));
    elements.pin.title = state.settings.alwaysOnTop ? '已置顶 · 点击取消' : '始终置顶 · 点击开启';
    const integrated = Boolean(state.integratedContent && !showingSettings && !state.loading && !state.error);
    // The native controls view owns the popup in every screen, including
    // settings and login. A second host copy would race it for keyboard focus.
    const showOpacity = Boolean(state.opacityEditor && controlsOnly);
    elements.opacityPopover.hidden = !showOpacity;
    elements.opacityButton.setAttribute('aria-expanded', String(Boolean(state.opacityEditor)));
    if (!opacityWorker && desiredOpacity === null) displayOpacity(state.settings.opacity);
    elements.refresh.disabled = showingSettings || !state.configured;
    elements.openBrowser.disabled = !state.configured;
    if (enteringOpacity && showOpacity) elements.toolbarRange.focus({ preventScroll: true });
    if (controlsOnly) return;
    elements.toolbar.hidden = integrated;
    if (!localError) elements.message.textContent = state.settings.profile || 'nblane';
    if (showingSettings && (enteringSettings || !settingsInitialized || !formDirty)) {
      fillForm(state.settings);
    }
    elements.settings.hidden = !showingSettings;
    elements.contentStatus.hidden = showingSettings || (!state.loading && !state.error);
    elements.alwaysOnTop.checked = state.settings.alwaysOnTop;
    elements.launchAtLogin.disabled = !state.canLaunchAtLogin;
    elements.backgroundBlur.checked = Boolean(state.settings.backgroundBlur);
    elements.backgroundBlur.disabled = !state.nativeTransparency || blurPending;
    const transparencyHint = byId('transparency-unavailable');
    transparencyHint.hidden = state.nativeTransparency && !state.reducedTransparency;
    transparencyHint.textContent = state.reducedTransparency
      ? '系统已开启减少透明度或增强对比度，背景暂时保持不透明。'
      : '当前系统使用不透明背景；Mac 上可调整背景透明度。';
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
        button.disabled = id === 'refresh-button' && (!state?.configured || state.screen === 'settings');
      }
    });
  }

  // Only one opacity write is in flight. A new slider value replaces the next
  // queued value, so a slow round trip can never restore an older position.
  function queueOpacity(opacity) {
    const normalized = Math.min(1, Math.max(0.1, opacity));
    desiredOpacity = normalized;
    previewOpacity = normalized;
    applySurface();
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
        previewOpacity = null;
        applySurface();
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

  elements.settingsRange.addEventListener('input', onOpacityInput);
  elements.toolbarRange.addEventListener('input', onOpacityInput);
  elements.backgroundBlur.addEventListener('change', async () => {
    const enabled = elements.backgroundBlur.checked;
    blurPending = true;
    elements.backgroundBlur.disabled = true;
    clearError();
    try {
      await invoke('set-background-blur', enabled);
    } catch (error) {
      if (state) elements.backgroundBlur.checked = Boolean(state.settings.backgroundBlur);
      showError(error);
    } finally {
      blurPending = false;
      elements.backgroundBlur.disabled = !state?.nativeTransparency;
    }
  });
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

  bindAction('refresh-button', 'retry');
  bindAction('opacity-button', 'toggle-opacity-editor');
  bindAction('settings-button', 'show-settings');
  bindAction('open-browser-button', 'open-browser');
  bindAction('pin-button', 'toggle-pin');
  bindAction('more-button', 'show-menu');
  bindAction('status-settings-button', 'show-settings');
  bindAction('cancel-settings', 'cancel-settings');
  bindAction('retry-button', 'retry');
  bindAction('settings-open-browser', 'open-browser');

  for (const input of [elements.serverUrl, elements.profile, elements.refreshInterval, elements.launchAtLogin]) {
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
      refreshIntervalSeconds: Number(elements.refreshInterval.value),
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
    if (event.key === 'Escape' && state?.opacityEditor) {
      event.preventDefault();
      try {
        await invoke('close-opacity-editor');
        elements.opacityButton.focus({ preventScroll: true });
      } catch (error) {
        showError(error);
      }
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

  document.addEventListener('pointerdown', (event) => {
    if (!state?.opacityEditor) return;
    if (event.target instanceof Element && event.target.closest('#opacity-popover, #opacity-button')) return;
    // Transparent gutters in the native view also intercept OS input; close
    // here instead of waiting for focus to reach the underlying task view.
    void invoke('close-opacity-editor').catch(showError);
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
