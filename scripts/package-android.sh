#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage: scripts/package-android.sh

Check, sign and package the nblane Trusted Web Activity.
The default signing configuration is read from .dev-data/android-signing/signing.env
when NBLANE_ANDROID_KEYSTORE is not set.

Environment:
  NBLANE_ANDROID_ALLOW_DIRTY       1 permits a development build from a dirty tree
  NBLANE_ANDROID_OUT               Output directory (default dist/android)
  NBLANE_ANDROID_BUILD_HOME        Gradle/Bubblewrap home (default local config or HOME)
  NBLANE_GRADLE_USER_HOME          Gradle cache (default build home's .gradle)
  NBLANE_ANDROID_SKIP_PWA_VALIDATION  1 skips Bubblewrap's remote PWA quality check
  NBLANE_ANDROID_KEYSTORE          Signing PKCS12 file
  NBLANE_ANDROID_KEY_ALIAS         Signing alias (default nblane)
  BUBBLEWRAP_KEYSTORE_PASSWORD     Keystore password
  BUBBLEWRAP_KEY_PASSWORD          Key password
EOF
  exit 0
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
twa_dir="$repo_root/packaging/android/twa"
manifest="$twa_dir/twa-manifest.json"
fail() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

for command_name in git npx python3 sha256sum; do
  command -v "$command_name" >/dev/null 2>&1 || fail "Missing command: $command_name"
done
[[ -f "$manifest" ]] || fail "Missing $manifest; generate the TWA project first."
[[ "${NBLANE_ANDROID_ALLOW_DIRTY:-0}" == "1" || -z "$(git -C "$repo_root" status --porcelain --untracked-files=all)" ]] || \
  fail "The working tree is dirty. Commit first or set NBLANE_ANDROID_ALLOW_DIRTY=1 for a development build."

build_home="${NBLANE_ANDROID_BUILD_HOME:-}"
if [[ -z "$build_home" ]]; then
  if [[ -f "$repo_root/.dev-data/android-home/.bubblewrap/config.json" ]]; then
    build_home="$repo_root/.dev-data/android-home"
  else
    build_home="$HOME"
  fi
fi
export HOME="$build_home"
export GRADLE_USER_HOME="${NBLANE_GRADLE_USER_HOME:-$HOME/.gradle}"
export npm_config_cache="${NBLANE_NPM_CACHE:-$repo_root/.dev-data/npm-cache}"

if [[ -f "$HOME/.bubblewrap/config.json" ]]; then
  readarray -t tool_paths < <(python3 - "$HOME/.bubblewrap/config.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
print(data.get("jdkPath", ""))
print(data.get("androidSdkPath", ""))
PY
)
  export JAVA_HOME="${JAVA_HOME:-${tool_paths[0]}}"
  export ANDROID_HOME="${ANDROID_HOME:-${tool_paths[1]}}"
  export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$ANDROID_HOME}"
fi
export ANDROID_HOME="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$ANDROID_HOME}"

if [[ -z "${NBLANE_ANDROID_KEYSTORE:-}" && -f "$repo_root/.dev-data/android-signing/signing.env" ]]; then
  set -a
  . "$repo_root/.dev-data/android-signing/signing.env"
  set +a
fi
[[ -n "${NBLANE_ANDROID_KEYSTORE:-}" ]] || fail "Set NBLANE_ANDROID_KEYSTORE or prepare .dev-data/android-signing/signing.env."
[[ -f "$NBLANE_ANDROID_KEYSTORE" ]] || fail "Signing key does not exist: $NBLANE_ANDROID_KEYSTORE"
[[ -n "${BUBBLEWRAP_KEYSTORE_PASSWORD:-}" && -n "${BUBBLEWRAP_KEY_PASSWORD:-}" ]] || \
  fail "Signing passwords must be supplied through the environment, not command arguments."

readarray -t metadata < <(python3 - "$manifest" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
for key in ("appVersion", "appVersionCode", "packageId"):
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, (str, int)) or not str(value).strip():
        raise SystemExit(f"Invalid {key}")
    print(value)
PY
)
version="${metadata[0]}"
application_id="${metadata[2]}"
[[ "$version" =~ ^[0-9A-Za-z._-]+$ ]] || fail "appVersion contains unsafe filename characters."

bubblewrap=(npx --yes @bubblewrap/cli@1.27.0)
if [[ -n "${BUBBLEWRAP_BIN:-}" ]]; then
  bubblewrap=("$BUBBLEWRAP_BIN")
fi
[[ -x "$twa_dir/gradlew" ]] || fail "Missing executable Gradle wrapper: $twa_dir/gradlew"
(
  cd "$twa_dir"
  ./gradlew lintDebug testDebugUnitTest assembleDebug
)
build_args=(build --manifest="$manifest" --signingKeyPath="$NBLANE_ANDROID_KEYSTORE" --signingKeyAlias="${NBLANE_ANDROID_KEY_ALIAS:-nblane}")
if [[ "${NBLANE_ANDROID_SKIP_PWA_VALIDATION:-0}" == "1" ]]; then
  build_args+=(--skipPwaValidation)
fi
(
  cd "$twa_dir"
  "${bubblewrap[@]}" "${build_args[@]}"
)

[[ -f "$twa_dir/app-release-signed.apk" ]] || fail "Signed APK was not generated."
[[ -f "$twa_dir/app-release-bundle.aab" ]] || fail "Signed App Bundle was not generated."
out_dir="${NBLANE_ANDROID_OUT:-$repo_root/dist/android}"
mkdir -p "$out_dir"
apk="$out_dir/nblane-$version-twa.apk"
aab="$out_dir/nblane-$version-twa.aab"
cp "$twa_dir/app-release-signed.apk" "$apk"
cp "$twa_dir/app-release-bundle.aab" "$aab"

build_tools="${NBLANE_ANDROID_BUILD_TOOLS:-36.1.0}"
if [[ -n "$ANDROID_HOME" && -x "$ANDROID_HOME/build-tools/$build_tools/apksigner" ]]; then
  "$ANDROID_HOME/build-tools/$build_tools/apksigner" verify "$apk"
  badging="$("$ANDROID_HOME/build-tools/$build_tools/aapt" dump badging "$apk")"
  [[ "$badging" == *"package: name='$application_id'"* ]] || fail "APK applicationId does not match twa-manifest.json."
fi
(
  cd "$out_dir"
  sha256sum "$(basename "$apk")" > "$(basename "$apk").sha256"
  sha256sum "$(basename "$aab")" > "$(basename "$aab").sha256"
)
printf 'VERSION=%s\nVERSION_CODE=%s\nAPPLICATION_ID=%s\nCOMMIT=%s\nBUILD_TIME=%s\nSOURCE_DIRTY=%s\n' \
  "$version" "${metadata[1]}" "$application_id" "$(git -C "$repo_root" rev-parse HEAD)" \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${NBLANE_ANDROID_ALLOW_DIRTY:-0}" > "$out_dir/BUILDINFO"
printf 'Created %s\nCreated %s\n' "$apk" "$aab"
