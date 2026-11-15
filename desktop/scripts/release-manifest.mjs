import { createHash, randomBytes } from 'node:crypto';
import { createReadStream } from 'node:fs';
import { lstat, mkdir, readFile, rename, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const values = new Map();
for (const argument of process.argv.slice(2)) {
  const match = /^--(dir|version|out)=(.+)$/.exec(argument);
  if (!match || values.has(match[1])) {
    throw new Error('Usage: node release-manifest.mjs --dir=<artifacts> --version=<major.minor.patch> --out=<manifest.json>');
  }
  values.set(match[1], match[2]);
}
if (values.size !== 3) {
  throw new Error('Required arguments: --dir, --version and --out.');
}
const version = values.get('version');
if (version.length > 64 || !/^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/.test(version)) {
  throw new Error('Version must be a numeric major.minor.patch release, without a suffix or path.');
}
const directory = path.resolve(values.get('dir'));
const output = path.resolve(values.get('out'));
const files = {};

async function regularFile(filename, optional = false) {
  let stat;
  try {
    stat = await lstat(filename);
  } catch (error) {
    if (optional && error.code === 'ENOENT') return null;
    throw error;
  }
  if (!stat.isFile()) throw new Error(`Expected a regular file: ${path.basename(filename)}`);
  return stat;
}

for (const arch of ['arm64', 'x64']) {
  // Only final release filenames are eligible. Candidate and unsigned bundles
  // are deliberately never discovered or substituted for a missing release.
  const filename = `nblane-sticker-${version}-mac-${arch}.zip`;
  const archive = path.join(directory, filename);
  const stat = await regularFile(archive, arch === 'x64');
  if (!stat) continue;
  if (!Number.isSafeInteger(stat.size) || stat.size <= 0) {
    throw new Error(`Archive must be non-empty: ${filename}`);
  }
  const checksumFile = `${archive}.sha256`;
  await regularFile(checksumFile);
  const checksum = await readFile(checksumFile, 'utf8');
  const match = /^([a-fA-F0-9]{64}) (?: |\*)([^\r\n]+)\r?\n?$/.exec(checksum);
  if (!match || match[2] !== filename) {
    throw new Error(`Checksum must name exactly ${filename}`);
  }
  const hash = createHash('sha256');
  for await (const chunk of createReadStream(archive)) hash.update(chunk);
  const digest = hash.digest('hex');
  if (digest !== match[1].toLowerCase()) throw new Error(`Checksum mismatch: ${filename}`);
  files[arch] = {
    url: `https://www.nblane.cloud/downloads/sticker/${version}/${filename}`,
    sha256: digest,
    size: stat.size,
  };
}

const manifest = {
  version,
  macosMinVersion: '13.0',
  publishedAt: new Date().toISOString(),
  signing: 'ad-hoc',
  files,
};
// Verify every archive before touching the destination. Keep the old manifest
// intact if validation or writing fails; rename publishes the new file at once.
await mkdir(path.dirname(output), { recursive: true });
const temporary = path.join(path.dirname(output), `.${path.basename(output)}.${randomBytes(8).toString('hex')}.tmp`);
try {
  await writeFile(temporary, `${JSON.stringify(manifest, null, 2)}\n`, { flag: 'wx', mode: 0o644 });
  await rename(temporary, output);
} finally {
  await rm(temporary, { force: true });
}
console.log(`Created release manifest for ${version}: ${Object.keys(files).join(', ')}`);
