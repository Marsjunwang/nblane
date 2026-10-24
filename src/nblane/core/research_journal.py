"""Reader JSONL and PDF snapshots for the agent undo journal."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
import tempfile
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any

from nblane.core import agent_policy, research_jsonl
from nblane.core.file_lock import locked_profile_write

JSONL_KIND_PREFIX = "jsonl:"
ASSET_KIND_PREFIX = "asset:"
ASSET_WILDCARD = "asset:*"

State = dict[str, Any]
RestoreTarget = tuple[str, State | None, State | None]

_JSONL_KEYS = {
    "annotations": "id",
    "chunks": "id",
    "translations": "id",
    "paper-pages": "page",
    "paper-segments": "segment_id",
    "paper-structure": "unit_id",
}
_SHA256 = re.compile(r"[0-9a-f]{64}")


class RestoreConflictError(RuntimeError):
    """A locked restore found that a target changed after the journal write."""

    def __init__(self, kind: str) -> None:
        super().__init__(kind)
        self.kind = kind


class SnapshotIntegrityError(RuntimeError):
    """A required content-addressed asset snapshot is missing or invalid."""


def _jsonl_target(pdir: Path, kind: str) -> tuple[str, Path, str]:
    relative = kind[len(JSONL_KIND_PREFIX):].strip()
    if (
        not relative
        or "\\" in relative
        or any(part in ("", ".", "..") for part in relative.split("/"))
    ):
        raise ValueError(f"unsupported journal JSONL file: {relative!r}")
    pure = PurePosixPath(relative)
    if (
        pure.is_absolute()
        or len(pure.parts) != 3
        or pure.parts[0] != "research"
        or pure.parts[1] not in _JSONL_KEYS
        or pure.suffix.lower() != ".jsonl"
    ):
        raise ValueError(f"unsupported journal JSONL file: {relative!r}")
    root = pdir.resolve()
    target = (root / Path(*pure.parts)).resolve()
    if target == root or root not in target.parents:
        raise ValueError(f"journal JSONL file escapes the profile: {relative!r}")
    return pure.as_posix(), target, _JSONL_KEYS[pure.parts[1]]


def jsonl_target(pdir: Path, kind: str) -> tuple[str, Path]:
    """Return a validated profile-relative JSONL path and absolute path."""
    relative, target, _key = _jsonl_target(pdir, kind)
    return relative, target


def _row_identity(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if value is None or isinstance(value, (dict, list)):
        return ""
    return str(value).strip()


def _row_states(rows: list[dict[str, Any]], key: str) -> dict[str, State]:
    out: dict[str, State] = {}
    for index, row in enumerate(rows):
        identity = _row_identity(row, key)
        if not identity:
            continue
        if identity in out:
            raise ValueError(f"duplicate JSONL journal key {key}={identity!r}")
        out[identity] = {"index": index, "item": row}
    return out


def jsonl_states(pdir: Path, kind: str) -> dict[str, State]:
    """Read keyed rows without retaining a whole-file journal state."""
    _relative, target, key = _jsonl_target(pdir, kind)
    return _row_states(research_jsonl.load_jsonl(target), key)


def _comparable(state: State | None) -> str:
    if state is None:
        return "null"
    return json.dumps(state.get("item"), sort_keys=True, ensure_ascii=False, default=str)


def _same_state(left: State | None, right: State | None) -> bool:
    return _comparable(left) == _comparable(right)


def restore_jsonl(pdir: Path, kind: str, targets: Sequence[RestoreTarget]) -> None:
    """Restore selected rows and recheck every ``after`` under the JSONL lock."""
    _relative, target, key = _jsonl_target(pdir, kind)

    def apply(rows: research_jsonl.JsonlRows) -> None:
        try:
            current = _row_states(rows, key)
        except ValueError as exc:
            raise RestoreConflictError(kind) from exc
        for identity, _before, after in targets:
            if not _same_state(current.get(identity), after):
                raise RestoreConflictError(kind)
        identities = {identity for identity, _before, _after in targets}
        restored = [row for row in rows if _row_identity(row, key) not in identities]
        before_states = [before for _identity, before, _after in targets if before is not None]
        for state in sorted(before_states, key=lambda item: int(item.get("index") or 0)):
            item = state.get("item")
            if not isinstance(item, dict):
                raise SnapshotIntegrityError(f"invalid JSONL snapshot for {kind}")
            index = max(0, min(int(state.get("index") or 0), len(restored)))
            restored.insert(index, copy.deepcopy(item))
        rows[:] = restored

    research_jsonl.mutate_jsonl(
        target,
        apply,
        action=f"undo agent write to {target.name}",
    )


def _asset_root(pdir: Path) -> Path:
    from nblane.core.research_papers._paths import research_asset_root

    return research_asset_root(pdir.resolve())


def _asset_path(pdir: Path, ref: str) -> Path:
    from nblane.core.research_papers._paths import _asset_path as asset_path

    clean = str(ref or "").strip()
    if not clean or clean == "*" or not clean.lower().endswith(".pdf"):
        raise ValueError(f"unsupported journal PDF asset: {ref!r}")
    return asset_path(pdir.resolve(), clean)


def _asset_refs(pdir: Path, kind: str) -> list[str]:
    if kind != ASSET_WILDCARD:
        if not kind.startswith(ASSET_KIND_PREFIX):
            raise ValueError(f"unsupported journal asset entity: {kind}")
        ref = kind[len(ASSET_KIND_PREFIX):].strip()
        _asset_path(pdir, ref)
        return [ref]
    root = _asset_root(pdir)
    if not root.exists():
        return []
    refs: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() != ".pdf":
            continue
        ref = path.relative_to(root).as_posix()
        _asset_path(pdir, ref)
        refs.append(ref)
    return sorted(refs)


def _hash_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _snapshot_ref(digest: str) -> str:
    return f"sha256/{digest[:2]}/{digest}"


def _asset_state(pdir: Path, ref: str) -> State:
    path = _asset_path(pdir, ref)
    if not path.exists():
        return {}
    if not path.is_file():
        raise ValueError(f"PDF asset is not a regular file: {ref}")
    digest, size = _hash_file(path)
    return {
        "item": {
            "ref": ref,
            "sha256": digest,
            "size": size,
            "snapshot_ref": _snapshot_ref(digest),
        }
    }


def asset_states(pdir: Path, kind: str) -> dict[str, State]:
    """Hash current PDFs without persisting their bytes."""
    out: dict[str, State] = {}
    for ref in _asset_refs(pdir, kind):
        state = _asset_state(pdir, ref)
        if state:
            out[ref] = state
    return out


def _asset_snapshot_root(pdir: Path) -> Path:
    resolved = pdir.resolve()
    identity = hashlib.sha256(os.fsencode(str(resolved))).hexdigest()
    return agent_policy.state_dir().expanduser().resolve() / "journal-assets" / identity


def _valid_snapshot_ref(state: State | None) -> str:
    if not isinstance(state, dict):
        return ""
    item = state.get("item")
    if not isinstance(item, dict):
        return ""
    digest = str(item.get("sha256") or "")
    ref = str(item.get("snapshot_ref") or "")
    if not _SHA256.fullmatch(digest) or ref != _snapshot_ref(digest):
        return ""
    return ref


def _snapshot_path(pdir: Path, state: State) -> tuple[Path, str, int]:
    item = state.get("item")
    if not isinstance(item, dict):
        raise SnapshotIntegrityError("invalid PDF journal state")
    digest = str(item.get("sha256") or "")
    ref = _valid_snapshot_ref(state)
    size = item.get("size")
    if not ref or isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise SnapshotIntegrityError("invalid PDF snapshot metadata")
    return _asset_snapshot_root(pdir) / Path(*PurePosixPath(ref).parts), digest, size


def _fsync_directory(path: Path) -> None:
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _atomic_copy(
    source: Path,
    target: Path,
    *,
    expected: tuple[str, int] | None = None,
) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=str(target.parent),
    )
    try:
        with source.open("rb") as reader, os.fdopen(fd, "wb") as writer:
            shutil.copyfileobj(reader, writer, length=1024 * 1024)
            writer.flush()
            os.fsync(writer.fileno())
        if expected is not None and _hash_file(Path(tmp_name)) != expected:
            raise SnapshotIntegrityError(f"PDF snapshot content mismatch: {source}")
        try:
            mode = target.stat().st_mode
        except FileNotFoundError:
            mode = source.stat().st_mode
        os.chmod(tmp_name, mode)
        os.replace(tmp_name, target)
        tmp_name = ""
        _fsync_directory(target.parent)
    finally:
        if tmp_name:
            try:
                os.unlink(tmp_name)
            except FileNotFoundError:
                pass


def _ensure_asset_snapshot(pdir: Path, state: State) -> None:
    item = state["item"]
    source = _asset_path(pdir, str(item["ref"]))
    destination, digest, size = _snapshot_path(pdir, state)
    if destination.exists():
        if destination.is_file() and _hash_file(destination) == (digest, size):
            return
        raise SnapshotIntegrityError(f"corrupt PDF snapshot: {destination}")
    _atomic_copy(source, destination, expected=(digest, size))


def prepare_asset_snapshots(pdir: Path, kinds: Sequence[str]) -> None:
    """Persist old PDF bytes for the pre-write phase only."""
    for kind in dict.fromkeys(kinds):
        if not kind.startswith(ASSET_KIND_PREFIX):
            continue
        for state in asset_states(pdir, kind).values():
            _ensure_asset_snapshot(pdir, state)


def _change_ref(pdir: Path, change: dict[str, Any]) -> str:
    kind = str(change.get("entity") or "")
    ref = str(change.get("id") or "")
    if kind == ASSET_WILDCARD:
        _asset_path(pdir, ref)
        return ref
    if not kind.startswith(ASSET_KIND_PREFIX):
        raise ValueError(f"unsupported journal asset entity: {kind}")
    expected = kind[len(ASSET_KIND_PREFIX):].strip()
    if ref != expected:
        raise SnapshotIntegrityError(f"PDF journal id does not match {kind}")
    _asset_path(pdir, ref)
    return ref


def _asset_referenced(pdir: Path, ref: str) -> bool:
    from nblane.core.research_sources import load_research_sources_raw

    raw = load_research_sources_raw(pdir) or {}
    rows = raw.get("sources") if isinstance(raw, dict) else []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        metadata = row.get("metadata")
        if isinstance(metadata, dict) and str(metadata.get("pdf_asset_ref") or "").strip() == ref:
            return True
    return False


def _delete_unreferenced_asset(pdir: Path, ref: str, path: Path) -> None:
    with locked_profile_write(pdir / "research", "sources.yaml"):
        if _asset_referenced(pdir, ref):
            return
        path.unlink(missing_ok=True)


def restore_assets(pdir: Path, changes: Sequence[dict[str, Any]]) -> None:
    """Restore PDF bytes after sources, preserving still-referenced new assets."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for change in changes:
        _change_ref(pdir, change)
        grouped.setdefault(str(change["entity"]), []).append(change)
    for kind, group in grouped.items():
        current = asset_states(pdir, kind)
        for change in group:
            if not _same_state(current.get(str(change["id"])), change.get("after")):
                raise RestoreConflictError(kind)
    for change in changes:
        ref = _change_ref(pdir, change)
        path = _asset_path(pdir, ref)
        before = change.get("before")
        if before is None:
            _delete_unreferenced_asset(pdir, ref, path)
            continue
        snapshot, digest, size = _snapshot_path(pdir, before)
        if not snapshot.is_file():
            raise SnapshotIntegrityError(f"missing PDF snapshot for {ref}")
        _atomic_copy(snapshot, path, expected=(digest, size))


@contextmanager
def rollback_assets(pdir: Path, changes: Sequence[dict[str, Any]]) -> Iterator[None]:
    """Restore the pre-undo PDF state if any part of undo fails."""
    targets: dict[str, Path] = {}
    for change in changes:
        ref = _change_ref(pdir, change)
        targets[ref] = _asset_path(pdir, ref)
    if not targets:
        yield
        return
    root = _asset_snapshot_root(pdir)
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rollback-", dir=str(root)) as tmp:
        backups: dict[str, tuple[Path, Path | None, tuple[str, int] | None]] = {}
        for index, (ref, path) in enumerate(targets.items()):
            backup = Path(tmp) / f"{index}.bin"
            if path.exists():
                if not path.is_file():
                    raise ValueError(f"PDF asset is not a regular file: {ref}")
                shutil.copyfile(path, backup)
                backups[ref] = (path, backup, _hash_file(backup))
            else:
                backups[ref] = (path, None, None)
        try:
            yield
        except Exception as original:
            if isinstance(original, RestoreConflictError):
                raise
            failures: list[str] = []
            for ref, (path, backup, fingerprint) in backups.items():
                try:
                    if backup is None:
                        if path.exists():
                            path.unlink()
                        continue
                    if path.is_file() and _hash_file(path) == fingerprint:
                        continue
                    _atomic_copy(backup, path)
                except (OSError, SnapshotIntegrityError) as exc:
                    failures.append(f"{ref}: {exc}")
            if failures:
                raise OSError(f"{original}; PDF rollback failed: {'; '.join(failures)}") from original
            raise


def _entry_snapshot_refs(entries: Sequence[dict[str, Any]]) -> set[str]:
    refs: set[str] = set()
    for entry in entries:
        for change in entry.get("changes") or []:
            if not isinstance(change, dict) or not str(change.get("entity") or "").startswith(ASSET_KIND_PREFIX):
                continue
            for side in ("before", "after"):
                ref = _valid_snapshot_ref(change.get(side))
                if ref:
                    refs.add(ref)
    return refs


def prune_asset_snapshots(
    pdir: Path,
    removed_entries: Sequence[dict[str, Any]],
    retained_entries: Sequence[dict[str, Any]],
) -> None:
    """Delete snapshots orphaned by entries actually pruned from the journal."""
    candidates = _entry_snapshot_refs(removed_entries)
    live = _entry_snapshot_refs(retained_entries)
    root = _asset_snapshot_root(pdir)
    for ref in sorted(candidates - live):
        (root / Path(*PurePosixPath(ref).parts)).unlink(missing_ok=True)


__all__ = [
    "ASSET_KIND_PREFIX",
    "ASSET_WILDCARD",
    "JSONL_KIND_PREFIX",
    "RestoreConflictError",
    "SnapshotIntegrityError",
    "asset_states",
    "jsonl_states",
    "jsonl_target",
    "prepare_asset_snapshots",
    "prune_asset_snapshots",
    "restore_assets",
    "restore_jsonl",
    "rollback_assets",
]
