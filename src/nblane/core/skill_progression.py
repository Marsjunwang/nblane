"""Tunable skill-progression rules (progress score per skill-tree node).

One node's ``progress`` answers "how close is this skill to its next rung":
``GET /api/v1/profiles/{name}/skill-tree`` attaches it to every node so the
SPA can render rung-up affordances without reimplementing the math.

Model (the constants below are the defaults; a profile can override them
in ``web-preferences.yaml`` under ``skill_progression``, read through
``rules_from_preferences`` into a ``ProgressionRules``):

- Rungs follow the skill-tree.yaml status ladder ``RUNG_ORDER``
  (locked -> learning -> solid -> expert). ``next_rung`` is the rung above
  the node's current status; expert has none (``threshold_next`` is null).
- Each of the node's *non-deprecated* ``evidence_refs`` that resolves to a
  pool row contributes (with ``COUNT_REVIEWED_ONLY`` only rows whose
  ``review_status`` is ``reviewed`` — AI-prefilled, unconfirmed evidence
  does not move a skill) its strength weight (``STRENGTH_WEIGHTS``: 弱 weak=1,
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
endpoint (三态 vocabulary plus ``expert``; ``lit`` lands as ``solid``), which
appends the
``skill.lit`` chronicle entry when the rung actually advances.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

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

# Only human-reviewed evidence scores (unreviewed rows are AI prefills).
COUNT_REVIEWED_ONLY = True

# Score required to advance from one rung to the next.
RUNG_THRESHOLDS: dict[tuple[str, str], int] = {
    ("locked", "learning"): 10,
    ("learning", "solid"): 30,
    ("solid", "expert"): 100,
}


# Upper bound for any configurable weight / threshold.
MAX_RULE_VALUE = 100_000


@dataclass
class ProgressionRules:
    """One profile's progression tuning; defaults mirror the constants."""

    weights: dict[str, int] = field(
        default_factory=lambda: {
            key: STRENGTH_WEIGHTS[key] for key in ("weak", "medium", "strong")
        }
    )
    breakthrough_bonus: int = BREAKTHROUGH_WEIGHT
    # Keyed by the target rung: learning / solid / expert.
    thresholds: dict[str, int] = field(
        default_factory=lambda: {
            to: value for (_from, to), value in RUNG_THRESHOLDS.items()
        }
    )
    breakthrough_unlocks: bool = True
    reviewed_only: bool = COUNT_REVIEWED_ONLY

    def strength_weight(self, strength: object) -> int:
        """Weight for one 分量; high_trust = strong, unrated/unknown = weak."""
        clean = str(strength or "").strip()
        if clean == "high_trust":
            clean = "strong"
        return self.weights.get(clean, self.weights.get("weak", DEFAULT_STRENGTH_WEIGHT))

    def to_dict(self) -> dict[str, Any]:
        """Serialize in the web-preferences.yaml shape."""
        return {
            "weights": dict(self.weights),
            "breakthrough_bonus": self.breakthrough_bonus,
            "thresholds": dict(self.thresholds),
            "breakthrough_unlocks": self.breakthrough_unlocks,
            "reviewed_only": self.reviewed_only,
        }


def _rule_int(value: object, default: int) -> int:
    try:
        parsed = int(value) if value is not None and str(value).strip() else default
    except (TypeError, ValueError):
        parsed = default
    return max(0, min(MAX_RULE_VALUE, parsed))


def _rule_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    if text in {"true", "1", "yes", "on"}:
        return True
    if text in {"false", "0", "no", "off"}:
        return False
    return default


def normalize_rules(raw: object) -> dict[str, Any]:
    """Clamp a stored ``skill_progression`` mapping onto the defaults."""
    source = raw if isinstance(raw, dict) else {}
    base = ProgressionRules()
    weights = source.get("weights") if isinstance(source.get("weights"), dict) else {}
    thresholds = (
        source.get("thresholds") if isinstance(source.get("thresholds"), dict) else {}
    )
    return ProgressionRules(
        weights={k: _rule_int(weights.get(k), v) for k, v in base.weights.items()},
        breakthrough_bonus=_rule_int(
            source.get("breakthrough_bonus"), base.breakthrough_bonus
        ),
        thresholds={
            k: _rule_int(thresholds.get(k), v) for k, v in base.thresholds.items()
        },
        breakthrough_unlocks=_rule_bool(
            source.get("breakthrough_unlocks"), base.breakthrough_unlocks
        ),
        reviewed_only=_rule_bool(source.get("reviewed_only"), base.reviewed_only),
    ).to_dict()


def rules_error(rules: dict[str, Any]) -> str | None:
    """Human-readable problem with normalized rules, or None when valid.

    Thresholds must climb strictly (learning < solid < expert) and be
    positive, or a rung would be "reached" with no evidence at all.
    """
    thresholds = rules.get("thresholds") or {}
    ladder = [thresholds.get(rung, 0) for rung in RUNG_ORDER[1:]]
    if ladder[0] <= 0:
        return "晋升门槛必须大于 0。"
    if any(lo >= hi for lo, hi in zip(ladder, ladder[1:])):
        return "晋升门槛必须逐级递增：在学 < 扎实 < 精通。"
    return None


def rules_from_preferences(preferences: dict[str, Any] | None) -> ProgressionRules:
    """Build the rules for one profile from its normalized web preferences."""
    data = normalize_rules((preferences or {}).get("skill_progression"))
    return ProgressionRules(
        weights=data["weights"],
        breakthrough_bonus=data["breakthrough_bonus"],
        thresholds=data["thresholds"],
        breakthrough_unlocks=data["breakthrough_unlocks"],
        reviewed_only=data["reviewed_only"],
    )


@dataclass
class EvidenceContribution:
    """How one linked pool row feeds (or does not feed) the node score."""

    evidence_id: str
    points: int = 0
    counted: bool = True
    strength: str = ""
    breakthrough: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "evidence_id": self.evidence_id,
            "points": self.points,
            "counted": self.counted,
            "strength": self.strength,
            "breakthrough": self.breakthrough,
        }


@dataclass
class NodeProgress:
    """Progression readout for one skill-tree node.

    ``points_to_next`` is the score still missing for the next rung (0 when
    met, None at the top); ``medium_needed`` restates it as a count of
    medium-strength evidence rows (None when not applicable).
    ``contributions`` lists every linked, non-deprecated pool row with the
    points it would add; ``counted`` is false for rows the rules skip
    (unreviewed under ``reviewed_only``).
    """

    score: int = 0
    next_rung: str | None = None
    threshold_next: int | None = None
    breakthrough_count: int = 0
    eligible: bool = False
    points_to_next: int | None = None
    medium_needed: int | None = None
    contributions: list[EvidenceContribution] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Serialize for API responses."""
        return {
            "score": self.score,
            "next_rung": self.next_rung,
            "threshold_next": self.threshold_next,
            "breakthrough_count": self.breakthrough_count,
            "eligible": self.eligible,
            "points_to_next": self.points_to_next,
            "medium_needed": self.medium_needed,
            "contributions": [item.to_dict() for item in self.contributions],
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


def threshold_for_next(
    status: object, rules: ProgressionRules | None = None
) -> int | None:
    """Score needed to reach the next rung; None when at the top."""
    nxt = next_rung(status)
    if nxt is None:
        return None
    return (rules or ProgressionRules()).thresholds.get(nxt)


def _evidence_weight(record: EvidenceRecord, rules: ProgressionRules) -> int:
    """Score contribution of one resolved (non-deprecated) pool row."""
    weight = rules.strength_weight(record.strength)
    if record.breakthrough:
        weight += rules.breakthrough_bonus
    return weight


def node_progress(
    node: dict,
    pool: EvidencePool | None,
    rules: ProgressionRules | None = None,
) -> NodeProgress:
    """Compute the progression readout for one raw skill-tree node dict.

    Only ``evidence_refs`` resolving to non-deprecated pool rows score (and,
    with ``rules.reviewed_only``, only reviewed ones) — inline ``evidence``
    rows are ungraded by definition and missing ids are skipped (validate
    catches dangling refs). *rules* defaults to the module constants.
    """
    rules = rules or ProgressionRules()
    index: dict[str, EvidenceRecord] = pool.by_id() if pool is not None else {}
    score = 0
    breakthrough_count = 0
    contributions: list[EvidenceContribution] = []
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
            counted = not (
                rules.reviewed_only and record.review_status.strip() != "reviewed"
            )
            points = _evidence_weight(record, rules)
            contributions.append(
                EvidenceContribution(
                    evidence_id=key,
                    points=points,
                    counted=counted,
                    strength=str(record.strength or "").strip(),
                    breakthrough=bool(record.breakthrough),
                )
            )
            if not counted:
                continue
            score += points
            if record.breakthrough:
                breakthrough_count += 1
    status = node.get("status")
    nxt = next_rung(status)
    threshold = threshold_for_next(status, rules)
    eligible = bool(
        nxt is not None
        and threshold is not None
        and (
            score >= threshold
            or (rules.breakthrough_unlocks and breakthrough_count >= 1)
        )
    )
    points_to_next = max(0, threshold - score) if threshold is not None else None
    medium = rules.weights.get("medium", 0)
    medium_needed = (
        math.ceil(points_to_next / medium)
        if points_to_next and medium > 0 and not eligible
        else None
    )
    return NodeProgress(
        score=score,
        next_rung=nxt,
        threshold_next=threshold,
        breakthrough_count=breakthrough_count,
        eligible=eligible,
        points_to_next=points_to_next,
        medium_needed=medium_needed,
        contributions=contributions,
    )
