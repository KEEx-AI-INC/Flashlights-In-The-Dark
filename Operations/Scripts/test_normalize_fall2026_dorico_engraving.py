#!/usr/bin/env python3

from __future__ import annotations

import tempfile
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

import normalize_fall2026_dorico_engraving as normalizer


class Fall2026DoricoEngravingNormalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary_directory = tempfile.TemporaryDirectory()
        base = Path(cls.temporary_directory.name)
        cls.output = base / "normalized.musicxml"
        cls.report_path = base / "report.json"
        cls.report = normalizer.transform(
            normalizer.DEFAULT_SOURCE,
            cls.output,
            cls.report_path,
            verify_chain=True,
        )
        cls.root = ET.parse(cls.output).getroot()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary_directory.cleanup()

    def test_canonical_semantics_and_casting_are_preserved(self) -> None:
        validation = self.report["validation"]
        self.assertTrue(validation["passed"])
        self.assertEqual(validation["note_count"], normalizer.EXPECTED_NOTE_COUNT)
        self.assertEqual(
            validation["lyric_anchor_count"], normalizer.EXPECTED_LYRIC_ANCHORS
        )
        self.assertTrue(validation["fall_replacements_preserved"])
        self.assertTrue(validation["canonical_structure_matches"])
        self.assertTrue(validation["lyric_semantics_match"])
        self.assertTrue(validation["five_line_overrides_match"])
        self.assertTrue(validation["casting_breaks_match"])

    def test_routing_uses_actual_multi_voice_topology(self) -> None:
        self.assertEqual(
            set(self.report["lyric_routing"]["multi_voice_parts"]),
            normalizer.EXPECTED_MULTI_VOICE_PARTS,
        )
        for ref in normalizer.iter_lyric_refs(self.root):
            expected = (
                "above"
                if ref.part in normalizer.EXPECTED_MULTI_VOICE_PARTS
                and ref.voice == "1"
                else "below"
            )
            self.assertEqual(ref.lyric.get("placement"), expected, ref.location())
        self.assertEqual(
            self.report["lyric_routing"]["third_lane_anchor_count"], 17
        )

    def test_safe_scope_removal_is_narrow(self) -> None:
        root = ET.parse(normalizer.DEFAULT_SOURCE).getroot()
        fixtures = [
            root.find(".//lyric"),
            root.find(".//direction/direction-type/words"),
            root.find(".//harmony/root/root-step"),
            root.find(".//direction/direction-type/dynamics/*"),
            root.find(".//notations/slur"),
        ]
        self.assertTrue(all(element is not None for element in fixtures))
        for index, element in enumerate(fixtures, start=1):
            assert element is not None
            element.set("relative-x", str(index))
        credit = root.find("credit/credit-words")
        assert credit is not None
        credit_before = credit.get("default-x")

        changes = normalizer.remove_safe_positioning(root)
        self.assertEqual(len(changes), len(fixtures))
        self.assertTrue(
            all(
                "relative-x" not in element.attrib
                for element in fixtures
                if element is not None
            )
        )
        self.assertEqual(credit.get("default-x"), credit_before)

    def test_actual_source_has_no_remaining_unsafe_offsets(self) -> None:
        self.assertEqual(self.report["position_attribute_change_count"], 0)
        self.assertEqual(self.report["ambiguity_flags"], [])
        self.assertEqual(len(self.report["preserved_positioning"]), 10)


if __name__ == "__main__":
    unittest.main()
