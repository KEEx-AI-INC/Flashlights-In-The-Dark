#!/usr/bin/env python3
"""Apply the approved Fall 2026 performer-score casting to MusicXML.

This is deliberately a layout-only post-processor.  It removes inherited
MusicXML page/system flags, applies the approved 15 music-page casting to all
six parts, and proves that parts, measures, lyrics, and the canonical musical
fingerprint are unchanged.

The sixteenth booklet page is intentionally not synthesized here.  MusicXML
4.0 permits ``<credit page="16">``, but Dorico does not reliably import
arbitrary page-attached ``credit-words`` or use them to allocate a trailing
page.  Create page 16 after import with a Dorico page-template override and a
text frame containing only approved edition/credit information.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path
import xml.etree.ElementTree as ET


DOCTYPE = (
    '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
    '"http://www.musicxml.org/dtds/partwise.dtd">'
)

EXPECTED_PART_IDS = ("P1", "P2", "P3", "P4", "P5", "P6")
EXPECTED_MEASURES_PER_PART = 151
EXPECTED_LYRIC_ANCHORS = 1376
EXPECTED_STRUCTURE_FINGERPRINT = (
    "82a6cfbb1b1856cf5af9a733c04df58ee2eeaacd2e611213de1b45ec6df3e111"
)

# Page 16 is backmatter created natively in Dorico.  These are the 15 pages
# containing music; each tuple is one system's inclusive measure range.
CASTING: tuple[tuple[tuple[int, int], ...], ...] = (
    ((1, 5), (6, 10)),
    ((11, 14), (15, 18)),
    ((19, 25), (26, 30)),
    ((31, 34), (35, 37)),
    ((38, 41), (42, 47)),
    ((48, 53), (54, 56)),
    ((57, 64), (65, 70)),
    ((71, 75), (76, 79)),
    ((80, 88),),
    ((89, 92), (93, 97)),
    ((98, 100), (101, 103)),
    ((104, 107), (108, 114)),
    ((115, 121), (122, 129)),
    ((130, 132), (133, 139)),
    ((140, 147), (148, 151)),
)

BREAK_ATTRIBUTES = ("new-page", "new-system", "blank-page", "page-number")

COLOPHON_FALLBACK = (
    "MusicXML page credits are not a reliable way to force a trailing page in "
    "Dorico. After import, add page 16 natively with a page-template override "
    "and a text frame containing only approved edition and credit information."
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_score_fingerprint(root: ET.Element) -> str:
    """Hash musical events while excluding lyrics and engraving metadata.

    This intentionally matches the fingerprint used for the validated Fall
    2026 import and its canonical v26 musical baseline.
    """
    rows: list[tuple] = []
    for part in root.findall("part"):
        part_id = part.get("id", "")
        divisions = 1
        for measure in part.findall("measure"):
            measure_id = measure.get("number", "")
            cursor = 0
            meter: list[tuple[str, str]] = []
            tempos: list[str] = []
            events: list[tuple] = []
            for item in measure:
                if item.tag == "attributes":
                    divisions_text = item.findtext("divisions")
                    if divisions_text:
                        divisions = int(divisions_text)
                    for time in item.findall("time"):
                        meter.append(
                            (time.findtext("beats", ""), time.findtext("beat-type", ""))
                        )
                elif item.tag == "direction":
                    for sound in item.findall(".//sound"):
                        if sound.get("tempo") is not None:
                            tempos.append(sound.get("tempo", ""))
                elif item.tag in {"backup", "forward"}:
                    duration = int(item.findtext("duration", "0"))
                    cursor += duration if item.tag == "forward" else -duration
                elif item.tag == "note":
                    voice = item.findtext("voice", "1")
                    duration = int(item.findtext("duration", "0"))
                    onset = Fraction(cursor, divisions)
                    length = Fraction(duration, divisions)
                    if item.find("rest") is not None:
                        sounding = "rest"
                    elif item.find("pitch") is not None:
                        pitch = item.find("pitch")
                        sounding = "".join(
                            [
                                pitch.findtext("step", ""),
                                pitch.findtext("alter", ""),
                                pitch.findtext("octave", ""),
                            ]
                        )
                    else:
                        sounding = "unpitched"
                    events.append(
                        (
                            voice,
                            str(onset),
                            str(length),
                            sounding,
                            bool(item.find("chord") is not None),
                        )
                    )
                    if item.find("chord") is None:
                        cursor += duration
            rows.append(
                (part_id, measure_id, tuple(meter), tuple(tempos), tuple(events))
            )
    payload = json.dumps(rows, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_casting_definition() -> None:
    flattened: list[int] = []
    for page in CASTING:
        if not 1 <= len(page) <= 2:
            raise ValueError(f"Each music page must contain one or two systems: {page}")
        for start, end in page:
            if start > end:
                raise ValueError(f"Invalid system range {start}-{end}")
            flattened.extend(range(start, end + 1))
    expected = list(range(1, EXPECTED_MEASURES_PER_PART + 1))
    if flattened != expected:
        raise ValueError("Casting must cover measures 1-151 exactly once and in order")
    if len(CASTING[0]) != 2:
        raise ValueError("Page 1 must contain exactly two systems")


def validate_score_shape(root: ET.Element) -> dict[str, object]:
    parts = root.findall("part")
    part_ids = tuple(part.get("id", "") for part in parts)
    if part_ids != EXPECTED_PART_IDS:
        raise ValueError(f"Expected parts {EXPECTED_PART_IDS}, found {part_ids}")

    expected_numbers = [
        str(number) for number in range(1, EXPECTED_MEASURES_PER_PART + 1)
    ]
    measure_counts: dict[str, int] = {}
    for part in parts:
        part_id = part.get("id", "")
        measures = part.findall("measure")
        measure_counts[part_id] = len(measures)
        numbers = [measure.get("number", "") for measure in measures]
        if numbers != expected_numbers:
            raise ValueError(
                f"{part_id} must contain consecutively numbered measures 1-151"
            )

    lyric_anchors = len(root.findall(".//lyric"))
    if lyric_anchors != EXPECTED_LYRIC_ANCHORS:
        raise ValueError(
            f"Expected {EXPECTED_LYRIC_ANCHORS} lyric anchors, found {lyric_anchors}"
        )

    fingerprint = normalized_score_fingerprint(root)
    if fingerprint != EXPECTED_STRUCTURE_FINGERPRINT:
        raise ValueError(
            "Source musical structure does not match the canonical Fall 2026 "
            f"fingerprint: {fingerprint}"
        )

    return {
        "part_ids": list(part_ids),
        "measure_counts": measure_counts,
        "lyric_anchors": lyric_anchors,
        "structure_fingerprint": fingerprint,
    }


def remove_break_flags(root: ET.Element) -> dict[str, int]:
    removed = {attribute: 0 for attribute in BREAK_ATTRIBUTES}
    for print_node in root.findall("./part/measure/print"):
        for attribute in BREAK_ATTRIBUTES:
            if attribute in print_node.attrib:
                del print_node.attrib[attribute]
                removed[attribute] += 1
    return removed


def find_or_create_print(measure: ET.Element) -> ET.Element:
    print_node = measure.find("print")
    if print_node is not None:
        return print_node
    print_node = ET.Element("print")
    measure.insert(0, print_node)
    return print_node


def apply_casting(root: ET.Element) -> None:
    page_starts = {page[0][0] for page in CASTING[1:]}
    system_starts = {system[0] for page in CASTING for system in page[1:]}

    for part in root.findall("part"):
        measures = {
            int(measure.get("number", "0")): measure
            for measure in part.findall("measure")
        }
        for measure_number in sorted(page_starts):
            find_or_create_print(measures[measure_number]).set("new-page", "yes")
        for measure_number in sorted(system_starts):
            find_or_create_print(measures[measure_number]).set("new-system", "yes")


def configure_break_supports(root: ET.Element) -> int:
    encoding = root.find("./identification/encoding")
    if encoding is None:
        raise ValueError("Expected identification/encoding metadata")

    removed = 0
    for support in list(encoding.findall("supports")):
        if support.get("element") == "print" and support.get("attribute") in {
            "new-page",
            "new-system",
        }:
            encoding.remove(support)
            removed += 1

    for attribute in ("new-system", "new-page"):
        ET.SubElement(
            encoding,
            "supports",
            {
                "element": "print",
                "attribute": attribute,
                "type": "yes",
                "value": "yes",
            },
        )
    return removed


def expected_break_map() -> dict[int, str]:
    result: dict[int, str] = {}
    for page_index, page in enumerate(CASTING):
        if page_index:
            result[page[0][0]] = "new-page"
        for system in page[1:]:
            result[system[0]] = "new-system"
    return result


def collect_break_map(part: ET.Element) -> dict[int, str]:
    result: dict[int, str] = {}
    for measure in part.findall("measure"):
        measure_number = int(measure.get("number", "0"))
        flags: list[str] = []
        for print_node in measure.findall("print"):
            for attribute in ("new-page", "new-system"):
                if print_node.get(attribute) == "yes":
                    flags.append(attribute)
            for attribute in ("blank-page", "page-number"):
                if attribute in print_node.attrib:
                    raise ValueError(
                        f"Unexpected {attribute} remains in {part.get('id')} measure "
                        f"{measure_number}"
                    )
        if len(flags) > 1:
            raise ValueError(
                f"Conflicting or duplicate break flags in {part.get('id')} measure "
                f"{measure_number}: {flags}"
            )
        if flags:
            result[measure_number] = flags[0]
    return result


def validate_applied_breaks(root: ET.Element) -> dict[str, object]:
    wanted = expected_break_map()
    maps: dict[str, dict[int, str]] = {}
    for part in root.findall("part"):
        part_id = part.get("id", "")
        actual = collect_break_map(part)
        if actual != wanted:
            raise ValueError(f"Break map mismatch in {part_id}: {actual}")
        maps[part_id] = actual

    page_instances = sum(
        1
        for part_map in maps.values()
        for value in part_map.values()
        if value == "new-page"
    )
    system_instances = sum(
        1
        for part_map in maps.values()
        for value in part_map.values()
        if value == "new-system"
    )
    return {
        "page_break_starts": [
            measure for measure, kind in wanted.items() if kind == "new-page"
        ],
        "system_break_starts": [
            measure for measure, kind in wanted.items() if kind == "new-system"
        ],
        "page_break_instances": page_instances,
        "system_break_instances": system_instances,
        "identical_across_parts": True,
    }


def write_musicxml(tree: ET.ElementTree, output: Path) -> None:
    ET.indent(tree, space="  ")
    body = ET.tostring(tree.getroot(), encoding="unicode", short_empty_elements=True)
    output.write_text(
        f"<?xml version='1.0' encoding='utf-8'?>\n{DOCTYPE}\n{body}\n",
        encoding="utf-8",
    )


def refuse_overwrite(paths: list[Path], force: bool) -> None:
    existing = [path for path in paths if path.exists()]
    if existing and not force:
        joined = ", ".join(str(path) for path in existing)
        raise FileExistsError(f"Refusing to overwrite without --force: {joined}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply the approved Fall 2026 MusicXML system/page casting.",
        epilog=COLOPHON_FALLBACK,
    )
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow replacement of an existing output and/or report file.",
    )
    args = parser.parse_args()

    if args.source.resolve() == args.output.resolve():
        raise ValueError("Source and output must be different files")
    refuse_overwrite([args.output, args.report], args.force)
    validate_casting_definition()

    tree = ET.parse(args.source)
    root = tree.getroot()
    source_hash = sha256(args.source)
    source_state = validate_score_shape(root)
    removed_break_flags = remove_break_flags(root)
    supports_removed = configure_break_supports(root)
    apply_casting(root)
    break_state = validate_applied_breaks(root)
    output_state = validate_score_shape(root)

    if source_state != output_state:
        raise ValueError(
            "Score counts or musical fingerprint changed while applying casting"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    write_musicxml(tree, args.output)

    reparsed_root = ET.parse(args.output).getroot()
    reparsed_state = validate_score_shape(reparsed_root)
    reparsed_break_state = validate_applied_breaks(reparsed_root)
    if reparsed_state != source_state or reparsed_break_state != break_state:
        raise ValueError("Written MusicXML did not pass round-trip validation")

    report = {
        "source": str(args.source),
        "output": str(args.output),
        "source_sha256": source_hash,
        "output_sha256": sha256(args.output),
        "score_validation": reparsed_state,
        "structure_matches": (
            reparsed_state["structure_fingerprint"]
            == source_state["structure_fingerprint"]
        ),
        "removed_break_attributes": removed_break_flags,
        "replaced_break_support_entries": supports_removed,
        "casting": {
            "music_pages": len(CASTING),
            "booklet_target_pages": 16,
            "systems": sum(len(page) for page in CASTING),
            "pages": [[f"{start}-{end}" for start, end in page] for page in CASTING],
            **break_state,
        },
        "colophon": {
            "musicxml_credit_added": False,
            "reliable_in_dorico": False,
            "fallback": COLOPHON_FALLBACK,
        },
    }
    args.report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
