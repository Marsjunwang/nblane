"""Tests for structured tag taxonomy helpers."""

from __future__ import annotations

import unittest

from nblane.core.tag_taxonomy import (
    TagFacets,
    merge_tag_facets,
    parse_tag_facets,
    tag_namespace,
    tag_value,
)


class TestTagTaxonomy(unittest.TestCase):
    """Namespaced workflow tags round-trip through structured facets."""

    def test_parse_tag_facets_groups_known_namespaces(self) -> None:
        """Known tag prefixes become structured fields, preserving leftovers."""
        facets = parse_tag_facets(
            [
                "flow/learning",
                "company/openai",
                "person/sam",
                "project/nblane",
                "habit/reading",
                "topic/agents",
                "company/openai",
            ]
        )

        self.assertEqual(
            facets,
            TagFacets(
                flow="learning",
                companies=["openai"],
                people=["sam"],
                projects=["nblane"],
                habits=["reading"],
                other=["topic/agents"],
            ),
        )

    def test_merge_tag_facets_serializes_back_to_plain_tags(self) -> None:
        """Structured fields produce one de-duplicated tag list."""
        tags = merge_tag_facets(
            flow="inbox",
            companies=["openai", " openai "],
            people="sam, greg",
            projects=["nblane"],
            habits=["workout"],
            other=["topic/agents", "topic/agents"],
        )

        self.assertEqual(
            tags,
            [
                "flow/inbox",
                "company/openai",
                "person/sam",
                "person/greg",
                "project/nblane",
                "habit/workout",
                "topic/agents",
            ],
        )

    def test_tag_namespace_and_value_handle_plain_tags(self) -> None:
        """Plain tags keep an empty namespace and return themselves as value."""
        self.assertEqual(tag_namespace("topic/agents"), "topic")
        self.assertEqual(tag_value("topic/agents"), "agents")
        self.assertEqual(tag_namespace("deep-work"), "")
        self.assertEqual(tag_value("deep-work"), "deep-work")


if __name__ == "__main__":
    unittest.main()
