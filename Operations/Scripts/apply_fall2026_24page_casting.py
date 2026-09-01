#!/usr/bin/env python3
"""Apply the readability-first Fall 2026 24-page performer-score casting.

The profile reserves pages 1-23 for music and page 24 for a nonblank native
Dorico colophon.  It is deliberately separate from the approved 15-music-page
casting so that the current performer-score MusicXML is never overwritten.

Only MusicXML page/system flags are changed.  All musical events, text,
five-line staff overrides, and lyric-routing metadata are preserved and
round-trip validated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import apply_fall2026_casting_breaks as base


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = (
    ROOT
    / "Engraving/Scores/Fall2026-Provenance/"
    "FlashlightsInTheDark_Fall2026_StageEClean.musicxml"
)
DEFAULT_OUTPUT = (
    ROOT
    / "Engraving/Scores/Fall2026-Provenance/"
    "FlashlightsInTheDark_Fall2026_Dorico24PageCasted.musicxml"
)
DEFAULT_REPORT = (
    ROOT
    / "Engraving/Scores/Fall2026-Provenance/"
    "FlashlightsInTheDark_Fall2026_24PageCastingReport.json"
)
STAGE_E_REPORT = (
    ROOT
    / "Engraving/Scores/Fall2026-Provenance/"
    "FlashlightsInTheDark_Fall2026_StageECleanupReport.json"
)

EXPECTED_NOTE_COUNT = 2787
BOOKLET_TARGET_PAGES = 24
MUSIC_PAGES = 23
COLOPHON_PAGE = 24

# One or two systems per music page.  The first page has exactly two systems.
# The eight-measure m.81-88 system is intentionally allowed because the entire
# musique-concrete passage is tacet and visually sparse.  Every other system is
# two to seven measures long.
CASTING: tuple[tuple[tuple[int, int], ...], ...] = (
    ((1, 6), (7, 10)),
    ((11, 12),),
    ((13, 14), (15, 16)),
    ((17, 20),),
    ((21, 25), (26, 31)),
    ((32, 36),),
    ((37, 39),),
    ((40, 42),),
    ((43, 45),),
    ((46, 52), (53, 56)),
    ((57, 61),),
    ((62, 66),),
    ((67, 70),),
    ((71, 76),),
    ((77, 80), (81, 88)),
    ((89, 92), (93, 97)),
    ((98, 101), (102, 103)),
    ((104, 107),),
    ((108, 112), (113, 114)),
    ((115, 118),),
    ((119, 124), (125, 129)),
    ((130, 134), (135, 139)),
    ((140, 145), (146, 151)),
)

# These assessments combine the Stage D visual audit with musical boundary
# checks in the normalized MusicXML.  Pages 3 and 7 are retained as explicit
# cautions: moving those turns would require re-compressing systems that Stage D
# proved cannot safely coexist on one page.
ODD_PAGE_TURNS: tuple[dict[str, object], ...] = (
    {
        "page": 1,
        "after_measure": 10,
        "rating": "marginal",
        "reason": (
            "The 1-6 / 7-10 split materially balances page 1, but one Light "
            "voice ties across the barline and several voices have no shared "
            "rest before m.11."
        ),
    },
    {
        "page": 3,
        "after_measure": 16,
        "rating": "unsafe-unavoidable",
        "reason": (
            "The text continues 'This | tender world' and one Light voice is "
            "tied across the barline.  Keeping the dense m.10-16 systems apart "
            "prevents the Stage D m.12/13 and m.16/17 collisions."
        ),
    },
    {
        "page": 5,
        "after_measure": 31,
        "rating": "strong",
        "reason": (
            "All parts have at least 4.5 quarter-note beats of turning time at "
            "the clock/Andante reset before m.32."
        ),
    },
    {
        "page": 7,
        "after_measure": 39,
        "rating": "unsafe-unavoidable",
        "reason": (
            "Tenor/Bass L is tied into m.40 and the Shining/bloom texture "
            "continues.  Adjacent two-system pairings in m.32-45 caused literal "
            "staff collisions in Stage D, so this page remains single-system."
        ),
    },
    {
        "page": 9,
        "after_measure": 45,
        "rating": "workable",
        "reason": (
            "No cross-bar ties; most parts have 2.5 or more quarter-note beats "
            "of clearance at the breathing-arc boundary."
        ),
    },
    {
        "page": 11,
        "after_measure": 61,
        "rating": "strong",
        "reason": (
            "Every active part has at least two quarter-note beats of rest and "
            "there are no cross-bar ties."
        ),
    },
    {
        "page": 13,
        "after_measure": 70,
        "rating": "workable",
        "reason": (
            "One shared quarter-note beat separates the colon at m.70 from the "
            "metered-forte return at m.71; there are no cross-bar ties."
        ),
    },
    {
        "page": 15,
        "after_measure": 88,
        "rating": "ideal",
        "reason": (
            "The musique-concrete block ends with at least six quarter-note "
            "beats of silence in every part before the m.89 lantern entrance."
        ),
    },
    {
        "page": 17,
        "after_measure": 103,
        "rating": "strong",
        "reason": (
            "All six parts have a one-quarter-note shared breath, with no ties, "
            "before the unified m.104 entrance."
        ),
    },
    {
        "page": 19,
        "after_measure": 114,
        "rating": "workable",
        "reason": (
            "There are no cross-bar ties and four parts have two beats of "
            "space; the page turn also places the aleatoric instruction at the "
            "top of page 20."
        ),
    },
    {
        "page": 21,
        "after_measure": 129,
        "rating": "workable-fast",
        "reason": (
            "The phrase closes on 'new home.' and no notes tie across; Shadow "
            "voices have only a half-beat before the second aleatoric field."
        ),
    },
    {
        "page": 23,
        "after_measure": 151,
        "rating": "end-of-music",
        "reason": "No live musical turn is required; page 24 is the colophon.",
    },
)

STAGE_D_COLLISIONS_ADDRESSED = (
    "m.12/13 separated by a page break",
    "m.16/17 separated by a page break",
    "m.36/37 separated by a page break",
    "m.42/43 separated by a page break",
    "m.61/62 separated by a page break",
    "m.69/70 absorbed into one m.67-70 system",
    "m.97/98 separated by a page break",
    "m.106/107 absorbed into one m.104-107 system",
    "m.118/119 separated by a page break",
    "m.143/144 replaced by balanced m.140-145 and m.146-151 systems",
)

COLOPHON_INSTRUCTION = (
    "After import, create a nonblank page 24 natively in Dorico with a page-"
    "template override and the approved edition/provenance colophon.  Do not "
    "append an empty page or rely on MusicXML credit-words to allocate it."
)


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def validate_profile() -> None:
    # Reuse the established exhaustive coverage checks by temporarily exposing
    # this separate profile to the shared layout-only validation helpers.
    base.CASTING = CASTING
    base.validate_casting_definition()
    if len(CASTING) != MUSIC_PAGES:
        raise ValueError(f"Expected {MUSIC_PAGES} music pages, found {len(CASTING)}")
    if len(CASTING[0]) != 2:
        raise ValueError("Page 1 must contain exactly two systems")

    for page_number, page in enumerate(CASTING, start=1):
        for start, end in page:
            length = end - start + 1
            if length > 10:
                raise ValueError(
                    f"Page {page_number} system {start}-{end} exceeds ten measures"
                )
            if length > 7 and (start, end) != (81, 88):
                raise ValueError(
                    f"Only the tacet m.81-88 system may exceed seven measures: "
                    f"{start}-{end}"
                )


def validate_extended_score_shape(root: ET.Element) -> dict[str, object]:
    state = base.validate_score_shape(root)
    note_count = len(root.findall(".//note"))
    if note_count != EXPECTED_NOTE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_NOTE_COUNT} MusicXML note elements, found {note_count}"
        )
    return {**state, "note_count": note_count}


def element_signature(element: ET.Element) -> tuple[object, ...]:
    text = element.text or ""
    if not text.strip():
        text = ""
    return (
        element.tag,
        tuple(sorted(element.attrib.items())),
        text,
        tuple(element_signature(child) for child in element),
    )


def lyric_semantic_rows(root: ET.Element) -> list[tuple[object, ...]]:
    rows: list[tuple[object, ...]] = []
    for part in root.findall("part"):
        part_id = part.get("id", "")
        for measure in part.findall("measure"):
            measure_number = measure.get("number", "")
            for note_index, note in enumerate(measure.findall("note"), start=1):
                voice = note.findtext("voice", "1")
                for lyric_index, lyric in enumerate(note.findall("lyric"), start=1):
                    rows.append(
                        (
                            part_id,
                            measure_number,
                            note_index,
                            voice,
                            lyric_index,
                            element_signature(lyric),
                        )
                    )
    return rows


def five_line_staff_rows(root: ET.Element) -> list[tuple[object, ...]]:
    rows: list[tuple[object, ...]] = []
    for part in root.findall("part"):
        part_id = part.get("id", "")
        for measure in part.findall("measure"):
            measure_number = measure.get("number", "")
            for details in measure.findall("./attributes/staff-details"):
                if details.get("print-object") == "no":
                    raise ValueError(
                        f"Hidden staff-details found in {part_id} measure "
                        f"{measure_number}"
                    )
                if details.findtext("staff-lines") != "5":
                    raise ValueError(
                        f"Non-five-line staff found in {part_id} measure "
                        f"{measure_number}"
                    )
                rows.append(
                    (part_id, measure_number, element_signature(details))
                )
    if not rows:
        raise ValueError("Expected explicit five-line staff overrides")
    return rows


def rows_hash(rows: list[tuple[object, ...]]) -> str:
    payload = json.dumps(
        rows, ensure_ascii=False, separators=(",", ":"), sort_keys=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def remove_empty_print_nodes(root: ET.Element) -> int:
    """Remove print shells left behind when an older break map is cleared."""
    removed = 0
    for measure in root.findall("./part/measure"):
        for print_node in list(measure.findall("print")):
            if (
                not print_node.attrib
                and len(print_node) == 0
                and not (print_node.text or "").strip()
            ):
                measure.remove(print_node)
                removed += 1
    return removed


def verify_stage_e_source(source: Path) -> dict[str, object]:
    if not STAGE_E_REPORT.exists():
        return {"verified": False, "reason": "Stage E cleanup report not found"}
    report = json.loads(STAGE_E_REPORT.read_text(encoding="utf-8"))
    validation = report.get("validation", {})
    expected_hash = report.get("output_sha256")
    actual_hash = base.sha256(source)
    verified = (
        source.resolve() == DEFAULT_SOURCE.resolve()
        and report.get("stage") == "E"
        and expected_hash == actual_hash
        and validation.get("passed") is True
        and validation.get("note_count") == EXPECTED_NOTE_COUNT
        and validation.get("lyric_anchor_count") == base.EXPECTED_LYRIC_ANCHORS
        and validation.get("canonical_structure_matches") is True
        and validation.get("fall_replacements_preserved") is True
        and validation.get("lyrics_text_attributes_and_placement_exact") is True
        and validation.get("dynamics_exact") is True
        and validation.get("harmonies_exact") is True
        and validation.get("direction_changes_exactly_logged") is True
    )
    return {
        "verified": verified,
        "stage": report.get("stage"),
        "report": display_path(STAGE_E_REPORT),
        "source_sha256_matches_report": expected_hash == actual_hash,
        "fall_replacements": 388 if verified else None,
        "lyric_routing_normalized": verified,
        "ensemble_direction_duplicates_removed": (
            report.get("ensemble_direction_cleanup", {}).get(
                "removed_duplicate_count"
            )
            if verified
            else None
        ),
        "redundant_page1_credits_removed": (
            report.get("page1_credit_cleanup", {}).get(
                "removed_redundant_count"
            )
            if verified
            else None
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Apply the optional readability-first 23-music-page Fall 2026 "
            "casting and reserve native Dorico page 24 for a colophon."
        ),
        epilog=COLOPHON_INSTRUCTION,
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow replacement of this profile's existing output/report only.",
    )
    args = parser.parse_args()

    if args.source.resolve() == args.output.resolve():
        raise ValueError("Source and output must be different files")
    base.refuse_overwrite([args.output, args.report], args.force)
    validate_profile()

    tree = ET.parse(args.source)
    root = tree.getroot()
    source_hash = base.sha256(args.source)
    source_state = validate_extended_score_shape(root)
    source_lyrics = lyric_semantic_rows(root)
    source_staff_rows = five_line_staff_rows(root)
    source_provenance = verify_stage_e_source(args.source)
    removed_break_flags = base.remove_break_flags(root)
    removed_empty_print_nodes = remove_empty_print_nodes(root)
    supports_removed = base.configure_break_supports(root)
    base.apply_casting(root)
    break_state = base.validate_applied_breaks(root)
    output_state = validate_extended_score_shape(root)
    output_lyrics = lyric_semantic_rows(root)
    output_staff_rows = five_line_staff_rows(root)
    if source_state != output_state:
        raise ValueError(
            "Score counts or musical fingerprint changed while applying casting"
        )
    if source_lyrics != output_lyrics:
        raise ValueError("Lyric semantics or routing changed while applying casting")
    if source_staff_rows != output_staff_rows:
        raise ValueError("Five-line staff overrides changed while applying casting")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    base.write_musicxml(tree, args.output)

    reparsed_root = ET.parse(args.output).getroot()
    reparsed_state = validate_extended_score_shape(reparsed_root)
    reparsed_break_state = base.validate_applied_breaks(reparsed_root)
    reparsed_lyrics = lyric_semantic_rows(reparsed_root)
    reparsed_staff_rows = five_line_staff_rows(reparsed_root)
    if (
        reparsed_state != source_state
        or reparsed_break_state != break_state
        or reparsed_lyrics != source_lyrics
        or reparsed_staff_rows != source_staff_rows
    ):
        raise ValueError("Written MusicXML did not pass round-trip validation")

    two_system_pages = [
        page_number
        for page_number, page in enumerate(CASTING, start=1)
        if len(page) == 2
    ]
    one_system_pages = [
        page_number
        for page_number, page in enumerate(CASTING, start=1)
        if len(page) == 1
    ]
    report = {
        "profile": "Fall 2026 readability-first 24-page performer score",
        "source": display_path(args.source),
        "output": display_path(args.output),
        "source_sha256": source_hash,
        "output_sha256": base.sha256(args.output),
        "source_provenance": source_provenance,
        "score_validation": reparsed_state,
        "structure_matches": (
            reparsed_state["structure_fingerprint"]
            == source_state["structure_fingerprint"]
        ),
        "semantic_preservation": {
            "lyrics_and_routing_match": reparsed_lyrics == source_lyrics,
            "lyric_semantic_hash": rows_hash(reparsed_lyrics),
            "five_line_staff_overrides_match": (
                reparsed_staff_rows == source_staff_rows
            ),
            "five_line_staff_override_hash": rows_hash(reparsed_staff_rows),
            "all_encoded_staves_visible": True,
        },
        "removed_break_attributes": removed_break_flags,
        "removed_empty_print_nodes": removed_empty_print_nodes,
        "replaced_break_support_entries": supports_removed,
        "casting": {
            "music_pages": len(CASTING),
            "booklet_target_pages": BOOKLET_TARGET_PAGES,
            "colophon_page": COLOPHON_PAGE,
            "systems": sum(len(page) for page in CASTING),
            "two_system_pages": two_system_pages,
            "one_system_pages": one_system_pages,
            "page_1_has_exactly_two_systems": len(CASTING[0]) == 2,
            "pages": [
                [f"{start}-{end}" for start, end in page] for page in CASTING
            ],
            **break_state,
        },
        "odd_page_turns": list(ODD_PAGE_TURNS),
        "stage_d_collision_response": list(STAGE_D_COLLISIONS_ADDRESSED),
        "colophon": {
            "musicxml_credit_added": False,
            "native_dorico_page_required": True,
            "page": COLOPHON_PAGE,
            "must_be_nonblank": True,
            "instruction": COLOPHON_INSTRUCTION,
        },
    }
    args.report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
