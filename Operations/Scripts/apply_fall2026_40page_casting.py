#!/usr/bin/env python3
"""Build the Fall 2026 40-page publication casting source.

The source is the provenance-validated 32-page MusicXML.  This generator
changes only MusicXML casting metadata: page/system break attributes, the
empty ``print`` shells left by the old cast, and the corresponding MusicXML
``supports`` declarations.  Music occupies pages 1-39; the existing nonblank
colophon supplies page 40.

Every musical, textual, lyric-routing, staff-line, and notation object is
round-trip checked against the input.  A canonical non-casting tree hash
proves layout-only equivalence after the new break map is applied.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import apply_fall2026_32page_casting as profile32


base = profile32.base
profile24 = profile32.profile24
ROOT = Path(__file__).resolve().parents[2]
PROVENANCE = ROOT / "Engraving/Scores/Fall2026-Provenance"

DEFAULT_SOURCE = (
    PROVENANCE / "FlashlightsInTheDark_Fall2026_Dorico32PageCasted.musicxml"
)
DEFAULT_OUTPUT = (
    PROVENANCE / "FlashlightsInTheDark_Fall2026_Dorico40PageCasted.musicxml"
)
DEFAULT_REPORT = (
    PROVENANCE / "FlashlightsInTheDark_Fall2026_40PageCastingReport.json"
)
DEFAULT_VALIDATION_REPORT = (
    PROVENANCE / "FlashlightsInTheDark_Fall2026_40PageSemanticValidation.json"
)
SOURCE_VALIDATION_REPORT = (
    PROVENANCE / "FlashlightsInTheDark_Fall2026_32PageSemanticValidation.json"
)
SOURCE_CASTING_REPORT = (
    PROVENANCE / "FlashlightsInTheDark_Fall2026_32PageCastingReport.json"
)
CAST_PLAN = PROVENANCE / "FALL_2026_40_PAGE_PUBLICATION_CAST.md"
COLOPHON = PROVENANCE / "FlashlightsInTheDark_Fall2026_Page40_Colophon.pdf"

EXPECTED_SOURCE_SHA256 = (
    "28eaade134594b196efd38d1d1f5a40504ba12176aaa373046ee6e0a3567b844"
)
EXPECTED_NONCASTING_HASH = (
    "852a7222fdb31cd21eb2f1056e529f8b944734599eeba821438fa55569be78b4"
)
EXPECTED_NOTE_COUNT = 2787
EXPECTED_FALL_REPLACEMENTS = 388
BOOKLET_TARGET_PAGES = 40
MUSIC_PAGES = 39
COLOPHON_PAGE = 40
EXPECTED_SYSTEMS = 42
EXPECTED_TWO_SYSTEM_PAGES = (1, 2, 31)
EXPECTED_SYSTEM_ONLY_STARTS = (4, 9, 113)
EXPECTED_PAGE_STARTS = (
    7,
    11,
    13,
    15,
    17,
    21,
    23,
    26,
    32,
    37,
    40,
    43,
    46,
    50,
    53,
    57,
    62,
    67,
    71,
    74,
    77,
    81,
    84,
    93,
    97,
    101,
    104,
    106,
    108,
    110,
    115,
    119,
    122,
    125,
    130,
    135,
    140,
    146,
)

# Exact 42-system / 39-music-page map approved in the publication cast plan.
# Pages 1, 2, and 31 carry two systems; all other music pages carry one.
CASTING: tuple[tuple[tuple[int, int], ...], ...] = (
    ((1, 3), (4, 6)),
    ((7, 8), (9, 10)),
    ((11, 12),),
    ((13, 14),),
    ((15, 16),),
    ((17, 20),),
    ((21, 22),),
    ((23, 25),),
    ((26, 31),),
    ((32, 36),),
    ((37, 39),),
    ((40, 42),),
    ((43, 45),),
    ((46, 49),),
    ((50, 52),),
    ((53, 56),),
    ((57, 61),),
    ((62, 66),),
    ((67, 70),),
    ((71, 73),),
    ((74, 76),),
    ((77, 80),),
    ((81, 83),),
    ((84, 92),),
    ((93, 96),),
    ((97, 100),),
    ((101, 103),),
    ((104, 105),),
    ((106, 107),),
    ((108, 109),),
    ((110, 112), (113, 114)),
    ((115, 118),),
    ((119, 121),),
    ((122, 124),),
    ((125, 129),),
    ((130, 134),),
    ((135, 139),),
    ((140, 145),),
    ((146, 151),),
)

COLOPHON_INSTRUCTION = (
    "Append the existing nonblank page-40 colophon only after all 39 Dorico "
    "music pages pass visual review. Do not synthesize a blank MusicXML page."
)


def display_path(path: Path) -> str:
    return profile32.display_path(path)


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        raise ValueError(f"Required provenance report is missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def validate_profile() -> None:
    # The shared helpers intentionally read their module-level CASTING profile.
    base.CASTING = CASTING
    base.validate_casting_definition()

    if len(CASTING) != MUSIC_PAGES:
        raise ValueError(f"Expected {MUSIC_PAGES} music pages, found {len(CASTING)}")
    if sum(len(page) for page in CASTING) != EXPECTED_SYSTEMS:
        raise ValueError(f"Expected {EXPECTED_SYSTEMS} systems")

    paired_pages = tuple(
        page_number
        for page_number, page in enumerate(CASTING, start=1)
        if len(page) == 2
    )
    if paired_pages != EXPECTED_TWO_SYSTEM_PAGES:
        raise ValueError(
            f"Expected paired pages {EXPECTED_TWO_SYSTEM_PAGES}, found {paired_pages}"
        )

    wanted = base.expected_break_map()
    page_starts = tuple(
        measure for measure, kind in wanted.items() if kind == "new-page"
    )
    system_starts = tuple(
        measure for measure, kind in wanted.items() if kind == "new-system"
    )
    if page_starts != EXPECTED_PAGE_STARTS:
        raise ValueError(f"Unexpected frame/page starts: {page_starts}")
    if system_starts != EXPECTED_SYSTEM_ONLY_STARTS:
        raise ValueError(f"Unexpected system-only starts: {system_starts}")

    for page_number, page in enumerate(CASTING, start=1):
        for start, end in page:
            length = end - start + 1
            if length > 10:
                raise ValueError(
                    f"Page {page_number} system {start}-{end} exceeds ten measures"
                )
            if length > 7 and (start, end) != (84, 92):
                raise ValueError(
                    f"Only sparse m.84-92 may exceed seven measures: {start}-{end}"
                )


def verify_source_provenance(source: Path) -> dict[str, object]:
    source_hash = base.sha256(source)
    validation = load_json(SOURCE_VALIDATION_REPORT)
    casting = load_json(SOURCE_CASTING_REPORT)

    validation_checks = validation.get("exact_checks", {})
    source_provenance = validation.get("source_provenance", {})
    score_validation = validation.get("score_validation", {})
    hashes = validation.get("hashes", {})
    verification = {
        "default_32_page_source": source.resolve() == DEFAULT_SOURCE.resolve(),
        "source_sha256_expected": source_hash == EXPECTED_SOURCE_SHA256,
        "validation_output_sha256_matches": (
            validation.get("output_sha256") == source_hash
        ),
        "casting_report_output_sha256_matches": (
            casting.get("output_sha256") == source_hash
        ),
        "source_validation_passed": validation.get("passed") is True,
        "all_source_exact_checks_passed": (
            isinstance(validation_checks, dict)
            and bool(validation_checks)
            and all(value is True for value in validation_checks.values())
        ),
        "stage_e_provenance_verified": (
            isinstance(source_provenance, dict)
            and source_provenance.get("verified") is True
            and source_provenance.get("stage") == "E"
        ),
        "all_388_fall_replacements_verified": (
            isinstance(source_provenance, dict)
            and source_provenance.get("fall_replacements")
            == EXPECTED_FALL_REPLACEMENTS
        ),
        "canonical_fingerprint_verified": (
            isinstance(score_validation, dict)
            and score_validation.get("structure_fingerprint")
            == base.EXPECTED_STRUCTURE_FINGERPRINT
        ),
        "source_noncasting_hash_verified": (
            isinstance(hashes, dict)
            and hashes.get("full_noncasting_tree_after_approved_normalizations")
            == EXPECTED_NONCASTING_HASH
        ),
    }
    if not all(verification.values()):
        failed = [name for name, passed in verification.items() if not passed]
        raise ValueError(f"32-page source provenance failed: {failed}")

    return {
        "verified": True,
        "source_sha256": source_hash,
        "expected_source_sha256": EXPECTED_SOURCE_SHA256,
        "source_validation_report": display_path(SOURCE_VALIDATION_REPORT),
        "source_validation_report_sha256": base.sha256(SOURCE_VALIDATION_REPORT),
        "source_casting_report": display_path(SOURCE_CASTING_REPORT),
        "source_casting_report_sha256": base.sha256(SOURCE_CASTING_REPORT),
        "stage_e_report": source_provenance.get("report"),
        "fall_replacements": EXPECTED_FALL_REPLACEMENTS,
        "verification": verification,
    }


def semantic_snapshot(root: ET.Element) -> dict[str, object]:
    score = profile24.validate_extended_score_shape(root)
    lyrics = profile24.lyric_semantic_rows(root)
    staff_rows = profile24.five_line_staff_rows(root)
    dynamics = profile32.contextual_rows(root, "dynamics")
    harmonies = profile32.top_level_rows(root, "harmony")
    directions = profile32.top_level_rows(root, "direction")
    source_report_directions = profile32.direction_rows_except_correction(root)
    return {
        "score": score,
        "lyrics": lyrics,
        "staff_rows": staff_rows,
        "dynamics": dynamics,
        "harmonies": harmonies,
        "directions": directions,
        "source_report_directions": source_report_directions,
        "noncasting_hash": profile32.noncasting_tree_hash(root),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build the separate 39-music-page Fall 2026 publication cast and "
            "reserve page 40 for the existing nonblank colophon."
        ),
        epilog=COLOPHON_INSTRUCTION,
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--validation-report", type=Path, default=DEFAULT_VALIDATION_REPORT
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow replacement of this 40-page profile's own artifacts only.",
    )
    args = parser.parse_args()

    if args.source.resolve() == args.output.resolve():
        raise ValueError("Source and output must be different files")
    base.refuse_overwrite(
        [args.output, args.report, args.validation_report], args.force
    )
    validate_profile()

    tree = ET.parse(args.source)
    root = tree.getroot()
    source_hash = base.sha256(args.source)
    source_provenance = verify_source_provenance(args.source)
    source = semantic_snapshot(root)
    if source["noncasting_hash"] != EXPECTED_NONCASTING_HASH:
        raise ValueError("Parsed source does not match the validated non-casting tree")
    if not profile32.verify_page_furniture_metadata(root):
        raise ValueError("Validated page-furniture metadata is missing")

    removed_break_flags = base.remove_break_flags(root)
    removed_empty_print_nodes = profile24.remove_empty_print_nodes(root)
    supports_removed = base.configure_break_supports(root)
    base.apply_casting(root)
    break_state = base.validate_applied_breaks(root)

    output = semantic_snapshot(root)
    if output != source:
        failed = [name for name in source if output[name] != source[name]]
        raise ValueError(f"Casting changed non-layout content: {failed}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.validation_report.parent.mkdir(parents=True, exist_ok=True)
    base.write_musicxml(tree, args.output)

    reparsed_root = ET.parse(args.output).getroot()
    reparsed = semantic_snapshot(reparsed_root)
    reparsed_break_state = base.validate_applied_breaks(reparsed_root)

    exact_checks = {
        "source_32_page_provenance_verified": source_provenance["verified"],
        "six_parts_151_measures": (
            reparsed["score"].get("part_ids") == list(base.EXPECTED_PART_IDS)
            and all(
                count == base.EXPECTED_MEASURES_PER_PART
                for count in reparsed["score"].get("measure_counts", {}).values()
            )
        ),
        "note_count_2787": (
            reparsed["score"].get("note_count") == EXPECTED_NOTE_COUNT
        ),
        "lyric_anchors_1376": (
            reparsed["score"].get("lyric_anchors")
            == base.EXPECTED_LYRIC_ANCHORS
        ),
        "canonical_musical_fingerprint": (
            reparsed["score"].get("structure_fingerprint")
            == base.EXPECTED_STRUCTURE_FINGERPRINT
        ),
        "all_388_fall_replacements_preserved": (
            source_provenance.get("fall_replacements")
            == EXPECTED_FALL_REPLACEMENTS
            and reparsed["lyrics"] == source["lyrics"]
        ),
        "lyrics_text_attributes_and_routing_exact": (
            reparsed["lyrics"] == source["lyrics"]
        ),
        "five_line_staff_states_exact": (
            reparsed["staff_rows"] == source["staff_rows"]
        ),
        "dynamics_exact": reparsed["dynamics"] == source["dynamics"],
        "harmonies_exact": reparsed["harmonies"] == source["harmonies"],
        "directions_exact": reparsed["directions"] == source["directions"],
        "page_furniture_metadata_exact": (
            profile32.verify_page_furniture_metadata(reparsed_root)
        ),
        "casting_breaks_exact": reparsed_break_state == break_state,
        "system_only_starts_exact": (
            tuple(reparsed_break_state["system_break_starts"])
            == EXPECTED_SYSTEM_ONLY_STARTS
        ),
        "frame_page_starts_exact": (
            tuple(reparsed_break_state["page_break_starts"])
            == EXPECTED_PAGE_STARTS
        ),
        "full_layout_only_equivalence": (
            reparsed["noncasting_hash"]
            == source["noncasting_hash"]
            == EXPECTED_NONCASTING_HASH
        ),
    }
    passed = all(exact_checks.values())
    if not passed:
        failed = [name for name, value in exact_checks.items() if not value]
        raise ValueError(f"Round-trip semantic validation failed: {failed}")

    paired_pages = [
        page_number
        for page_number, page in enumerate(CASTING, start=1)
        if len(page) == 2
    ]
    single_system_pages = [
        page_number
        for page_number, page in enumerate(CASTING, start=1)
        if len(page) == 1
    ]
    lengths = [end - start + 1 for page in CASTING for start, end in page]

    if not CAST_PLAN.exists() or not CAST_PLAN.stat().st_size:
        raise ValueError("The 40-page publication cast plan is missing or empty")
    if not COLOPHON.exists() or not COLOPHON.stat().st_size:
        raise ValueError("The page-40 colophon is missing or empty")

    casting_state = {
        "music_pages": MUSIC_PAGES,
        "booklet_target_pages": BOOKLET_TARGET_PAGES,
        "colophon_page": COLOPHON_PAGE,
        "systems": EXPECTED_SYSTEMS,
        "paired_pages": paired_pages,
        "single_system_pages": single_system_pages,
        "page_1_has_exactly_two_systems": len(CASTING[0]) == 2,
        "system_measure_lengths": lengths,
        "minimum_system_measures": min(lengths),
        "maximum_system_measures": max(lengths),
        "only_over_seven_system": "84-92 (m.84-88 tacet)",
        "pages": [
            [f"{start}-{end}" for start, end in page] for page in CASTING
        ],
        **reparsed_break_state,
    }
    hashes = {
        "canonical_structure": reparsed["score"]["structure_fingerprint"],
        "lyrics_and_routing": profile32.rows_hash(reparsed["lyrics"]),
        "five_line_staff_states": profile32.rows_hash(reparsed["staff_rows"]),
        "dynamics": profile32.rows_hash(reparsed["dynamics"]),
        "harmonies": profile32.rows_hash(reparsed["harmonies"]),
        "directions": profile32.rows_hash(reparsed["directions"]),
        "full_noncasting_tree": reparsed["noncasting_hash"],
    }
    colophon_state = {
        "path": display_path(COLOPHON),
        "exists": True,
        "sha256": base.sha256(COLOPHON),
        "bytes": COLOPHON.stat().st_size,
        "page": COLOPHON_PAGE,
        "must_be_nonblank": True,
        "musicxml_credit_added": False,
        "pdf_appended_or_modified": False,
        "instruction": COLOPHON_INSTRUCTION,
    }

    output_hash = base.sha256(args.output)
    validation_report = {
        "profile": "Fall 2026 40-page saddle-stitch performer score",
        "source": display_path(args.source),
        "output": display_path(args.output),
        "source_sha256": source_hash,
        "output_sha256": output_hash,
        "passed": passed,
        "source_provenance": source_provenance,
        "score_validation": reparsed["score"],
        "exact_checks": exact_checks,
        "hashes": hashes,
        "authorized_change_boundary": {
            "break_attributes_only": True,
            "removed_prior_break_attributes": removed_break_flags,
            "removed_empty_break_print_nodes": removed_empty_print_nodes,
            "replaced_break_support_entries": supports_removed,
            "unlogged_textual_differences": 0,
            "runtime_assets_changed": False,
        },
        "casting": casting_state,
    }
    args.validation_report.write_text(
        json.dumps(validation_report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    report = {
        "profile": "Fall 2026 40-page saddle-stitch performer score",
        "source": display_path(args.source),
        "output": display_path(args.output),
        "semantic_validation_report": display_path(args.validation_report),
        "source_sha256": source_hash,
        "output_sha256": output_hash,
        "publication_cast_plan": {
            "path": display_path(CAST_PLAN),
            "sha256": base.sha256(CAST_PLAN),
        },
        "source_provenance": source_provenance,
        "score_validation": reparsed["score"],
        "semantic_validation_passed": passed,
        "layout_only_equivalence": {
            "passed": exact_checks["full_layout_only_equivalence"],
            "source_noncasting_tree_sha256": source["noncasting_hash"],
            "output_noncasting_tree_sha256": reparsed["noncasting_hash"],
        },
        "authorized_change_boundary": validation_report[
            "authorized_change_boundary"
        ],
        "casting": casting_state,
        "colophon": colophon_state,
    }
    args.report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
