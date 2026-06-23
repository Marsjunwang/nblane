"""Source/static checks for the React Kanban read-mode provenance."""

from __future__ import annotations

import unittest
from pathlib import Path

_FRONTEND = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "nblane"
    / "kanban_board_component"
    / "frontend"
)
_SRC = _FRONTEND / "src" / "index.html"
_STATIC = _FRONTEND / "static" / "index.html"


class TestKanbanComponentReadMode(unittest.TestCase):
    """The default React board must show project/milestone in read mode."""

    def test_source_renders_project_provenance(self) -> None:
        text = _SRC.read_text(encoding="utf-8")
        # Read-mode provenance helper exists and is invoked in the card body.
        self.assertIn("projectProvenanceHtml", text)
        self.assertIn("project_label_maps", text)
        self.assertIn("projectLabelFor", text)
        self.assertIn("milestoneLabelFor", text)

    def test_static_build_matches_source(self) -> None:
        # `npm run build` copies src -> static; they must stay identical so the
        # deployed component reflects the source change.
        self.assertEqual(
            _SRC.read_text(encoding="utf-8"),
            _STATIC.read_text(encoding="utf-8"),
            msg="static/index.html is stale; run `npm run build`",
        )


if __name__ == "__main__":
    unittest.main()
