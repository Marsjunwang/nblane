"""Tunable skill-progression rules (progress score per skill-tree node).

One node's ``progress`` answers "how close is this skill to its next rung":
``GET /api/v1/profiles/{name}/skill-tree`` attaches it to every node so the
SPA can render rung-up affordances without reimplementing the math.

Model (all constants below are the tuning surface — adjust here, not in
callers):

- Rungs follow the skill-tree.yaml status ladder ``RUNG_ORDER``
  (locked -> learning -> solid -> expert). ``next_rung`` is the rung above
  the node's current status; expert has none (``threshold_next`` is null).
- Each of the node's *non-deprecated* ``evidence_refs`` that resolves to a
  pool row contributes its strength weight (``STRENGTH_WEIGHTS``: 弱 weak=1,
  中 medium=10, 强 strong=100; ``high_trust`` scores as strong, unrated or
  unknown strengths score ``DEFAULT_STRENGTH_WEIGHT``) plus
  ``BREAKTHROUGH_WEIGHT`` (1000) when the row carries ``breakthrough: true``
  — a landmark proof outweighs any amount of routine evidence.
- ``threshold_next`` is the score needed for the next rung
  (``RUNG_THRESHOLDS``: locked->learning 10, learning->solid 30,
  solid->expert 100).
- ``eligible`` is true when a next rung exists AND
  (``score >= threshold_next`` OR ``breakthrough_count >= 1``): one
  breakthrough alone justifies the rung-up prompt. Expert nodes are never
  eligible — there is no next rung.

Eligibility is advisory: status writes still go through the existing PATCH
endpoint (三态 vocabulary; ``lit`` lands as ``solid``), which appends the
``skill.lit`` chronicle entry when the rung actually advances.
"""

from __future__ import annotations

from dataclasses import dataclass

from nblane.core.models import EvidencePool, EvidenceRecord

# The status ladder, lowest to highest. Unknown/empty statuses score as the
# bottom rung (locked).
RUNG_ORDER: tuple[str, ...] = ("locked", "learning", "solid", "expert")

# 分量 -> score weight. ``high_trust`` (paper/official-source grade) scores
# as strong; anything unrated/unknown falls back to DEFAULT_STRENGTH_WEIGHT.
STRENGTH_WEIGHTS: dict[str, int] = {
    "weak": 1,
    "medium": 10,
    "strong": 100,
    "high_trust": 100,
}
DEFAULT_STRENGTH_WEIGHT = 1

# A breakthrough evidence row adds this on top of its strength weight.
BREAKTHROUGH_WEIGHT = 1000

# Score required to advance from one rung to the next.
RUNG_THRESHOLDS: dict[tuple[str, str], int] = {
    ("locked", "learning"): 10,
    ("learning", "solid"): 30,
    ("solid", "expert"): 100,
}


@dataclass
class NodeProgress:
    """Progression readout for one skill-tree node."""

    score: int = 0
    next_rung: str | None = None
    threshold_next: int | None = None
    breakthrough_count: int = 0
    eligible: bool = False

    def to_dict(self) -> dict[str, object]:
        """Serialize for API responses."""
        return {
            "score": self.score,
            "next_rung": self.next_rung,
            "threshold_next": self.threshold_next,
            "breakthrough_count": self.breakthrough_count,
            "eligible": self.eligible,
        }


def rung_index(status: object) -> int:
    """Position of *status* on the ladder; unknown/empty counts as locked."""
    clean = str(status or "").strip()
    try:
        return RUNG_ORDER.index(clean)
    except ValueError:
        return 0


def next_rung(status: object) -> str | None:
    """The rung above *status*, or None for the top rung (expert)."""
    index = rung_index(status)
    if index >= len(RUNG_ORDER) - 1:
        return None
    return RUNG_ORDER[index + 1]


def threshold_for_next(status: object) -> int | None:
    """Score needed to reach the next rung; None when at the top."""
    nxt = next_rung(status)
    if nxt is None:
        return None
    current = RUNG_ORDER[rung_index(status)]
    return RUNG_THRESHOLDS.get((current, nxt))


def _evidence_weight(record: EvidenceRecord) -> int:
    """Score contribution of one resolved (non-deprecated) pool row."""
    weight = STRENGTH_WEIGHTS.get(
        str(record.strength or "").strip(), DEFAULT_STRENGTH_WEIGHT
    )
    if record.breakthrough:
        weight += BREAKTHROUGH_WEIGHT
    return weight


def node_progress(node: dict, pool: EvidencePool | None) -> NodeProgress:
    """Compute the progression readout for one raw skill-tree node dict.

    Only ``evidence_refs`` resolving to non-deprecated pool rows score —
    inline ``evidence`` rows are ungraded by definition and missing ids are
    skipped (validate catches dangling refs).
    """
    index: dict[str, EvidenceRecord] = pool.by_id() if pool is not None else {}
    score = 0
    breakthrough_count = 0
    seen: set[str] = set()
    raw_refs = node.get("evidence_refs") or []
    if isinstance(raw_refs, list):
        for rid in raw_refs:
            if not isinstance(rid, str):
                continue
            key = rid.strip()
            if not key or key in seen:
                continue
            seen.add(key)
            record = index.get(key)
            if record is None or record.deprecated:
                continue
            score += _evidence_weight(record)
            if record.breakthrough:
                breakthrough_count += 1
    status = node.get("status")
    nxt = next_rung(status)
    threshold = threshold_for_next(status)
    eligible = bool(
        nxt is not None
        and threshold is not None
        and (score >= threshold or breakthrough_count >= 1)
    )
    return NodeProgress(
        score=score,
        next_rung=nxt,
        threshold_next=threshold,
        breakthrough_count=breakthrough_count,
        eligible=eligible,
    )
