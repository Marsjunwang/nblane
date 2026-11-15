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
    more: byId('more-button'),
    controlError: byId('control-error'),
    alwaysOnTop: byId('always-on-top'),
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
  let previewOpacity = null;
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
    const effective = previewOpacity !== null && state?.nativeBlur && !state?.reducedTransparency
      ? previewOpacity : state?.effectiveOpacity ?? 1;
    const opacity = Number.isFinite(effective) ? Math.min(1, Math.max(0.4, effective)) : 1;
    // Keep the view and every glyph fully opaque. Only the host's background
    // color receives alpha; the compact controls view contributes no second tint.
    document.documentElement.style.setProperty('--sticker-surface-alpha', String(opacity));
  }

  function displayOpacity(opacity) {
    const percent = Math.round(opacity * 100);
    elements.settingsRange.value = String(percent);
    elements.settingsRange.setAttribute('aria-valuetext', `${percent}% 背景不透明`);
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
    applySurface();
    const showingSettings = state.screen === 'settings';
    elements.pin.setAttribute('aria-pressed', String(state.settings.alwaysOnTop));
    elements.pin.title = state.settings.alwaysOnTop ? '已置顶 · 点击取消' : '始终置顶 · 点击开启';
    if (controlsOnly) return;
    elements.toolbar.hidden = Boolean(state.integratedContent && !showingSettings && !state.loading && !state.error);
    if (!localError) elements.message.textContent = state.settings.profile || 'nblane';
    if (showingSettings && (enteringSettings || !settingsInitialized || !formDirty)) {
      fillForm(state.settings);
    }
    elements.settings.hidden = !showingSettings;
    elements.contentStatus.hidden = showingSettings || (!state.loading && !state.error);
    elements.alwaysOnTop.checked = state.settings.alwaysOnTop;
    if (!opacityWorker && desiredOpacity === null) displayOpacity(state.settings.opacity);
    elements.launchAtLogin.disabled = !state.canLaunchAtLogin;
    const transparencyHint = byId('transparency-unavailable');
    transparencyHint.hidden = state.nativeBlur && !state.reducedTransparency;
    transparencyHint.textContent = state.reducedTransparency
      ? '系统已开启减少透明度或增强对比度，背景暂时保持不透明。'
      : '当前系统使用清晰的不透明背景；Mac 上可显示模糊背景。';
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

  // Only one opacity write is in flight. A new slider value replaces the next
  // queued value, so a slow round trip can never restore an older position.
  function queueOpacity(opacity) {
    const normalized = Math.min(1, Math.max(0.4, opacity));
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
  bindAction('more-button', 'show-menu');
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
