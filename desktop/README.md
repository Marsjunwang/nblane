# nblane Sticker

An independent macOS window for the hosted nblane mini task view, with
always-on-top controls, whole-window opacity, a menu-bar entry, and persistent
window settings. Remote pages run without Node.js or a preload bridge.

The canonical usage, packaging and validation guide is
[中文桌面贴纸手册](../docs/zh/guides/desktop-sticker.md).

Requires Node.js 24. On macOS:

```sh
npm ci --prefix desktop
npm start --prefix desktop
```

For a locally signed Apple Silicon build:

```sh
npm run package:mac --prefix desktop -- --arch=arm64
```

Use `--arch=x64` for Intel Macs. Local signing does not include Apple
notarization. Linux cross-builds require `--unsigned` (inspection only) or
`--candidate` with `NBLANE_STICKER_RCODESIGN` pointing to rcodesign 0.29.0.
Candidates have recursive ad-hoc bundle signatures but still require Apple's
verification and a native launch test; neither mode is a verified macOS release.

The macOS workflow tests the app extracted from the final ZIP on each native
architecture before uploading artifacts. This checks package integrity and
launch, not Gatekeeper approval or notarization.
