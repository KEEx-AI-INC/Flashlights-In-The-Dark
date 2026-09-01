#!/usr/bin/env python3
"""Derive the page-36 colophon from the validated Academico page-32 proof."""

from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, TextStringObject


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "FlashlightsInTheDark_Fall2026_Page32_Colophon.pdf"
OUTPUT = HERE / "FlashlightsInTheDark_Fall2026_Page36_Colophon.pdf"


def build() -> Path:
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)

    reader = PdfReader(str(SOURCE), strict=True)
    if reader.is_encrypted or len(reader.pages) != 1:
        raise ValueError("The validated page-32 source must be one unencrypted page")

    writer = PdfWriter(clone_from=str(SOURCE))
    page = writer.pages[0]
    content = ContentStream(page.get_contents(), writer)
    replacements = 0
    for operands, operator in content.operations:
        if operator == b"Tj" and len(operands) == 1 and str(operands[0]) == "32":
            operands[0] = TextStringObject("36")
            replacements += 1
    if replacements != 1:
        raise ValueError(f"Expected one page-number text object; found {replacements}")
    page.replace_contents(content)

    writer.add_metadata(
        {
            "/Title": "Flashlights in the Dark - Fall 2026 Performer Score - Page 36 Colophon",
            "/Author": "Jon D. Nelson",
            "/Subject": (
                "Standalone page-36 colophon for the validated Fall 2026 "
                "performer-score edition"
            ),
            "/Keywords": (
                "Flashlights in the Dark, Fall 2026, performer score, page 36, "
                "colophon, Fall 2026 Working Text, canonical v26 score fingerprint"
            ),
        }
    )
    with OUTPUT.open("wb") as stream:
        writer.write(stream)
    return OUTPUT


if __name__ == "__main__":
    print(build())
