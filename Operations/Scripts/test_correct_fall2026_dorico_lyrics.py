#!/usr/bin/env python3

from __future__ import annotations

import tempfile
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

import correct_fall2026_dorico_lyrics as cleaner


class Fall2026DoricoLyricCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary_directory = tempfile.TemporaryDirectory()
        base = Path(cls.temporary_directory.name)
        cls.output = base / "corrected.musicxml"
        cls.report_path = base / "report.json"
        cls.report = cleaner.transform(
            cleaner.DEFAULT_SOURCE, cls.output, cls.report_path
        )
        cls.root = ET.parse(cls.output).getroot()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary_directory.cleanup()

    def refs(self, **selector: str) -> list[cleaner.LyricRef]:
        return cleaner.select_lyrics(self.root, **selector)

    def test_structural_and_anchor_validation(self) -> None:
        validation = self.report["validation"]
        self.assertTrue(validation["passed"])
        self.assertTrue(validation["lyric_anchor_locations_match"])
        self.assertTrue(validation["musical_semantics_match"])
        self.assertEqual(
            validation["output_shape"]["lyric_anchor_count"],
            cleaner.EXPECTED_LYRIC_ANCHORS,
        )

    def test_every_lyric_is_routed_by_voice(self) -> None:
        for ref in cleaner.iter_lyric_refs(self.root):
            expected = "above" if ref.voice == "1" else "below"
            self.assertEqual(ref.lyric.get("placement"), expected, ref.location())
        self.assertGreater(
            self.report["lyric_routing"]["extra_lower_lane_anchors"], 0
        )

    def test_definite_word_repairs(self) -> None:
        for part in ("P1", "P2", "P3"):
            self.assertEqual(
                len(self.refs(part=part, measure="18", text="love")), 1
            )
            self.assertEqual(len(self.refs(part=part, measure="19", text="ove")), 0)
        for part, measure in (
            ("P3", "51"),
            ("P4", "50"),
            ("P5", "50"),
            ("P6", "50"),
        ):
            self.assertEqual(len(self.refs(part=part, measure=measure, text="ced")), 1)
            self.assertEqual(len(self.refs(part=part, measure=measure, text="ceed")), 0)
        self.assertEqual(len(self.refs(part="P6", measure="103", text="(Yours")), 1)
        self.assertEqual(len(self.refs(part="P6", measure="103", text="too.)")), 1)

    def test_literal_aleatoric_wording_and_review_items_are_preserved(self) -> None:
        self.assertEqual(len(self.report["ambiguity_flags"]), 5)
        self.assertTrue(
            all(
                item["preserved"] == cleaner.LITERAL_ALEATORIC_DIRECTION
                for item in self.report["ambiguity_flags"]
            )
        )
        self.assertEqual(
            len(self.refs(part="P1", measure="20", text="though")), 1
        )


if __name__ == "__main__":
    unittest.main()
