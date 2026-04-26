"""Tests for public evidence curation helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core import public_curation
from nblane.core.public_site import PublicSiteError


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(
            data,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _make_profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    profile.mkdir(parents=True)
    _write_yaml(
        profile / "evidence-pool.yaml",
        {
            "profile": name,
            "evidence_entries": [
                {
                    "id": "ev_one",
                    "type": "project",
                    "title": "Piper robot reproduction",
                    "summary": "Verified robot reproduction trace.",
                },
                {
                    "id": "ev_two",
                    "type": "practice",
                    "title": "Piper demo repair",
                    "summary": "Verified demo repair trace.",
                },
                {
                    "id": "ev_paper",
                    "type": "paper",
                    "title": "Pose Paper",
                    "date": "2026",
                    "summary": "Peer-reviewed pose estimation fact.",
                },
                {
                    "id": "ev_patent",
                    "type": "practice",
                    "title": "Shoe Placement Patent",
                    "date": "2025",
                    "summary": "Patent evidence for shoe placement.",
                },
            ],
        },
    )
    _write_yaml(
        profile / "skill-tree.yaml",
        {
            "profile": name,
            "nodes": [
                {
                    "id": "real_robot_ops",
                    "status": "solid",
                    "evidence_refs": ["ev_one", "ev_two"],
                },
                {
                    "id": "pose_estimation",
                    "status": "expert",
                    "evidence_refs": ["ev_paper", "ev_patent"],
                },
            ],
        },
    )
    _write_yaml(profile / "projects.yaml", {"projects": []})
    _write_yaml(profile / "outputs.yaml", {"outputs": []})
    return profile


class TestPublicCuration(unittest.TestCase):
    """Evidence-to-public-layer curation behavior."""

    def test_group_project_writes_draft_without_changing_evidence(self) -> None:
        """Multiple evidence refs become one draft project."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            evidence_before = (profile / "evidence-pool.yaml").read_text(
                encoding="utf-8"
            )

            with patch(
                "nblane.core.public_curation.profile_dir",
                lambda _n: profile,
            ):
                result = public_curation.group_project(
                    "alice",
                    project_id="piper-home-robot",
                    title="Piper / Home Robot Project",
                    evidence_ids=["ev_one", "ev_two", "ev_two"],
                    tags=["robotics"],
                )

            self.assertEqual(result.warnings, [])
            self.assertEqual(result.project["status"], "draft")
            self.assertEqual(
                result.project["evidence_refs"],
                ["ev_one", "ev_two"],
            )
            self.assertIn("real_robot_ops", result.project["skill_refs"])
            self.assertEqual(
                (profile / "evidence-pool.yaml").read_text(encoding="utf-8"),
                evidence_before,
            )

    def test_group_project_rejects_duplicate_id_and_missing_refs(self) -> None:
        """Project ids and evidence refs must be valid."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            with patch(
                "nblane.core.public_curation.profile_dir",
                lambda _n: profile,
            ):
                public_curation.group_project(
                    "alice",
                    project_id="demo",
                    title="Demo",
                    evidence_ids=["ev_one"],
                )
                with self.assertRaises(PublicSiteError):
                    public_curation.group_project(
                        "alice",
                        project_id="demo",
                        title="Demo again",
                        evidence_ids=["ev_two"],
                    )
                with self.assertRaises(PublicSiteError):
                    public_curation.group_project(
                        "alice",
                        project_id="missing",
                        title="Missing",
                        evidence_ids=["does_not_exist"],
                    )

    def test_group_project_warns_and_skips_already_used_evidence(self) -> None:
        """Evidence already used by another project is not duplicated."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            with patch(
                "nblane.core.public_curation.profile_dir",
                lambda _n: profile,
            ):
                public_curation.group_project(
                    "alice",
                    project_id="first",
                    title="First",
                    evidence_ids=["ev_one"],
                )
                result = public_curation.group_project(
                    "alice",
                    project_id="second",
                    title="Second",
                    evidence_ids=["ev_one", "ev_two"],
                )

            self.assertTrue(result.warnings)
            self.assertEqual(result.project["evidence_refs"], ["ev_two"])

    def test_hydrate_creates_output_drafts_only_when_requested(self) -> None:
        """Paper and patent evidence can become one-to-one output drafts."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            output_path = profile / "outputs.yaml"
            before = output_path.read_text(encoding="utf-8")

            with patch(
                "nblane.core.public_curation.profile_dir",
                lambda _n: profile,
            ):
                preview = public_curation.hydrate_public_drafts("alice")
                self.assertFalse(preview.written)
                self.assertEqual(
                    output_path.read_text(encoding="utf-8"),
                    before,
                )
                written = public_curation.hydrate_public_drafts(
                    "alice",
                    write_drafts=True,
                )

            self.assertTrue(written.written)
            self.assertEqual(len(written.outputs), 2)
            data = yaml.safe_load(output_path.read_text(encoding="utf-8"))
            types = {item["type"] for item in data["outputs"]}
            self.assertEqual(types, {"paper", "patent"})
            self.assertFalse(
                (profile / "projects.yaml")
                .read_text(encoding="utf-8")
                .count("ev_paper")
            )


if __name__ == "__main__":
    unittest.main()
