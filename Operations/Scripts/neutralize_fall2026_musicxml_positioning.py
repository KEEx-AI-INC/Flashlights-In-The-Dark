#!/usr/bin/env python3
"""Create a position-neutral copy of the Fall 2026 24-page MusicXML.

This is a deliberately narrow, non-destructive import-preparation pass.  It
removes MusicXML presentation coordinates (``default-x``, ``default-y``,
``relative-x``, and ``relative-y``), legacy font overrides in semantic text
objects, local print-layout spacing nodes, and explicit visual-only ``offset``
elements (``sound=\"no\"``).  It preserves semantic ``offset`` elements,
including harmony and direction timing anchors, as well as page/system breaks,
page size, lyric placement, musical events, and all text.

The generated report includes a complete lyric-extender inventory and an
audit of lyric anchors that share part/measure/time/voice/number/placement
coordinates.  No lyric anchor is deleted by this pass.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Iterator
import xml.etree.ElementTree as ET

import apply_fall2026_24page_casting as casting


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = (
    ROOT
    / "Engraving/Scores/Fall2026-Provenance/"
    "FlashlightsInTheDark_Fall2026_Dorico24PageCasted.musicxml"
)
DEFAULT_OUTPUT = (
    ROOT
    / "Engraving/Scores/Fall2026-Provenance/"
    "FlashlightsInTheDark_Fall2026_Dorico24PageImportNeutral.musicxml"
)
DEFAULT_REPORT = (
    ROOT
    / "Engraving/Scores/Fall2026-Provenance/"
    "FlashlightsInTheDark_Fall2026_ImportNeutralizationReport.json"
)
CASTING_REPORT = (
    ROOT
    / "Engraving/Scores/Fall2026-Provenance/"
    "FlashlightsInTheDark_Fall2026_24PageCastingReport.json"
)

POSITION_ATTRIBUTES = ("default-x", "default-y", "relative-x", "relative-y")
TYPOGRAPHY_ATTRIBUTES = (
    "font-family",
    "font-size",
    "font-style",
    "font-weight",
    "letter-spacing",
)
# These are semantic text/label objects whose meaning is carried by their
# element/text content.  Their local typography is presentation data that
# should yield to Dorico's project-wide paragraph and notation styles.
TYPOGRAPHY_SCOPE_ROOTS = {
    "credit-words",
    "lyric",
    "words",
    "rehearsal",
    "metronome",
    "dynamics",
    "part-name",
    "part-abbreviation",
    "group-name",
    "group-abbreviation",
    "instrument-name",
    "work-title",
    "movement-title",
    "creator",
    "rights",
    "kind",
    "root-step",
    "root-alter",
    "bass-step",
    "bass-alter",
    "degree-value",
    "degree-alter",
    "degree-type",
}
BREAK_ATTRIBUTES = ("new-page", "new-system", "blank-page", "page-number")
LOCAL_PRINT_SPACING_NODES = {"system-layout", "staff-layout", "measure-layout"}
EXPECTED_NOTE_COUNT = 2787
EXPECTED_LYRIC_ANCHORS = 1376
EXPECTED_FALL_REPLACEMENTS = 388
EXPECTED_FINGERPRINT = (
    "82a6cfbb1b1856cf5af9a733c04df58ee2eeaacd2e611213de1b45ec6df3e111"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def hash_json(payload: Any) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def semantic_element(element: ET.Element) -> dict[str, Any]:
    """Return a whitespace-insensitive but otherwise exact element payload."""
    text = element.text
    if text is not None and not text.strip():
        text = None
    return {
        "tag": element.tag,
        "attributes": dict(sorted(element.attrib.items())),
        "text": text,
        "children": [semantic_element(child) for child in element],
    }


def semantic_hash(root: ET.Element) -> str:
    return hash_json(semantic_element(root))


def indexed_children(element: ET.Element) -> Iterable[tuple[ET.Element, str]]:
    counts: Counter[str] = Counter()
    for child in element:
        counts[child.tag] += 1
        yield child, f"{child.tag}[{counts[child.tag]}]"


def iter_contextual_elements(
    root: ET.Element,
) -> Iterator[tuple[ET.Element, ET.Element | None, str, str | None, str | None]]:
    """Yield elements with parent, indexed path, part id, and measure number."""

    def walk(
        element: ET.Element,
        parent: ET.Element | None,
        path: str,
        part_id: str | None,
        measure_number: str | None,
    ) -> Iterator[
        tuple[ET.Element, ET.Element | None, str, str | None, str | None]
    ]:
        if element.tag == "part":
            part_id = element.get("id")
        elif element.tag == "measure":
            measure_number = element.get("number")
        yield element, parent, path, part_id, measure_number
        for child, suffix in indexed_children(element):
            yield from walk(
                child,
                element,
                f"{path}/{suffix}",
                part_id,
                measure_number,
            )

    yield from walk(root, None, root.tag, None, None)


def position_attribute_counts(root: ET.Element) -> dict[str, int]:
    return {
        attribute: sum(1 for element in root.iter() if attribute in element.attrib)
        for attribute in POSITION_ATTRIBUTES
    }


def remove_position_attributes(root: ET.Element) -> list[dict[str, Any]]:
    removals: list[dict[str, Any]] = []
    for element, _parent, path, part_id, measure_number in list(
        iter_contextual_elements(root)
    ):
        for attribute in POSITION_ATTRIBUTES:
            if attribute not in element.attrib:
                continue
            removals.append(
                {
                    "path": path,
                    "part": part_id,
                    "measure": measure_number,
                    "element": element.tag,
                    "attribute": attribute,
                    "before": element.attrib.pop(attribute),
                    "after": None,
                    "reason": (
                        "Removed a presentation-only Finale coordinate so Dorico "
                        "can apply its own global engraving defaults."
                    ),
                }
            )
    return removals


def scoped_typography_attribute_counts(
    root: ET.Element,
) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)

    def walk(element: ET.Element, active_scope: str | None = None) -> None:
        scope = active_scope
        if element.tag in TYPOGRAPHY_SCOPE_ROOTS:
            scope = element.tag
        if scope is not None:
            for attribute in TYPOGRAPHY_ATTRIBUTES:
                if attribute in element.attrib:
                    counts[element.tag][attribute] += 1
        for child in element:
            walk(child, scope)

    walk(root)
    return {
        tag: dict(sorted(attributes.items()))
        for tag, attributes in sorted(counts.items())
    }


def remove_legacy_typography(root: ET.Element) -> list[dict[str, Any]]:
    removals: list[dict[str, Any]] = []

    def walk(
        element: ET.Element,
        path: str,
        part_id: str | None,
        measure_number: str | None,
        active_scope: str | None = None,
    ) -> None:
        if element.tag == "part":
            part_id = element.get("id")
        elif element.tag == "measure":
            measure_number = element.get("number")

        scope = active_scope
        if element.tag in TYPOGRAPHY_SCOPE_ROOTS:
            scope = element.tag
        if scope is not None:
            for attribute in TYPOGRAPHY_ATTRIBUTES:
                if attribute not in element.attrib:
                    continue
                removals.append(
                    {
                        "path": path,
                        "part": part_id,
                        "measure": measure_number,
                        "scope": scope,
                        "element": element.tag,
                        "attribute": attribute,
                        "before": element.attrib.pop(attribute),
                        "after": None,
                        "reason": (
                            "Removed a legacy presentation font override so "
                            "Dorico's global notation/paragraph style controls it."
                        ),
                    }
                )
        for child, suffix in indexed_children(element):
            walk(
                child,
                f"{path}/{suffix}",
                part_id,
                measure_number,
                scope,
            )

    walk(root, root.tag, None, None)
    return removals


def remove_print_only_offsets(root: ET.Element) -> list[dict[str, Any]]:
    """Remove only offsets explicitly marked as visual, never timing anchors."""
    removals: list[dict[str, Any]] = []
    for element, parent, path, part_id, measure_number in list(
        iter_contextual_elements(root)
    ):
        if element.tag != "offset" or element.get("sound") != "no":
            continue
        if parent is None:
            raise ValueError("An offset element unexpectedly has no parent")
        removals.append(
            {
                "path": path,
                "part": part_id,
                "measure": measure_number,
                "parent": parent.tag,
                "value": (element.text or "").strip(),
                "attributes": dict(sorted(element.attrib.items())),
                "reason": (
                    "Removed an explicitly visual-only offset (sound=no); it "
                    "does not carry playback or cue timing."
                ),
            }
        )
        parent.remove(element)
    return removals


def remove_local_print_spacing(root: ET.Element) -> list[dict[str, Any]]:
    """Remove local print spacing while retaining page size and break flags."""
    removals: list[dict[str, Any]] = []
    for print_node, _parent, path, part_id, measure_number in list(
        iter_contextual_elements(root)
    ):
        if print_node.tag != "print":
            continue
        for child in list(print_node):
            if child.tag not in LOCAL_PRINT_SPACING_NODES:
                continue
            removals.append(
                {
                    "path": f"{path}/{child.tag}",
                    "part": part_id,
                    "measure": measure_number,
                    "element": child.tag,
                    "before": semantic_element(child),
                    "reason": (
                        "Removed an imported measure-local print spacing block; "
                        "page-layout and page/system break metadata remain intact."
                    ),
                }
            )
            print_node.remove(child)
    return removals


def remove_empty_print_shells(root: ET.Element) -> list[dict[str, Any]]:
    """Drop print shells made empty by spacing removal, never break-bearing nodes."""
    removals: list[dict[str, Any]] = []
    for print_node, parent, path, part_id, measure_number in list(
        iter_contextual_elements(root)
    ):
        if print_node.tag != "print" or parent is None:
            continue
        if print_node.attrib or len(print_node) or (print_node.text or "").strip():
            continue
        removals.append(
            {
                "path": path,
                "part": part_id,
                "measure": measure_number,
                "reason": "Removed an empty print shell after spacing neutralization.",
            }
        )
        parent.remove(print_node)
    return removals


def break_payload(root: ET.Element) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for part in root.findall("part"):
        part_id = part.get("id", "")
        for measure in part.findall("measure"):
            for index, print_node in enumerate(measure.findall("print"), start=1):
                attrs = [
                    [attribute, print_node.get(attribute)]
                    for attribute in BREAK_ATTRIBUTES
                    if attribute in print_node.attrib
                ]
                if attrs:
                    rows.append(
                        [part_id, measure.get("number", ""), index, attrs]
                    )
    return rows


def page_layout_payload(root: ET.Element) -> list[dict[str, Any]]:
    return [
        {"path": path, "value": semantic_element(element)}
        for element, _parent, path, _part_id, _measure_number in (
            iter_contextual_elements(root)
        )
        if element.tag == "page-layout"
    ]


def staff_line_payload(root: ET.Element) -> list[list[str | None]]:
    rows: list[list[str | None]] = []
    for part in root.findall("part"):
        part_id = part.get("id")
        for measure in part.findall("measure"):
            for details in measure.findall("./attributes/staff-details"):
                rows.append(
                    [
                        part_id,
                        measure.get("number"),
                        details.get("number"),
                        details.get("print-object"),
                        details.findtext("staff-lines"),
                    ]
                )
    return rows


def semantic_offset_inventory(root: ET.Element) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for element, parent, path, part_id, measure_number in (
        iter_contextual_elements(root)
    ):
        if element.tag != "offset" or element.get("sound") == "no":
            continue
        rows.append(
            {
                "path": path,
                "part": part_id,
                "measure": measure_number,
                "parent": None if parent is None else parent.tag,
                "value": (element.text or "").strip(),
                "attributes": dict(sorted(element.attrib.items())),
                "classification": (
                    "semantic timing anchor; sound defaults to yes when omitted"
                    if element.get("sound") is None
                    else "semantic timing anchor; sound=yes"
                ),
                "action": "preserved",
            }
        )
    return rows


def lyric_signature(lyric: ET.Element) -> str:
    """Hash lyric semantics while ignoring removable presentation attributes."""
    clone = deepcopy(lyric)
    for element in clone.iter():
        for attribute in (*POSITION_ATTRIBUTES, *TYPOGRAPHY_ATTRIBUTES):
            element.attrib.pop(attribute, None)
    return hash_json(semantic_element(clone))


def lyric_inventory(root: ET.Element) -> dict[str, Any]:
    anchors: list[dict[str, Any]] = []
    extenders: list[dict[str, Any]] = []
    by_coordinate: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)

    for part in root.findall("part"):
        part_id = part.get("id", "")
        divisions = 1
        for measure in part.findall("measure"):
            measure_number = measure.get("number", "")
            cursor = 0
            last_onset = 0
            note_index = 0
            for item in measure:
                if item.tag == "attributes":
                    divisions_text = item.findtext("divisions")
                    if divisions_text:
                        divisions = int(divisions_text)
                    continue
                if item.tag == "backup":
                    cursor -= int(item.findtext("duration", "0"))
                    continue
                if item.tag == "forward":
                    cursor += int(item.findtext("duration", "0"))
                    continue
                if item.tag != "note":
                    continue

                note_index += 1
                is_chord = item.find("chord") is not None
                onset = last_onset if is_chord else cursor
                if not is_chord:
                    last_onset = onset
                voice = item.findtext("voice", "1")
                onset_quarters = str(Fraction(onset, divisions))

                for lyric_index, lyric in enumerate(item.findall("lyric"), start=1):
                    number = lyric.get("number", "1")
                    placement = lyric.get("placement")
                    text = lyric.findtext("text")
                    row = {
                        "part": part_id,
                        "measure": measure_number,
                        "duration_offset": onset,
                        "divisions": divisions,
                        "quarter_note_offset": onset_quarters,
                        "note_index": note_index,
                        "lyric_index": lyric_index,
                        "voice": voice,
                        "number": number,
                        "placement": placement,
                        "syllabic": lyric.findtext("syllabic"),
                        "text": text,
                        "signature": lyric_signature(lyric),
                    }
                    anchors.append(row)
                    coordinate = (
                        part_id,
                        measure_number,
                        onset_quarters,
                        voice,
                        number,
                        "" if placement is None else placement,
                    )
                    by_coordinate[coordinate].append(row)

                    for extend_index, extend in enumerate(
                        lyric.findall("extend"), start=1
                    ):
                        extenders.append(
                            {
                                **{
                                    key: row[key]
                                    for key in (
                                        "part",
                                        "measure",
                                        "duration_offset",
                                        "divisions",
                                        "quarter_note_offset",
                                        "note_index",
                                        "lyric_index",
                                        "voice",
                                        "number",
                                        "placement",
                                        "syllabic",
                                        "text",
                                    )
                                },
                                "extend_index": extend_index,
                                "extend_type": extend.get("type"),
                                "extend_attributes": dict(
                                    sorted(extend.attrib.items())
                                ),
                            }
                        )

                if not is_chord and item.find("grace") is None:
                    cursor += int(item.findtext("duration", "0"))

    coordinate_clusters: list[dict[str, Any]] = []
    exact_duplicate_clusters: list[dict[str, Any]] = []
    nonidentical_clusters: list[dict[str, Any]] = []
    exact_duplicate_anchor_count = 0
    for coordinate, occurrences in sorted(by_coordinate.items()):
        if len(occurrences) < 2:
            continue
        signature_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for occurrence in occurrences:
            signature_groups[occurrence["signature"]].append(occurrence)
        occurrence_rows = [
            {
                key: occurrence[key]
                for key in (
                    "note_index",
                    "lyric_index",
                    "syllabic",
                    "text",
                    "signature",
                )
            }
            | {
                "extends": [
                    {
                        "type": extend.get("type"),
                        "attributes": dict(sorted(extend.attrib.items())),
                    }
                    for extend in (
                        measure_lyric_element(
                            root,
                            occurrence["part"],
                            occurrence["measure"],
                            occurrence["note_index"],
                            occurrence["lyric_index"],
                        ).findall("extend")
                    )
                ]
            }
            for occurrence in occurrences
        ]
        cluster = {
            "coordinate": {
                "part": coordinate[0],
                "measure": coordinate[1],
                "quarter_note_offset": coordinate[2],
                "voice": coordinate[3],
                "number": coordinate[4],
                "placement": coordinate[5] or None,
            },
            "anchor_count": len(occurrences),
            "occurrences": occurrence_rows,
        }
        coordinate_clusters.append(cluster)

        duplicate_groups = [
            group for group in signature_groups.values() if len(group) > 1
        ]
        if duplicate_groups:
            exact_duplicate_anchor_count += sum(len(group) for group in duplicate_groups)
            exact_duplicate_clusters.append(
                {
                    **cluster,
                    "duplicate_group_sizes": [len(group) for group in duplicate_groups],
                    "action": "preserved",
                    "reason": (
                        "Inventory-only safeguard: lyric anchor count must remain "
                        "1,376. Review before any future semantic deletion."
                    ),
                }
            )
        else:
            nonidentical_clusters.append(
                {
                    **cluster,
                    "action": "preserved",
                    "reason": (
                        "Same coordinate but distinct lyric semantics; not a "
                        "demonstrably exact duplicate."
                    ),
                }
            )

    extender_types = Counter(item["extend_type"] for item in extenders)
    return {
        "anchor_count": len(anchors),
        "anchor_semantic_hash": hash_json(
            [
                [
                    item["part"],
                    item["measure"],
                    item["quarter_note_offset"],
                    item["note_index"],
                    item["lyric_index"],
                    item["voice"],
                    item["number"],
                    item["placement"],
                    item["signature"],
                ]
                for item in anchors
            ]
        ),
        "extend_element_count": len(extenders),
        "extend_type_counts": dict(sorted(extender_types.items(), key=str)),
        "extend_elements": extenders,
        "same_coordinate_cluster_count": len(coordinate_clusters),
        "same_coordinate_anchor_count": sum(
            item["anchor_count"] for item in coordinate_clusters
        ),
        "exact_duplicate_cluster_count": len(exact_duplicate_clusters),
        "exact_duplicate_anchor_count": exact_duplicate_anchor_count,
        "exact_duplicate_clusters": exact_duplicate_clusters,
        "same_coordinate_nonidentical_cluster_count": len(nonidentical_clusters),
        "same_coordinate_nonidentical_clusters": nonidentical_clusters,
        "lyric_anchors_removed": 0,
    }


def measure_lyric_element(
    root: ET.Element,
    part_id: str,
    measure_number: str,
    note_index: int,
    lyric_index: int,
) -> ET.Element:
    part = root.find(f"./part[@id='{part_id}']")
    if part is None:
        raise ValueError(f"Missing part {part_id}")
    measure = part.find(f"./measure[@number='{measure_number}']")
    if measure is None:
        raise ValueError(f"Missing {part_id} measure {measure_number}")
    notes = measure.findall("note")
    lyrics = notes[note_index - 1].findall("lyric")
    return lyrics[lyric_index - 1]


def verify_provenance(source: Path) -> dict[str, Any]:
    report = json.loads(CASTING_REPORT.read_text(encoding="utf-8"))
    state = report.get("score_validation", {})
    source_provenance = report.get("source_provenance", {})
    actual_hash = sha256(source)
    if report.get("output_sha256") != actual_hash:
        raise ValueError("Source does not match the 24-page casting report")
    if state.get("note_count") != EXPECTED_NOTE_COUNT:
        raise ValueError("Casting report does not record 2,787 note elements")
    if state.get("lyric_anchors") != EXPECTED_LYRIC_ANCHORS:
        raise ValueError("Casting report does not record 1,376 lyric anchors")
    if state.get("structure_fingerprint") != EXPECTED_FINGERPRINT:
        raise ValueError("Casting report does not match the canonical fingerprint")
    if source_provenance.get("fall_replacements") != EXPECTED_FALL_REPLACEMENTS:
        raise ValueError("Casting report does not record 388 Fall replacements")
    if source_provenance.get("verified") is not True:
        raise ValueError("24-page source provenance is not validated")
    return {
        "casting_report": display_path(CASTING_REPORT),
        "casting_report_sha256": sha256(CASTING_REPORT),
        "source_sha256_matches_casting_report": True,
        "fall_replacements": EXPECTED_FALL_REPLACEMENTS,
        "verified": True,
    }


def apply_neutralization(root: ET.Element) -> dict[str, Any]:
    position_removals = remove_position_attributes(root)
    typography_removals = remove_legacy_typography(root)
    visual_offset_removals = remove_print_only_offsets(root)
    print_spacing_removals = remove_local_print_spacing(root)
    empty_print_removals = remove_empty_print_shells(root)
    return {
        "position_attribute_removals": position_removals,
        "typography_attribute_removals": typography_removals,
        "visual_only_offset_removals": visual_offset_removals,
        "local_print_spacing_removals": print_spacing_removals,
        "empty_print_shell_removals": empty_print_removals,
    }


def transform(
    source: Path,
    output: Path,
    report_path: Path,
    *,
    force: bool = False,
    verify_chain: bool = True,
) -> dict[str, Any]:
    if source.resolve() == output.resolve():
        raise ValueError("Source and output must be different files")
    casting.base.refuse_overwrite([output, report_path], force)
    casting.validate_profile()

    provenance = verify_provenance(source) if verify_chain else None
    tree = ET.parse(source)
    root = tree.getroot()
    source_state = casting.validate_extended_score_shape(root)
    source_breaks = casting.base.validate_applied_breaks(root)
    source_break_payload = break_payload(root)
    source_page_layout = page_layout_payload(root)
    source_staff_lines = staff_line_payload(root)
    source_lyrics = lyric_inventory(root)
    source_semantic_offsets = semantic_offset_inventory(root)
    source_position_counts = position_attribute_counts(root)
    source_typography_counts = scoped_typography_attribute_counts(root)
    source_semantic_hash = semantic_hash(root)

    if source_state["note_count"] != EXPECTED_NOTE_COUNT:
        raise ValueError("Source note-element count is not 2,787")
    if source_state["lyric_anchors"] != EXPECTED_LYRIC_ANCHORS:
        raise ValueError("Source lyric-anchor count is not 1,376")
    if source_state["structure_fingerprint"] != EXPECTED_FINGERPRINT:
        raise ValueError("Source does not match the canonical musical fingerprint")
    if not source_staff_lines or any(row[-1] != "5" for row in source_staff_lines):
        raise ValueError("Source contains a non-five-line staff override")

    expected_root = deepcopy(root)
    expected_changes = apply_neutralization(expected_root)
    expected_semantic_hash = semantic_hash(expected_root)

    changes = apply_neutralization(root)
    if changes != expected_changes or semantic_hash(root) != expected_semantic_hash:
        raise ValueError("Neutralization was not deterministic")

    transformed_state = casting.validate_extended_score_shape(root)
    transformed_breaks = casting.base.validate_applied_breaks(root)
    transformed_lyrics = lyric_inventory(root)
    transformed_staff_lines = staff_line_payload(root)
    transformed_page_layout = page_layout_payload(root)
    transformed_semantic_offsets = semantic_offset_inventory(root)
    if transformed_state != source_state:
        raise ValueError("Parts, measures, anchors, or musical fingerprint changed")
    if transformed_breaks != source_breaks or break_payload(root) != source_break_payload:
        raise ValueError("Page/system break metadata changed")
    if transformed_lyrics != source_lyrics:
        raise ValueError("Lyric text, routing, extenders, or anchor topology changed")
    if transformed_staff_lines != source_staff_lines:
        raise ValueError("Five-line staff overrides changed")
    if transformed_page_layout != source_page_layout:
        raise ValueError("Page size or page-layout metadata changed")
    if transformed_semantic_offsets != source_semantic_offsets:
        raise ValueError("Semantic harmony/direction timing offsets changed")

    output.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    casting.base.write_musicxml(tree, output)

    reparsed = ET.parse(output).getroot()
    roundtrip_state = casting.validate_extended_score_shape(reparsed)
    roundtrip_breaks = casting.base.validate_applied_breaks(reparsed)
    roundtrip_lyrics = lyric_inventory(reparsed)
    roundtrip_staff_lines = staff_line_payload(reparsed)
    roundtrip_page_layout = page_layout_payload(reparsed)
    roundtrip_offsets = semantic_offset_inventory(reparsed)
    output_position_counts = position_attribute_counts(reparsed)
    output_typography_counts = scoped_typography_attribute_counts(reparsed)
    remaining_print_spacing = [
        {"path": path, "element": element.tag}
        for element, _parent, path, _part_id, _measure_number in (
            iter_contextual_elements(reparsed)
        )
        if element.tag in LOCAL_PRINT_SPACING_NODES
        and "/print[" in path
    ]
    remaining_visual_offsets = [
        {"path": path, "value": (element.text or "").strip()}
        for element, _parent, path, _part_id, _measure_number in (
            iter_contextual_elements(reparsed)
        )
        if element.tag == "offset" and element.get("sound") == "no"
    ]

    validation = {
        "passed": (
            roundtrip_state == source_state
            and roundtrip_breaks == source_breaks
            and break_payload(reparsed) == source_break_payload
            and roundtrip_lyrics == source_lyrics
            and roundtrip_staff_lines == source_staff_lines
            and roundtrip_page_layout == source_page_layout
            and roundtrip_offsets == source_semantic_offsets
            and semantic_hash(reparsed) == expected_semantic_hash
            and all(value == 0 for value in output_position_counts.values())
            and not output_typography_counts
            and not remaining_print_spacing
            and not remaining_visual_offsets
        ),
        "part_ids": roundtrip_state["part_ids"],
        "measure_counts": roundtrip_state["measure_counts"],
        "note_count": roundtrip_state["note_count"],
        "lyric_anchor_count": roundtrip_state["lyric_anchors"],
        "fall_replacement_count": (
            EXPECTED_FALL_REPLACEMENTS if provenance is not None else None
        ),
        "structure_fingerprint": roundtrip_state["structure_fingerprint"],
        "canonical_structure_matches": (
            roundtrip_state["structure_fingerprint"] == EXPECTED_FINGERPRINT
        ),
        "break_metadata_matches": (
            roundtrip_breaks == source_breaks
            and break_payload(reparsed) == source_break_payload
        ),
        "page_layout_matches": roundtrip_page_layout == source_page_layout,
        "lyric_semantics_match": roundtrip_lyrics == source_lyrics,
        "semantic_offsets_match": roundtrip_offsets == source_semantic_offsets,
        "five_line_overrides_match": roundtrip_staff_lines == source_staff_lines,
        "five_line_override_count": len(roundtrip_staff_lines),
        "all_encoded_staves_five_line": bool(roundtrip_staff_lines)
        and all(row[-1] == "5" for row in roundtrip_staff_lines),
        "source_semantic_hash": source_semantic_hash,
        "allowed_change_projection_hash": expected_semantic_hash,
        "output_semantic_hash": semantic_hash(reparsed),
        "output_matches_allowed_change_projection": (
            semantic_hash(reparsed) == expected_semantic_hash
        ),
        "remaining_position_attributes": output_position_counts,
        "remaining_legacy_typography_attributes": output_typography_counts,
        "remaining_local_print_spacing": remaining_print_spacing,
        "remaining_visual_only_offsets": remaining_visual_offsets,
    }
    if not validation["passed"]:
        raise ValueError(f"Round-trip position-neutral validation failed: {validation}")

    semantic_offset_parents = Counter(
        item["parent"] for item in roundtrip_offsets
    )
    report = {
        "profile": (
            "Fall 2026 24-page Dorico position-and-typography-neutral import source"
        ),
        "source": display_path(source),
        "output": display_path(output),
        "source_sha256": sha256(source),
        "output_sha256": sha256(output),
        "provenance": provenance,
        "neutralization": {
            "source_position_attribute_counts": source_position_counts,
            "position_attribute_removal_count": len(
                changes["position_attribute_removals"]
            ),
            "position_attribute_removals": changes[
                "position_attribute_removals"
            ],
            "source_typography_attribute_counts": source_typography_counts,
            "typography_attribute_removal_count": len(
                changes["typography_attribute_removals"]
            ),
            "typography_attribute_removals": changes[
                "typography_attribute_removals"
            ],
            "visual_only_offset_removal_count": len(
                changes["visual_only_offset_removals"]
            ),
            "visual_only_offset_removals": changes[
                "visual_only_offset_removals"
            ],
            "local_print_spacing_removal_count": len(
                changes["local_print_spacing_removals"]
            ),
            "local_print_spacing_removals": changes[
                "local_print_spacing_removals"
            ],
            "empty_print_shell_removal_count": len(
                changes["empty_print_shell_removals"]
            ),
            "empty_print_shell_removals": changes[
                "empty_print_shell_removals"
            ],
            "semantic_offset_preserved_count": len(roundtrip_offsets),
            "semantic_offset_parent_counts": dict(
                sorted(semantic_offset_parents.items(), key=str)
            ),
            "semantic_offsets_preserved": roundtrip_offsets,
            "semantic_offset_policy": (
                "Preserved every offset whose sound attribute is yes or omitted; "
                "these are timing anchors, not cosmetic x/y overrides."
            ),
        },
        "lyric_inventory": roundtrip_lyrics,
        "casting": roundtrip_breaks,
        "page_layout": {
            "count": len(roundtrip_page_layout),
            "hash": hash_json(roundtrip_page_layout),
            "matches_source": roundtrip_page_layout == source_page_layout,
        },
        "staff_lines": {
            "override_count": len(roundtrip_staff_lines),
            "all_five_line": all(row[-1] == "5" for row in roundtrip_staff_lines),
            "hash": hash_json(roundtrip_staff_lines),
        },
        "validation": validation,
    }
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Create a separate position-and-typography-neutral MusicXML copy "
            "for a clean "
            "Dorico import."
        )
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow replacement of this transform's output/report only.",
    )
    parser.add_argument(
        "--skip-provenance-check",
        action="store_true",
        help="For isolated test fixtures only; production runs verify the chain.",
    )
    args = parser.parse_args()
    report = transform(
        args.source,
        args.output,
        args.report,
        force=args.force,
        verify_chain=not args.skip_provenance_check,
    )
    summary = {
        "output": report["output"],
        "output_sha256": report["output_sha256"],
        "position_attribute_removal_count": report["neutralization"][
            "position_attribute_removal_count"
        ],
        "typography_attribute_removal_count": report["neutralization"][
            "typography_attribute_removal_count"
        ],
        "local_print_spacing_removal_count": report["neutralization"][
            "local_print_spacing_removal_count"
        ],
        "semantic_offset_preserved_count": report["neutralization"][
            "semantic_offset_preserved_count"
        ],
        "lyric_extend_element_count": report["lyric_inventory"][
            "extend_element_count"
        ],
        "exact_duplicate_lyric_cluster_count": report["lyric_inventory"][
            "exact_duplicate_cluster_count"
        ],
        "validation_passed": report["validation"]["passed"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
