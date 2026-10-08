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


def _base_forms(word: str) -> list[str]:
    """Return likely dictionary headwords for an inflected English word.

    A small rule set (plural, -ed, -ing, comparative, -ly) covers most misses
    in papers ("capabilities", "embodied", "grounded"). Candidates are only
    used when they exist in the dictionary, so over-generation is harmless.
    """

    out: list[str] = []

    def add(candidate: str) -> None:
        if len(candidate) >= 2 and candidate != word and candidate not in out:
            out.append(candidate)

    if word.endswith("ies") and len(word) > 4:
        add(word[:-3] + "y")
    if word.endswith("ied") and len(word) > 4:
        add(word[:-3] + "y")
    if word.endswith("es"):
        add(word[:-2])
    if word.endswith("s") and not word.endswith("ss"):
        add(word[:-1])
    for suffix in ("ed", "ing", "er", "est"):
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            stem = word[: -len(suffix)]
            add(stem)
            add(stem + "e")
            # Doubled consonant: "stopped" -> "stop".
            if len(stem) > 2 and stem[-1] == stem[-2]:
                add(stem[:-1])
    if word.endswith("ly") and len(word) > 4:
        add(word[:-2])
        if word.endswith("ily"):
            add(word[:-3] + "y")
    return out


def headword_candidates(text: str) -> list[str]:
    """Return ``text`` lowercased plus its likely base forms, most specific first."""

    word = (text or "").strip().lower()
    if not word:
        return []
    return [word, *_base_forms(word)]


def lookup(text: str) -> str | None:
    """Return an offline Chinese gloss for a single English word, or None.

    Falls back to the base form of an inflected word; the gloss then names
    the headword it came from, e.g. ``(capability) [..] n. 能力``.
    """

    if not is_lookupable(text):
        return None
    word = text.strip().lower()
    table = _dictionary()
    gloss = table.get(word)
    if gloss:
        return gloss
    for candidate in _base_forms(word):
        gloss = table.get(candidate)
        if gloss:
            return f"({candidate}) {gloss}"
    return None


def available() -> bool:
    """Return whether the offline dictionary data is present and non-empty."""

    return bool(_dictionary())
