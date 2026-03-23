"""Append lightweight Q/A records for later crystallization."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from nblane.core.io import profile_dir


def append_interaction_record(
    profile: str,
    *,
    question: str,
    answer: str,
    skill_ids: list[str],
) -> Path:
    """Append one JSON object as a line under ``interactions/*.jsonl``."""
    pdir = profile_dir(profile)
    idir = pdir / "interactions"
    idir.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = idir / f"{day}.jsonl"
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "question": question.strip(),
        "answer": answer.strip(),
        "skill_ids": [s.strip() for s in skill_ids if s.strip()],
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(
            json.dumps(record, ensure_ascii=False) + "\n"
        )
    return path
