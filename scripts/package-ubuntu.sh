#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/package-ubuntu.sh

Build an Ubuntu installation archive from the repository containing this script.

Options:
  -h, --help  Show this help and exit.

Environment:
  NBLANE_PACKAGE_OUT           Output directory (default: dist/ubuntu).
  NBLANE_PACKAGE_ALLOW_DIRTY   Set to 1 to package working-tree changes.
  NBLANE_PACKAGE_OFFLINE       Set to 0 to skip the offline wheelhouse
                               (default: 1).
EOF
}

if [[ $# -gt 0 ]]; then
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Error: unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

allow_dirty="${NBLANE_PACKAGE_ALLOW_DIRTY:-0}"
offline="${NBLANE_PACKAGE_OFFLINE:-1}"
case "$allow_dirty" in
  0|1) ;;
  *)
    printf 'Error: NBLANE_PACKAGE_ALLOW_DIRTY must be 0 or 1.\n' >&2
    exit 2
    ;;
esac
case "$offline" in
  0|1) ;;
  *)
    printf 'Error: NBLANE_PACKAGE_OFFLINE must be 0 or 1.\n' >&2
    exit 2
    ;;
esac

for required_command in git tar sha256sum; do
  if ! command -v "$required_command" >/dev/null 2>&1; then
    printf 'Error: required command not found: %s\n' "$required_command" >&2
    exit 1
  fi
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  printf 'Error: %s is not a Git working tree.\n' "$repo_root" >&2
  exit 1
fi

if [[ "$allow_dirty" != "1" && -n "$(git status --porcelain --untracked-files=all)" ]]; then
  printf 'Error: the working tree is dirty. Commit or stash changes, or set NBLANE_PACKAGE_ALLOW_DIRTY=1 for a development build.\n' >&2
  exit 2
fi

commit="$(git rev-parse --verify HEAD)"
installer="$repo_root/packaging/ubuntu/install.sh"
if [[ ! -f "$installer" ]]; then
  printf 'Error: production installer not found: %s\n' "$installer" >&2
  exit 1
fi
if [[ ! -f "$repo_root/pyproject.toml" ]]; then
  printf 'Error: pyproject.toml not found in %s.\n' "$repo_root" >&2
  exit 1
fi

if [[ -x "$repo_root/.venv/bin/python" ]]; then
  python_bin="$repo_root/.venv/bin/python"
elif [[ -n "${VIRTUAL_ENV:-}" && -x "$VIRTUAL_ENV/bin/python" ]]; then
  python_bin="$VIRTUAL_ENV/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  python_bin="$(command -v python3)"
else
  printf 'Error: Python 3.11 or newer is required to read pyproject.toml.\n' >&2
  exit 1
fi

version="$("$python_bin" - "$repo_root/pyproject.toml" <<'PY'
import sys
import tomllib

with open(sys.argv[1], "rb") as pyproject:
    data = tomllib.load(pyproject)
version = data.get("project", {}).get("version")
if not isinstance(version, str) or not version:
    raise SystemExit("Error: project.version must be a non-empty string in pyproject.toml.")
if any(character in version for character in "/\\\r\n"):
    raise SystemExit("Error: project.version contains characters unsafe for an archive name.")
print(version)
PY
)"

out_dir="${NBLANE_PACKAGE_OUT:-dist/ubuntu}"
if [[ "$out_dir" != /* ]]; then
  out_dir="$repo_root/$out_dir"
fi
archive_name="nblane-${version}-ubuntu.tar.gz"
source_name="nblane-${version}-source.tar.gz"
build_time="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

work_dir="$(mktemp -d "${TMPDIR:-/tmp}/nblane-package.XXXXXX")"
trap 'rm -rf "$work_dir"' EXIT
package_dir="$work_dir/package"
raw_source="$work_dir/source.tar"
mkdir -p "$package_dir/packaging/ubuntu"

if [[ "$allow_dirty" == "1" ]]; then
  git ls-files -coz --exclude-standard |
    while IFS= read -r -d '' path; do
      if [[ -e "$path" || -L "$path" ]]; then
        printf '%s\0' "$path"
      fi
    done |
    tar --create --file="$raw_source" --no-recursion --null \
      --verbatim-files-from --files-from=-
else
  git archive --format=tar --output="$raw_source" HEAD
fi

"$python_bin" - "$raw_source" "$package_dir/$source_name" <<'PY'
import sys
import tarfile
from pathlib import PurePosixPath

raw_path, output_path = sys.argv[1:]
root_data_directories = {
    ".dev-assets",
    ".dev-data",
    ".venv",
    "build",
    "dist",
    "test-results",
}
local_directories = {
    "__pycache__",
    ".git",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    "node_modules",
}
environment_templates = {".env.example", ".env.sample", ".env.template"}


def excluded(name: str) -> bool:
    parts = PurePosixPath(name).parts
    if not parts:
        return False
    if name.startswith("/") or ".." in parts:
        raise ValueError(f"Unsafe source archive path: {name}")
    base = parts[-1]
    if parts[0] in root_data_directories:
        return True
    if any(part in local_directories for part in parts):
        return True
    if any(part.endswith(".egg-info") for part in parts):
        return True
    if base == ".env" or (
        base.startswith(".env.") and base not in environment_templates
    ):
        return True
    if base in {".reader-token-secret", ".coverage", ".DS_Store"}:
        return True
    if parts == ("config.yaml",):
        return True
    if len(parts) >= 2 and parts[0] == "profiles" and parts[1] != "template":
        return True
    if len(parts) >= 2 and parts[:2] == ("schemas", ".learned"):
        return True
    if len(parts) >= 2 and parts[0] == "auth" and parts != (
        "auth",
        "users.example.yaml",
    ):
        return True
    if len(parts) >= 3 and parts[:3] in {
        ("tests", "e2e", ".auth"),
        ("tests", "e2e", "audit-out"),
    }:
        return True
    if parts == (
        "src",
        "nblane",
        "home_dashboard_component",
        "frontend",
        "playground",
        "data",
        "snapshot.json",
    ):
        return True
    if base.endswith((".pyc", ".pyo")):
        return True
    return base.startswith("tmux-") and base.endswith(".log")


with tarfile.open(raw_path, "r:") as source, tarfile.open(
    output_path, "w:gz", format=tarfile.PAX_FORMAT
) as target:
    for member in source:
        while member.name.startswith("./"):
            member.name = member.name[2:]
        if not member.name or excluded(member.name):
            continue
        member.pax_headers.pop("path", None)
        member.uid = 0
        member.gid = 0
        member.uname = ""
        member.gname = ""
        if member.isreg():
            extracted = source.extractfile(member)
            if extracted is None:
                raise RuntimeError(f"Cannot read source archive member: {member.name}")
            target.addfile(member, extracted)
        else:
            target.addfile(member)
PY

cat > "$package_dir/install.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
bash "$(dirname -- "${BASH_SOURCE[0]}")/packaging/ubuntu/install.sh" "$@"
EOF
chmod +x "$package_dir/install.sh"
cp "$installer" "$package_dir/packaging/ubuntu/install.sh"

{
  printf 'VERSION=%s\n' "$version"
  printf 'COMMIT=%s\n' "$commit"
  printf 'BUILD_TIME=%s\n' "$build_time"
  printf 'SOURCE_ARCHIVE=%s\n' "$source_name"
} > "$package_dir/BUILDINFO"

if [[ "$offline" == "1" ]]; then
  locked_requirements="$package_dir/requirements-locked.txt"
  if ! command -v uv >/dev/null 2>&1; then
    printf 'Error: uv is required to export locked dependencies. Install uv, or set NBLANE_PACKAGE_OFFLINE=0 for a development-only package.\n' >&2
    exit 1
  fi
  uv export --frozen --no-hashes --no-dev --no-emit-project \
    -o "$locked_requirements"
  printf '\nsetuptools>=68.0\nwheel\n' >> "$locked_requirements"
  mkdir -p "$package_dir/wheelhouse"
  "$python_bin" -m pip download \
    --requirement "$locked_requirements" \
    --dest "$package_dir/wheelhouse"
fi

package_entries=(install.sh packaging "$source_name" BUILDINFO)
if [[ "$offline" == "1" ]]; then
  package_entries+=(requirements-locked.txt wheelhouse)
fi

tar -czf "$work_dir/$archive_name" -C "$package_dir" "${package_entries[@]}"
mkdir -p "$out_dir"
mv "$work_dir/$archive_name" "$out_dir/$archive_name"
cp "$package_dir/BUILDINFO" "$out_dir/BUILDINFO"
(
  cd "$out_dir"
  sha256sum "$archive_name" > "$archive_name.sha256"
)

printf 'Created %s\n' "$out_dir/$archive_name"
printf 'Created %s\n' "$out_dir/$archive_name.sha256"
printf 'Created %s\n' "$out_dir/BUILDINFO"
