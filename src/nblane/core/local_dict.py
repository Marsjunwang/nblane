"""Offline English->Chinese dictionary for fast word-level translation.

Backed by a vendored, frequency-filtered subset of ECDICT
(``data/ecdict_mini.csv``). Lookups avoid an LLM round-trip for single words
and short phrases. Falls back to the LLM path when a term is not found.
"""

from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parent / "data" / "ecdict_mini.csv"
_WORDISH = re.compile(r"^[A-Za-z][A-Za-z'\-]*$")


@lru_cache(maxsize=1)
def _dictionary() -> dict[str, str]:
    table: dict[str, str] = {}
    if not _DATA_PATH.is_file():
        return table
    try:
        with _DATA_PATH.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                word = (row.get("word") or "").strip().lower()
                translation = (row.get("translation") or "").strip()
                if not word or not translation:
                    continue
                phonetic = (row.get("phonetic") or "").strip()
                if phonetic:
                    translation = f"[{phonetic}] {translation}"
                table[word] = translation
    except (OSError, csv.Error):
        return {}
    return table


def is_lookupable(text: str) -> bool:
    """Return whether ``text`` is a single word eligible for dictionary lookup."""

    clean = (text or "").strip()
    if not clean or len(clean) > 32:
        return False
    return bool(_WORDISH.match(clean))


def lookup(text: str) -> str | None:
    """Return an offline Chinese gloss for a single English word, or None."""

    if not is_lookupable(text):
        return None
    return _dictionary().get(text.strip().lower())


def available() -> bool:
    """Return whether the offline dictionary data is present and non-empty."""

    return bool(_dictionary())
