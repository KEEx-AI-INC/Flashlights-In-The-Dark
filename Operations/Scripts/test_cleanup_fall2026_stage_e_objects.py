#!/usr/bin/env python3

from __future__ import annotations

import tempfile
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

import cleanup_fall2026_stage_e_objects as cleanup


class Fall2026StageEObjectCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary_directory = tempfile.TemporaryDirectory()
        base = Path(cls.temporary_directory.name)
        cls.output = base / "stage-e.musicxml"
        cls.report_path = base / "report.json"
        cls.report = cleanup.transform(
            cleanup.DEFAULT_SOURCE,
            cls.output,
            cls.report_path,
            verify_chain=True,
        )
        cls.root = ET.parse(cls.output).getroot()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary_directory.cleanup()

    def test_full_semantic_validation_passes(self) -> None:
        validation = self.report["validation"]
        self.assertTrue(validation["passed"])
        self.assertEqual(validation["part_ids"], ["P1", "P2", "P3", "P4", "P5", "P6"])
        self.assertEqual(set(validation["measure_counts"].values()), {151})
        self.assertEqual(validation["note_count"], 2787)
        self.assertEqual(validation["lyric_anchor_count"], 1376)
        self.assertEqual(validation["fall_replacement_count"], 388)
        self.assertEqual(
            validation["structure_fingerprint"],
            cleanup.EXPECTED_STRUCTURE_FINGERPRINT,
        )
        for key in (
            "notes_exact",
            "lyrics_text_attributes_and_placement_exact",
            "dynamics_exact",
            "harmonies_exact",
            "direction_changes_exactly_logged",
            "semantic_metadata_exact",
            "five_line_overrides_exact",
            "casting_breaks_exact",
            "fall_replacements_preserved",
        ):
            self.assertTrue(validation[key], key)

    def test_aleatoric_direction_is_once_above_top_staff(self) -> None:
        cleanup.assert_aleatoric_result(self.root)
        section = self.report["ensemble_direction_cleanup"]
        self.assertEqual(section["removed_duplicate_count"], 3)
        self.assertEqual(
            {
                (item["part"], item["measure"])
                for item in section["removed_duplicates"]
            },
            {("P2", 115), ("P2", 130), ("P3", 130)},
        )
        self.assertEqual(section["exact_wording_preserved"], cleanup.ALEATORIC_TEXT)
        for measure in (115, 130):
            matches = cleanup.find_word_directions(
                self.root, "P1", measure, cleanup.ALEATORIC_TEXT
            )
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0][1].get("placement"), "above")

    def test_only_redundant_title_template_credits_are_removed(self) -> None:
        section = self.report["page1_credit_cleanup"]
        self.assertEqual(section["removed_redundant_count"], 3)
        self.assertEqual(
            {item["role"] for item in section["removed_redundant"]},
            {"title", "composer", "copyright"},
        )
        remaining = {
            cleanup.credit_text(credit)
            for credit in self.root.findall("credit")
            if credit.get("page") == "1"
        }
        self.assertEqual(remaining, set(cleanup.APPROVED_UNIQUE_CREDITS))
        self.assertEqual(self.root.findtext("./work/work-title"), "Flashlights in the Dark")
        self.assertEqual(self.root.findtext("movement-title"), "Flashlights in the Dark")
        self.assertEqual(
            self.root.findtext("./identification/creator[@type='composer']"),
            "Jon D. Nelson",
        )
        self.assertEqual(self.root.findtext("./identification/rights"), "© 2025")

    def test_dense_harmony_is_exact_and_flagged_for_dorico(self) -> None:
        audit = self.report["harmony_spacing_audit"]
        self.assertEqual(audit["measure_range"], [93, 97])
        self.assertEqual(audit["harmony_count"], 9)
        self.assertEqual(audit["musicxml_changes"], [])
        self.assertEqual(audit["action"], "dorico_only")
        self.assertEqual(audit["unsafe_local_position_attributes"], [])

    def test_other_cross_part_directions_are_conservatively_preserved(self) -> None:
        clusters = self.report["ensemble_direction_cleanup"][
            "other_exact_cross_part_clusters"
        ]
        keys = {
            (item["measure"], tuple(text.strip() for text in item["texts"]))
            for item in clusters
        }
        self.assertIn((112, ("subito",)), keys)
        self.assertIn((7, ("listen for primer tone",)), keys)
        self.assertTrue(all(item["action"] == "preserved" for item in clusters))

    def test_output_is_deterministic(self) -> None:
        base = Path(self.temporary_directory.name)
        second_output = base / "stage-e-second.musicxml"
        second_report = base / "report-second.json"
        cleanup.transform(
            cleanup.DEFAULT_SOURCE,
            second_output,
            second_report,
            verify_chain=True,
        )
        self.assertEqual(self.output.read_bytes(), second_output.read_bytes())


if __name__ == "__main__":
    unittest.main()
