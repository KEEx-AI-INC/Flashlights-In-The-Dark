#!/usr/bin/env python3
"""Build the separate Fall 2026 32-page performer-score casting source.

The profile places music on pages 1-31 and reserves page 32 for the existing
nonblank saddle-stitch colophon.  It starts from the validated Stage E source,
does not overwrite the 24-page profile, and changes only:

* MusicXML page/system break flags;
* two page-one credit objects that the Dorico page template supplies instead;
* one approved orthographic correction in the P1 m.55 direction.

The removed credit values are retained in ``identification/miscellaneous``.
Every musical, lyric, dynamic, harmony, staff, and timing invariant is checked
before the generated source and reports are written.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import apply_fall2026_24page_casting as profile24


base = profile24.base
ROOT = Path(__file__).resolve().parents[2]
PROVENANCE = ROOT / "Engraving/Scores/Fall2026-Provenance"

DEFAULT_SOURCE = PROVENANCE / "FlashlightsInTheDark_Fall2026_StageEClean.musicxml"
DEFAULT_OUTPUT = (
    PROVENANCE / "FlashlightsInTheDark_Fall2026_Dorico32PageCasted.musicxml"
)
DEFAULT_REPORT = (
    PROVENANCE / "FlashlightsInTheDark_Fall2026_32PageCastingReport.json"
)
DEFAULT_VALIDATION_REPORT = (
    PROVENANCE / "FlashlightsInTheDark_Fall2026_32PageSemanticValidation.json"
)
COLOPHON = PROVENANCE / "FlashlightsInTheDark_Fall2026_Page32_Colophon.pdf"

EXPECTED_NOTE_COUNT = profile24.EXPECTED_NOTE_COUNT
BOOKLET_TARGET_PAGES = 32
MUSIC_PAGES = 31
COLOPHON_PAGE = 32
EXPECTED_SYSTEMS = 36
EXPECTED_TWO_SYSTEM_PAGES = (1, 6, 20, 21, 27)

# 36 systems on 31 music pages.  Five pages carry two systems; every other
# page carries one.  The lyric-heavy m.21-25 and m.108-112 spans, and the
# horizontally overloaded m.46-52 span, are deliberately subdivided.  The
# only system longer than seven measures is the sparse m.84-92 system: m.84-88
# is entirely tacet and m.89-92 contains only the light lantern/chord entrance.
CASTING: tuple[tuple[tuple[int, int], ...], ...] = (
    ((1, 6), (7, 10)),
    ((11, 12),),
    ((13, 14),),
    ((15, 16),),
    ((17, 20),),
    ((21, 22), (23, 25)),
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
    ((71, 76),),
    ((77, 83),),
    ((84, 92), (93, 97)),
    ((98, 101), (102, 103)),
    ((104, 107),),
    ((108, 109),),
    ((110, 112),),
    ((113, 114),),
    ((115, 118),),
    ((119, 124), (125, 129)),
    ((130, 134),),
    ((135, 139),),
    ((140, 145),),
    ((146, 151),),
)

PAIRING_RATIONALES: tuple[dict[str, object], ...] = (
    {
        "page": 1,
        "systems": ["1-6", "7-10"],
        "reason": (
            "Required two-system title page; the Stage F balance is retained."
        ),
    },
    {
        "page": 6,
        "systems": ["21-22", "23-25"],
        "reason": (
            "The former m.21-25 system is split at the complete Shadow phrase "
            "'in the night'; Stage F proved this page region can hold two "
            "systems without a system-on-system collision."
        ),
    },
    {
        "page": 20,
        "systems": ["84-92", "93-97"],
        "reason": (
            "Stage C rendered this sparse/tacet-plus-chord pairing without a "
            "vertical collision; the first system contains five tacet measures."
        ),
    },
    {
        "page": 21,
        "systems": ["98-101", "102-103"],
        "reason": (
            "Stage F proved the two systems are physically separate; the pair "
            "keeps the complete 'yours too' phrase before the strong turn."
        ),
    },
    {
        "page": 27,
        "systems": ["119-124", "125-129"],
        "reason": (
            "Stage F passed this pairing with only local cleanup and it closes "
            "the first aleatoric field at 'new home.' before the turn."
        ),
    },
)

ODD_PAGE_TURNS: tuple[dict[str, object], ...] = (
    {
        "page": 1,
        "after_measure": 10,
        "rating": "marginal",
        "reason": (
            "Page 1 must retain two systems. One Light voice ties across and "
            "several voices have no shared rest before m.11."
        ),
    },
    {
        "page": 3,
        "after_measure": 14,
        "rating": "marginal",
        "reason": (
            "The Baritone Shadow line ties across, but the remembered-question "
            "gesture closes before the new 'Look at'/'build' material."
        ),
    },
    {
        "page": 5,
        "after_measure": 20,
        "rating": "unsafe-unavoidable",
        "reason": (
            "Five parts tie or continue text into m.21. Avoiding this turn would "
            "recompress the dense m.11-25 lyric systems."
        ),
    },
    {
        "page": 7,
        "after_measure": 31,
        "rating": "strong",
        "reason": (
            "All parts have at least 4.5 quarter-note beats of turning time at "
            "the clock/Andante reset before m.32."
        ),
    },
    {
        "page": 9,
        "after_measure": 39,
        "rating": "unsafe-unavoidable",
        "reason": (
            "Tenor/Bass L ties into m.40 and the Shining/bloom texture continues; "
            "the surrounding systems previously collided when paired."
        ),
    },
    {
        "page": 11,
        "after_measure": 45,
        "rating": "workable",
        "reason": (
            "No cross-bar tie; most parts have at least 2.5 beats of clearance "
            "at the breathing-arc boundary."
        ),
    },
    {
        "page": 13,
        "after_measure": 52,
        "rating": "unsafe-unavoidable",
        "reason": (
            "Light material and the Shadow question continue into m.53. The turn "
            "is retained so the former m.46-52 system can be divided for legibility."
        ),
    },
    {
        "page": 15,
        "after_measure": 61,
        "rating": "strong",
        "reason": (
            "Every active part has at least two quarter-note beats of clearance "
            "and there are no cross-bar ties."
        ),
    },
    {
        "page": 17,
        "after_measure": 70,
        "rating": "workable",
        "reason": (
            "One shared beat, no ties, and a colon precede the metered-forte "
            "'new world' return."
        ),
    },
    {
        "page": 19,
        "after_measure": 83,
        "rating": "ideal",
        "reason": (
            "The turn occurs inside the completely tacet m.81-88 block, leaving "
            "five further silent measures before the m.89 lantern entrance."
        ),
    },
    {
        "page": 21,
        "after_measure": 103,
        "rating": "strong",
        "reason": (
            "All six parts have a shared breath and no ties after the complete "
            "'yours too' phrase, before the unified m.104 entrance."
        ),
    },
    {
        "page": 23,
        "after_measure": 109,
        "rating": "workable-fast",
        "reason": (
            "No notes tie across; the comma after 'with love' provides a textual "
            "articulation, though there is no long shared rest."
        ),
    },
    {
        "page": 25,
        "after_measure": 114,
        "rating": "workable",
        "reason": (
            "No cross-bar ties; the turn puts the consolidated aleatoric "
            "instruction at the top of page 26."
        ),
    },
    {
        "page": 27,
        "after_measure": 129,
        "rating": "workable-fast",
        "reason": (
            "The phrase closes on 'new home.' with no cross-bar ties; Shadow "
            "voices have only a half-beat before the next field."
        ),
    },
    {
        "page": 29,
        "after_measure": 139,
        "rating": "unsafe-unavoidable",
        "reason": (
            "All six parts sustain into the final m.140 texture. Moving the turn "
            "would require an overlong or vertically incompatible final system."
        ),
    },
    {
        "page": 31,
        "after_measure": 151,
        "rating": "end-of-music",
        "reason": "No live musical turn is required; page 32 is the colophon.",
    },
)

PAGE_FURNITURE_FIELDS = (
    (
        "fall2026-project-subtitle",
        "Set in 2076",
        "Dorico first-page template supplies the visible subtitle.",
    ),
    (
        "fall2026-project-commission",
        "Commissioned by the Philharmonic Chorus of Madison",
        "Dorico first-page template supplies the visible commission line.",
    ),
)

DIRECTION_CORRECTION = {
    "part": "P1",
    "measure": 55,
    "before": "reversed -impact sound event ",
    "after": "reversed-impact sound event",
    "source_word_spans": ["reversed", "-impact sound event"],
    "reason": (
        "Remove the erroneous space before the existing hyphen and the trailing "
        "space; retain the direction at the same musical position."
    ),
}

COLOPHON_INSTRUCTION = (
    "Use the existing nonblank page-32 colophon after the 31-page Dorico music "
    "proof is visually approved. Do not synthesize a blank MusicXML page and do "
    "not append or modify PDFs during this casting-source step."
)


def display_path(path: Path) -> str:
    return profile24.display_path(path)


def rows_hash(rows: object) -> str:
    payload = json.dumps(
        rows, ensure_ascii=False, separators=(",", ":"), sort_keys=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_profile() -> None:
    base.CASTING = CASTING
    base.validate_casting_definition()
    if len(CASTING) != MUSIC_PAGES:
        raise ValueError(f"Expected {MUSIC_PAGES} music pages, found {len(CASTING)}")
    if sum(len(page) for page in CASTING) != EXPECTED_SYSTEMS:
        raise ValueError(f"Expected {EXPECTED_SYSTEMS} systems")
    if len(CASTING[0]) != 2:
        raise ValueError("Page 1 must contain exactly two systems")

    two_system_pages = tuple(
        number for number, page in enumerate(CASTING, start=1) if len(page) == 2
    )
    if two_system_pages != EXPECTED_TWO_SYSTEM_PAGES:
        raise ValueError(
            f"Expected paired pages {EXPECTED_TWO_SYSTEM_PAGES}, found "
            f"{two_system_pages}"
        )

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


def element_signature(element: ET.Element) -> tuple[object, ...]:
    return profile24.element_signature(element)


def contextual_rows(root: ET.Element, tag: str) -> list[tuple[object, ...]]:
    rows: list[tuple[object, ...]] = []
    for part in root.findall("part"):
        part_id = part.get("id", "")
        for measure in part.findall("measure"):
            measure_number = measure.get("number", "")
            for index, element in enumerate(measure.findall(f".//{tag}"), start=1):
                rows.append(
                    (part_id, measure_number, index, element_signature(element))
                )
    return rows


def top_level_rows(root: ET.Element, tag: str) -> list[tuple[object, ...]]:
    rows: list[tuple[object, ...]] = []
    for part in root.findall("part"):
        part_id = part.get("id", "")
        for measure in part.findall("measure"):
            measure_number = measure.get("number", "")
            for index, element in enumerate(measure.findall(tag), start=1):
                rows.append(
                    (part_id, measure_number, index, element_signature(element))
                )
    return rows


def direction_rows_except_correction(
    root: ET.Element,
) -> list[tuple[object, ...]]:
    rows: list[tuple[object, ...]] = []
    for part in root.findall("part"):
        part_id = part.get("id", "")
        for measure in part.findall("measure"):
            measure_number = int(measure.get("number", "0"))
            for index, direction in enumerate(measure.findall("direction"), start=1):
                words = tuple(
                    "".join(item.itertext())
                    for item in direction.findall("./direction-type/words")
                )
                if (
                    part_id == DIRECTION_CORRECTION["part"]
                    and measure_number == DIRECTION_CORRECTION["measure"]
                    and words
                    in {
                        tuple(DIRECTION_CORRECTION["source_word_spans"]),
                        (DIRECTION_CORRECTION["after"],),
                    }
                ):
                    continue
                rows.append(
                    (
                        part_id,
                        str(measure_number),
                        index,
                        element_signature(direction),
                    )
                )
    return rows


def credit_text(credit: ET.Element) -> str:
    return "\n".join(
        "".join(words.itertext()) for words in credit.findall("credit-words")
    )


def normalize_page_furniture(root: ET.Element) -> list[dict[str, object]]:
    credits = list(root.findall("credit"))
    expected_values = {value for _, value, _ in PAGE_FURNITURE_FIELDS}
    found_values = [credit_text(credit) for credit in credits]
    if set(found_values) != expected_values or len(found_values) != len(expected_values):
        raise ValueError(
            "Expected exactly the two residual page-one subtitle/commission "
            f"credits, found {found_values}"
        )
    if any(credit.get("page") != "1" for credit in credits):
        raise ValueError("Residual subtitle/commission credits must be on page 1")

    identification = root.find("identification")
    if identification is None:
        raise ValueError("Expected identification metadata")
    miscellaneous = identification.find("miscellaneous")
    if miscellaneous is None:
        miscellaneous = ET.SubElement(identification, "miscellaneous")

    existing_names = {
        field.get("name", "")
        for field in miscellaneous.findall("miscellaneous-field")
    }
    entries: list[dict[str, object]] = []
    for name, value, reason in PAGE_FURNITURE_FIELDS:
        if name in existing_names:
            raise ValueError(f"Metadata field {name!r} already exists")
        credit = next(item for item in credits if credit_text(item) == value)
        words = credit.find("credit-words")
        entry = {
            "page": 1,
            "credit_text_removed": value,
            "credit_attributes_before": dict(sorted(credit.attrib.items())),
            "credit_words_attributes_before": (
                dict(sorted(words.attrib.items())) if words is not None else {}
            ),
            "metadata_field_added": name,
            "metadata_value": value,
            "visible_source_after_import": "Dorico first-page template",
            "reason": reason,
        }
        root.remove(credit)
        field = ET.SubElement(miscellaneous, "miscellaneous-field", {"name": name})
        field.text = value
        entries.append(entry)

    return entries


def normalize_direction_text(root: ET.Element) -> dict[str, object]:
    part = root.find(f"./part[@id='{DIRECTION_CORRECTION['part']}']")
    if part is None:
        raise ValueError("Missing P1")
    measure = part.find(f"./measure[@number='{DIRECTION_CORRECTION['measure']}']")
    if measure is None:
        raise ValueError("Missing P1 m.55")

    matches: list[ET.Element] = []
    expected_spans = tuple(DIRECTION_CORRECTION["source_word_spans"])
    for direction in measure.findall("direction"):
        spans = tuple(
            "".join(words.itertext())
            for words in direction.findall("./direction-type/words")
        )
        if spans == expected_spans:
            matches.append(direction)
    if len(matches) != 1:
        raise ValueError(
            "Expected one P1 m.55 direction with word spans "
            f"{expected_spans}, found {len(matches)}"
        )

    direction = matches[0]
    direction_type = direction.find("direction-type")
    if direction_type is None:
        raise ValueError("Direction has no direction-type")
    words_nodes = direction_type.findall("words")
    if len(words_nodes) != 2:
        raise ValueError("Expected exactly two words spans in the m.55 direction")
    before_direction_attributes = dict(sorted(direction.attrib.items()))
    before_offset = direction.findtext("offset")
    before_staff = direction.findtext("staff")
    before_sound = [element_signature(sound) for sound in direction.findall("sound")]

    words_nodes[0].text = str(DIRECTION_CORRECTION["after"])
    direction_type.remove(words_nodes[1])

    after_spans = tuple(
        "".join(words.itertext())
        for words in direction.findall("./direction-type/words")
    )
    if after_spans != (DIRECTION_CORRECTION["after"],):
        raise ValueError("The m.55 direction did not normalize to one exact span")
    if dict(sorted(direction.attrib.items())) != before_direction_attributes:
        raise ValueError("Direction placement attributes changed")
    if direction.findtext("offset") != before_offset:
        raise ValueError("Direction offset changed")
    if direction.findtext("staff") != before_staff:
        raise ValueError("Direction staff assignment changed")
    if [element_signature(sound) for sound in direction.findall("sound")] != before_sound:
        raise ValueError("Direction playback data changed")

    return {
        **DIRECTION_CORRECTION,
        "direction_attributes_preserved": True,
        "offset_before_after": [before_offset, direction.findtext("offset")],
        "staff_before_after": [before_staff, direction.findtext("staff")],
        "playback_sound_elements_preserved": True,
        "word_spans_after": list(after_spans),
    }


def verify_page_furniture_metadata(root: ET.Element) -> bool:
    if root.findall("credit"):
        return False
    fields = {
        field.get("name", ""): field.text or ""
        for field in root.findall(
            "./identification/miscellaneous/miscellaneous-field"
        )
    }
    return all(fields.get(name) == value for name, value, _ in PAGE_FURNITURE_FIELDS)


def strip_casting_metadata(root: ET.Element) -> None:
    base.remove_break_flags(root)
    profile24.remove_empty_print_nodes(root)
    encoding = root.find("./identification/encoding")
    if encoding is not None:
        for support in list(encoding.findall("supports")):
            if support.get("element") == "print" and support.get("attribute") in {
                "new-page",
                "new-system",
            }:
                encoding.remove(support)


def noncasting_tree_hash(root: ET.Element) -> str:
    clone = copy.deepcopy(root)
    strip_casting_metadata(clone)
    return rows_hash(element_signature(clone))


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build the separate 31-music-page Fall 2026 casting and reserve "
            "page 32 for the existing nonblank colophon."
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
        help="Allow replacement of this 32-page profile's own artifacts only.",
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
    source_state = profile24.validate_extended_score_shape(root)
    source_lyrics = profile24.lyric_semantic_rows(root)
    source_staff_rows = profile24.five_line_staff_rows(root)
    source_dynamics = contextual_rows(root, "dynamics")
    source_harmonies = top_level_rows(root, "harmony")
    source_other_directions = direction_rows_except_correction(root)
    source_provenance = profile24.verify_stage_e_source(args.source)
    if not source_provenance.get("verified"):
        raise ValueError("The default Stage E source provenance did not validate")

    page_furniture_changes = normalize_page_furniture(root)
    direction_change = normalize_direction_text(root)

    normalized_state = profile24.validate_extended_score_shape(root)
    normalized_lyrics = profile24.lyric_semantic_rows(root)
    normalized_staff_rows = profile24.five_line_staff_rows(root)
    normalized_dynamics = contextual_rows(root, "dynamics")
    normalized_harmonies = top_level_rows(root, "harmony")
    normalized_other_directions = direction_rows_except_correction(root)
    if source_state != normalized_state:
        raise ValueError("Approved text/page-furniture normalization changed music")
    if source_lyrics != normalized_lyrics:
        raise ValueError("Approved normalization changed lyrics or routing")
    if source_staff_rows != normalized_staff_rows:
        raise ValueError("Approved normalization changed five-line staff overrides")
    if source_dynamics != normalized_dynamics:
        raise ValueError("Approved normalization changed dynamics")
    if source_harmonies != normalized_harmonies:
        raise ValueError("Approved normalization changed harmonies")
    if source_other_directions != normalized_other_directions:
        raise ValueError("An unapproved direction changed")
    if not verify_page_furniture_metadata(root):
        raise ValueError("Page-one credits were not safely retained as metadata")

    expected_noncasting_hash = noncasting_tree_hash(root)
    removed_break_flags = base.remove_break_flags(root)
    removed_empty_print_nodes = profile24.remove_empty_print_nodes(root)
    supports_removed = base.configure_break_supports(root)
    base.apply_casting(root)
    break_state = base.validate_applied_breaks(root)

    output_state = profile24.validate_extended_score_shape(root)
    output_lyrics = profile24.lyric_semantic_rows(root)
    output_staff_rows = profile24.five_line_staff_rows(root)
    output_dynamics = contextual_rows(root, "dynamics")
    output_harmonies = top_level_rows(root, "harmony")
    output_other_directions = direction_rows_except_correction(root)
    if output_state != source_state:
        raise ValueError("Casting changed score counts or musical fingerprint")
    if output_lyrics != source_lyrics:
        raise ValueError("Casting changed lyrics or routing")
    if output_staff_rows != source_staff_rows:
        raise ValueError("Casting changed five-line staff overrides")
    if output_dynamics != source_dynamics:
        raise ValueError("Casting changed dynamics")
    if output_harmonies != source_harmonies:
        raise ValueError("Casting changed harmonies")
    if output_other_directions != source_other_directions:
        raise ValueError("Casting changed an unapproved direction")
    if noncasting_tree_hash(root) != expected_noncasting_hash:
        raise ValueError("Non-casting score content changed while applying breaks")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.validation_report.parent.mkdir(parents=True, exist_ok=True)
    base.write_musicxml(tree, args.output)

    reparsed_root = ET.parse(args.output).getroot()
    reparsed_state = profile24.validate_extended_score_shape(reparsed_root)
    reparsed_break_state = base.validate_applied_breaks(reparsed_root)
    reparsed_lyrics = profile24.lyric_semantic_rows(reparsed_root)
    reparsed_staff_rows = profile24.five_line_staff_rows(reparsed_root)
    reparsed_dynamics = contextual_rows(reparsed_root, "dynamics")
    reparsed_harmonies = top_level_rows(reparsed_root, "harmony")
    reparsed_other_directions = direction_rows_except_correction(reparsed_root)

    exact_checks = {
        "score_shape_and_canonical_fingerprint": reparsed_state == source_state,
        "note_count_2787": reparsed_state.get("note_count") == EXPECTED_NOTE_COUNT,
        "six_parts_151_measures": (
            reparsed_state.get("part_ids") == list(base.EXPECTED_PART_IDS)
            and all(
                count == base.EXPECTED_MEASURES_PER_PART
                for count in reparsed_state.get("measure_counts", {}).values()
            )
        ),
        "lyric_anchors_1376": (
            reparsed_state.get("lyric_anchors") == base.EXPECTED_LYRIC_ANCHORS
        ),
        "lyrics_text_attributes_and_routing_exact": (
            reparsed_lyrics == source_lyrics
        ),
        "all_388_fall_replacements_preserved": (
            source_provenance.get("fall_replacements") == 388
            and reparsed_lyrics == source_lyrics
        ),
        "five_line_staff_overrides_exact": (
            reparsed_staff_rows == source_staff_rows
        ),
        "dynamics_exact": reparsed_dynamics == source_dynamics,
        "harmonies_exact": reparsed_harmonies == source_harmonies,
        "all_unapproved_directions_exact": (
            reparsed_other_directions == source_other_directions
        ),
        "page_furniture_values_preserved_in_metadata": (
            verify_page_furniture_metadata(reparsed_root)
        ),
        "casting_breaks_exact": reparsed_break_state == break_state,
        "full_noncasting_tree_exact_after_approved_normalizations": (
            noncasting_tree_hash(reparsed_root) == expected_noncasting_hash
        ),
    }
    passed = all(exact_checks.values())
    if not passed:
        failed = [name for name, value in exact_checks.items() if not value]
        raise ValueError(f"Round-trip semantic validation failed: {failed}")

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
    lengths = [end - start + 1 for page in CASTING for start, end in page]
    colophon_state = {
        "path": display_path(COLOPHON),
        "exists": COLOPHON.exists(),
        "sha256": base.sha256(COLOPHON) if COLOPHON.exists() else None,
        "bytes": COLOPHON.stat().st_size if COLOPHON.exists() else None,
        "page": COLOPHON_PAGE,
        "must_be_nonblank": True,
        "musicxml_credit_added": False,
        "pdf_appended_or_modified": False,
        "instruction": COLOPHON_INSTRUCTION,
    }
    if not colophon_state["exists"] or not colophon_state["bytes"]:
        raise ValueError("Existing page-32 colophon is missing or empty")

    semantic_validation = {
        "profile": "Fall 2026 32-page saddle-stitch performer score",
        "source": display_path(args.source),
        "output": display_path(args.output),
        "source_sha256": source_hash,
        "output_sha256": base.sha256(args.output),
        "passed": passed,
        "source_provenance": source_provenance,
        "score_validation": reparsed_state,
        "exact_checks": exact_checks,
        "hashes": {
            "canonical_structure": reparsed_state["structure_fingerprint"],
            "lyrics_and_routing": rows_hash(reparsed_lyrics),
            "five_line_staff_overrides": rows_hash(reparsed_staff_rows),
            "dynamics": rows_hash(reparsed_dynamics),
            "harmonies": rows_hash(reparsed_harmonies),
            "unapproved_directions": rows_hash(reparsed_other_directions),
            "full_noncasting_tree_after_approved_normalizations": (
                expected_noncasting_hash
            ),
        },
        "approved_changes": {
            "page_furniture_only": page_furniture_changes,
            "direction_text": direction_change,
            "unlogged_textual_differences": 0,
        },
        "casting": {
            "music_pages": MUSIC_PAGES,
            "booklet_target_pages": BOOKLET_TARGET_PAGES,
            "systems": EXPECTED_SYSTEMS,
            "page_1_has_exactly_two_systems": True,
            "paired_pages": two_system_pages,
            "single_system_pages": one_system_pages,
            "minimum_system_measures": min(lengths),
            "maximum_system_measures": max(lengths),
            "only_over_seven_system": "84-92 (m.84-88 tacet)",
            **reparsed_break_state,
        },
    }
    args.validation_report.write_text(
        json.dumps(semantic_validation, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    report = {
        "profile": "Fall 2026 32-page saddle-stitch performer score",
        "source": display_path(args.source),
        "output": display_path(args.output),
        "semantic_validation_report": display_path(args.validation_report),
        "source_sha256": source_hash,
        "output_sha256": base.sha256(args.output),
        "source_provenance": source_provenance,
        "score_validation": reparsed_state,
        "semantic_validation_passed": passed,
        "approved_normalizations": {
            "page_furniture_only": page_furniture_changes,
            "direction_text": direction_change,
        },
        "removed_break_attributes": removed_break_flags,
        "removed_empty_print_nodes": removed_empty_print_nodes,
        "replaced_break_support_entries": supports_removed,
        "casting": {
            "music_pages": MUSIC_PAGES,
            "booklet_target_pages": BOOKLET_TARGET_PAGES,
            "colophon_page": COLOPHON_PAGE,
            "systems": EXPECTED_SYSTEMS,
            "paired_pages": two_system_pages,
            "single_system_pages": one_system_pages,
            "pairing_count": len(two_system_pages),
            "page_1_has_exactly_two_systems": True,
            "pages": [
                [f"{start}-{end}" for start, end in page] for page in CASTING
            ],
            "horizontal_splits": {
                "former_21-25": ["21-22", "23-25"],
                "former_46-52": ["46-49", "50-52"],
                "former_108-112": ["108-109", "110-112"],
            },
            "sparse_recast": {
                "former_77-80_81-88_89-92": ["77-83", "84-92"]
            },
            "system_measure_lengths": lengths,
            **reparsed_break_state,
        },
        "paired_page_evidence": list(PAIRING_RATIONALES),
        "odd_page_turns": list(ODD_PAGE_TURNS),
        "colophon": colophon_state,
    }
    args.report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
