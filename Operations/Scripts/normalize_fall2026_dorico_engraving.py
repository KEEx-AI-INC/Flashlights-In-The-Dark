#!/usr/bin/env python3
"""Conservatively normalize engraving metadata in the cast Fall 2026 score.

The input is the lyric-corrected, page-cast performer-score MusicXML.  This
pass removes only local positioning attributes inside semantic engraving
objects that Dorico can place itself, and normalizes lyric placement by the
actual voice topology of each staff.  It preserves musical events, lyric text
and anchors, five-line staff overrides, and every approved casting break.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable
import xml.etree.ElementTree as ET

from apply_fall2026_casting_breaks import (
    EXPECTED_LYRIC_ANCHORS,
    EXPECTED_STRUCTURE_FINGERPRINT,
    collect_break_map,
    expected_break_map,
    normalized_score_fingerprint,
    validate_score_shape,
)
from correct_fall2026_dorico_lyrics import iter_lyric_refs


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = (
    ROOT / "Engraving/Scores/FlashlightsInTheDark_Fall2026_PerformerScore.musicxml"
)
DEFAULT_OUTPUT = (
    ROOT
    / "Engraving/Scores/Fall2026-Provenance/FlashlightsInTheDark_Fall2026_DoricoNormalized.musicxml"
)
DEFAULT_REPORT = (
    ROOT
    / "Engraving/Scores/Fall2026-Provenance/FlashlightsInTheDark_Fall2026_DoricoNormalizationReport.json"
)
IMPORT_REPORT = (
    ROOT
    / "Engraving/Scores/Fall2026-Provenance/FlashlightsInTheDark_Fall2026_ImportReport.json"
)
IMPORT_VALIDATION = (
    ROOT
    / "Engraving/Scores/Fall2026-Provenance/FlashlightsInTheDark_Fall2026_ImportValidation.json"
)
TEXT_CORRECTION_REPORT = (
    ROOT
    / "Engraving/Scores/Fall2026-Provenance/FlashlightsInTheDark_Fall2026_TextCorrectionReport.json"
)
CASTING_REPORT = (
    ROOT
    / "Engraving/Scores/Fall2026-Provenance/FlashlightsInTheDark_Fall2026_FinalCastingReport.json"
)

DOCTYPE = (
    '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
    '"http://www.musicxml.org/dtds/partwise.dtd">'
)

POSITION_ATTRIBUTES = ("default-x", "default-y", "relative-x", "relative-y")
SAFE_SCOPE_ROOTS = {"lyric", "direction", "harmony", "dynamics", "notations"}
EXPECTED_NOTE_COUNT = 2787
EXPECTED_FALL_REPLACEMENTS = 388
EXPECTED_MULTI_VOICE_PARTS = {"P4", "P5", "P6"}


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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_provenance_chain(source: Path) -> dict[str, Any]:
    import_report = load_json(IMPORT_REPORT)
    import_validation = load_json(IMPORT_VALIDATION)
    text_report = load_json(TEXT_CORRECTION_REPORT)
    casting_report = load_json(CASTING_REPORT)
    source_hash = sha256(source)

    if import_report.get("matched_rows") != EXPECTED_FALL_REPLACEMENTS:
        raise ValueError("Import report no longer records 388 matched Fall replacements")
    if import_validation.get("matched_targets") != EXPECTED_FALL_REPLACEMENTS:
        raise ValueError("Import validation no longer records 388 matched Fall targets")
    if not import_validation.get("structure_matches"):
        raise ValueError("Fall import validation does not match canonical structure")
    if text_report.get("output_sha256") != casting_report.get("source_sha256"):
        raise ValueError("Text-correction and final-casting reports are not chained")
    if casting_report.get("output_sha256") != source_hash:
        raise ValueError("Source does not match the final casting report")

    return {
        "fall_replacements": EXPECTED_FALL_REPLACEMENTS,
        "import_output_sha256": import_report.get("output_sha256"),
        "text_corrected_sha256": text_report.get("output_sha256"),
        "cast_source_sha256": source_hash,
        "reports_chain": True,
    }


def indexed_children(element: ET.Element) -> Iterable[tuple[ET.Element, str]]:
    counts: Counter[str] = Counter()
    for child in element:
        counts[child.tag] += 1
        yield child, f"{child.tag}[{counts[child.tag]}]"


def remove_safe_positioning(root: ET.Element) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for part in root.findall("part"):
        part_id = part.get("id", "")
        for measure in part.findall("measure"):
            measure_number = measure.get("number", "")

            def walk(
                element: ET.Element,
                path: str,
                active_scope: str | None = None,
            ) -> None:
                scope = active_scope
                if scope is None and element.tag in SAFE_SCOPE_ROOTS:
                    scope = element.tag
                if scope is not None:
                    for attribute in POSITION_ATTRIBUTES:
                        if attribute not in element.attrib:
                            continue
                        before = element.attrib.pop(attribute)
                        changes.append(
                            {
                                "part": part_id,
                                "measure": measure_number,
                                "path": path,
                                "scope": scope,
                                "element": element.tag,
                                "attribute": attribute,
                                "before": before,
                                "after": None,
                                "reason": (
                                    "Removed a Finale local offset from a semantic "
                                    "engraving object so Dorico can place it globally."
                                ),
                            }
                        )
                for child, child_path in indexed_children(element):
                    walk(child, f"{path}/{child_path}", scope)

            for child, child_path in indexed_children(measure):
                walk(child, f"measure[{measure_number}]/{child_path}")
    return changes


def scan_remaining_positioning(root: ET.Element) -> dict[str, list[dict[str, Any]]]:
    preserved_page_furniture: list[dict[str, Any]] = []
    ambiguities: list[dict[str, Any]] = []
    for element in root.iter():
        for attribute in POSITION_ATTRIBUTES:
            if attribute not in element.attrib:
                continue
            item = {
                "element": element.tag,
                "attribute": attribute,
                "value": element.get(attribute),
                "text": (element.text or "").strip() or None,
            }
            if element.tag == "credit-words":
                item["reason"] = (
                    "Preserved intentional first-page credit positioning outside "
                    "the music frame."
                )
                preserved_page_furniture.append(item)
            else:
                item["reason"] = (
                    "Positioning lies outside the explicitly safe semantic scopes; "
                    "left unchanged for manual review."
                )
                ambiguities.append(item)
    return {
        "preserved_page_furniture": preserved_page_furniture,
        "ambiguities": ambiguities,
    }


def measure_lyric_onsets(measure: ET.Element) -> dict[int, set[str]]:
    cursor = 0
    last_onset = 0
    result: dict[int, set[str]] = defaultdict(set)
    for item in measure:
        if item.tag == "note":
            onset = last_onset if item.find("chord") is not None else cursor
            if item.find("chord") is None:
                last_onset = onset
            if any((lyric.findtext("text") or "").strip() for lyric in item.findall("lyric")):
                result[onset].add(item.findtext("voice", "1"))
            if item.find("chord") is None and item.find("grace") is None:
                cursor += int(item.findtext("duration", "0"))
        elif item.tag == "backup":
            cursor -= int(item.findtext("duration", "0"))
        elif item.tag == "forward":
            cursor += int(item.findtext("duration", "0"))
    return result


def detect_multi_voice_parts(root: ET.Element) -> dict[str, list[dict[str, Any]]]:
    evidence: dict[str, list[dict[str, Any]]] = {}
    for part in root.findall("part"):
        part_id = part.get("id", "")
        hits: list[dict[str, Any]] = []
        for measure in part.findall("measure"):
            for onset, voices in measure_lyric_onsets(measure).items():
                if len(voices) > 1:
                    hits.append(
                        {
                            "measure": measure.get("number", ""),
                            "duration_offset": onset,
                            "voices": sorted(voices),
                        }
                    )
        if hits:
            evidence[part_id] = hits
    if set(evidence) != EXPECTED_MULTI_VOICE_PARTS:
        raise ValueError(
            f"Unexpected simultaneous lyric-voice topology: {sorted(evidence)}"
        )
    return evidence


def normalize_lyric_placement(
    root: ET.Element, multi_voice_parts: set[str]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    third_lane_before: list[list[Any]] = []
    for ref in iter_lyric_refs(root):
        if ref.voice != "1" and ref.lyric.get("number", "1") != "1":
            third_lane_before.append(
                [
                    ref.part,
                    ref.measure,
                    ref.note_index,
                    ref.lyric_index,
                    ref.voice,
                    ref.lyric.get("number", "1"),
                ]
            )

        if ref.part in multi_voice_parts and ref.voice == "1":
            target = "above"
            rationale = "upper voice in a staff with simultaneous lyric voices"
        else:
            target = "below"
            rationale = (
                "lower voice or conventional placement on a staff without "
                "simultaneous lyric voices"
            )
        before = ref.lyric.get("placement")
        if before == target:
            continue
        ref.lyric.set("placement", target)
        changes.append(
            {
                **ref.location(),
                "attribute": "placement",
                "before": before,
                "after": target,
                "reason": rationale,
            }
        )

    third_lane_after = [
        [
            ref.part,
            ref.measure,
            ref.note_index,
            ref.lyric_index,
            ref.voice,
            ref.lyric.get("number", "1"),
        ]
        for ref in iter_lyric_refs(root)
        if ref.voice != "1" and ref.lyric.get("number", "1") != "1"
    ]
    if third_lane_before != third_lane_after:
        raise ValueError("Third lyric-lane anchor assignment changed")
    if any(
        ref.lyric.get("placement") != "below"
        for ref in iter_lyric_refs(root)
        if ref.voice != "1" and ref.lyric.get("number", "1") != "1"
    ):
        raise ValueError("Third lyric lane is not consistently below")

    summary = {
        "multi_voice_parts": sorted(multi_voice_parts),
        "placement_changes": len(changes),
        "third_lane_anchor_count": len(third_lane_after),
        "third_lane_anchor_hash": hash_json(third_lane_after),
        "rule": {
            "multi_voice_staff_voice_1": "above",
            "lower_voices": "below",
            "single_voice_staff": "below",
            "third_stream": "retain its lyric number and place below",
        },
    }
    return changes, summary


def lyric_semantic_payload(root: ET.Element) -> list[list[Any]]:
    result: list[list[Any]] = []
    for ref in iter_lyric_refs(root):
        extend = ref.lyric.find("extend")
        result.append(
            [
                ref.part,
                ref.measure,
                ref.note_index,
                ref.lyric_index,
                ref.voice,
                ref.lyric.get("number", "1"),
                ref.lyric.findtext("syllabic"),
                ref.lyric.findtext("text"),
                None if extend is None else extend.get("type"),
            ]
        )
    return result


def staff_line_payload(root: ET.Element) -> list[list[str | None]]:
    result: list[list[str | None]] = []
    for part in root.findall("part"):
        for measure in part.findall("measure"):
            for staff_lines in measure.findall("./attributes/staff-details/staff-lines"):
                result.append(
                    [part.get("id"), measure.get("number"), staff_lines.text]
                )
    return result


def validate_casting(root: ET.Element) -> dict[str, Any]:
    wanted = expected_break_map()
    maps: dict[str, dict[int, str]] = {}
    for part in root.findall("part"):
        part_id = part.get("id", "")
        actual = collect_break_map(part)
        if actual != wanted:
            raise ValueError(f"Casting breaks changed in {part_id}")
        maps[part_id] = actual
    return {
        "identical_across_parts": len({json.dumps(m, sort_keys=True) for m in maps.values()}) == 1,
        "page_break_starts": [key for key, value in wanted.items() if value == "new-page"],
        "system_break_starts": [key for key, value in wanted.items() if value == "new-system"],
        "break_instances": sum(len(values) for values in maps.values()),
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
        raise FileExistsError(
            "Refusing to overwrite without --force: "
            + ", ".join(str(path) for path in existing)
        )


def transform(
    source: Path,
    output: Path,
    report_path: Path,
    *,
    force: bool = False,
    verify_chain: bool = True,
) -> dict[str, Any]:
    if source.resolve() == output.resolve():
        raise ValueError("Source and output must differ")
    refuse_overwrite([output, report_path], force)

    provenance = verify_provenance_chain(source) if verify_chain else None
    tree = ET.parse(source)
    root = tree.getroot()
    source_state = validate_score_shape(root)
    if normalized_score_fingerprint(root) != EXPECTED_STRUCTURE_FINGERPRINT:
        raise ValueError("Source does not match the canonical musical fingerprint")
    if source_state["lyric_anchors"] != EXPECTED_LYRIC_ANCHORS:
        raise ValueError("Source lyric-anchor count is not 1,376")
    if len(root.findall("./part/measure/note")) != EXPECTED_NOTE_COUNT:
        raise ValueError("Source note count is not 2,787")

    lyric_before = lyric_semantic_payload(root)
    lyric_hash_before = hash_json(lyric_before)
    staff_lines_before = staff_line_payload(root)
    if not staff_lines_before or any(row[2] != "5" for row in staff_lines_before):
        raise ValueError("Source contains a non-five-line staff override")
    casting_before = validate_casting(root)

    position_changes = remove_safe_positioning(root)
    voice_evidence = detect_multi_voice_parts(root)
    placement_changes, routing = normalize_lyric_placement(root, set(voice_evidence))
    remaining_positioning = scan_remaining_positioning(root)

    lyric_after = lyric_semantic_payload(root)
    staff_lines_after = staff_line_payload(root)
    output_state = validate_score_shape(root)
    casting_after = validate_casting(root)
    if source_state != output_state:
        raise ValueError("Score shape or canonical fingerprint changed")
    if lyric_before != lyric_after:
        raise ValueError("Lyric anchors, text, syllabification, or lane numbers changed")
    if staff_lines_before != staff_lines_after:
        raise ValueError("Five-line staff overrides changed")
    if casting_before != casting_after:
        raise ValueError("Casting breaks changed")

    output.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    write_musicxml(tree, output)
    reparsed = ET.parse(output).getroot()

    roundtrip_state = validate_score_shape(reparsed)
    roundtrip_casting = validate_casting(reparsed)
    roundtrip_lyrics = lyric_semantic_payload(reparsed)
    roundtrip_staff_lines = staff_line_payload(reparsed)
    roundtrip_positions = scan_remaining_positioning(reparsed)
    placement_errors = []
    for ref in iter_lyric_refs(reparsed):
        target = (
            "above"
            if ref.part in EXPECTED_MULTI_VOICE_PARTS and ref.voice == "1"
            else "below"
        )
        if ref.lyric.get("placement") != target:
            placement_errors.append(ref.location())

    validation = {
        "passed": (
            roundtrip_state == source_state
            and roundtrip_casting == casting_before
            and roundtrip_lyrics == lyric_before
            and roundtrip_staff_lines == staff_lines_before
            and not roundtrip_positions["ambiguities"]
            and not placement_errors
        ),
        "part_ids": source_state["part_ids"],
        "measure_counts": source_state["measure_counts"],
        "note_count": len(reparsed.findall("./part/measure/note")),
        "lyric_anchor_count": len(reparsed.findall(".//lyric")),
        "fall_replacements_preserved": (
            provenance is None
            or provenance["fall_replacements"] == EXPECTED_FALL_REPLACEMENTS
        ),
        "structure_fingerprint": roundtrip_state["structure_fingerprint"],
        "canonical_structure_matches": (
            roundtrip_state["structure_fingerprint"]
            == EXPECTED_STRUCTURE_FINGERPRINT
        ),
        "lyric_semantic_hash_before": lyric_hash_before,
        "lyric_semantic_hash_after": hash_json(roundtrip_lyrics),
        "lyric_semantics_match": roundtrip_lyrics == lyric_before,
        "five_line_override_hash_before": hash_json(staff_lines_before),
        "five_line_override_hash_after": hash_json(roundtrip_staff_lines),
        "five_line_overrides_match": roundtrip_staff_lines == staff_lines_before,
        "casting_breaks_match": roundtrip_casting == casting_before,
        "casting": roundtrip_casting,
        "placement_errors": placement_errors,
        "unsafe_positioning_ambiguities": roundtrip_positions["ambiguities"],
    }
    if not validation["passed"]:
        raise ValueError(f"Round-trip normalization validation failed: {validation}")

    report = {
        "source": display_path(source),
        "output": display_path(output),
        "source_sha256": sha256(source),
        "output_sha256": sha256(output),
        "provenance": provenance,
        "position_attribute_changes": position_changes,
        "position_attribute_change_count": len(position_changes),
        "lyric_placement_changes": placement_changes,
        "lyric_placement_change_count": len(placement_changes),
        "lyric_routing": routing,
        "multi_voice_evidence": voice_evidence,
        "preserved_positioning": remaining_positioning["preserved_page_furniture"],
        "ambiguity_flags": remaining_positioning["ambiguities"],
        "validation": validation,
    }
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    report = transform(
        args.source, args.output, args.report, force=args.force, verify_chain=True
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
