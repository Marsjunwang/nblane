'use strict';

const { contextBridge, ipcRenderer } = require('electron');

const ACTIONS = new Set([
  'get-state',
  'save-settings',
  'set-opacity',
  'set-pin',
  'toggle-pin',
  'hide',
  'retry',
  'open-browser',
  'quit',
  'show-settings',
  'cancel-settings',
]);

// The local toolbar receives only named window actions. The remote task view
// has no preload script and cannot reach this bridge.
contextBridge.exposeInMainWorld('nblaneSticker', Object.freeze({
  invoke(action, payload) {
    if (!ACTIONS.has(action)) return Promise.reject(new Error('不支持的窗口操作。'));
    return ipcRenderer.invoke('sticker:invoke', action, payload);
  },
  onState(callback) {
    if (typeof callback !== 'function') throw new TypeError('State listener must be a function');
    const listener = (_event, state) => callback(state);
    ipcRenderer.on('sticker:state', listener);
    return () => ipcRenderer.removeListener('sticker:state', listener);
  },
}));
