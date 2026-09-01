#!/usr/bin/env python3
"""Build an even-numbered colophon page for the Fall 2026 performer score."""

import argparse

from pathlib import Path

import CoreText
import Foundation
import Quartz


HERE = Path(__file__).resolve().parent
DEFAULT_PAGE_NUMBER = 24

PAGE_WIDTH = 612.0
PAGE_HEIGHT = 792.0

INK = Quartz.CGColorCreateGenericRGB(0.090, 0.090, 0.090, 1.0)
QUIET = Quartz.CGColorCreateGenericRGB(0.353, 0.353, 0.353, 1.0)
RULE = Quartz.CGColorCreateGenericRGB(0.604, 0.604, 0.604, 1.0)


def make_line(text: str, font_name: str, size: float, color, tracking: float = 0.0):
    font = CoreText.CTFontCreateWithName(font_name, size, None)
    attributes = {
        CoreText.kCTFontAttributeName: font,
        CoreText.kCTForegroundColorAttributeName: color,
    }
    if tracking:
        attributes[CoreText.kCTKernAttributeName] = tracking
    attributed = Foundation.NSAttributedString.alloc().initWithString_attributes_(text, attributes)
    return CoreText.CTLineCreateWithAttributedString(attributed)


def line_width(line) -> float:
    width, _, _, _ = CoreText.CTLineGetTypographicBounds(line, None, None, None)
    return width


def draw_text(
    context,
    text: str,
    x: float,
    baseline: float,
    font: str,
    size: float,
    color=INK,
    tracking=0.0,
):
    line = make_line(text, font, size, color, tracking)
    Quartz.CGContextSetTextPosition(context, x, baseline)
    CoreText.CTLineDraw(line, context)


def draw_centered(
    context,
    text: str,
    baseline: float,
    font: str,
    size: float,
    color=INK,
    tracking=0.0,
):
    line = make_line(text, font, size, color, tracking)
    x = (PAGE_WIDTH - line_width(line)) / 2.0
    Quartz.CGContextSetTextPosition(context, x, baseline)
    CoreText.CTLineDraw(line, context)


def draw_rule(context, x1: float, y: float, x2: float, width: float):
    Quartz.CGContextSetStrokeColorWithColor(context, RULE)
    Quartz.CGContextSetLineWidth(context, width)
    Quartz.CGContextMoveToPoint(context, x1, y)
    Quartz.CGContextAddLineToPoint(context, x2, y)
    Quartz.CGContextStrokePath(context)


def build(page_number: int = DEFAULT_PAGE_NUMBER) -> Path:
    if page_number <= 0 or page_number % 2:
        raise ValueError("The saddle-stitch colophon must be an even-numbered page")
    output = HERE / f"FlashlightsInTheDark_Fall2026_Page{page_number}_Colophon.pdf"
    for path in (
        Path("/Library/Fonts/Academico-Regular.otf"),
        Path("/Library/Fonts/Academico-Bold.otf"),
        Path("/Library/Fonts/Academico-Italic.otf"),
    ):
        if not path.exists():
            raise FileNotFoundError(path)

    output_url = Foundation.NSURL.fileURLWithPath_(str(output))
    media_box = Quartz.CGRectMake(0, 0, PAGE_WIDTH, PAGE_HEIGHT)
    metadata = {
        Quartz.kCGPDFContextTitle: (
            f"Flashlights in the Dark - Fall 2026 Performer Score - Page {page_number} Colophon"
        ),
        Quartz.kCGPDFContextAuthor: "Jon D. Nelson",
        Quartz.kCGPDFContextSubject: (
            f"Standalone page-{page_number} colophon for the validated Fall 2026 "
            "performer-score edition"
        ),
        Quartz.kCGPDFContextKeywords: [
            "Flashlights in the Dark",
            "Fall 2026",
            "performer score",
            f"page {page_number}",
            "colophon",
            "Fall 2026 Working Text",
            "canonical v26 score fingerprint",
        ],
    }
    context = Quartz.CGPDFContextCreateWithURL(output_url, media_box, metadata)
    if context is None:
        raise RuntimeError(f"Could not create {output}")

    Quartz.CGPDFContextBeginPage(context, None)
    Quartz.CGContextSetTextMatrix(context, Quartz.CGAffineTransformIdentity)
    Quartz.CGContextSetRGBFillColor(context, 1, 1, 1, 1)
    Quartz.CGContextFillRect(context, media_box)

    # Compact running furniture for this even-numbered (left-hand) page.
    draw_centered(
        context,
        "FLASHLIGHTS IN THE DARK  /  FALL 2026 PERFORMER SCORE",
        PAGE_HEIGHT - 39,
        "Academico",
        7.4,
        QUIET,
        0.52,
    )
    draw_rule(context, 54, PAGE_HEIGHT - 49, PAGE_WIDTH - 62, 0.35)

    # Edition and authorship.
    draw_centered(context, "FLASHLIGHTS IN THE DARK", 584, "Academico Bold", 18, INK, 0.65)
    draw_centered(context, "Fall 2026 Performer-Score Edition", 556, "Academico Italic", 12.2)
    draw_centered(context, "Set in 2076", 535, "Academico", 10.8, QUIET)

    draw_centered(context, "Music by Jon D. Nelson", 484, "Academico", 11.2)
    draw_centered(context, "Text by Clare Malinowski & Jon Nelson", 464, "Academico", 11.2)
    draw_centered(
        context,
        "Commissioned by the Philharmonic Chorus of Madison",
        434,
        "Academico Italic",
        10.4,
        QUIET,
    )

    draw_rule(context, 187, 395, PAGE_WIDTH - 187, 0.45)

    # Current edition provenance. These claims describe the validated casting
    # source and do not imply completion of the final visual publication proof.
    draw_centered(context, "EDITORIAL BASIS", 353, "Academico Bold", 8.2, QUIET, 1.05)
    draw_centered(context, "Lyrics: Fall 2026 Working Text", 326, "Academico", 10.6)
    draw_centered(context, "Musical structure: canonical v26 score fingerprint", 307, "Academico", 10.6)
    draw_centered(
        context,
        "Validated source: six vocal parts / 151 measures / 1,376 lyric anchors",
        285,
        "Academico",
        9.4,
        QUIET,
    )

    draw_centered(
        context,
        "This engraving pass preserves the notes, rhythms, measure structure,",
        249,
        "Academico",
        9.7,
        QUIET,
    )
    draw_centered(
        context,
        "and cue timing. Show-control and runtime assets remain unchanged.",
        233,
        "Academico",
        9.7,
        QUIET,
    )
    draw_centered(
        context,
        "All 388 approved Fall text replacements are present in the validated source.",
        202,
        "Academico Italic",
        9.2,
        QUIET,
    )
    draw_centered(
        context,
        "Text-semantic changes are recorded in the Fall 2026 engraving correction log.",
        184,
        "Academico Italic",
        9.2,
        QUIET,
    )

    draw_centered(context, "© 2025", 105, "Academico", 9.4, QUIET)

    # Outside page number for a left-hand page in the saddle-stitched booklet.
    draw_text(context, str(page_number), 46, 34, "Academico", 9.5)

    Quartz.CGPDFContextEndPage(context)
    Quartz.CGPDFContextClose(context)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--page-number", type=int, default=DEFAULT_PAGE_NUMBER)
    args = parser.parse_args()
    build(args.page_number)
