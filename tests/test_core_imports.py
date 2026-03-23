"""Verify all nblane.core modules are importable."""

from __future__ import annotations

import unittest


class TestCoreImports(unittest.TestCase):
    """Every core module should import without error."""

    def test_import_paths(self) -> None:
        """nblane.core.paths should expose REPO_ROOT."""
        from nblane.core.paths import REPO_ROOT

        self.assertTrue(REPO_ROOT.exists())

    def test_import_models(self) -> None:
        """nblane.core.models should define all data classes."""
        from nblane.core.models import (
            GapResult,
            KanbanTask,
            Schema,
            SchemaNode,
            SkillNode,
            SkillTree,
        )

        node = SkillNode(id="test", status="locked")
        self.assertEqual(node.status, "locked")

    def test_import_io(self) -> None:
        """nblane.core.io should expose list functions."""
        from nblane.core.io import (
            list_profiles,
            list_schemas,
            list_teams,
        )

        self.assertIsInstance(list_profiles(), list)
        self.assertIsInstance(list_schemas(), list)
        self.assertIsInstance(list_teams(), list)

    def test_import_gap(self) -> None:
        """nblane.core.gap should expose analyze."""
        from nblane.core.gap import analyze

        self.assertTrue(callable(analyze))

    def test_import_context(self) -> None:
        """nblane.core.context should expose generate."""
        from nblane.core.context import generate

        self.assertTrue(callable(generate))

    def test_import_validate(self) -> None:
        """nblane.core.validate should expose validators."""
        from nblane.core.validate import (
            run_all_profiles,
            validate_one,
        )

        self.assertTrue(callable(validate_one))
        self.assertTrue(callable(run_all_profiles))

    def test_import_sync(self) -> None:
        """nblane.core.sync should expose sync functions."""
        from nblane.core.sync import (
            get_drifted_blocks,
            write_generated_blocks,
        )

        self.assertTrue(callable(get_drifted_blocks))
        self.assertTrue(callable(write_generated_blocks))

    def test_import_status(self) -> None:
        """nblane.core.status should expose summary."""
        from nblane.core.status import summarize_all

        self.assertTrue(callable(summarize_all))

    def test_import_team(self) -> None:
        """nblane.core.team should expose summarize_team."""
        from nblane.core.team import summarize_team

        self.assertTrue(callable(summarize_team))

    def test_import_llm(self) -> None:
        """nblane.core.llm should expose is_configured."""
        from nblane.core.llm import is_configured

        self.assertIsInstance(is_configured(), bool)

    def test_import_profile_ingest(self) -> None:
        """nblane.core.profile_ingest should expose merge."""
        from nblane.core.profile_ingest import merge_ingest_patch

        self.assertTrue(callable(merge_ingest_patch))


if __name__ == "__main__":
    unittest.main()
