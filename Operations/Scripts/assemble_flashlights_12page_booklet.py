#!/usr/bin/env python3
"""Assemble the 12-page Flashlights in the Dark performer booklet.

The source PDF pages are copied without scaling, cropping, or content changes.
Page 11 is intentionally blank so the final music page has no facing content.
The performer-resources sheet is placed on page 12 as the booklet back cover;
only its printed folio is updated from 11 to 12.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import os
from pathlib import Path
import tempfile

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COVER_PRELIM = (
    REPO_ROOT
    / "Engraving/Issued-Materials/Fall-2026/Cover-and-Preliminary-Pages"
    / "2026_0825_FlashlightsInTheDark_CoverAndPrelim_03.pdf"
)
DEFAULT_SCORE = REPO_ROOT / "FlashlightsInTheDark_v36 - Score.pdf"
DEFAULT_RESOURCES = (
    REPO_ROOT / "output/pdf/FlashlightsInTheDark_Page11_PerformerResources.pdf"
)
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "output/pdf/FlashlightsInTheDark_Fall2026_12Page_PerformerBooklet_BackCoverResources.pdf"
)

LETTER_WIDTH = 612.0
LETTER_HEIGHT = 792.0
EXPECTED_PAGE_COUNTS = (2, 8, 1)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_source(path: Path, expected_pages: int) -> PdfReader:
    if not path.is_file():
        raise FileNotFoundError(f"Missing source PDF: {path}")

    reader = PdfReader(path)
    if reader.is_encrypted:
        raise ValueError(f"Encrypted source PDF is not supported: {path}")
    if len(reader.pages) != expected_pages:
        raise ValueError(
            f"Expected {expected_pages} pages in {path}, found {len(reader.pages)}"
        )

    for page_number, page in enumerate(reader.pages, start=1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        rotation = int(page.get("/Rotate", 0)) % 360
        if abs(width - LETTER_WIDTH) > 0.01 or abs(height - LETTER_HEIGHT) > 0.01:
            raise ValueError(
                f"Page {page_number} of {path} is {width:g} x {height:g} pt; "
                "expected 612 x 792 pt"
            )
        if rotation != 0:
            raise ValueError(
                f"Page {page_number} of {path} has rotation {rotation}; expected 0"
            )

    return reader


def resources_page_with_updated_folio(page):
    """Return a copy of the resources page with its visible folio changed to 12."""
    page = copy.deepcopy(page)
    contents = page.get_contents()
    if contents is None:
        raise ValueError("Performer-resources page has no content stream")

    old_folio = b"(11) Tj"
    new_folio = b"(12) Tj"
    data = contents.get_data()
    if data.count(old_folio) != 1:
        raise ValueError(
            "Expected exactly one page-11 folio token in the resources PDF"
        )

    updated_stream = DecodedStreamObject()
    updated_stream.set_data(data.replace(old_folio, new_folio, 1))
    page[NameObject("/Contents")] = updated_stream
    return page


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cover-prelim", type=Path, default=DEFAULT_COVER_PRELIM)
    parser.add_argument("--score", type=Path, default=DEFAULT_SCORE)
    parser.add_argument("--resources", type=Path, default=DEFAULT_RESOURCES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sources = (args.cover_prelim, args.score, args.resources)
    readers = [
        validate_source(path.resolve(), expected)
        for path, expected in zip(sources, EXPECTED_PAGE_COUNTS, strict=True)
    ]

    writer = PdfWriter()
    for page in readers[0].pages:
        writer.add_page(page)
    for page in readers[1].pages:
        writer.add_page(page)
    writer.add_blank_page(width=LETTER_WIDTH, height=LETTER_HEIGHT)
    writer.add_page(resources_page_with_updated_folio(readers[2].pages[0]))

    if len(writer.pages) != 12:
        raise RuntimeError(f"Internal error: assembled {len(writer.pages)} pages, not 12")

    writer.add_metadata(
        {
            "/Title": "Flashlights in the Dark — Fall 2026 Performer Booklet",
            "/Author": "Jon D. Nelson",
            "/Subject": "12-page performer score with technical resources on the back cover",
            "/Creator": "Flashlights in the Dark booklet assembler",
        }
    )

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=f".{output.stem}.", suffix=".tmp", dir=output.parent,
            delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            writer.write(temporary)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, output)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    print("Assembled page order:")
    print(f"  1-2   {args.cover_prelim.resolve()}")
    print(f"  3-10  {args.score.resolve()}")
    print("  11    intentionally blank US Letter page")
    print(f"  12    {args.resources.resolve()} (visible folio updated to 12)")
    print("Source SHA-256:")
    for source in sources:
        resolved = source.resolve()
        print(f"  {sha256(resolved)}  {resolved}")
    print(f"Output SHA-256:\n  {sha256(output)}  {output}")


if __name__ == "__main__":
    main()
