#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

from pypdf import PdfReader, PdfWriter


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import assemble_fall2026_performer_score_pdf as assembler  # noqa: E402


COLOPHON = (
    assembler.ROOT
    / "Engraving/Scores/Fall2026-Provenance/"
    "FlashlightsInTheDark_Fall2026_Page40_Colophon.pdf"
)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_pdf(
    path: Path,
    page_count: int,
    *,
    wrong_size_page: int | None = None,
    rotated_page: int | None = None,
    password: str | None = None,
) -> None:
    writer = PdfWriter()
    for page_number in range(1, page_count + 1):
        if page_number == wrong_size_page:
            page = writer.add_blank_page(width=595, height=842)
        else:
            page = writer.add_blank_page(width=612, height=792)
        if page_number == rotated_page:
            page.rotate(90)
    if password is not None:
        writer.encrypt(password)
    with path.open("wb") as stream:
        writer.write(stream)


@unittest.skipUnless(COLOPHON.is_file(), "Validated page-40 colophon is absent")
class Fall2026PdfAssemblyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder_context = tempfile.TemporaryDirectory()
        self.folder = Path(self.folder_context.name)
        self.music = self.folder / "music.pdf"
        self.output = self.folder / "booklet.pdf"
        self.report = self.folder / "booklet.json"

    def tearDown(self) -> None:
        self.folder_context.cleanup()

    def assemble(self, colophon: Path = COLOPHON, **kwargs):
        return assembler.assemble(
            self.music,
            colophon,
            self.output,
            self.report,
            **kwargs,
        )

    def assert_refused_without_outputs(self, message: str, callback) -> None:
        with self.assertRaisesRegex(assembler.AssemblyError, message):
            callback()
        self.assertFalse(self.output.exists())
        self.assertFalse(self.report.exists())

    def test_page_40_colophon_matches_pinned_hash_and_metadata(self) -> None:
        reader = PdfReader(COLOPHON)
        metadata = reader.metadata
        self.assertEqual(file_hash(COLOPHON), assembler.EXPECTED_COLOPHON_SHA256)
        self.assertEqual(len(reader.pages), 1)
        self.assertEqual(
            metadata.title,
            "Flashlights in the Dark - Fall 2026 Performer Score - Page 40 Colophon",
        )
        self.assertEqual(
            metadata.subject,
            "Standalone page-40 colophon for the validated Fall 2026 "
            "performer-score edition",
        )
        self.assertIn("page 40", metadata.get("/Keywords", ""))

    def test_valid_inputs_produce_verified_40_page_pdf_and_json_report(self) -> None:
        write_pdf(self.music, 39)
        music_before = self.music.read_bytes()
        colophon_before = COLOPHON.read_bytes()

        result = self.assemble()

        self.assertEqual(self.music.read_bytes(), music_before)
        self.assertEqual(COLOPHON.read_bytes(), colophon_before)
        self.assertEqual(len(PdfReader(self.output).pages), 40)
        persisted = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(persisted, result)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(
            result["profile"],
            "Fall 2026 40-page saddle-stitch performer score",
        )
        self.assertEqual(result["output"]["sha256"], file_hash(self.output))
        self.assertEqual(result["output"]["page_count"], 40)
        self.assertEqual(len(result["output"]["pages"]), 40)
        self.assertEqual(
            result["output"]["pages"][-1]["content_sha256"],
            result["inputs"]["page_40_colophon"]["pages"][0][
                "content_sha256"
            ],
        )
        self.assertTrue(result["assembly"]["input_files_unchanged"])
        self.assertTrue(result["assembly"]["pdf_installed_atomically"])
        self.assertEqual(result["assembly"]["music_pages_copied"], 39)
        self.assertEqual(result["assembly"]["colophon_output_page"], 40)
        self.assertTrue(
            result["assembly"]["page_40_content_hash_matches_colophon"]
        )

    def test_wrong_music_page_count_is_refused(self) -> None:
        write_pdf(self.music, 38)
        self.assert_refused_without_outputs(
            "music PDF must contain exactly 39",
            self.assemble,
        )

    def test_wrong_colophon_page_count_is_refused(self) -> None:
        write_pdf(self.music, 39)
        wrong_colophon = self.folder / "two-page-colophon.pdf"
        write_pdf(wrong_colophon, 2)
        self.assert_refused_without_outputs(
            "colophon PDF must contain exactly 1",
            lambda: self.assemble(
                wrong_colophon,
                expected_colophon_sha256=file_hash(wrong_colophon),
            ),
        )

    def test_wrong_page_size_is_refused(self) -> None:
        write_pdf(self.music, 39, wrong_size_page=17)
        self.assert_refused_without_outputs(
            "music page 17 MediaBox is not US Letter",
            self.assemble,
        )

    def test_rotated_page_is_refused(self) -> None:
        write_pdf(self.music, 39, rotated_page=8)
        self.assert_refused_without_outputs(
            "music page 8 has a nonzero rotation",
            self.assemble,
        )

    def test_encrypted_inputs_are_refused(self) -> None:
        with self.subTest("music"):
            write_pdf(self.music, 39, password="secret")
            self.assert_refused_without_outputs(
                "music PDF is encrypted",
                self.assemble,
            )

        self.music.unlink(missing_ok=True)
        write_pdf(self.music, 39)
        encrypted_colophon = self.folder / "encrypted-colophon.pdf"
        write_pdf(encrypted_colophon, 1, password="secret")
        with self.subTest("colophon"):
            self.assert_refused_without_outputs(
                "colophon PDF is encrypted",
                lambda: self.assemble(
                    encrypted_colophon,
                    expected_colophon_sha256=file_hash(encrypted_colophon),
                ),
            )

    def test_unvalidated_colophon_hash_is_refused(self) -> None:
        write_pdf(self.music, 39)
        substitute = self.folder / "substitute-colophon.pdf"
        write_pdf(substitute, 1)
        self.assert_refused_without_outputs(
            "does not match the validated page-40 colophon",
            lambda: self.assemble(substitute),
        )

    def test_existing_output_is_not_overwritten_without_replace(self) -> None:
        write_pdf(self.music, 39)
        sentinel = b"do not overwrite\n"
        self.output.write_bytes(sentinel)
        with self.assertRaisesRegex(assembler.AssemblyError, "already exists"):
            self.assemble()
        self.assertEqual(self.output.read_bytes(), sentinel)
        self.assertFalse(self.report.exists())

    def test_input_and_output_alias_is_refused(self) -> None:
        write_pdf(self.music, 39)
        with self.assertRaisesRegex(
            assembler.AssemblyError,
            "music input and output PDF must be different files",
        ):
            assembler.assemble(
                self.music,
                COLOPHON,
                self.music,
                self.report,
            )
        self.assertEqual(len(PdfReader(self.music).pages), 39)
        self.assertFalse(self.report.exists())


if __name__ == "__main__":
    unittest.main()
