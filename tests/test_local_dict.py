"""Tests for the offline word-level dictionary."""

from __future__ import annotations

import unittest

from nblane.core import local_dict


class TestLocalDict(unittest.TestCase):
    def test_dictionary_data_present(self) -> None:
        self.assertTrue(local_dict.available())

    def test_lookup_common_word_case_insensitive(self) -> None:
        lower = local_dict.lookup("model")
        upper = local_dict.lookup("Model")
        self.assertTrue(lower)
        self.assertEqual(lower, upper)

    def test_lookup_rejects_phrases_and_punctuation(self) -> None:
        self.assertIsNone(local_dict.lookup("neural network"))
        self.assertIsNone(local_dict.lookup("model,"))
        self.assertIsNone(local_dict.lookup(""))

    def test_is_lookupable(self) -> None:
        self.assertTrue(local_dict.is_lookupable("gradient"))
        self.assertFalse(local_dict.is_lookupable("the cat sat"))
        self.assertFalse(local_dict.is_lookupable("a" * 40))

    def test_lookup_includes_phonetics(self) -> None:
        gloss = local_dict.lookup("model")
        self.assertTrue(gloss)
        # Phonetics are prefixed in square brackets ahead of the translation.
        self.assertTrue(gloss.startswith("["))
        self.assertIn("]", gloss)


if __name__ == "__main__":
    unittest.main()
