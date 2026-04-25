"""Tests for Streamlit cache wrappers."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from nblane import web_cache


class TestWebCache(unittest.TestCase):
    """Web cache falls back cleanly outside Streamlit runtime."""

    def test_load_skill_tree_raw_falls_back_without_runtime(self) -> None:
        """CLI/test imports can use wrappers without an active Streamlit app."""
        expected = {"profile": "u1", "nodes": []}
        with (
            patch(
                "nblane.web_cache._streamlit_runtime_exists",
                return_value=False,
            ),
            patch(
                "nblane.web_cache.io.load_skill_tree_raw",
                return_value=expected,
            ) as load_raw,
        ):
            got = web_cache.load_skill_tree_raw("u1")

        self.assertEqual(got, expected)
        load_raw.assert_called_once_with("u1")

    def test_clear_web_cache_noops_without_runtime(self) -> None:
        """Cache clearing is safe from non-Streamlit contexts."""
        with (
            patch(
                "nblane.web_cache._streamlit_runtime_exists",
                return_value=False,
            ),
            patch("nblane.web_cache.st.cache_data.clear") as clear,
        ):
            web_cache.clear_web_cache()

        clear.assert_not_called()


if __name__ == "__main__":
    unittest.main()
