#!/usr/bin/env python3
"""Derive the page-40 colophon from the validated Academico page-32 proof."""

from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile

import CoreText
import Foundation
import Quartz
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, TextStringObject


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "FlashlightsInTheDark_Fall2026_Page32_Colophon.pdf"
OUTPUT = HERE / "FlashlightsInTheDark_Fall2026_Page40_Colophon.pdf"
EXPECTED_SOURCE_SHA256 = (
    "ce18e28d992f2054a7209ce2271b54bf497158756a0ceef83af9c94d5e26be4a"
)
PAGE_WIDTH = 612.0
PAGE_HEIGHT = 792.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_page_number_overlay(path: Path) -> None:
    """Draw the new folio with a fresh subset that includes the digit 4."""

    font_path = Path("/Library/Fonts/Academico-Regular.otf")
    if not font_path.is_file():
        raise FileNotFoundError(font_path)

    output_url = Foundation.NSURL.fileURLWithPath_(str(path))
    media_box = Quartz.CGRectMake(0, 0, PAGE_WIDTH, PAGE_HEIGHT)
    context = Quartz.CGPDFContextCreateWithURL(output_url, media_box, None)
    if context is None:
        raise RuntimeError(f"Could not create temporary folio overlay: {path}")

    Quartz.CGPDFContextBeginPage(context, None)
    Quartz.CGContextSetTextMatrix(context, Quartz.CGAffineTransformIdentity)
    font = CoreText.CTFontCreateWithName("Academico", 9.5, None)
    attributes = {
        CoreText.kCTFontAttributeName: font,
        CoreText.kCTForegroundColorAttributeName: (
            Quartz.CGColorCreateGenericRGB(0.090, 0.090, 0.090, 1.0)
        ),
    }
    attributed = Foundation.NSAttributedString.alloc().initWithString_attributes_(
        "40", attributes
    )
    line = CoreText.CTLineCreateWithAttributedString(attributed)
    Quartz.CGContextSetTextPosition(context, 46, 34)
    CoreText.CTLineDraw(line, context)
    Quartz.CGPDFContextEndPage(context)
    Quartz.CGPDFContextClose(context)


def build() -> Path:
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)
    source_sha256 = sha256(SOURCE)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise ValueError(
            "The page-32 colophon does not match the validated source "
            f"({source_sha256})"
        )

    reader = PdfReader(str(SOURCE), strict=True)
    if reader.is_encrypted or len(reader.pages) != 1:
        raise ValueError("The validated page-32 source must be one unencrypted page")

    writer = PdfWriter(clone_from=str(SOURCE))
    page = writer.pages[0]
    content = ContentStream(page.get_contents(), writer)
    replacements = 0
    for operands, operator in content.operations:
        if operator == b"Tj" and len(operands) == 1 and str(operands[0]) == "32":
            operands[0] = TextStringObject("")
            replacements += 1
    if replacements != 1:
        raise ValueError(f"Expected one page-number text object; found {replacements}")
    page.replace_contents(content)

    overlay_handle = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    overlay_path = Path(overlay_handle.name)
    overlay_handle.close()
    try:
        build_page_number_overlay(overlay_path)
        overlay_reader = PdfReader(str(overlay_path), strict=True)
        if overlay_reader.is_encrypted or len(overlay_reader.pages) != 1:
            raise ValueError("The temporary page-number overlay is invalid")
        page.merge_page(overlay_reader.pages[0])
    finally:
        overlay_path.unlink(missing_ok=True)

    writer.add_metadata(
        {
            "/Title": (
                "Flashlights in the Dark - Fall 2026 Performer Score - "
                "Page 40 Colophon"
            ),
            "/Author": "Jon D. Nelson",
            "/Subject": (
                "Standalone page-40 colophon for the validated Fall 2026 "
                "performer-score edition"
            ),
            "/Keywords": (
                "Flashlights in the Dark, Fall 2026, performer score, page 40, "
                "colophon, Fall 2026 Working Text, canonical v26 score fingerprint"
            ),
        }
    )
    with OUTPUT.open("wb") as stream:
        writer.write(stream)
    return OUTPUT


if __name__ == "__main__":
    print(build())
