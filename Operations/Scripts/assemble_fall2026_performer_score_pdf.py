#!/usr/bin/env python3
"""Assemble the frozen Fall 2026 performer-score PDF booklet.

The assembler accepts exactly 39 unencrypted, unrotated US Letter music pages
and the already validated one-page colophon.  It copies those pages into a new
40-page PDF, verifies the written candidate, and only then installs the PDF and
its JSON audit report.  Input files are opened read-only and are never replaced.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError


ROOT = Path(__file__).resolve().parents[2]
PROVENANCE = ROOT / "Engraving/Scores/Fall2026-Provenance"

DEFAULT_COLOPHON = (
    PROVENANCE / "FlashlightsInTheDark_Fall2026_Page40_Colophon.pdf"
)
DEFAULT_OUTPUT = (
    ROOT
    / "Engraving/Scores/FlashlightsInTheDark_Fall2026_PerformerScore_PrintFinal.pdf"
)
DEFAULT_REPORT = (
    PROVENANCE
    / "FlashlightsInTheDark_Fall2026_FinalPdfAssemblyReport.json"
)

EXPECTED_MUSIC_PAGES = 39
EXPECTED_COLOPHON_PAGES = 1
EXPECTED_OUTPUT_PAGES = 40
EXPECTED_COLOPHON_SHA256 = (
    "b0733166639d6c9f98c292d5bcd04e6be8ae147a017e7fe1593480c151cd2203"
)

LETTER_BOX = (0.0, 0.0, 612.0, 792.0)
GEOMETRY_TOLERANCE_POINTS = 0.1


class AssemblyError(ValueError):
    """Raised when an input or assembled PDF fails a publication safeguard."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _page_content_sha256(page: Any) -> str:
    contents = page.get_contents()
    payload = b"" if contents is None else contents.get_data()
    return hashlib.sha256(payload).hexdigest()


def _box_values(box: Any) -> list[float]:
    return [float(value) for value in box]


def _geometry(page: Any, page_number: int) -> dict[str, Any]:
    media_box = _box_values(page.mediabox)
    crop_box = _box_values(page.cropbox)
    rotation = int(page.rotation or 0)
    user_unit = float(page.get("/UserUnit", 1.0))
    return {
        "page": page_number,
        "media_box_points": media_box,
        "crop_box_points": crop_box,
        "width_points": media_box[2] - media_box[0],
        "height_points": media_box[3] - media_box[1],
        "rotation_degrees": rotation,
        "user_unit": user_unit,
        "content_sha256": _page_content_sha256(page),
    }


def _box_is_letter(box: list[float]) -> bool:
    return all(
        abs(actual - expected) <= GEOMETRY_TOLERANCE_POINTS
        for actual, expected in zip(box, LETTER_BOX, strict=True)
    )


def _audit_pdf(
    path: Path,
    *,
    label: str,
    expected_pages: int,
    expected_sha256: str | None = None,
) -> tuple[PdfReader, dict[str, Any]]:
    if not path.is_file():
        raise AssemblyError(f"{label} PDF does not exist: {path}")
    if path.stat().st_size == 0:
        raise AssemblyError(f"{label} PDF is empty: {path}")

    file_hash = sha256_file(path)
    try:
        reader = PdfReader(str(path), strict=True)
    except (OSError, PdfReadError) as exc:
        raise AssemblyError(f"{label} PDF cannot be read: {exc}") from exc

    if reader.is_encrypted:
        raise AssemblyError(f"{label} PDF is encrypted; encrypted input is refused")

    page_count = len(reader.pages)
    if page_count != expected_pages:
        raise AssemblyError(
            f"{label} PDF must contain exactly {expected_pages} page(s); "
            f"found {page_count}"
        )

    if expected_sha256 is not None and file_hash != expected_sha256:
        raise AssemblyError(
            f"{label} PDF SHA-256 does not match the validated page-40 "
            f"colophon ({file_hash})"
        )

    pages: list[dict[str, Any]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        geometry = _geometry(page, page_number)
        if geometry["rotation_degrees"] != 0:
            raise AssemblyError(
                f"{label} page {page_number} has a nonzero rotation "
                f"({geometry['rotation_degrees']} degrees)"
            )
        if abs(geometry["user_unit"] - 1.0) > 1e-9:
            raise AssemblyError(
                f"{label} page {page_number} has unsupported UserUnit "
                f"{geometry['user_unit']}"
            )
        if not _box_is_letter(geometry["media_box_points"]):
            raise AssemblyError(
                f"{label} page {page_number} MediaBox is not US Letter: "
                f"{geometry['media_box_points']}"
            )
        if not _box_is_letter(geometry["crop_box_points"]):
            raise AssemblyError(
                f"{label} page {page_number} CropBox is not US Letter: "
                f"{geometry['crop_box_points']}"
            )
        pages.append(geometry)

    return reader, {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": file_hash,
        "encrypted": False,
        "page_count": page_count,
        "pages": pages,
    }


def _same_path(left: Path, right: Path) -> bool:
    if left.resolve() == right.resolve():
        return True
    if left.exists() and right.exists():
        return os.path.samefile(left, right)
    return False


def _validate_destinations(
    music_pdf: Path,
    colophon_pdf: Path,
    output_pdf: Path,
    report_json: Path,
    *,
    replace: bool,
) -> None:
    paths = {
        "music input": music_pdf,
        "colophon input": colophon_pdf,
        "output PDF": output_pdf,
        "JSON report": report_json,
    }
    pairs = (
        ("music input", "colophon input"),
        ("music input", "output PDF"),
        ("music input", "JSON report"),
        ("colophon input", "output PDF"),
        ("colophon input", "JSON report"),
        ("output PDF", "JSON report"),
    )
    for left_name, right_name in pairs:
        if _same_path(paths[left_name], paths[right_name]):
            raise AssemblyError(f"{left_name} and {right_name} must be different files")

    if not replace:
        for label, path in (("output PDF", output_pdf), ("JSON report", report_json)):
            if path.exists():
                raise AssemblyError(
                    f"{label} already exists; pass --replace to replace it atomically: "
                    f"{path}"
                )


def _copy_metadata(reader: PdfReader, writer: PdfWriter) -> None:
    metadata = reader.metadata or {}
    retained = {
        str(key): str(value)
        for key, value in metadata.items()
        if isinstance(key, str) and key.startswith("/") and value is not None
    }
    if retained:
        writer.add_metadata(retained)


def _temporary_path(destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
        delete=False,
    )
    path = Path(handle.name)
    handle.close()
    return path


def _write_pdf_candidate(
    music_reader: PdfReader,
    colophon_reader: PdfReader,
    destination: Path,
) -> None:
    writer = PdfWriter()
    _copy_metadata(music_reader, writer)
    for page in music_reader.pages:
        writer.add_page(page)
    writer.add_page(colophon_reader.pages[0])

    with destination.open("wb") as stream:
        writer.write(stream)
        stream.flush()
        os.fsync(stream.fileno())


def _write_json_candidate(payload: dict[str, Any], destination: Path) -> None:
    with destination.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def assemble(
    music_pdf: Path,
    colophon_pdf: Path = DEFAULT_COLOPHON,
    output_pdf: Path = DEFAULT_OUTPUT,
    report_json: Path = DEFAULT_REPORT,
    *,
    replace: bool = False,
    expected_colophon_sha256: str = EXPECTED_COLOPHON_SHA256,
) -> dict[str, Any]:
    """Validate, assemble, verify, and atomically install the final booklet."""

    music_pdf = Path(music_pdf)
    colophon_pdf = Path(colophon_pdf)
    output_pdf = Path(output_pdf)
    report_json = Path(report_json)
    _validate_destinations(
        music_pdf,
        colophon_pdf,
        output_pdf,
        report_json,
        replace=replace,
    )

    music_reader, music_audit = _audit_pdf(
        music_pdf,
        label="music",
        expected_pages=EXPECTED_MUSIC_PAGES,
    )
    colophon_reader, colophon_audit = _audit_pdf(
        colophon_pdf,
        label="colophon",
        expected_pages=EXPECTED_COLOPHON_PAGES,
        expected_sha256=expected_colophon_sha256,
    )

    output_temp = _temporary_path(output_pdf)
    report_temp = _temporary_path(report_json)
    installed_output = False
    try:
        _write_pdf_candidate(music_reader, colophon_reader, output_temp)
        _, output_audit = _audit_pdf(
            output_temp,
            label="assembled output",
            expected_pages=EXPECTED_OUTPUT_PAGES,
        )

        music_hashes = [page["content_sha256"] for page in music_audit["pages"]]
        output_music_hashes = [
            page["content_sha256"]
            for page in output_audit["pages"][:EXPECTED_MUSIC_PAGES]
        ]
        colophon_content_hash = colophon_audit["pages"][0]["content_sha256"]
        output_colophon_hash = output_audit["pages"][-1]["content_sha256"]
        if output_music_hashes != music_hashes:
            raise AssemblyError("assembled output changed one or more music pages")
        if output_colophon_hash != colophon_content_hash:
            raise AssemblyError("assembled page 40 is not the validated colophon page")

        music_after = sha256_file(music_pdf)
        colophon_after = sha256_file(colophon_pdf)
        if music_after != music_audit["sha256"]:
            raise AssemblyError("music input changed during assembly")
        if colophon_after != colophon_audit["sha256"]:
            raise AssemblyError("colophon input changed during assembly")

        output_audit["path"] = str(output_pdf.resolve())
        report = {
            "schema_version": 1,
            "status": "passed",
            "profile": "Fall 2026 40-page saddle-stitch performer score",
            "inputs": {
                "music": {
                    **music_audit,
                    "sha256_after_assembly": music_after,
                    "unchanged": True,
                },
                "page_40_colophon": {
                    **colophon_audit,
                    "sha256_after_assembly": colophon_after,
                    "unchanged": True,
                    "validated_sha256_expected": expected_colophon_sha256,
                },
            },
            "output": output_audit,
            "assembly": {
                "music_pages_copied": EXPECTED_MUSIC_PAGES,
                "colophon_pages_appended": EXPECTED_COLOPHON_PAGES,
                "colophon_output_page": EXPECTED_OUTPUT_PAGES,
                "output_page_count": EXPECTED_OUTPUT_PAGES,
                "booklet_page_count_divisible_by_four": True,
                "music_page_content_hashes_preserved": True,
                "page_40_content_hash_matches_colophon": True,
                "input_files_unchanged": True,
                "pdf_installed_atomically": True,
            },
        }
        _write_json_candidate(report, report_temp)

        if not replace and (output_pdf.exists() or report_json.exists()):
            raise AssemblyError(
                "an output appeared during assembly; refusing to overwrite it"
            )
        os.replace(output_temp, output_pdf)
        installed_output = True
        os.replace(report_temp, report_json)
        return report
    except Exception:
        if installed_output and not report_json.exists():
            output_pdf.unlink(missing_ok=True)
        raise
    finally:
        output_temp.unlink(missing_ok=True)
        report_temp.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Append the validated page-40 colophon to a frozen 39-page Dorico "
            "music PDF after strict Letter/rotation/encryption preflight."
        )
    )
    parser.add_argument("--music-pdf", type=Path, required=True)
    parser.add_argument("--colophon-pdf", type=Path, default=DEFAULT_COLOPHON)
    parser.add_argument("--output-pdf", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Atomically replace existing output/report files; inputs stay read-only.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        report = assemble(
            args.music_pdf,
            args.colophon_pdf,
            args.output_pdf,
            args.report_json,
            replace=args.replace,
        )
    except AssemblyError as exc:
        raise SystemExit(f"PDF assembly refused: {exc}") from exc
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
