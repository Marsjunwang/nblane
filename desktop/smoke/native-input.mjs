import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const directory = fileURLToPath(new URL('./', import.meta.url));

/** OS events exercise native hit testing; CDP and DOM events bypass drag regions. */
export function createNativeInput(temporaryDirectory) {
  let command;
  let prefix;
  if (process.platform === 'darwin') {
    command = path.join(temporaryDirectory, 'native-input');
    execFileSync('/usr/bin/xcrun', ['swiftc', path.join(directory, 'native-input.swift'),
      '-module-cache-path', path.join(temporaryDirectory, 'swift-cache'), '-o', command],
    { timeout: 60_000, stdio: 'pipe' });
    prefix = [];
  } else if (process.platform === 'linux' && process.env.DISPLAY) {
    command = 'python3';
    prefix = [path.join(directory, 'native-input.py')];
  } else {
    throw new Error('Native input smoke requires macOS or an X11 display; no CDP fallback is allowed.');
  }
  const run = (...arguments_) => execFileSync(command, [...prefix, ...arguments_], {
    timeout: 10_000, stdio: 'pipe',
  });
  return {
    click(x, y) {
      if (!Number.isFinite(x) || !Number.isFinite(y)) throw new Error('Invalid native pointer coordinates');
      run('click', String(Math.round(x)), String(Math.round(y)));
    },
    escape() { run('escape'); },
  };
}
