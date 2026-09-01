#!/usr/bin/env python3

from __future__ import annotations

from copy import deepcopy
import tempfile
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

import neutralize_fall2026_musicxml_positioning as neutralizer


class Fall2026PositionNeutralizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary_directory = tempfile.TemporaryDirectory()
        base = Path(cls.temporary_directory.name)
        cls.output = base / "position-neutral.musicxml"
        cls.report_path = base / "report.json"
        cls.report = neutralizer.transform(
            neutralizer.DEFAULT_SOURCE,
            cls.output,
            cls.report_path,
            verify_chain=True,
        )
        cls.root = ET.parse(cls.output).getroot()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary_directory.cleanup()

    def test_full_semantic_baseline_and_casting_are_preserved(self) -> None:
        validation = self.report["validation"]
        self.assertTrue(validation["passed"])
        self.assertEqual(validation["part_ids"], ["P1", "P2", "P3", "P4", "P5", "P6"])
        self.assertTrue(all(count == 151 for count in validation["measure_counts"].values()))
        self.assertEqual(validation["note_count"], 2787)
        self.assertEqual(validation["lyric_anchor_count"], 1376)
        self.assertEqual(validation["fall_replacement_count"], 388)
        self.assertEqual(validation["structure_fingerprint"], neutralizer.EXPECTED_FINGERPRINT)
        self.assertTrue(validation["break_metadata_matches"])
        self.assertTrue(validation["page_layout_matches"])
        self.assertTrue(validation["lyric_semantics_match"])
        self.assertTrue(validation["semantic_offsets_match"])
        self.assertTrue(validation["all_encoded_staves_five_line"])

    def test_all_position_and_print_spacing_overrides_are_neutralized(self) -> None:
        neutralization = self.report["neutralization"]
        self.assertEqual(
            neutralization["source_position_attribute_counts"],
            {"default-x": 2, "default-y": 2, "relative-x": 0, "relative-y": 0},
        )
        self.assertEqual(neutralization["position_attribute_removal_count"], 4)
        self.assertTrue(
            all(
                attribute not in element.attrib
                for element in self.root.iter()
                for attribute in neutralizer.POSITION_ATTRIBUTES
            )
        )
        self.assertEqual(neutralization["visual_only_offset_removal_count"], 0)
        self.assertEqual(neutralization["local_print_spacing_removal_count"], 0)
        self.assertEqual(self.report["validation"]["remaining_local_print_spacing"], [])
        self.assertEqual(self.report["validation"]["remaining_visual_only_offsets"], [])

    def test_legacy_text_typography_is_neutralized_for_global_dorico_styles(self) -> None:
        neutralization = self.report["neutralization"]
        self.assertEqual(
            neutralization["source_typography_attribute_counts"],
            {
                "credit-words": {"font-family": 2, "font-size": 2},
                "dynamics": {"font-style": 6},
                "metronome": {"font-weight": 1},
                "rehearsal": {"font-weight": 16},
                "words": {"font-style": 24, "font-weight": 2},
            },
        )
        self.assertEqual(neutralization["typography_attribute_removal_count"], 53)
        self.assertEqual(
            self.report["validation"]["remaining_legacy_typography_attributes"],
            {},
        )

    def test_timing_offsets_are_preserved_not_misclassified_as_layout(self) -> None:
        neutralization = self.report["neutralization"]
        self.assertEqual(neutralization["semantic_offset_preserved_count"], 54)
        self.assertEqual(
            neutralization["semantic_offset_parent_counts"],
            {"direction": 48, "harmony": 6},
        )
        self.assertEqual(len(self.root.findall(".//offset")), 54)
        self.assertTrue(
            all(offset.get("sound") != "no" for offset in self.root.findall(".//offset"))
        )

    def test_lyric_extenders_and_duplicate_audit_are_exact(self) -> None:
        lyrics = self.report["lyric_inventory"]
        self.assertEqual(lyrics["anchor_count"], 1376)
        self.assertEqual(lyrics["extend_element_count"], 685)
        self.assertEqual(
            lyrics["extend_type_counts"],
            {"continue": 3, "start": 341, "stop": 341},
        )
        self.assertEqual(lyrics["same_coordinate_cluster_count"], 3)
        self.assertEqual(lyrics["same_coordinate_anchor_count"], 6)
        self.assertEqual(lyrics["exact_duplicate_cluster_count"], 0)
        self.assertEqual(lyrics["exact_duplicate_anchor_count"], 0)
        self.assertEqual(lyrics["same_coordinate_nonidentical_cluster_count"], 3)
        self.assertEqual(lyrics["lyric_anchors_removed"], 0)

    def test_fixture_removes_only_visual_layout_data(self) -> None:
        root = deepcopy(ET.parse(neutralizer.DEFAULT_SOURCE).getroot())
        note = root.find("./part/measure/note")
        lyric = root.find(".//lyric")
        self.assertIsNotNone(note)
        self.assertIsNotNone(lyric)
        assert note is not None and lyric is not None
        note.set("relative-x", "9")
        lyric.set("default-y", "-80")

        measure = root.find("./part/measure")
        self.assertIsNotNone(measure)
        assert measure is not None
        print_node = ET.Element("print", {"new-system": "yes"})
        system_layout = ET.SubElement(print_node, "system-layout")
        ET.SubElement(system_layout, "system-distance").text = "240"
        page_layout = ET.SubElement(print_node, "page-layout")
        ET.SubElement(page_layout, "page-height").text = "1862.667"
        measure.insert(0, print_node)

        direction = ET.SubElement(measure, "direction")
        ET.SubElement(direction, "direction-type")
        visual_offset = ET.SubElement(direction, "offset", {"sound": "no"})
        visual_offset.text = "16"
        semantic_direction = ET.SubElement(measure, "direction")
        ET.SubElement(semantic_direction, "direction-type")
        semantic_offset = ET.SubElement(semantic_direction, "offset")
        semantic_offset.text = "8"

        changes = neutralizer.apply_neutralization(root)
        self.assertEqual(len(changes["position_attribute_removals"]), 6)
        self.assertNotIn("relative-x", note.attrib)
        self.assertNotIn("default-y", lyric.attrib)
        self.assertEqual(len(changes["typography_attribute_removals"]), 53)
        self.assertEqual(len(changes["local_print_spacing_removals"]), 1)
        self.assertIsNone(print_node.find("system-layout"))
        self.assertIsNotNone(print_node.find("page-layout"))
        self.assertEqual(print_node.get("new-system"), "yes")
        self.assertEqual(len(changes["visual_only_offset_removals"]), 1)
        self.assertIsNone(direction.find("offset"))
        self.assertEqual(semantic_direction.findtext("offset"), "8")


if __name__ == "__main__":
    unittest.main()
