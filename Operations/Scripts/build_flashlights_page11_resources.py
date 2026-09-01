#!/usr/bin/env python3
"""Build the standalone page-11 performer resources sheet.

The output is a US Letter portrait PDF intended to be inserted as page 11 of
the 12-page saddle-stitched performer booklet. Page 12 remains blank at the
booklet-assembly stage. QR symbols encode stable KEEx.AI aliases rather than
the changeable downstream store URLs.
"""

from pathlib import Path

import CoreText
import Foundation
import Quartz


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output/pdf/FlashlightsInTheDark_Page11_PerformerResources.pdf"

PAGE_WIDTH = 612.0
PAGE_HEIGHT = 792.0

INK = Quartz.CGColorCreateGenericRGB(0.090, 0.090, 0.090, 1.0)
QUIET = Quartz.CGColorCreateGenericRGB(0.353, 0.353, 0.353, 1.0)
RULE = Quartz.CGColorCreateGenericRGB(0.604, 0.604, 0.604, 1.0)
PALE = Quartz.CGColorCreateGenericRGB(0.955, 0.955, 0.955, 1.0)
WHITE = Quartz.CGColorCreateGenericRGB(1.0, 1.0, 1.0, 1.0)

REGULAR = "Garamond"
BOLD = "Garamond Bold"
ITALIC = "Garamond Italic"

QR_CODES = (
    {
        "label": "RESOURCE HUB",
        "url": "https://keex.ai/flashlights",
        "display": "keex.ai/flashlights",
        "note": "Practice media + updates",
    },
    {
        "label": "iPHONE / iPAD",
        "url": "https://keex.ai/flashlights/ios",
        "display": "keex.ai/flashlights/ios",
        "note": "Install or update",
    },
    {
        "label": "ANDROID",
        "url": "https://keex.ai/flashlights/android",
        "display": "keex.ai/flashlights/android",
        "note": "Install or update",
    },
)


def make_line(text: str, font_name: str, size: float, color=INK, tracking: float = 0.0):
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


def text_width(text: str, font: str, size: float, tracking: float = 0.0) -> float:
    return line_width(make_line(text, font, size, tracking=tracking))


def draw_text(context, text: str, x: float, baseline: float, font: str, size: float, color=INK, tracking: float = 0.0):
    line = make_line(text, font, size, color, tracking)
    Quartz.CGContextSetTextPosition(context, x, baseline)
    CoreText.CTLineDraw(line, context)


def draw_centered(context, text: str, baseline: float, font: str, size: float, color=INK, tracking: float = 0.0):
    line = make_line(text, font, size, color, tracking)
    Quartz.CGContextSetTextPosition(context, (PAGE_WIDTH - line_width(line)) / 2.0, baseline)
    CoreText.CTLineDraw(line, context)


def wrap_lines(text: str, font: str, size: float, max_width: float) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if text_width(candidate, font, size) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def draw_wrapped(
    context,
    text: str,
    x: float,
    baseline: float,
    width: float,
    *,
    font: str = REGULAR,
    size: float = 9.0,
    leading: float = 11.2,
    color=INK,
) -> float:
    for line in wrap_lines(text, font, size, width):
        draw_text(context, line, x, baseline, font, size, color)
        baseline -= leading
    return baseline


def draw_bullets(
    context,
    items: list[str],
    x: float,
    baseline: float,
    width: float,
    *,
    size: float = 8.4,
    leading: float = 10.2,
    item_gap: float = 4.0,
) -> float:
    dot_x = x + 2.2
    text_x = x + 11.0
    text_width_available = width - 11.0
    for item in items:
        lines = wrap_lines(item, REGULAR, size, text_width_available)
        Quartz.CGContextSetFillColorWithColor(context, INK)
        Quartz.CGContextFillEllipseInRect(context, Quartz.CGRectMake(dot_x, baseline + 2.0, 2.3, 2.3))
        for line in lines:
            draw_text(context, line, text_x, baseline, REGULAR, size)
            baseline -= leading
        baseline -= item_gap
    return baseline


def draw_rule(context, x1: float, y: float, x2: float, width: float = 0.35):
    Quartz.CGContextSetStrokeColorWithColor(context, RULE)
    Quartz.CGContextSetLineWidth(context, width)
    Quartz.CGContextMoveToPoint(context, x1, y)
    Quartz.CGContextAddLineToPoint(context, x2, y)
    Quartz.CGContextStrokePath(context)


def draw_section_label(context, text: str, x: float, baseline: float):
    draw_text(context, text, x, baseline, BOLD, 8.0, QUIET, 1.0)


def make_qr_image(payload: str):
    data_bytes = payload.encode("utf-8")
    data = Foundation.NSData.dataWithBytes_length_(data_bytes, len(data_bytes))
    qr_filter = Quartz.CIFilter.filterWithName_("CIQRCodeGenerator")
    qr_filter.setDefaults()
    qr_filter.setValue_forKey_(data, "inputMessage")
    qr_filter.setValue_forKey_("H", "inputCorrectionLevel")
    image = qr_filter.valueForKey_("outputImage")
    if image is None:
        raise RuntimeError(f"Could not generate QR code for {payload}")
    extent = image.extent()
    module_count = int(round(extent.size.width))
    scale = 28.0
    scaled = image.imageByApplyingTransform_(Quartz.CGAffineTransformMakeScale(scale, scale))
    ci_context = Quartz.CIContext.contextWithOptions_(None)
    cg_image = ci_context.createCGImage_fromRect_(scaled, scaled.extent())
    if cg_image is None:
        raise RuntimeError(f"Could not rasterize QR code for {payload}")
    return cg_image, module_count


def draw_qr(context, payload: str, x: float, y: float, size: float):
    image, module_count = make_qr_image(payload)
    quiet_modules = 4
    full_modules = module_count + (2 * quiet_modules)
    module_size = size / full_modules
    inset = quiet_modules * module_size
    image_rect = Quartz.CGRectMake(x + inset, y + inset, module_count * module_size, module_count * module_size)

    Quartz.CGContextSetFillColorWithColor(context, WHITE)
    Quartz.CGContextFillRect(context, Quartz.CGRectMake(x, y, size, size))
    Quartz.CGContextSaveGState(context)
    Quartz.CGContextSetInterpolationQuality(context, Quartz.kCGInterpolationNone)
    Quartz.CGContextDrawImage(context, image_rect, image)
    Quartz.CGContextRestoreGState(context)


def build() -> Path:
    for font_name in (REGULAR, BOLD, ITALIC):
        font = CoreText.CTFontCreateWithName(font_name, 12.0, None)
        if font is None:
            raise RuntimeError(f"Required font is unavailable: {font_name}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    output_url = Foundation.NSURL.fileURLWithPath_(str(OUTPUT))
    media_box = Quartz.CGRectMake(0, 0, PAGE_WIDTH, PAGE_HEIGHT)
    metadata = {
        Quartz.kCGPDFContextTitle: "Flashlights in the Dark - Page 11 Performer Resources",
        Quartz.kCGPDFContextAuthor: "Jon D. Nelson",
        Quartz.kCGPDFContextSubject: "Standalone page-11 technical and performer resource page",
        Quartz.kCGPDFContextKeywords: [
            "Flashlights in the Dark",
            "performer score",
            "page 11",
            "electronics",
            "QR code",
            "keex.ai/flashlights",
        ],
    }
    context = Quartz.CGPDFContextCreateWithURL(output_url, media_box, metadata)
    if context is None:
        raise RuntimeError(f"Could not create {OUTPUT}")

    Quartz.CGPDFContextBeginPage(context, None)
    Quartz.CGContextSetTextMatrix(context, Quartz.CGAffineTransformIdentity)
    Quartz.CGContextSetFillColorWithColor(context, WHITE)
    Quartz.CGContextFillRect(context, media_box)

    # Running furniture follows the current score's restrained Garamond style.
    draw_centered(context, "Flashlights in the Dark", 758, REGULAR, 10.0)
    draw_text(context, "11", 550, 758, REGULAR, 10.0)
    draw_rule(context, 54, 747, PAGE_WIDTH - 62)

    draw_centered(context, "PERFORMER RESOURCES", 712, BOLD, 18.0, INK, 0.55)
    draw_centered(context, "Electronics, rehearsal support, and permanent links", 690, ITALIC, 10.6, QUIET)

    draw_section_label(context, "PERMANENT ONLINE HOME", 54, 659)
    draw_text(context, "simphoni.ai/flashlights", 54, 635, BOLD, 15.5)
    draw_wrapped(
        context,
        "This is the permanent home for Flashlights in the Dark and the public starting point for its ever-evolving singer resources. The short address keex.ai/flashlights opens the same hub.",
        54,
        617,
        PAGE_WIDTH - 116,
        size=9.0,
        leading=11.0,
        color=QUIET,
    )
    draw_rule(context, 54, 581, PAGE_WIDTH - 62)

    left_x = 54.0
    left_width = 302.0
    right_x = 382.0
    right_width = 168.0

    draw_section_label(context, "THE ELECTRONICS, IN BRIEF", left_x, 557)
    draw_wrapped(
        context,
        "Flashlights in the Dark is an electro-acoustic work for choir, assigned singer smartphones, and a Mac-based conductor console. During performance, all devices join a dedicated, closed Wi-Fi network. The console sends low-latency OSC cues that route synchronized audio and flashlight sequences to each singer's assigned device. Internet access is not part of the live control path.",
        left_x,
        537,
        left_width,
        size=8.9,
        leading=10.8,
    )

    draw_section_label(context, "LEARNING THE PIECE", left_x, 448)
    draw_wrapped(
        context,
        "The hub provides part-by-part practice audio, mixer controls, score and production materials, setup help, and current rehearsal notes. The client also includes Trigger Practice for previewing the audio and lighting assigned to your seat. Use headphones for individual audio practice.",
        left_x,
        428,
        left_width,
        size=8.9,
        leading=10.8,
    )

    draw_section_label(context, "BEFORE REHEARSAL OR PERFORMANCE", right_x, 557)
    draw_bullets(
        context,
        [
            "Install or update the current client before rehearsal.",
            "Fully charge the device and bring its charging cable.",
            "Allow Camera and Local Network access. No microphone or Bluetooth pairing is needed.",
            "Join the production Wi-Fi, select your assigned seat or slot, and keep the app open in the foreground.",
            "Production verifies every device before cues are armed.",
        ],
        right_x,
        537,
        right_width,
    )

    # Accessible production note.
    Quartz.CGContextSetFillColorWithColor(context, PALE)
    Quartz.CGContextFillRect(context, Quartz.CGRectMake(54, 350, PAGE_WIDTH - 116, 42))
    draw_section_label(context, "LIGHTING ADVISORY", 66, 373)
    draw_text(
        context,
        "Bright, rapidly changing phone-light sequences are used. Follow production and venue accessibility guidance.",
        179,
        373,
        REGULAR,
        8.2,
        INK,
    )

    draw_section_label(context, "ABOUT THE COMPOSER", 54, 324)
    draw_wrapped(
        context,
        "Jon D. Nelson is a composer, pianist, creative technologist, and educator whose work connects contemporary classical composition with networked performance, electronics, recording, and spatial media. He earned composition degrees from the Royal College of Music and Ball State University and is Founder & Creative Technologist for KEEx.AI / Simphoni, developing human-directed creative technologies centered on artistic judgment and agency.",
        54,
        304,
        PAGE_WIDTH - 116,
        size=8.7,
        leading=10.5,
    )
    draw_text(context, "jondnelson.com", 54, 253, BOLD, 9.2)
    draw_text(context, "Portfolio and biography", 123, 253, ITALIC, 8.6, QUIET)

    draw_rule(context, 54, 235, PAGE_WIDTH - 62)
    draw_centered(context, "SCAN FROM THIS PRINTED SCORE", 215, BOLD, 8.0, QUIET, 1.05)
    draw_centered(
        context,
        "The permanent KEEx addresses printed below can be retargeted without changing the score.",
        201,
        ITALIC,
        7.7,
        QUIET,
    )

    centers = (132.0, 306.0, 480.0)
    qr_size = 96.0
    qr_y = 84.0
    for center_x, item in zip(centers, QR_CODES):
        draw_centered_in_column = lambda text, y, font, size, color=INK, tracking=0.0: (
            draw_text(
                context,
                text,
                center_x - text_width(text, font, size, tracking) / 2.0,
                y,
                font,
                size,
                color,
                tracking,
            )
        )
        draw_centered_in_column(item["label"], 188, BOLD, 7.8, QUIET, 0.75)
        draw_qr(context, item["url"], center_x - qr_size / 2.0, qr_y, qr_size)
        draw_centered_in_column(item["display"], 72, BOLD, 7.2)
        draw_centered_in_column(item["note"], 60, ITALIC, 7.3, QUIET)

    draw_centered(context, "(c) 2025 Jon D. Nelson", 30, REGULAR, 8.0, QUIET)

    Quartz.CGPDFContextEndPage(context)
    Quartz.CGPDFContextClose(context)
    return OUTPUT


if __name__ == "__main__":
    print(build())
