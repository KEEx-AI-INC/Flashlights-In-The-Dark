#!/usr/bin/env python3

from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_fall2026_performer_score as validator


PROVENANCE = ROOT / "Engraving/Scores/Fall2026-Provenance"
CANONICAL_XML = (
    PROVENANCE / "FlashlightsInTheDark_Fall2026_Dorico24PageCasted.musicxml"
)
COLOPHON_PDF = (
    PROVENANCE / "FlashlightsInTheDark_Fall2026_Page24_Colophon.pdf"
)


def check_by_name(section: dict, name: str) -> validator.Check:
    return next(item for item in section["checks"] if item.name == name)


class Fall2026PerformerScoreValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not CANONICAL_XML.is_file():
            raise unittest.SkipTest("Canonical Fall 2026 casting fixture is absent")
        cls.canonical_root = ET.parse(CANONICAL_XML).getroot()

    def write_mutation(self, root: ET.Element, folder: Path, name: str) -> Path:
        path = folder / name
        ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
        return path

    def test_canonical_musicxml_passes_every_semantic_check(self) -> None:
        result = validator.validate_musicxml(CANONICAL_XML)
        self.assertEqual(result["status"], "passed")
        self.assertTrue(all(item.status == "pass" for item in result["checks"]))
        self.assertEqual(result["note_count"], 2787)
        self.assertEqual(result["lyric_anchor_count"], 1376)
        self.assertEqual(
            result["lyric_placement_distribution"], {"above": 579, "below": 797}
        )
        self.assertEqual(
            result["musical_fingerprint"], validator.EXPECTED_FINGERPRINT
        )
        self.assertEqual(
            result["third_lane_anchor_hash"], validator.EXPECTED_THIRD_LANE_HASH
        )

    def test_note_deletion_fails_count_and_fingerprint(self) -> None:
        root = copy.deepcopy(self.canonical_root)
        measure = next(
            item for item in root.findall("./part/measure") if item.find("note") is not None
        )
        note = measure.find("note")
        self.assertIsNotNone(note)
        measure.remove(note)
        with tempfile.TemporaryDirectory() as folder:
            path = self.write_mutation(root, Path(folder), "note-deleted.musicxml")
            result = validator.validate_musicxml(path)
        self.assertEqual(check_by_name(result, "note_elements").status, "fail")
        self.assertEqual(
            check_by_name(result, "canonical_musical_fingerprint").status,
            "fail",
        )

    def test_single_lyric_placement_change_fails_routing(self) -> None:
        root = copy.deepcopy(self.canonical_root)
        lyric = next(item for item in root.findall(".//lyric") if item.get("placement") == "above")
        lyric.set("placement", "below")
        with tempfile.TemporaryDirectory() as folder:
            path = self.write_mutation(root, Path(folder), "bad-placement.musicxml")
            result = validator.validate_musicxml(path)
        self.assertEqual(
            check_by_name(result, "lyric_placement_distribution").status,
            "fail",
        )
        self.assertEqual(check_by_name(result, "lyric_routing_rule").status, "fail")

    def test_non_five_line_override_fails(self) -> None:
        root = copy.deepcopy(self.canonical_root)
        staff_lines = root.find(".//staff-details/staff-lines")
        self.assertIsNotNone(staff_lines)
        staff_lines.text = "1"
        with tempfile.TemporaryDirectory() as folder:
            path = self.write_mutation(root, Path(folder), "one-line.musicxml")
            result = validator.validate_musicxml(path)
        self.assertEqual(
            check_by_name(result, "five_line_staves_throughout").status,
            "fail",
        )

    def test_third_lane_anchor_change_fails_content_and_lane_hash(self) -> None:
        root = copy.deepcopy(self.canonical_root)
        target = None
        for part_id, _, _, _, voice, lyric in validator.iter_lyrics(root):
            if part_id == "P4" and voice == "2" and lyric.get("number") == "2":
                target = lyric
                break
        self.assertIsNotNone(target)
        target.set("number", "1")
        with tempfile.TemporaryDirectory() as folder:
            path = self.write_mutation(root, Path(folder), "bad-third-lane.musicxml")
            result = validator.validate_musicxml(path)
        self.assertEqual(
            check_by_name(result, "canonical_lyric_content").status,
            "fail",
        )
        self.assertEqual(
            check_by_name(result, "stable_third_lyric_lane").status,
            "fail",
        )

    def test_retained_provenance_chain_proves_all_replacements(self) -> None:
        xml_result = validator.validate_musicxml(CANONICAL_XML)
        result = validator.validate_provenance(
            PROVENANCE,
            lyric_content_hash=xml_result["lyric_content_hash"],
        )
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["approved_replacement_count"], 388)
        self.assertEqual(
            check_by_name(result, "all_388_approved_replacements").status,
            "pass",
        )

    def test_missing_pdf_keeps_delivery_incomplete(self) -> None:
        report = validator.validate_delivery(
            CANONICAL_XML,
            None,
            provenance_dir=PROVENANCE,
            final_delivery=True,
        )
        self.assertEqual(report["status"], "incomplete")
        self.assertFalse(report["final_delivery_pass"])

    def test_candidate_flag_cannot_claim_final_pass(self) -> None:
        report = validator.validate_delivery(
            CANONICAL_XML,
            None,
            provenance_dir=PROVENANCE,
            final_delivery=False,
        )
        self.assertFalse(report["final_delivery_pass"])
        self.assertEqual(report["status"], "incomplete")

    @unittest.skipUnless(COLOPHON_PDF.is_file(), "Colophon PDF fixture is absent")
    def test_one_page_colophon_fails_booklet_count_but_passes_pdf_readability(self) -> None:
        if not validator.find_poppler_tool("pdfinfo"):
            self.skipTest("Poppler pdfinfo is unavailable")
        result = validator.validate_pdf(COLOPHON_PDF)
        self.assertEqual(check_by_name(result, "booklet_page_count").status, "fail")
        self.assertEqual(
            check_by_name(result, "letter_portrait_geometry").status,
            "pass",
        )
        nonblank = next(
            (item for item in result["checks"] if item.name == "nonblank_pages"),
            None,
        )
        if nonblank is not None:
            self.assertEqual(nonblank.status, "pass")

    @unittest.skipUnless(COLOPHON_PDF.is_file(), "Colophon PDF fixture is absent")
    def test_pypdf_font_fallback_recurses_and_finds_embedded_fonts(self) -> None:
        fonts, error = validator.audit_fonts_with_pypdf(COLOPHON_PDF)
        if fonts is None and error and error.startswith("pypdf unavailable"):
            self.skipTest(error)
        self.assertIsNone(error)
        self.assertTrue(fonts)
        self.assertTrue(all(font["embedded"] for font in fonts or []))
        self.assertTrue(
            any("Academico" in font["name"] for font in fonts or [])
        )


if __name__ == "__main__":
    unittest.main()
