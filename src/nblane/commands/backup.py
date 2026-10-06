"""``nblane backup`` — run by the daily systemd --user timer."""

from __future__ import annotations

import sys

from nblane.core import backup_targets


def cmd_backup(command: str, *, target: str = "") -> None:
    """``status`` prints each target; ``run`` snapshots and pushes (exit 1 on any failure)."""
    if command == "status":
        for item in backup_targets.status()["targets"]:
            remote = item["remote_url"] or "（无远端）"
            print(f"{item['id']}: {item['path']} → {remote}；未推送 {item['ahead']}，未提交 {item['dirty']}")
        return
    try:
        results = backup_targets.run_backup(target or None)
    except backup_targets.BackupError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    failed = 0
    for result in results:
        if result["ok"]:
            note = "已提交并推送" if result["committed"] else "已推送"
            print(f"[OK] {result['id']}：{note}")
        else:
            failed += 1
            print(f"[失败] {result['id']}：{result['error']}", file=sys.stderr)
    sys.exit(1 if failed else 0)
