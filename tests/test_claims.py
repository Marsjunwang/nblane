"""Tests for P2 claim bridge helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.commands.evidence import cmd_evidence_pool_remove
from nblane.core.claims import (
    accepted_claims,
    accepted_claim_index_for_profile,
    apply_claim_candidates,
    apply_claim_candidates_to_book,
    claim_index,
    claim_index_for_profile,
    claim_usage_index,
    generate_claim_candidates_for_scope,
    generate_claim_candidates,
    load_claim_book,
    migrate_legacy_claims,
    supporting_evidence_signature,
)


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


class TestClaims(unittest.TestCase):
    """Claim candidates stay draft-first and dedupe on apply."""

    def _profile(self, root: Path) -> Path:
        profile = root / "alice"
        profile.mkdir()
        _write_yaml(
            profile / "evidence-pool.yaml",
            {
                "profile": "alice",
                "evidence_entries": [
                    {
                        "id": "ev_1",
                        "type": "project",
                        "title": "Built dashboard payload",
                        "summary": "Implemented dashboard payload normalization.",
                        "review_status": "reviewed",
                        "public_readiness": "draftable",
                        "project_refs": ["project:nblane"],
                        "source_refs": ["commit:abc"],
                    }
                ],
            },
        )
        _write_yaml(
            profile / "skill-tree.yaml",
            {
                "schema": "robotics-engineer",
                "nodes": [
                    {
                        "id": "ros2_basics",
                        "status": "solid",
                        "evidence_refs": ["ev_1"],
                    }
                ],
            },
        )
        return profile

    def test_generate_claim_candidates_is_non_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            before = (profile / "evidence-pool.yaml").read_text(encoding="utf-8")

            candidates = generate_claim_candidates(profile, ["ev_1"])

            after = (profile / "evidence-pool.yaml").read_text(encoding="utf-8")
            self.assertEqual(after, before)
            self.assertEqual(len(candidates), 1)
            self.assertEqual(candidates[0]["evidence_refs"], ["ev_1"])
            self.assertEqual(candidates[0]["skill_refs"], ["ros2_basics"])

    def test_apply_claim_candidates_dedupes_and_indexes_usage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            pool = yaml.safe_load(
                (profile / "evidence-pool.yaml").read_text(encoding="utf-8")
            )
            candidates = generate_claim_candidates(profile, ["ev_1"])

            merged, applied, warnings = apply_claim_candidates(
                pool,
                candidates,
                known_skill_ids={"ros2_basics"},
            )
            merged2, applied2, warnings2 = apply_claim_candidates(
                merged,
                candidates,
                known_skill_ids={"ros2_basics"},
            )

            self.assertEqual(warnings, [])
            self.assertEqual(warnings2, [])
            self.assertEqual(len(applied), 1)
            self.assertEqual(len(applied2), 1)
            self.assertEqual(len(accepted_claims(merged2)), 1)
            usage = claim_usage_index(merged2)
            self.assertEqual(
                usage["by_evidence"]["ev_1"][0]["id"],
                accepted_claims(merged2)[0]["id"],
            )

    def test_profile_claim_book_falls_back_to_legacy_and_migrates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            pool_path = profile / "evidence-pool.yaml"
            pool = yaml.safe_load(pool_path.read_text(encoding="utf-8"))
            pool["claims"] = [
                {
                    "id": "claim:legacy",
                    "status": "accepted",
                    "text": "Legacy claim.",
                    "evidence_refs": ["ev_1"],
                }
            ]
            _write_yaml(pool_path, pool)

            fallback = load_claim_book(profile)
            self.assertEqual(fallback["claims"][0]["id"], "claim:legacy")

            moved = migrate_legacy_claims(profile)
            after_pool = yaml.safe_load(pool_path.read_text(encoding="utf-8"))
            after_book = yaml.safe_load(
                (profile / "claims.yaml").read_text(encoding="utf-8")
            )
            self.assertEqual(moved, 1)
            self.assertNotIn("claims", after_pool)
            self.assertEqual(after_book["claims"][0]["id"], "claim:legacy")

    def test_apply_claim_candidates_to_book_writes_claims_yaml_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            candidates = generate_claim_candidates(profile, ["ev_1"])

            _, applied, warnings = apply_claim_candidates_to_book(
                profile,
                candidates,
                known_skill_ids={"ros2_basics"},
            )

            pool = yaml.safe_load(
                (profile / "evidence-pool.yaml").read_text(encoding="utf-8")
            )
            book = yaml.safe_load(
                (profile / "claims.yaml").read_text(encoding="utf-8")
            )
            self.assertEqual(warnings, [])
            self.assertEqual(len(applied), 1)
            self.assertNotIn("claims", pool)
            self.assertEqual(book["claims"][0]["evidence_refs"], ["ev_1"])
            self.assertTrue(book["claims"][0]["supporting_evidence_signature"])
            self.assertEqual(
                list(accepted_claim_index_for_profile(profile)),
                [book["claims"][0]["id"]],
            )

    def test_claim_scope_derives_project_and_goal_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            _write_yaml(
                profile / "goals.yaml",
                {
                    "schema_version": "1.0",
                    "profile": "alice",
                    "current_goal_id": "goal:ship",
                    "goals": [
                        {
                            "id": "goal:ship",
                            "title": "Ship the system",
                            "status": "active",
                            "evidence_refs": ["ev_1"],
                        }
                    ],
                },
            )
            _write_yaml(
                profile / "project-board.yaml",
                {
                    "schema_version": "1.0",
                    "profile": "alice",
                    "project_cases": [
                        {
                            "id": "project:nblane",
                            "title": "nblane",
                            "status": "active",
                            "goal_refs": ["goal:ship"],
                            "evidence_refs": ["ev_1"],
                        }
                    ],
                },
            )

            with patch("nblane.core.claims.llm.is_configured", return_value=False):
                candidates = generate_claim_candidates_for_scope(
                    profile,
                    "project",
                    scope_id="project:nblane",
                )

            self.assertEqual(len(candidates), 1)
            self.assertEqual(candidates[0]["project_refs"], ["project:nblane"])
            self.assertEqual(candidates[0]["goal_refs"], ["goal:ship"])
            self.assertEqual(candidates[0]["evidence_refs"], ["ev_1"])

    def test_supporting_evidence_signature_marks_refresh_needed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            signature = supporting_evidence_signature(profile, ["ev_1"])
            _write_yaml(
                profile / "claims.yaml",
                {
                    "schema_version": "1.0",
                    "profile": "alice",
                    "claims": [
                        {
                            "id": "claim:stale",
                            "status": "accepted",
                            "text": "Known claim.",
                            "evidence_refs": ["ev_1"],
                            "supporting_evidence_signature": signature,
                        }
                    ],
                },
            )
            pool_path = profile / "evidence-pool.yaml"
            pool = yaml.safe_load(pool_path.read_text(encoding="utf-8"))
            pool["evidence_entries"][0]["summary"] = "Changed summary."
            _write_yaml(pool_path, pool)

            claim = claim_index_for_profile(profile)["claim:stale"]

            self.assertEqual(claim["refresh_status"], "needs_refresh")
            self.assertIn("Supporting evidence changed", claim["stale_reason"])

    def test_apply_skips_unknown_evidence_and_drops_unknown_skill(self) -> None:
        pool = {"profile": "t", "evidence_entries": [{"id": "ev_1", "title": "A"}]}

        merged, applied, warnings = apply_claim_candidates(
            pool,
            [
                {
                    "text": "Unknown evidence claim.",
                    "evidence_refs": ["missing"],
                },
                {
                    "text": "Known evidence claim.",
                    "evidence_refs": ["ev_1"],
                    "skill_refs": ["missing_skill"],
                },
            ],
            known_skill_ids={"ros2_basics"},
        )

        self.assertEqual(len(applied), 1)
        self.assertEqual(accepted_claims(merged)[0]["skill_refs"], [])
        self.assertTrue(any("unknown evidence" in item for item in warnings))
        self.assertTrue(any("unknown skill ref" in item for item in warnings))

    def test_apply_drops_skill_refs_when_known_skill_set_is_empty(self) -> None:
        pool = {"profile": "t", "evidence_entries": [{"id": "ev_1", "title": "A"}]}

        merged, applied, warnings = apply_claim_candidates(
            pool,
            [
                {
                    "text": "Known evidence claim.",
                    "evidence_refs": ["ev_1"],
                    "skill_refs": ["missing_skill"],
                },
            ],
            known_skill_ids=set(),
        )

        self.assertEqual(len(applied), 1)
        self.assertEqual(accepted_claims(merged)[0]["skill_refs"], [])
        self.assertTrue(any("unknown skill ref" in item for item in warnings))

    def test_accepted_claims_excludes_non_accepted_raw_status(self) -> None:
        pool = {
            "profile": "t",
            "evidence_entries": [{"id": "ev_1", "title": "A"}],
            "claims": [
                {
                    "id": "claim:ok",
                    "status": "accepted",
                    "text": "Accepted claim.",
                    "evidence_refs": ["ev_1"],
                },
                {
                    "id": "claim:rejected",
                    "status": "rejected",
                    "text": "Rejected claim.",
                    "evidence_refs": ["ev_1"],
                },
            ],
        }

        self.assertEqual(
            [claim["id"] for claim in accepted_claims(pool)],
            ["claim:ok"],
        )
        self.assertEqual(claim_index(pool)["claim:rejected"]["status"], "rejected")

    def test_cli_pool_remove_preserves_top_level_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._profile(root)
            pool = yaml.safe_load(
                (profile / "evidence-pool.yaml").read_text(encoding="utf-8")
            )
            pool["evidence_entries"].append(
                {"id": "ev_remove", "type": "project", "title": "Remove me"}
            )
            pool["claims"] = [
                {
                    "id": "claim:keep",
                    "status": "accepted",
                    "text": "Keep this claim.",
                    "evidence_refs": ["ev_1"],
                    "skill_refs": ["ros2_basics"],
                }
            ]
            _write_yaml(profile / "evidence-pool.yaml", pool)
            (profile / "SKILL.md").write_text("Skill context", encoding="utf-8")

            with (
                patch("nblane.commands.common.safe_profile_dir", lambda _n: profile),
                patch("nblane.core.profile_io.PROFILES_DIR", root),
                patch("nblane.core.io.profile_dir", lambda _n: profile),
                patch("nblane.core.ingest_apply.profile_dir", lambda _n: profile),
                patch("nblane.core.sync.write_generated_blocks", lambda _p: None),
            ):
                cmd_evidence_pool_remove("alice", ["ev_remove"])

            after = yaml.safe_load(
                (profile / "evidence-pool.yaml").read_text(encoding="utf-8")
            )
            self.assertEqual(after["claims"][0]["id"], "claim:keep")
            self.assertNotIn(
                "ev_remove",
                [item.get("id") for item in after.get("evidence_entries", [])],
            )


if __name__ == "__main__":
    unittest.main()
