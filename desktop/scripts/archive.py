"""Preserve macOS bundle symlinks and executable modes in a cross-build ZIP."""

from __future__ import annotations

import os
from pathlib import Path
import stat
import sys
import zipfile


def archive_bundle(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
        bundle.write(source, source.name + "/")
        for directory, directories, files in os.walk(source, followlinks=False):
            for name in directories + files:
                item = Path(directory) / name
                if item.is_symlink():
                    entry = zipfile.ZipInfo(item.relative_to(source.parent).as_posix())
                    entry.create_system = 3
                    entry.external_attr = (stat.S_IFLNK | 0o777) << 16
                    bundle.writestr(entry, os.readlink(item))
                else:
                    bundle.write(item, item.relative_to(source.parent))


if __name__ == "__main__":
    archive_bundle(Path(sys.argv[1]), Path(sys.argv[2]))
