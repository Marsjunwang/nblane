import { createHash } from 'node:crypto';
import { createReadStream } from 'node:fs';
import { cp, mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { packager } from '@electron/packager';
import './theme.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const args = process.argv.slice(2);
const arch = args.find((arg) => arg.startsWith('--arch='))?.slice(7) ?? process.arch;
const unsigned = args.includes('--unsigned');
const candidate = args.includes('--candidate');
if (!['arm64', 'x64'].includes(arch) || (unsigned && candidate)
    || args.some((arg) => !['--unsigned', '--candidate'].includes(arg) && !arg.startsWith('--arch='))) {
  throw new Error('Usage: npm run package:mac -- --arch=arm64|x64 [--unsigned|--candidate]');
}
if (process.platform !== 'darwin' && !unsigned && !candidate) {
  throw new Error('Build on macOS for local code signing. Cross-builds are inspection/candidate artifacts only.');
}
const crossSigner = process.env.NBLANE_STICKER_RCODESIGN || 'rcodesign';
if (candidate) execFileSync(crossSigner, ['--version'], { stdio: 'inherit' });
const metadata = JSON.parse(await readFile(path.join(root, 'package.json'), 'utf8'));
const outputRoot = fileURLToPath(new URL('../../dist/desktop/', import.meta.url));
const output = candidate ? path.join(outputRoot, 'candidates')
  : unsigned ? path.join(outputRoot, 'inspection') : outputRoot;
const stage = await mkdtemp(path.join(tmpdir(), 'nblane-sticker-package-'));
try {
  // An explicit allowlist keeps tests, development tools and local state out of the app.
  for (const entry of ['main.cjs', 'preload.cjs', 'lib', 'renderer']) {
    await cp(path.join(root, entry), path.join(stage, entry), { recursive: true });
  }
  await cp(path.join(root, '../LICENSE'), path.join(stage, 'LICENSE'));
  await writeFile(path.join(stage, 'package.json'), JSON.stringify({
    name: metadata.name, productName: metadata.productName,
    version: metadata.version, description: metadata.description, main: metadata.main,
  }, null, 2) + '\n');
  const [bundleDirectory] = await packager({
    dir: stage, out: output, name: metadata.productName, platform: 'darwin', arch,
    electronVersion: metadata.devDependencies.electron, appBundleId: 'cloud.nblane.sticker',
    appCategoryType: 'public.app-category.productivity',
    icon: path.join(stage, 'renderer/app.icns'),
    asar: true, overwrite: true, prune: false, darwinDarkModeSupport: true,
    ...(unsigned || candidate ? {} : { osxSign: {
      identity: '-', identityValidation: false, preAutoEntitlements: false,
      preEmbedProvisioningProfile: false,
      optionsForFile: () => ({ hardenedRuntime: false }),
    } }),
  });
  const app = path.join(bundleDirectory, `${metadata.productName}.app`);
  if (candidate) {
    // Re-sign nested code and seal the entire renamed bundle, not only Mach-O pages.
    // This does not replace Apple's codesign verification or Gatekeeper acceptance.
    execFileSync(crossSigner, ['--config-file', '/dev/null', 'sign', '--timestamp-url', 'none', app], { stdio: 'inherit' });
  }
  const suffix = candidate ? '-candidate' : unsigned ? '-unsigned' : '';
  const filename = `nblane-sticker-${metadata.version}-mac-${arch}${suffix}.zip`;
  const archive = path.join(output, filename);
  await mkdir(output, { recursive: true });
  await rm(archive, { force: true });
  if (process.platform === 'darwin') {
    if (!unsigned) execFileSync('/usr/bin/codesign', ['--verify', '--deep', '--strict', app], { stdio: 'inherit' });
    execFileSync('/usr/bin/ditto', ['-c', '-k', '--sequesterRsrc', '--keepParent', app, archive], { stdio: 'inherit' });
  } else {
    execFileSync('python3', [path.join(root, 'scripts/archive.py'), app, archive], { stdio: 'inherit' });
  }
  const hash = createHash('sha256');
  for await (const chunk of createReadStream(archive)) hash.update(chunk);
  await writeFile(`${archive}.sha256`, `${hash.digest('hex')}  ${filename}\n`);
  console.log(`Created ${archive}`);
  console.log(unsigned ? 'Inspection only: no complete bundle signature. Do not distribute for installation.'
    : candidate ? 'Candidate only: recursively ad-hoc signed; requires macOS verification. Not notarized.'
    : 'Locally signed build; Apple notarization is not included.');
} finally {
  await rm(stage, { recursive: true, force: true });
}
