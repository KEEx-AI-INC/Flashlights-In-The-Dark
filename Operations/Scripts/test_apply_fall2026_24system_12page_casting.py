#!/usr/bin/env python3

from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

import apply_fall2026_24system_12page_casting as casting


class Fall202624System12PageCastingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary_directory = tempfile.TemporaryDirectory()
        base = Path(cls.temporary_directory.name)
        cls.output = base / "cast.musicxml"
        cls.report_path = base / "cast-report.json"
        cls.validation_path = base / "semantic-validation.json"
        cls.report = casting.build(
            casting.DEFAULT_SOURCE,
            cls.output,
            cls.report_path,
            cls.validation_path,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary_directory.cleanup()

    def test_exact_two_system_page_profile(self) -> None:
        casting.validate_profile()
        profile = self.report["casting"]
        self.assertEqual(profile["music_pages"], 12)
        self.assertEqual(profile["systems"], 24)
        self.assertEqual(profile["systems_per_page"], 2)
        self.assertTrue(profile["every_page_has_exactly_two_systems"])
        self.assertEqual(profile["blank_pages"], [])
        self.assertEqual(profile["page_1_systems"], ["1-3", "4-6"])

    def test_exact_break_starts(self) -> None:
        profile = self.report["casting"]
        self.assertEqual(
            profile["page_break_starts"],
            [7, 14, 23, 37, 46, 58, 71, 93, 104, 115, 130],
        )
        self.assertEqual(
            profile["system_break_starts"],
            [4, 11, 17, 29, 41, 53, 66, 81, 99, 110, 122, 140],
        )
        self.assertTrue(profile["identical_across_parts"])

    def test_semantics_and_layout_only_equivalence(self) -> None:
        self.assertTrue(self.report["semantic_validation_passed"])
        self.assertTrue(self.report["layout_only_equivalence"]["passed"])
        score = self.report["score_validation"]
        self.assertEqual(score["part_ids"], ["P1", "P2", "P3", "P4", "P5", "P6"])
        self.assertEqual(set(score["measure_counts"].values()), {151})
        self.assertEqual(score["note_count"], 2787)
        self.assertEqual(score["lyric_anchors"], 1376)
        self.assertEqual(
            score["structure_fingerprint"],
            casting.base.EXPECTED_STRUCTURE_FINGERPRINT,
        )

    def test_output_is_deterministic(self) -> None:
        base = Path(self.temporary_directory.name)
        second = base / "cast-second.musicxml"
        casting.build(
            casting.DEFAULT_SOURCE,
            second,
            base / "cast-report-second.json",
            base / "semantic-validation-second.json",
        )
        self.assertEqual(self.output.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
