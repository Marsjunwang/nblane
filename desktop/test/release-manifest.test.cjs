'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const script = path.join(__dirname, '../scripts/release-manifest.mjs');
const version = '0.1.3';

function fixture(t) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'nblane-release-manifest-'));
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  return { directory, output: path.join(directory, 'published', 'latest.json') };
}

function archive(directory, arch, suffix = '') {
  // These bytes exercise archive integrity, not executable or signing validation.
  const filename = `nblane-sticker-${version}-mac-${arch}${suffix}.zip`;
  const bytes = Buffer.from(`fixture archive for ${arch}\0\xff`, 'utf8');
  const digest = createHash('sha256').update(bytes).digest('hex');
  fs.writeFileSync(path.join(directory, filename), bytes);
  fs.writeFileSync(path.join(directory, `${filename}.sha256`), `${digest}  ${filename}\n`);
  return { filename, bytes, digest };
}

function run({ directory, output }, overrides = []) {
  return spawnSync(process.execPath, [script, `--dir=${directory}`, `--version=${version}`, `--out=${output}`, ...overrides], {
    encoding: 'utf8', timeout: 10_000,
  });
}

test('publishes verified ARM and optional Intel archives with exact versioned URLs', (t) => {
  const state = fixture(t);
  const arm = archive(state.directory, 'arm64');
  let result = run(state);
  assert.equal(result.status, 0, result.stderr);
  let manifest = JSON.parse(fs.readFileSync(state.output, 'utf8'));
  assert.deepEqual(Object.keys(manifest.files), ['arm64']);
  assert.deepEqual(manifest.files.arm64, {
    url: `https://www.nblane.cloud/downloads/sticker/${version}/${arm.filename}`,
    sha256: arm.digest,
    size: arm.bytes.length,
  });
  assert.equal(manifest.version, version);
  assert.equal(manifest.macosMinVersion, '13.0');
  assert.equal(manifest.signing, 'ad-hoc');
  assert.equal(new Date(manifest.publishedAt).toISOString(), manifest.publishedAt);

  const intel = archive(state.directory, 'x64');
  result = run(state);
  assert.equal(result.status, 0, result.stderr);
  manifest = JSON.parse(fs.readFileSync(state.output, 'utf8'));
  assert.deepEqual(manifest.files.x64, {
    url: `https://www.nblane.cloud/downloads/sticker/${version}/${intel.filename}`,
    sha256: intel.digest,
    size: intel.bytes.length,
  });
  assert.deepEqual(fs.readdirSync(path.dirname(state.output)), ['latest.json']);
});

test('checksum corruption leaves the existing manifest unchanged', (t) => {
  const state = fixture(t);
  const arm = archive(state.directory, 'arm64');
  assert.equal(run(state).status, 0);
  const previous = fs.readFileSync(state.output, 'utf8');
  fs.appendFileSync(path.join(state.directory, arm.filename), 'changed');
  const result = run(state);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Checksum mismatch/);
  assert.equal(fs.readFileSync(state.output, 'utf8'), previous);
  assert.deepEqual(fs.readdirSync(path.dirname(state.output)), ['latest.json']);
});

test('rejects mislabeled or multi-entry checksums and missing Intel checksums', (t) => {
  const state = fixture(t);
  const arm = archive(state.directory, 'arm64');
  const checksumPath = path.join(state.directory, `${arm.filename}.sha256`);
  for (const checksum of [
    `${arm.digest}  other.zip\n`,
    `${arm.digest}  ../${arm.filename}\n`,
    `${arm.digest}  ${arm.filename}\n${arm.digest}  other.zip\n`,
  ]) {
    fs.writeFileSync(checksumPath, checksum);
    assert.notEqual(run(state).status, 0);
    assert.equal(fs.existsSync(state.output), false);
  }
  archive(state.directory, 'arm64');
  const intel = archive(state.directory, 'x64');
  fs.unlinkSync(path.join(state.directory, `${intel.filename}.sha256`));
  assert.notEqual(run(state).status, 0);
  assert.equal(fs.existsSync(state.output), false);
});

test('candidate and unsigned filenames never substitute for a release', (t) => {
  const state = fixture(t);
  archive(state.directory, 'arm64', '-candidate');
  archive(state.directory, 'arm64', '-unsigned');
  assert.notEqual(run(state).status, 0);
  assert.equal(fs.existsSync(state.output), false);
});

test('rejects unsafe versions, duplicate and unknown arguments', (t) => {
  const state = fixture(t);
  archive(state.directory, 'arm64');
  for (const unsafe of ['../0.1.3', '0.1.3-candidate', '0.1.3-unsigned', '01.2.3', '0.1', '0.1.3/anything']) {
    const result = spawnSync(process.execPath, [script, `--dir=${state.directory}`, `--version=${unsafe}`, `--out=${state.output}`], { encoding: 'utf8' });
    assert.notEqual(result.status, 0, unsafe);
  }
  assert.notEqual(run(state, ['--unsigned']).status, 0);
  assert.notEqual(run(state, [`--version=${version}`]).status, 0);
  assert.equal(fs.existsSync(state.output), false);
});

test('rejects empty archives and symlinked inputs', (t) => {
  const state = fixture(t);
  const arm = archive(state.directory, 'arm64');
  const filename = path.join(state.directory, arm.filename);
  fs.writeFileSync(filename, '');
  assert.notEqual(run(state).status, 0);
  if (process.platform !== 'win32') {
    fs.unlinkSync(filename);
    const other = path.join(state.directory, 'source.zip');
    fs.writeFileSync(other, arm.bytes);
    fs.symlinkSync(other, filename);
    assert.notEqual(run(state).status, 0);
  }
  assert.equal(fs.existsSync(state.output), false);
});
