#!/usr/bin/env python3
"""Build the Fall 2026 24-system / 12-page two-system casting source.

The immediate input is the provenance-validated 40-page cast.  This generator
strips its casting metadata and applies a compact 24-system map with exactly
two systems on each of 12 nonblank music pages.  It never edits a Dorico
project, PDF, show-control file, or runtime asset.

The output is accepted only when a MusicXML round trip preserves the complete
non-casting tree plus the canonical six-part/151-measure musical and lyric
semantics.  Collision clearance is deliberately a separate Dorico visual-QA
gate; source-side validation cannot prove it.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import apply_fall2026_40page_casting as profile40


base = profile40.base
profile32 = profile40.profile32
profile24 = profile40.profile24
ROOT = Path(__file__).resolve().parents[2]
PROVENANCE = ROOT / "Engraving/Scores/Fall2026-Provenance"

DEFAULT_SOURCE = (
    PROVENANCE / "FlashlightsInTheDark_Fall2026_Dorico40PageCasted.musicxml"
)
DEFAULT_OUTPUT = (
    PROVENANCE / "FlashlightsInTheDark_Fall2026_Dorico24System12PageCasted.musicxml"
)
DEFAULT_REPORT = (
    PROVENANCE / "FlashlightsInTheDark_Fall2026_24System12PageCastingReport.json"
)
DEFAULT_VALIDATION_REPORT = (
    PROVENANCE
    / "FlashlightsInTheDark_Fall2026_24System12PageSemanticValidation.json"
)
SOURCE_CASTING_REPORT = (
    PROVENANCE / "FlashlightsInTheDark_Fall2026_40PageCastingReport.json"
)
SOURCE_VALIDATION_REPORT = (
    PROVENANCE / "FlashlightsInTheDark_Fall2026_40PageSemanticValidation.json"
)
CAST_PLAN = PROVENANCE / "FALL_2026_24_SYSTEM_12_PAGE_CASTING_PLAN.md"

EXPECTED_SOURCE_SHA256 = (
    "13100f95f471ef52e23bee1db91784cb2d6a5794e88f73c5a621fd964bb65827"
)
EXPECTED_SOURCE_CASTING_REPORT_SHA256 = (
    "0204c63c3329058aa6c857a89766d470cc09fc72c6b46fbe4121e8637f167ebc"
)
EXPECTED_SOURCE_VALIDATION_REPORT_SHA256 = (
    "c7a048d79980e48b2dfaf0603bca8f55a7e01227e85d2b5c95194318a5464a9b"
)
EXPECTED_NONCASTING_HASH = (
    "852a7222fdb31cd21eb2f1056e529f8b944734599eeba821438fa55569be78b4"
)
EXPECTED_NOTE_COUNT = 2787
EXPECTED_FALL_REPLACEMENTS = 388
MUSIC_PAGES = 12
BOOKLET_TARGET_PAGES = 12
EXPECTED_SYSTEMS = 24
SYSTEMS_PER_PAGE = 2

# Exact map frozen by the independent compact-cast audit.  The fixed opening
# retains m.1-3 / m.4-6; all later pairs balance horizontal density against
# the physical-turn spine at m.6, 22, 45, 70, 103, and 129.
CASTING: tuple[tuple[tuple[int, int], ...], ...] = (
    ((1, 3), (4, 6)),
    ((7, 10), (11, 13)),
    ((14, 16), (17, 22)),
    ((23, 28), (29, 36)),
    ((37, 40), (41, 45)),
    ((46, 52), (53, 57)),
    ((58, 65), (66, 70)),
    ((71, 80), (81, 92)),
    ((93, 98), (99, 103)),
    ((104, 109), (110, 114)),
    ((115, 121), (122, 129)),
    ((130, 139), (140, 151)),
)

VISUAL_QA_INSTRUCTION = (
    "Import into a separate Dorico project, apply the approved compact global "
    "staff-size and vertical-spacing settings, then render all 12 pages at "
    "print resolution. Reject any collision, clipped object, unstable lyric "
    "lane, overlapping system, or unreadable dense passage."
)


def display_path(path: Path) -> str:
    return profile40.display_path(path)


def load_json(path: Path) -> dict[str, object]:
    return profile40.load_json(path)


def expected_page_starts() -> tuple[int, ...]:
    return tuple(page[0][0] for page in CASTING[1:])


def expected_system_starts() -> tuple[int, ...]:
    return tuple(page[1][0] for page in CASTING)


def validate_profile() -> None:
    if not CASTING:
        raise ValueError("The approved 24-system casting map has not been installed")

    base.CASTING = CASTING
    base.validate_casting_definition()

    if len(CASTING) != MUSIC_PAGES:
        raise ValueError(f"Expected {MUSIC_PAGES} pages, found {len(CASTING)}")
    if sum(len(page) for page in CASTING) != EXPECTED_SYSTEMS:
        raise ValueError(f"Expected {EXPECTED_SYSTEMS} systems")
    if any(len(page) != SYSTEMS_PER_PAGE for page in CASTING):
        raise ValueError("Every page must contain exactly two systems")
    if CASTING[0] != ((1, 3), (4, 6)):
        raise ValueError("Page 1 must remain exactly m.1-3 / m.4-6")

    wanted = base.expected_break_map()
    page_starts = tuple(k for k, v in wanted.items() if v == "new-page")
    system_starts = tuple(k for k, v in wanted.items() if v == "new-system")
    if page_starts != expected_page_starts():
        raise ValueError(f"Unexpected page starts: {page_starts}")
    if system_starts != expected_system_starts():
        raise ValueError(f"Unexpected system starts: {system_starts}")
    if len(page_starts) != MUSIC_PAGES - 1:
        raise ValueError("A 12-page profile must contain 11 page starts")
    if len(system_starts) != MUSIC_PAGES:
        raise ValueError("Every page must contain one second-system start")


def verify_source_provenance(source: Path) -> dict[str, object]:
    source_hash = base.sha256(source)
    validation = load_json(SOURCE_VALIDATION_REPORT)
    casting = load_json(SOURCE_CASTING_REPORT)

    exact = validation.get("exact_checks", {})
    hashes = validation.get("hashes", {})
    score = validation.get("score_validation", {})
    upstream = validation.get("source_provenance", {})
    source_cast = casting.get("casting", {})
    layout = casting.get("layout_only_equivalence", {})
    checks = {
        "default_40_page_source": source.resolve() == DEFAULT_SOURCE.resolve(),
        "source_sha256_expected": source_hash == EXPECTED_SOURCE_SHA256,
        "source_casting_report_sha256_expected": (
            base.sha256(SOURCE_CASTING_REPORT)
            == EXPECTED_SOURCE_CASTING_REPORT_SHA256
        ),
        "source_validation_report_sha256_expected": (
            base.sha256(SOURCE_VALIDATION_REPORT)
            == EXPECTED_SOURCE_VALIDATION_REPORT_SHA256
        ),
        "casting_report_output_matches_source": (
            casting.get("output_sha256") == source_hash
        ),
        "validation_report_output_matches_source": (
            validation.get("output_sha256") == source_hash
        ),
        "source_reports_passed": (
            casting.get("semantic_validation_passed") is True
            and validation.get("passed") is True
        ),
        "all_source_exact_checks_passed": (
            isinstance(exact, dict)
            and bool(exact)
            and all(value is True for value in exact.values())
        ),
        "source_40_page_cast_shape_verified": (
            isinstance(source_cast, dict)
            and source_cast.get("music_pages") == 39
            and source_cast.get("systems") == 42
            and source_cast.get("booklet_target_pages") == 40
        ),
        "stage_e_chain_and_replacements_verified": (
            isinstance(upstream, dict)
            and upstream.get("verified") is True
            and upstream.get("fall_replacements") == EXPECTED_FALL_REPLACEMENTS
        ),
        "canonical_fingerprint_verified": (
            isinstance(score, dict)
            and score.get("structure_fingerprint")
            == base.EXPECTED_STRUCTURE_FINGERPRINT
        ),
        "source_noncasting_hash_verified": (
            isinstance(hashes, dict)
            and hashes.get("full_noncasting_tree") == EXPECTED_NONCASTING_HASH
            and isinstance(layout, dict)
            and layout.get("passed") is True
            and layout.get("output_noncasting_tree_sha256")
            == EXPECTED_NONCASTING_HASH
        ),
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise ValueError(f"40-page source provenance failed: {failed}")

    return {
        "verified": True,
        "source_sha256": source_hash,
        "source_casting_report": display_path(SOURCE_CASTING_REPORT),
        "source_casting_report_sha256": base.sha256(SOURCE_CASTING_REPORT),
        "source_validation_report": display_path(SOURCE_VALIDATION_REPORT),
        "source_validation_report_sha256": base.sha256(SOURCE_VALIDATION_REPORT),
        "stage_e_report": upstream.get("stage_e_report"),
        "fall_replacements": EXPECTED_FALL_REPLACEMENTS,
        "checks": checks,
    }


def semantic_snapshot(root: ET.Element) -> dict[str, object]:
    return profile40.semantic_snapshot(root)


def build(
    source_path: Path,
    output_path: Path,
    report_path: Path,
    validation_path: Path,
    *,
    force: bool = False,
) -> dict[str, object]:
    if source_path.resolve() == output_path.resolve():
        raise ValueError("Source and output must be different files")
    base.refuse_overwrite([output_path, report_path, validation_path], force)
    validate_profile()
    if not CAST_PLAN.exists() or not CAST_PLAN.stat().st_size:
        raise ValueError("The 24-system / 12-page cast plan is missing or empty")

    tree = ET.parse(source_path)
    root = tree.getroot()
    source_hash = base.sha256(source_path)
    provenance = verify_source_provenance(source_path)
    before = semantic_snapshot(root)
    if before["noncasting_hash"] != EXPECTED_NONCASTING_HASH:
        raise ValueError("Source does not match the validated non-casting tree")
    if not profile32.verify_page_furniture_metadata(root):
        raise ValueError("Validated page-furniture metadata is missing")

    removed_break_flags = base.remove_break_flags(root)
    removed_print_nodes = profile24.remove_empty_print_nodes(root)
    replaced_supports = base.configure_break_supports(root)
    base.apply_casting(root)
    applied_breaks = base.validate_applied_breaks(root)

    after = semantic_snapshot(root)
    if after != before:
        changed = [key for key in before if before[key] != after[key]]
        raise ValueError(f"Casting changed non-layout content: {changed}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    validation_path.parent.mkdir(parents=True, exist_ok=True)
    base.write_musicxml(tree, output_path)

    reparsed_root = ET.parse(output_path).getroot()
    reparsed = semantic_snapshot(reparsed_root)
    reparsed_breaks = base.validate_applied_breaks(reparsed_root)
    exact_checks = {
        "source_40_page_provenance_verified": provenance["verified"],
        "six_parts_151_measures": (
            reparsed["score"].get("part_ids") == list(base.EXPECTED_PART_IDS)
            and all(
                value == base.EXPECTED_MEASURES_PER_PART
                for value in reparsed["score"].get("measure_counts", {}).values()
            )
        ),
        "note_count_2787": (
            reparsed["score"].get("note_count") == EXPECTED_NOTE_COUNT
        ),
        "lyric_anchors_1376": (
            reparsed["score"].get("lyric_anchors") == base.EXPECTED_LYRIC_ANCHORS
        ),
        "canonical_musical_fingerprint": (
            reparsed["score"].get("structure_fingerprint")
            == base.EXPECTED_STRUCTURE_FINGERPRINT
        ),
        "all_388_fall_replacements_preserved": (
            provenance.get("fall_replacements") == EXPECTED_FALL_REPLACEMENTS
            and reparsed["lyrics"] == before["lyrics"]
        ),
        "lyrics_text_attributes_and_routing_exact": (
            reparsed["lyrics"] == before["lyrics"]
        ),
        "five_line_staff_states_exact": (
            reparsed["staff_rows"] == before["staff_rows"]
        ),
        "dynamics_exact": reparsed["dynamics"] == before["dynamics"],
        "harmonies_exact": reparsed["harmonies"] == before["harmonies"],
        "directions_exact": reparsed["directions"] == before["directions"],
        "page_furniture_metadata_exact": (
            profile32.verify_page_furniture_metadata(reparsed_root)
        ),
        "casting_breaks_exact": reparsed_breaks == applied_breaks,
        "page_break_starts_exact": (
            tuple(reparsed_breaks["page_break_starts"])
            == expected_page_starts()
        ),
        "system_break_starts_exact": (
            tuple(reparsed_breaks["system_break_starts"])
            == expected_system_starts()
        ),
        "page_1_exact_m1_3_m4_6": CASTING[0] == ((1, 3), (4, 6)),
        "twelve_music_pages_exact": len(CASTING) == MUSIC_PAGES,
        "two_systems_on_every_page": all(
            len(page) == SYSTEMS_PER_PAGE for page in CASTING
        ),
        "twenty_four_systems_exact": (
            sum(len(page) for page in CASTING) == EXPECTED_SYSTEMS
        ),
        "no_blank_page_ranges": all(
            all(start <= end for start, end in page) for page in CASTING
        ),
        "booklet_count_divisible_by_four": BOOKLET_TARGET_PAGES % 4 == 0,
        "full_layout_only_equivalence": (
            reparsed["noncasting_hash"]
            == before["noncasting_hash"]
            == EXPECTED_NONCASTING_HASH
        ),
    }
    passed = all(exact_checks.values())
    if not passed:
        failed = [key for key, value in exact_checks.items() if not value]
        raise ValueError(f"Round-trip semantic validation failed: {failed}")

    lengths = [end - start + 1 for page in CASTING for start, end in page]
    casting = {
        "music_pages": MUSIC_PAGES,
        "booklet_target_pages": BOOKLET_TARGET_PAGES,
        "colophon_page": None,
        "systems": EXPECTED_SYSTEMS,
        "systems_per_page": SYSTEMS_PER_PAGE,
        "every_page_has_exactly_two_systems": True,
        "page_1_systems": ["1-3", "4-6"],
        "all_pages_contain_music": True,
        "blank_pages": [],
        "system_measure_lengths": lengths,
        "minimum_system_measures": min(lengths),
        "maximum_system_measures": max(lengths),
        "pages": [[f"{a}-{b}" for a, b in page] for page in CASTING],
        **reparsed_breaks,
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
    change_boundary = {
        "break_attributes_only": True,
        "removed_prior_break_attributes": removed_break_flags,
        "removed_empty_break_print_nodes": removed_print_nodes,
        "replaced_break_support_entries": replaced_supports,
        "unlogged_textual_differences": 0,
        "live_dorico_project_changed": False,
        "engraving_scale_changed": False,
        "pdf_changed": False,
        "runtime_assets_changed": False,
    }
    visual_qa = {
        "status": "pending_dorico_import_and_full_page_render",
        "collision_clearance_verified": False,
        "instruction": VISUAL_QA_INSTRUCTION,
    }
    output_hash = base.sha256(output_path)
    validation_report = {
        "profile": "Fall 2026 24-system / 12-page two-system performer score",
        "source": display_path(source_path),
        "output": display_path(output_path),
        "source_sha256": source_hash,
        "output_sha256": output_hash,
        "passed": passed,
        "source_provenance": provenance,
        "score_validation": reparsed["score"],
        "exact_checks": exact_checks,
        "hashes": hashes,
        "authorized_change_boundary": change_boundary,
        "casting": casting,
        "visual_qa": visual_qa,
    }
    validation_path.write_text(
        json.dumps(validation_report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    report = {
        "profile": "Fall 2026 24-system / 12-page two-system performer score",
        "source": display_path(source_path),
        "output": display_path(output_path),
        "semantic_validation_report": display_path(validation_path),
        "source_sha256": source_hash,
        "output_sha256": output_hash,
        "casting_plan": {
            "path": display_path(CAST_PLAN),
            "sha256": base.sha256(CAST_PLAN),
        },
        "source_provenance": provenance,
        "score_validation": reparsed["score"],
        "semantic_validation_passed": passed,
        "layout_only_equivalence": {
            "passed": exact_checks["full_layout_only_equivalence"],
            "source_noncasting_tree_sha256": before["noncasting_hash"],
            "output_noncasting_tree_sha256": reparsed["noncasting_hash"],
        },
        "authorized_change_boundary": change_boundary,
        "casting": casting,
        "visual_qa": visual_qa,
    }
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build the separate 24-system / 12-page Fall 2026 cast with "
            "exactly two systems on every page."
        ),
        epilog=VISUAL_QA_INSTRUCTION,
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
        help="Allow replacement of this profile's own generated artifacts only.",
    )
    args = parser.parse_args()
    report = build(
        args.source,
        args.output,
        args.report,
        args.validation_report,
        force=args.force,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
