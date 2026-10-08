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

    def test_lookup_falls_back_to_base_form(self) -> None:
        # Inflected words missing from the dictionary resolve to their
        # headword, which is named in the gloss.
        gloss = local_dict.lookup("capabilities")
        self.assertTrue(gloss)
        self.assertTrue(gloss.startswith("(capability) "))
        self.assertTrue(local_dict.lookup("embodied").startswith("(embody) "))
        self.assertTrue(local_dict.lookup("trajectories").startswith("(trajectory) "))
        # A direct hit is returned as is, without a headword prefix.
        self.assertFalse(local_dict.lookup("model").startswith("("))

    def test_headword_candidates(self) -> None:
        self.assertEqual(local_dict.headword_candidates("Policies")[:2], ["policies", "policy"])
        self.assertEqual(local_dict.headword_candidates(""), [])

    def test_lookup_includes_phonetics(self) -> None:
        gloss = local_dict.lookup("model")
        self.assertTrue(gloss)
        # Phonetics are prefixed in square brackets ahead of the translation.
        self.assertTrue(gloss.startswith("["))
        self.assertIn("]", gloss)


if __name__ == "__main__":
    unittest.main()
