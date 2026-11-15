'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { randomUUID } = require('node:crypto');
const { normalizeSettings, validBounds } = require('./policy.cjs');

function readState(filename) {
  let state = {};
  try {
    state = JSON.parse(fs.readFileSync(filename, 'utf8'));
  } catch {
    // Missing or malformed preferences must never make the sticker unreachable.
  }
  return {
    settings: normalizeSettings(state?.settings),
    bounds: validBounds(state?.bounds) ? state.bounds : null,
  };
}

/** Persist preferences only; authentication belongs to Chromium's private session. */
function writeState(filename, state) {
  fs.mkdirSync(path.dirname(filename), { recursive: true, mode: 0o700 });
  const temporary = `${filename}.${process.pid}.${randomUUID()}.tmp`;
  const content = {
    settings: normalizeSettings(state.settings),
    bounds: validBounds(state.bounds) ? {
      x: state.bounds.x, y: state.bounds.y, width: state.bounds.width, height: state.bounds.height,
    } : null,
  };
  try {
    fs.writeFileSync(temporary, `${JSON.stringify(content, null, 2)}\n`, { mode: 0o600, flag: 'wx' });
    fs.renameSync(temporary, filename);
  } finally {
    try { fs.unlinkSync(temporary); } catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
}

module.exports = { readState, writeState };
