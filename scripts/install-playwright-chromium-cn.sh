#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Install Playwright Chromium assets from China-friendly mirrors.

Usage:
  npm run test:e2e:install:cn

Environment overrides:
  NBLANE_CHROME_FOR_TESTING_MIRROR    Chrome for Testing mirror base URL
  NBLANE_PLAYWRIGHT_BINARY_MIRROR     Playwright binary mirror base URL
  PLAYWRIGHT_BROWSERS_PATH            Playwright browser cache directory
  NBLANE_PLAYWRIGHT_FORCE_INSTALL=1   Re-download even if cached
EOF
  exit 0
fi

case "$(uname -s)-$(uname -m)" in
  Linux-x86_64|Linux-amd64) ;;
  *)
    echo "This mirror installer currently supports Linux x64 only." >&2
    echo "Use 'npm run test:e2e:install' for other platforms." >&2
    exit 1
    ;;
esac

if [ ! -f node_modules/playwright-core/browsers.json ]; then
  echo "Missing node_modules/playwright-core/browsers.json. Run 'npm install' first." >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required." >&2
  exit 1
fi

if ! command -v unzip >/dev/null 2>&1; then
  echo "unzip is required." >&2
  exit 1
fi

eval "$(
  node <<'NODE'
const fs = require("node:fs");
const data = JSON.parse(fs.readFileSync("node_modules/playwright-core/browsers.json", "utf8"));
function browser(name) {
  const row = data.browsers.find((item) => item.name === name);
  if (!row) throw new Error(`Missing ${name} in browsers.json`);
  return row;
}
const chromium = browser("chromium");
const headless = browser("chromium-headless-shell");
const ffmpeg = browser("ffmpeg");
for (const [key, value] of Object.entries({
  CHROMIUM_REVISION: chromium.revision,
  CHROMIUM_VERSION: chromium.browserVersion,
  HEADLESS_REVISION: headless.revision,
  HEADLESS_VERSION: headless.browserVersion,
  FFMPEG_REVISION: ffmpeg.revision,
})) {
  console.log(`${key}=${JSON.stringify(String(value))}`);
}
NODE
)"

CACHE_DIR="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/.cache/ms-playwright}"
MIRROR_BASE="${NBLANE_CHROME_FOR_TESTING_MIRROR:-https://cdn.npmmirror.com/binaries/chrome-for-testing}"
PLAYWRIGHT_MIRROR_BASE="${NBLANE_PLAYWRIGHT_BINARY_MIRROR:-https://cdn.npmmirror.com/binaries/playwright}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

download_and_extract() {
  local url="$1"
  local dest="$2"
  local zip_path="$TMP_DIR/$(basename "$url")"
  local extract_dir="$TMP_DIR/extract-$(basename "$dest")"

  if [[ "${NBLANE_PLAYWRIGHT_FORCE_INSTALL:-}" != "1" && -f "$dest/INSTALLATION_COMPLETE" ]]; then
    echo "Already installed: $dest"
    return
  fi

  echo "Downloading $url"
  curl -L --fail --retry 3 --connect-timeout 20 --progress-bar "$url" -o "$zip_path"
  rm -rf "$extract_dir" "$dest"
  mkdir -p "$extract_dir" "$(dirname "$dest")"
  unzip -q "$zip_path" -d "$extract_dir"
  mkdir -p "$dest"
  shopt -s dotglob nullglob
  mv "$extract_dir"/* "$dest"/
  shopt -u dotglob nullglob
  touch "$dest/INSTALLATION_COMPLETE" "$dest/DEPENDENCIES_VALIDATED"
}

download_and_extract \
  "$MIRROR_BASE/$CHROMIUM_VERSION/linux64/chrome-linux64.zip" \
  "$CACHE_DIR/chromium-$CHROMIUM_REVISION"

download_and_extract \
  "$MIRROR_BASE/$HEADLESS_VERSION/linux64/chrome-headless-shell-linux64.zip" \
  "$CACHE_DIR/chromium_headless_shell-$HEADLESS_REVISION"

download_and_extract \
  "$PLAYWRIGHT_MIRROR_BASE/builds/ffmpeg/$FFMPEG_REVISION/ffmpeg-linux.zip" \
  "$CACHE_DIR/ffmpeg-$FFMPEG_REVISION"

echo "Installed Playwright Chromium assets to $CACHE_DIR"
