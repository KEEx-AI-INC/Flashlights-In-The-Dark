#!/usr/bin/env python3
"""Validate the Fall 2026 performer-score delivery artifacts.

The MusicXML audit is semantic and deterministic.  It reuses the repository's
canonical musical fingerprint implementation and separately checks lyric
content, routing, staff-line state, and the retained 388-replacement
provenance chain.

The optional PDF audit uses Poppler when it is available.  It verifies Letter
portrait geometry, booklet page count, page boxes, embedded fonts, nonblank
rendered pages, and a conservative raster safe margin.  It does not replace a
human collision/readability review.

No invocation is called a final-delivery pass unless both artifacts pass and
``--final-delivery`` is supplied.  A MusicXML-only run is intentionally
reported as incomplete.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any, Iterable
import xml.etree.ElementTree as ET

from apply_fall2026_casting_breaks import normalized_score_fingerprint


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROVENANCE_DIR = (
    ROOT / "Engraving/Scores/Fall2026-Provenance"
)

EXPECTED_PART_IDS = ("P1", "P2", "P3", "P4", "P5", "P6")
EXPECTED_MEASURES_PER_PART = 151
EXPECTED_NOTE_COUNT = 2787
EXPECTED_LYRIC_ANCHORS = 1376
EXPECTED_FALL_REPLACEMENTS = 388
EXPECTED_FINGERPRINT = (
    "82a6cfbb1b1856cf5af9a733c04df58ee2eeaacd2e611213de1b45ec6df3e111"
)
EXPECTED_LYRIC_CONTENT_HASH = (
    "72f5540e2185493c391811dce60d2bdca444a7e00a500e85ddab73cabbb2e796"
)
EXPECTED_PLACEMENT_DISTRIBUTION = {"above": 579, "below": 797}
EXPECTED_MULTI_VOICE_PARTS = {"P4", "P5", "P6"}
EXPECTED_THIRD_LANE_COUNT = 17
EXPECTED_THIRD_LANE_HASH = (
    "3f301228e87caff7526f080fb458806dd6caf64666d6c02e1974e9cdd35bcb9c"
)
EXPECTED_STAGE_E_SHA256 = (
    "a21c0bdce98afe6b365b641e3e5c36d45d66bbf7c222be4d325441ae2e7f06f7"
)

LETTER_WIDTH_POINTS = 612.0
LETTER_HEIGHT_POINTS = 792.0
PAGE_SIZE_TOLERANCE_POINTS = 1.0
DEFAULT_SAFE_MARGIN_POINTS = 18.0
RASTER_DPI = 36

PROVENANCE_REPORTS = {
    "import_report": "FlashlightsInTheDark_Fall2026_ImportReport.json",
    "import_validation": "FlashlightsInTheDark_Fall2026_ImportValidation.json",
    "text_correction": "FlashlightsInTheDark_Fall2026_TextCorrectionReport.json",
    "normalization": "FlashlightsInTheDark_Fall2026_DoricoNormalizationReport.json",
    "stage_e": "FlashlightsInTheDark_Fall2026_StageECleanupReport.json",
    "casting_24_page": "FlashlightsInTheDark_Fall2026_24PageCastingReport.json",
}
STAGE_E_REFERENCE = "FlashlightsInTheDark_Fall2026_StageEClean.musicxml"


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    expected: Any
    actual: Any
    detail: str = ""


def check(
    name: str,
    passed: bool,
    *,
    expected: Any,
    actual: Any,
    detail: str = "",
) -> Check:
    return Check(
        name=name,
        status="pass" if passed else "fail",
        expected=expected,
        actual=actual,
        detail=detail,
    )


def not_checked(name: str, detail: str, *, expected: Any = None) -> Check:
    return Check(
        name=name,
        status="not_checked",
        expected=expected,
        actual=None,
        detail=detail,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_json(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def section_status(checks: Iterable[Check]) -> str:
    statuses = {item.status for item in checks}
    if "fail" in statuses:
        return "failed"
    if "not_checked" in statuses:
        return "incomplete"
    return "passed"


def lyric_content_rows(root: ET.Element) -> list[list[Any]]:
    """Match the established lyric-semantic payload used by normalization.

    Placement and visual offsets are deliberately excluded.  They are audited
    independently, so a Dorico re-export cannot hide text, syllabification, or
    anchor changes behind layout metadata.
    """

    rows: list[list[Any]] = []
    for part in root.findall("part"):
        part_id = part.get("id", "")
        for measure in part.findall("measure"):
            measure_number = measure.get("number", "")
            for note_index, note in enumerate(measure.findall("note"), start=1):
                voice = note.findtext("voice", "1")
                for lyric_index, lyric in enumerate(
                    note.findall("lyric"), start=1
                ):
                    extend = lyric.find("extend")
                    rows.append(
                        [
                            part_id,
                            measure_number,
                            note_index,
                            lyric_index,
                            voice,
                            lyric.get("number", "1"),
                            lyric.findtext("syllabic"),
                            lyric.findtext("text"),
                            None if extend is None else extend.get("type"),
                        ]
                    )
    return rows


def iter_lyrics(
    root: ET.Element,
) -> Iterable[tuple[str, str, int, int, str, ET.Element]]:
    for part in root.findall("part"):
        part_id = part.get("id", "")
        for measure in part.findall("measure"):
            measure_number = measure.get("number", "")
            for note_index, note in enumerate(measure.findall("note"), start=1):
                voice = note.findtext("voice", "1")
                for lyric_index, lyric in enumerate(
                    note.findall("lyric"), start=1
                ):
                    yield (
                        part_id,
                        measure_number,
                        note_index,
                        lyric_index,
                        voice,
                        lyric,
                    )


def measure_lyric_onsets(measure: ET.Element) -> dict[int, set[str]]:
    cursor = 0
    last_onset = 0
    result: dict[int, set[str]] = defaultdict(set)
    for item in measure:
        if item.tag == "note":
            onset = last_onset if item.find("chord") is not None else cursor
            if item.find("chord") is None:
                last_onset = onset
            if item.findall("lyric"):
                result[onset].add(item.findtext("voice", "1"))
            if item.find("chord") is None and item.find("grace") is None:
                cursor += int(item.findtext("duration", "0"))
        elif item.tag == "backup":
            cursor -= int(item.findtext("duration", "0"))
        elif item.tag == "forward":
            cursor += int(item.findtext("duration", "0"))
    return result


def detect_multi_voice_parts(root: ET.Element) -> dict[str, int]:
    evidence: dict[str, int] = {}
    for part in root.findall("part"):
        hits = 0
        for measure in part.findall("measure"):
            hits += sum(
                1
                for voices in measure_lyric_onsets(measure).values()
                if len(voices) > 1
            )
        if hits:
            evidence[part.get("id", "")] = hits
    return evidence


def audit_staff_lines(root: ET.Element) -> dict[str, Any]:
    explicit_by_part: Counter[str] = Counter()
    non_five_line: list[dict[str, Any]] = []
    hidden: list[dict[str, Any]] = []
    malformed: list[dict[str, Any]] = []

    for part in root.findall("part"):
        part_id = part.get("id", "")
        for measure in part.findall("measure"):
            measure_number = measure.get("number", "")
            for details in measure.findall("./attributes/staff-details"):
                staff_number = details.get("number", "1")
                if details.get("print-object") == "no":
                    hidden.append(
                        {
                            "part": part_id,
                            "measure": measure_number,
                            "staff": staff_number,
                        }
                    )
                staff_lines = details.find("staff-lines")
                if staff_lines is None:
                    continue
                explicit_by_part[part_id] += 1
                value = (staff_lines.text or "").strip()
                try:
                    parsed = int(value)
                except ValueError:
                    malformed.append(
                        {
                            "part": part_id,
                            "measure": measure_number,
                            "staff": staff_number,
                            "value": value,
                        }
                    )
                    continue
                if parsed != 5:
                    non_five_line.append(
                        {
                            "part": part_id,
                            "measure": measure_number,
                            "staff": staff_number,
                            "value": parsed,
                        }
                    )

    missing_explicit = [
        part_id for part_id in EXPECTED_PART_IDS if explicit_by_part[part_id] == 0
    ]
    return {
        "explicit_override_count": sum(explicit_by_part.values()),
        "explicit_by_part": dict(sorted(explicit_by_part.items())),
        "parts_without_explicit_five_line_state": missing_explicit,
        "non_five_line_states": non_five_line,
        "malformed_states": malformed,
        "hidden_staff_states": hidden,
        "passed": not (
            missing_explicit or non_five_line or malformed or hidden
        ),
    }


def validate_musicxml(path: Path) -> dict[str, Any]:
    checks: list[Check] = []
    result: dict[str, Any] = {
        "path": display_path(path),
        "sha256": None,
        "checks": checks,
    }
    if not path.is_file():
        checks.append(
            check(
                "musicxml_exists",
                False,
                expected="existing MusicXML file",
                actual="missing",
            )
        )
        result["status"] = "failed"
        return result

    result["sha256"] = sha256(path)
    checks.append(
        check(
            "musicxml_exists",
            True,
            expected="existing MusicXML file",
            actual="present",
        )
    )
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        checks.append(
            check(
                "musicxml_parses",
                False,
                expected="well-formed MusicXML",
                actual=f"{type(exc).__name__}: {exc}",
            )
        )
        result["status"] = "failed"
        return result

    checks.append(
        check(
            "musicxml_root",
            root.tag == "score-partwise",
            expected="score-partwise",
            actual=root.tag,
        )
    )
    parts = root.findall("part")
    part_ids = tuple(part.get("id", "") for part in parts)
    checks.append(
        check(
            "part_count",
            len(parts) == len(EXPECTED_PART_IDS),
            expected=len(EXPECTED_PART_IDS),
            actual=len(parts),
        )
    )
    checks.append(
        check(
            "part_ids",
            part_ids == EXPECTED_PART_IDS,
            expected=list(EXPECTED_PART_IDS),
            actual=list(part_ids),
            detail=(
                "The canonical fingerprint includes part IDs; preserving them "
                "also keeps the editorial part mapping stable."
            ),
        )
    )

    measure_counts = {
        part.get("id", ""): len(part.findall("measure")) for part in parts
    }
    expected_measure_counts = {
        part_id: EXPECTED_MEASURES_PER_PART for part_id in EXPECTED_PART_IDS
    }
    checks.append(
        check(
            "measures_per_part",
            measure_counts == expected_measure_counts,
            expected=expected_measure_counts,
            actual=measure_counts,
        )
    )
    numbering_errors: dict[str, list[str]] = {}
    expected_numbers = [
        str(number) for number in range(1, EXPECTED_MEASURES_PER_PART + 1)
    ]
    for part in parts:
        actual_numbers = [
            measure.get("number", "") for measure in part.findall("measure")
        ]
        if actual_numbers != expected_numbers:
            numbering_errors[part.get("id", "")] = actual_numbers[:12]
    checks.append(
        check(
            "measure_numbering",
            not numbering_errors,
            expected="consecutive measures 1-151 in every part",
            actual=("consecutive" if not numbering_errors else numbering_errors),
        )
    )

    note_count = len(root.findall("./part/measure/note"))
    lyric_count = len(root.findall(".//lyric"))
    checks.append(
        check(
            "note_elements",
            note_count == EXPECTED_NOTE_COUNT,
            expected=EXPECTED_NOTE_COUNT,
            actual=note_count,
        )
    )
    checks.append(
        check(
            "lyric_anchors",
            lyric_count == EXPECTED_LYRIC_ANCHORS,
            expected=EXPECTED_LYRIC_ANCHORS,
            actual=lyric_count,
        )
    )

    try:
        fingerprint = normalized_score_fingerprint(root)
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        fingerprint = f"error: {type(exc).__name__}: {exc}"
    checks.append(
        check(
            "canonical_musical_fingerprint",
            fingerprint == EXPECTED_FINGERPRINT,
            expected=EXPECTED_FINGERPRINT,
            actual=fingerprint,
            detail=(
                "Computed with Operations/Scripts/"
                "apply_fall2026_casting_breaks.py."
            ),
        )
    )

    lyric_rows = lyric_content_rows(root)
    lyric_content_hash = hash_json(lyric_rows)
    checks.append(
        check(
            "canonical_lyric_content",
            lyric_content_hash == EXPECTED_LYRIC_CONTENT_HASH,
            expected=EXPECTED_LYRIC_CONTENT_HASH,
            actual=lyric_content_hash,
            detail=(
                "Covers anchor location, voice, lyric number, syllabification, "
                "text, and extender state while excluding visual offsets."
            ),
        )
    )

    placement_counts: Counter[str] = Counter()
    routing_errors: list[dict[str, Any]] = []
    lane_placements: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    third_lane_rows: list[list[Any]] = []
    third_lane_placement_errors: list[dict[str, Any]] = []
    for (
        part_id,
        measure_number,
        note_index,
        lyric_index,
        voice,
        lyric,
    ) in iter_lyrics(root):
        placement = lyric.get("placement") or "<missing>"
        lyric_number = lyric.get("number", "1")
        placement_counts[placement] += 1
        lane_placements[(part_id, voice, lyric_number)].add(placement)
        target = (
            "above"
            if part_id in EXPECTED_MULTI_VOICE_PARTS and voice == "1"
            else "below"
        )
        if placement != target:
            routing_errors.append(
                {
                    "part": part_id,
                    "measure": measure_number,
                    "note_index": note_index,
                    "lyric_index": lyric_index,
                    "voice": voice,
                    "lyric_number": lyric_number,
                    "expected": target,
                    "actual": placement,
                }
            )
        if voice != "1" and lyric_number != "1":
            row = [
                part_id,
                measure_number,
                note_index,
                lyric_index,
                voice,
                lyric_number,
            ]
            third_lane_rows.append(row)
            if placement != "below":
                third_lane_placement_errors.append(
                    {"anchor": row, "placement": placement}
                )

    actual_distribution = dict(sorted(placement_counts.items()))
    checks.append(
        check(
            "lyric_placement_distribution",
            actual_distribution == EXPECTED_PLACEMENT_DISTRIBUTION,
            expected=EXPECTED_PLACEMENT_DISTRIBUTION,
            actual=actual_distribution,
        )
    )
    checks.append(
        check(
            "lyric_routing_rule",
            not routing_errors,
            expected=(
                "voice 1 above on P4-P6; every other lyric-bearing voice below"
            ),
            actual={
                "error_count": len(routing_errors),
                "preview": routing_errors[:12],
            },
        )
    )

    multi_voice_evidence = detect_multi_voice_parts(root)
    checks.append(
        check(
            "multi_voice_topology",
            set(multi_voice_evidence) == EXPECTED_MULTI_VOICE_PARTS,
            expected=sorted(EXPECTED_MULTI_VOICE_PARTS),
            actual=multi_voice_evidence,
        )
    )

    third_lane_hash = hash_json(third_lane_rows)
    checks.append(
        check(
            "stable_third_lyric_lane",
            (
                len(third_lane_rows) == EXPECTED_THIRD_LANE_COUNT
                and third_lane_hash == EXPECTED_THIRD_LANE_HASH
                and not third_lane_placement_errors
            ),
            expected={
                "anchor_count": EXPECTED_THIRD_LANE_COUNT,
                "anchor_hash": EXPECTED_THIRD_LANE_HASH,
                "placement": "below",
            },
            actual={
                "anchor_count": len(third_lane_rows),
                "anchor_hash": third_lane_hash,
                "placement_errors": third_lane_placement_errors[:12],
            },
            detail=(
                "The additional lower stream retains lyric number 2 and its "
                "exact P4 voice-2 anchor sequence."
            ),
        )
    )
    lane_switches = {
        "/".join(key): sorted(values)
        for key, values in lane_placements.items()
        if len(values) != 1
    }
    checks.append(
        check(
            "no_per_syllable_lane_switching",
            not lane_switches,
            expected="one placement for each part/voice/lyric-number lane",
            actual=("stable" if not lane_switches else lane_switches),
        )
    )

    staff_audit = audit_staff_lines(root)
    checks.append(
        check(
            "five_line_staves_throughout",
            staff_audit["passed"],
            expected=(
                "an explicit five-line state in every part, no non-five-line "
                "changes, and no hidden staff-details"
            ),
            actual=staff_audit,
        )
    )

    result.update(
        {
            "status": section_status(checks),
            "part_ids": list(part_ids),
            "measure_counts": measure_counts,
            "note_count": note_count,
            "lyric_anchor_count": lyric_count,
            "musical_fingerprint": fingerprint,
            "lyric_content_hash": lyric_content_hash,
            "lyric_placement_distribution": actual_distribution,
            "third_lane_anchor_hash": third_lane_hash,
        }
    )
    return result


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("top-level JSON value is not an object")
    return payload


def validate_provenance(
    provenance_dir: Path | None,
    *,
    lyric_content_hash: str | None,
) -> dict[str, Any]:
    checks: list[Check] = []
    result: dict[str, Any] = {
        "path": None if provenance_dir is None else display_path(provenance_dir),
        "checks": checks,
    }
    if provenance_dir is None:
        checks.append(
            not_checked(
                "fall_replacement_provenance",
                "Provenance checking was explicitly skipped.",
                expected=EXPECTED_FALL_REPLACEMENTS,
            )
        )
        result["status"] = "incomplete"
        return result

    paths = {
        key: provenance_dir / filename
        for key, filename in PROVENANCE_REPORTS.items()
    }
    missing = [key for key, path in paths.items() if not path.is_file()]
    if missing:
        checks.append(
            not_checked(
                "provenance_report_set",
                "One or more retained Fall provenance reports are unavailable.",
                expected=sorted(paths),
            )
        )
        result["missing_reports"] = missing
        result["status"] = "incomplete"
        return result

    reports: dict[str, dict[str, Any]] = {}
    load_errors: dict[str, str] = {}
    for key, path in paths.items():
        try:
            reports[key] = load_json(path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            load_errors[key] = f"{type(exc).__name__}: {exc}"
    checks.append(
        check(
            "provenance_reports_parse",
            not load_errors,
            expected="six readable JSON provenance reports",
            actual=("readable" if not load_errors else load_errors),
        )
    )
    if load_errors:
        result["status"] = "failed"
        return result

    import_report = reports["import_report"]
    import_ok = (
        import_report.get("ledger_rows") == EXPECTED_FALL_REPLACEMENTS
        and import_report.get("matched_rows") == EXPECTED_FALL_REPLACEMENTS
        and import_report.get("structure_matches") is True
        and import_report.get("source_structure_fingerprint")
        == EXPECTED_FINGERPRINT
        and import_report.get("output_structure_fingerprint")
        == EXPECTED_FINGERPRINT
    )
    checks.append(
        check(
            "approved_replacement_import_report",
            import_ok,
            expected={
                "ledger_rows": EXPECTED_FALL_REPLACEMENTS,
                "matched_rows": EXPECTED_FALL_REPLACEMENTS,
                "canonical_structure": True,
            },
            actual={
                "ledger_rows": import_report.get("ledger_rows"),
                "matched_rows": import_report.get("matched_rows"),
                "structure_matches": import_report.get("structure_matches"),
                "source_fingerprint": import_report.get(
                    "source_structure_fingerprint"
                ),
                "output_fingerprint": import_report.get(
                    "output_structure_fingerprint"
                ),
            },
        )
    )

    import_validation = reports["import_validation"]
    import_validation_ok = (
        import_validation.get("ledger_rows") == EXPECTED_FALL_REPLACEMENTS
        and import_validation.get("matched_targets")
        == EXPECTED_FALL_REPLACEMENTS
        and import_validation.get("baseline_lyric_coordinates")
        == EXPECTED_LYRIC_ANCHORS
        and import_validation.get("export_lyric_coordinates")
        == EXPECTED_LYRIC_ANCHORS
        and import_validation.get("baseline_precondition_failures") == 0
        and import_validation.get("target_mismatches") == 0
        and import_validation.get("unchanged_lyric_mismatches") == 0
        and import_validation.get("structure_matches") is True
        and import_validation.get("baseline_structure_fingerprint")
        == EXPECTED_FINGERPRINT
        and import_validation.get("export_structure_fingerprint")
        == EXPECTED_FINGERPRINT
    )
    checks.append(
        check(
            "approved_replacement_target_validation",
            import_validation_ok,
            expected={
                "matched_targets": EXPECTED_FALL_REPLACEMENTS,
                "target_mismatches": 0,
                "unchanged_lyric_mismatches": 0,
            },
            actual={
                "matched_targets": import_validation.get("matched_targets"),
                "baseline_precondition_failures": import_validation.get(
                    "baseline_precondition_failures"
                ),
                "target_mismatches": import_validation.get(
                    "target_mismatches"
                ),
                "unchanged_lyric_mismatches": import_validation.get(
                    "unchanged_lyric_mismatches"
                ),
                "structure_matches": import_validation.get("structure_matches"),
            },
        )
    )

    text_validation = reports["text_correction"].get("validation", {})
    text_ok = (
        text_validation.get("passed") is True
        and text_validation.get("output_shape", {}).get("note_count")
        == EXPECTED_NOTE_COUNT
        and text_validation.get("output_shape", {}).get("lyric_anchor_count")
        == EXPECTED_LYRIC_ANCHORS
        and text_validation.get("lyric_anchor_locations_match") is True
        and text_validation.get("musical_semantics_match") is True
    )
    checks.append(
        check(
            "logged_text_correction_stage",
            text_ok,
            expected="passed with musical semantics and lyric anchors preserved",
            actual={
                "passed": text_validation.get("passed"),
                "lyric_anchor_locations_match": text_validation.get(
                    "lyric_anchor_locations_match"
                ),
                "musical_semantics_match": text_validation.get(
                    "musical_semantics_match"
                ),
            },
        )
    )

    normalization_validation = reports["normalization"].get("validation", {})
    normalization_ok = (
        normalization_validation.get("passed") is True
        and normalization_validation.get("note_count") == EXPECTED_NOTE_COUNT
        and normalization_validation.get("lyric_anchor_count")
        == EXPECTED_LYRIC_ANCHORS
        and normalization_validation.get("fall_replacements_preserved") is True
        and normalization_validation.get("canonical_structure_matches") is True
        and normalization_validation.get("lyric_semantic_hash_after")
        == EXPECTED_LYRIC_CONTENT_HASH
        and normalization_validation.get("lyric_semantics_match") is True
        and not normalization_validation.get("placement_errors")
    )
    checks.append(
        check(
            "normalization_provenance",
            normalization_ok,
            expected="validated normalization retaining all Fall text",
            actual={
                "passed": normalization_validation.get("passed"),
                "fall_replacements_preserved": normalization_validation.get(
                    "fall_replacements_preserved"
                ),
                "lyric_semantic_hash_after": normalization_validation.get(
                    "lyric_semantic_hash_after"
                ),
                "placement_error_count": len(
                    normalization_validation.get("placement_errors") or []
                ),
            },
        )
    )

    stage_e_report = reports["stage_e"]
    stage_e_validation = stage_e_report.get("validation", {})
    stage_e_ok = (
        stage_e_report.get("stage") == "E"
        and stage_e_report.get("output_sha256") == EXPECTED_STAGE_E_SHA256
        and stage_e_report.get("provenance", {}).get("reports_chain") is True
        and stage_e_report.get("provenance", {}).get("fall_replacements")
        == EXPECTED_FALL_REPLACEMENTS
        and stage_e_validation.get("passed") is True
        and stage_e_validation.get("fall_replacement_count")
        == EXPECTED_FALL_REPLACEMENTS
        and stage_e_validation.get("fall_replacements_preserved") is True
        and stage_e_validation.get("canonical_structure_matches") is True
        and stage_e_validation.get("lyrics_text_attributes_and_placement_exact")
        is True
    )
    checks.append(
        check(
            "stage_e_provenance_chain",
            stage_e_ok,
            expected={
                "stage": "E",
                "output_sha256": EXPECTED_STAGE_E_SHA256,
                "fall_replacements": EXPECTED_FALL_REPLACEMENTS,
                "validation_passed": True,
            },
            actual={
                "stage": stage_e_report.get("stage"),
                "output_sha256": stage_e_report.get("output_sha256"),
                "reports_chain": stage_e_report.get("provenance", {}).get(
                    "reports_chain"
                ),
                "fall_replacements": stage_e_validation.get(
                    "fall_replacement_count"
                ),
                "validation_passed": stage_e_validation.get("passed"),
            },
        )
    )

    casting = reports["casting_24_page"]
    casting_validation = casting.get("score_validation", {})
    casting_ok = (
        casting.get("source_provenance", {}).get("verified") is True
        and casting.get("source_provenance", {}).get("fall_replacements")
        == EXPECTED_FALL_REPLACEMENTS
        and casting_validation.get("note_count") == EXPECTED_NOTE_COUNT
        and casting_validation.get("lyric_anchors") == EXPECTED_LYRIC_ANCHORS
        and casting_validation.get("structure_fingerprint")
        == EXPECTED_FINGERPRINT
        and casting.get("semantic_preservation", {}).get(
            "lyrics_and_routing_match"
        )
        is True
        and casting.get("semantic_preservation", {}).get(
            "five_line_staff_overrides_match"
        )
        is True
    )
    checks.append(
        check(
            "readability_casting_provenance",
            casting_ok,
            expected="validated 24-page casting source provenance",
            actual={
                "source_verified": casting.get("source_provenance", {}).get(
                    "verified"
                ),
                "fall_replacements": casting.get("source_provenance", {}).get(
                    "fall_replacements"
                ),
                "structure_fingerprint": casting_validation.get(
                    "structure_fingerprint"
                ),
                "lyrics_and_routing_match": casting.get(
                    "semantic_preservation", {}
                ).get("lyrics_and_routing_match"),
            },
        )
    )

    normalization_report = reports["normalization"]
    normalization_provenance = normalization_report.get("provenance", {})
    stage_e_reference = provenance_dir / STAGE_E_REFERENCE
    casting_output_value = str(casting.get("output", ""))
    casting_output_path = Path(casting_output_value)
    if not casting_output_path.is_absolute():
        casting_output_path = ROOT / casting_output_path
    actual_normalization_report_sha = sha256(paths["normalization"])
    actual_stage_e_sha = (
        sha256(stage_e_reference) if stage_e_reference.is_file() else None
    )
    actual_casting_output_sha = (
        sha256(casting_output_path) if casting_output_path.is_file() else None
    )
    hash_chain_evidence = {
        "import_to_normalization": (
            import_report.get("output_sha256"),
            normalization_provenance.get("import_output_sha256"),
        ),
        "text_correction_to_normalization": (
            reports["text_correction"].get("output_sha256"),
            normalization_provenance.get("text_corrected_sha256"),
        ),
        "normalization_to_stage_e": (
            normalization_report.get("output_sha256"),
            stage_e_report.get("source_sha256"),
        ),
        "normalization_report_to_stage_e": (
            actual_normalization_report_sha,
            stage_e_report.get("provenance", {}).get(
                "normalization_report_sha256"
            ),
        ),
        "stage_e_file": (
            actual_stage_e_sha,
            stage_e_report.get("output_sha256"),
        ),
        "stage_e_to_24_page_cast": (
            stage_e_report.get("output_sha256"),
            casting.get("source_sha256"),
        ),
        "24_page_cast_file": (
            actual_casting_output_sha,
            casting.get("output_sha256"),
        ),
    }
    hash_chain_ok = (
        normalization_provenance.get("reports_chain") is True
        and all(
            left is not None and left == right
            for left, right in hash_chain_evidence.values()
        )
    )
    checks.append(
        check(
            "provenance_sha256_chain",
            hash_chain_ok,
            expected="matching SHA-256 links from import through the 24-page cast",
            actual={
                key: {"upstream": left, "downstream": right}
                for key, (left, right) in hash_chain_evidence.items()
            },
        )
    )

    reference_actual_sha = actual_stage_e_sha
    checks.append(
        check(
            "canonical_stage_e_reference",
            reference_actual_sha == EXPECTED_STAGE_E_SHA256,
            expected=EXPECTED_STAGE_E_SHA256,
            actual=reference_actual_sha,
        )
    )

    provenance_chain_ok = all(
        item.status == "pass" for item in checks if item.name != "all_388_approved_replacements"
    )
    replacement_ok = (
        provenance_chain_ok
        and lyric_content_hash == EXPECTED_LYRIC_CONTENT_HASH
    )
    ledger_path = Path(str(import_report.get("ledger", "")))
    if not ledger_path.is_absolute():
        ledger_path = ROOT / ledger_path
    checks.append(
        check(
            "all_388_approved_replacements",
            replacement_ok,
            expected=EXPECTED_FALL_REPLACEMENTS,
            actual=(
                EXPECTED_FALL_REPLACEMENTS if replacement_ok else "unproven"
            ),
            detail=(
                "Established by the retained 388-row import/target-validation "
                "chain plus the exact canonical lyric-content hash. The original "
                f"ledger file is {'available' if ledger_path.is_file() else 'not retained in this checkout'}; "
                "the signed-off report records its SHA-256."
            ),
        )
    )

    result.update(
        {
            "status": section_status(checks),
            "report_files": {
                key: display_path(path) for key, path in paths.items()
            },
            "ledger_path_recorded": str(import_report.get("ledger", "")),
            "ledger_available": ledger_path.is_file(),
            "approved_replacement_count": (
                EXPECTED_FALL_REPLACEMENTS if replacement_ok else None
            ),
        }
    )
    return result


def find_poppler_tool(name: str) -> str | None:
    direct = shutil.which(name)
    if direct:
        return direct

    anchors = [shutil.which("pdfinfo"), shutil.which("pdftoppm")]
    for anchor in (item for item in anchors if item):
        anchor_path = Path(anchor).resolve()
        for parent in list(anchor_path.parents)[:6]:
            for relative in (
                Path("native/poppler/poppler/bin") / name,
                Path("native/poppler/bin") / name,
                Path("bin") / name,
            ):
                candidate = parent / relative
                if candidate.is_file() and candidate.stat().st_mode & 0o111:
                    return str(candidate)
    return None


def run_tool(command: list[str], *, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )


def parse_pdfinfo(output: str) -> dict[str, Any]:
    pages_match = re.search(r"^Pages:\s+(\d+)\s*$", output, re.MULTILINE)
    encrypted_match = re.search(
        r"^Encrypted:\s+([^\n]+)$", output, re.MULTILINE
    )
    sizes: dict[int, tuple[float, float]] = {}
    rotations: dict[int, int] = {}
    boxes: dict[int, dict[str, tuple[float, float, float, float]]] = defaultdict(dict)

    for match in re.finditer(
        r"^Page\s+(\d+)\s+size:\s+([\d.]+)\s+x\s+([\d.]+)\s+pts",
        output,
        re.MULTILINE,
    ):
        sizes[int(match.group(1))] = (float(match.group(2)), float(match.group(3)))
    for match in re.finditer(
        r"^Page\s+(\d+)\s+rot:\s+(-?\d+)\s*$", output, re.MULTILINE
    ):
        rotations[int(match.group(1))] = int(match.group(2))
    for match in re.finditer(
        r"^Page\s+(\d+)\s+"
        r"(MediaBox|CropBox|BleedBox|TrimBox|ArtBox):\s+"
        r"(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s*$",
        output,
        re.MULTILINE,
    ):
        boxes[int(match.group(1))][match.group(2)] = tuple(
            float(match.group(index)) for index in range(3, 7)
        )

    return {
        "page_count": int(pages_match.group(1)) if pages_match else None,
        "encrypted": encrypted_match.group(1).strip() if encrypted_match else None,
        "sizes": sizes,
        "rotations": rotations,
        "boxes": dict(boxes),
    }


def box_is_valid_and_contained(
    box: tuple[float, float, float, float],
    media: tuple[float, float, float, float],
    tolerance: float = 0.1,
) -> bool:
    x0, y0, x1, y1 = box
    mx0, my0, mx1, my1 = media
    return (
        x1 > x0
        and y1 > y0
        and x0 >= mx0 - tolerance
        and y0 >= my0 - tolerance
        and x1 <= mx1 + tolerance
        and y1 <= my1 + tolerance
    )


def parse_pdffonts(output: str) -> list[dict[str, Any]]:
    fonts: list[dict[str, Any]] = []
    tail_pattern = re.compile(
        r"\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+(\d+)\s+(\d+)\s*$"
    )
    for line in output.splitlines():
        if not line.strip() or line.startswith("name") or set(line.strip()) == {"-"}:
            continue
        match = tail_pattern.search(line)
        if not match:
            continue
        fonts.append(
            {
                "name": line.split()[0],
                "embedded": match.group(1) == "yes",
                "subset": match.group(2) == "yes",
                "unicode_map": match.group(3) == "yes",
                "object": f"{match.group(4)} {match.group(5)}",
            }
        )
    return fonts


def audit_fonts_with_pypdf(
    path: Path,
) -> tuple[list[dict[str, Any]] | None, str | None]:
    """Recursively inspect PDF font resources when ``pdffonts`` is absent.

    Fonts can live in page resources, Form XObjects, or tiling patterns.  A
    Type 0 font stores its descriptor on descendant CID fonts, while ordinary
    fonts normally store it directly.  Type 3 glyph programs are embedded in
    ``/CharProcs`` and therefore count as embedded without ``/FontFile*``.
    """

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        return None, f"pypdf unavailable: {exc}"

    try:
        reader = PdfReader(str(path))
    except Exception as exc:  # pypdf exposes several parser exception types
        return None, f"pypdf could not read PDF: {type(exc).__name__}: {exc}"

    def dereference(value: Any) -> Any:
        try:
            return value.get_object()
        except AttributeError:
            return value

    def object_key(value: Any) -> tuple[Any, ...]:
        reference = getattr(value, "indirect_reference", None)
        if reference is None and hasattr(value, "idnum"):
            reference = value
        if reference is not None:
            return (
                "indirect",
                getattr(reference, "idnum", None),
                getattr(reference, "generation", None),
            )
        return ("direct", id(value))

    def descriptor_embedded(descriptor: Any) -> tuple[bool, list[str]]:
        descriptor = dereference(descriptor)
        if not hasattr(descriptor, "get"):
            return False, []
        streams = [
            key
            for key in ("/FontFile", "/FontFile2", "/FontFile3")
            if descriptor.get(key) is not None
        ]
        return bool(streams), streams

    fonts_by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    visited_resources: set[tuple[Any, ...]] = set()

    def inspect_font(resource_name: str, font_value: Any, location: str) -> None:
        font = dereference(font_value)
        if not hasattr(font, "get"):
            return
        key = object_key(font_value)
        subtype = str(font.get("/Subtype", ""))
        base_font = str(font.get("/BaseFont", resource_name)).lstrip("/")
        descriptor_results: list[tuple[bool, list[str]]] = []
        direct_descriptor = font.get("/FontDescriptor")
        if direct_descriptor is not None:
            descriptor_results.append(descriptor_embedded(direct_descriptor))
        for descendant_value in font.get("/DescendantFonts", []) or []:
            descendant = dereference(descendant_value)
            if hasattr(descendant, "get"):
                descriptor = descendant.get("/FontDescriptor")
                if descriptor is not None:
                    descriptor_results.append(descriptor_embedded(descriptor))

        if subtype == "/Type3":
            embedded = font.get("/CharProcs") is not None
            streams = ["/CharProcs"] if embedded else []
        else:
            embedded = bool(descriptor_results) and all(
                item[0] for item in descriptor_results
            )
            streams = sorted(
                {stream for _, names in descriptor_results for stream in names}
            )
        item = fonts_by_key.setdefault(
            key,
            {
                "name": base_font,
                "resource_names": set(),
                "subtype": subtype,
                "embedded": embedded,
                "embedding_streams": streams,
                "locations": set(),
            },
        )
        item["resource_names"].add(resource_name)
        item["locations"].add(location)
        # A repeated resource reference must not weaken a positive result, but
        # a contradictory negative inspection should remain visible.
        item["embedded"] = bool(item["embedded"] and embedded)
        item["embedding_streams"] = sorted(
            set(item["embedding_streams"]) | set(streams)
        )

    def walk_resources(resources_value: Any, location: str) -> None:
        resources = dereference(resources_value)
        if not hasattr(resources, "get"):
            return
        key = object_key(resources_value)
        if key in visited_resources:
            return
        visited_resources.add(key)

        fonts = dereference(resources.get("/Font", {}))
        if hasattr(fonts, "items"):
            for resource_name, font_value in fonts.items():
                inspect_font(str(resource_name).lstrip("/"), font_value, location)

        for container_name in ("/XObject", "/Pattern"):
            container = dereference(resources.get(container_name, {}))
            if not hasattr(container, "items"):
                continue
            for resource_name, resource_value in container.items():
                resource = dereference(resource_value)
                if hasattr(resource, "get") and resource.get("/Resources") is not None:
                    walk_resources(
                        resource.get("/Resources"),
                        f"{location}/{container_name.lstrip('/')}/"
                        f"{str(resource_name).lstrip('/')}",
                    )

    try:
        for page_number, page in enumerate(reader.pages, start=1):
            walk_resources(page.get("/Resources"), f"page {page_number}")
    except Exception as exc:
        return None, f"pypdf font traversal failed: {type(exc).__name__}: {exc}"

    fonts: list[dict[str, Any]] = []
    for item in fonts_by_key.values():
        normalized = dict(item)
        normalized["resource_names"] = sorted(item["resource_names"])
        normalized["locations"] = sorted(item["locations"])
        fonts.append(normalized)
    fonts.sort(key=lambda item: (item["name"], item["subtype"]))
    return fonts, None


def read_pgm(path: Path) -> tuple[int, int, int, bytes]:
    data = path.read_bytes()
    index = 0

    def token() -> bytes:
        nonlocal index
        while index < len(data):
            if data[index:index + 1] == b"#":
                newline = data.find(b"\n", index)
                index = len(data) if newline < 0 else newline + 1
            elif data[index:index + 1].isspace():
                index += 1
            else:
                break
        start = index
        while index < len(data) and not data[index:index + 1].isspace():
            index += 1
        return data[start:index]

    magic = token()
    width = int(token())
    height = int(token())
    max_value = int(token())
    if magic != b"P5" or max_value > 255:
        raise ValueError(f"Unsupported PGM format in {path.name}")
    if index >= len(data) or not data[index:index + 1].isspace():
        raise ValueError(f"Malformed PGM header in {path.name}")
    if data[index:index + 2] == b"\r\n":
        index += 2
    else:
        index += 1
    pixels = data[index:index + width * height]
    if len(pixels) != width * height:
        raise ValueError(f"Truncated PGM pixel data in {path.name}")
    return width, height, max_value, pixels


def audit_raster_pages(
    pdf_path: Path,
    *,
    page_count: int,
    pdftoppm: str,
    safe_margin_points: float,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="fall2026-pdf-preflight-") as folder:
        prefix = Path(folder) / "page"
        completed = run_tool(
            [
                pdftoppm,
                "-f",
                "1",
                "-l",
                str(page_count),
                "-gray",
                "-r",
                str(RASTER_DPI),
                str(pdf_path),
                str(prefix),
            ]
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "pdftoppm failed")
        images = sorted(Path(folder).glob("page-*.pgm"))
        if len(images) != page_count:
            raise RuntimeError(
                f"Expected {page_count} rendered pages, found {len(images)}"
            )

        safe_pixels = math.ceil(safe_margin_points * RASTER_DPI / 72.0)
        pages: list[dict[str, Any]] = []
        blank_pages: list[int] = []
        safe_margin_violations: list[dict[str, Any]] = []
        for page_number, image_path in enumerate(images, start=1):
            width, height, max_value, pixels = read_pgm(image_path)
            threshold = int(max_value * 0.96)
            dark_indices = [
                index for index, value in enumerate(pixels) if value < threshold
            ]
            minimum_ink = max(8, int(width * height * 0.00002))
            if len(dark_indices) < minimum_ink:
                blank_pages.append(page_number)
                pages.append(
                    {
                        "page": page_number,
                        "dark_pixels": len(dark_indices),
                        "content_bbox_pixels": None,
                    }
                )
                continue

            xs = [index % width for index in dark_indices]
            ys = [index // width for index in dark_indices]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            margins = {
                "left": min_x,
                "right": width - 1 - max_x,
                "top": min_y,
                "bottom": height - 1 - max_y,
            }
            if min(margins.values()) < safe_pixels:
                safe_margin_violations.append(
                    {
                        "page": page_number,
                        "required_pixels": safe_pixels,
                        "margins_pixels": margins,
                    }
                )
            pages.append(
                {
                    "page": page_number,
                    "dark_pixels": len(dark_indices),
                    "content_bbox_pixels": [min_x, min_y, max_x, max_y],
                    "margins_pixels": margins,
                }
            )

    return {
        "dpi": RASTER_DPI,
        "safe_margin_points": safe_margin_points,
        "safe_margin_pixels": safe_pixels,
        "blank_pages": blank_pages,
        "safe_margin_violations": safe_margin_violations,
        "pages": pages,
    }


def validate_pdf(
    path: Path | None,
    *,
    safe_margin_points: float = DEFAULT_SAFE_MARGIN_POINTS,
) -> dict[str, Any]:
    checks: list[Check] = []
    result: dict[str, Any] = {
        "path": None if path is None else display_path(path),
        "sha256": None,
        "checks": checks,
    }
    if path is None:
        checks.append(
            not_checked(
                "final_pdf_supplied",
                "No PDF was supplied; booklet preflight is pending.",
                expected="final performer-score PDF",
            )
        )
        result["status"] = "incomplete"
        return result
    if not path.is_file():
        checks.append(
            check(
                "final_pdf_exists",
                False,
                expected="existing PDF file",
                actual="missing",
            )
        )
        result["status"] = "failed"
        return result

    result["sha256"] = sha256(path)
    checks.append(
        check(
            "final_pdf_exists",
            True,
            expected="existing PDF file",
            actual="present",
        )
    )

    pdfinfo = find_poppler_tool("pdfinfo")
    if not pdfinfo:
        checks.append(
            not_checked(
                "pdf_geometry_and_page_boxes",
                "Poppler pdfinfo is unavailable.",
                expected="Letter portrait pages with safe boxes",
            )
        )
        result["status"] = "incomplete"
        return result

    summary = run_tool([pdfinfo, str(path)])
    if summary.returncode != 0:
        checks.append(
            check(
                "pdfinfo_reads_pdf",
                False,
                expected="readable PDF",
                actual=summary.stderr.strip() or "pdfinfo failed",
            )
        )
        result["status"] = "failed"
        return result
    summary_data = parse_pdfinfo(summary.stdout)
    page_count = summary_data["page_count"]
    if not isinstance(page_count, int) or page_count < 1:
        checks.append(
            check(
                "pdf_page_count_readable",
                False,
                expected="positive page count",
                actual=page_count,
            )
        )
        result["status"] = "failed"
        return result

    detailed = run_tool(
        [pdfinfo, "-f", "1", "-l", str(page_count), "-box", str(path)]
    )
    if detailed.returncode != 0:
        checks.append(
            check(
                "pdfinfo_page_detail",
                False,
                expected="per-page geometry and boxes",
                actual=detailed.stderr.strip() or "pdfinfo -box failed",
            )
        )
        result["status"] = "failed"
        return result
    info = parse_pdfinfo(detailed.stdout)
    info["page_count"] = page_count
    info["encrypted"] = summary_data["encrypted"]

    encrypted = str(info.get("encrypted") or "").lower()
    checks.append(
        check(
            "pdf_unencrypted",
            encrypted.startswith("no"),
            expected="no",
            actual=info.get("encrypted"),
        )
    )
    checks.append(
        check(
            "booklet_page_count",
            page_count % 4 == 0,
            expected="positive page count divisible by 4",
            actual=page_count,
        )
    )

    expected_pages = set(range(1, page_count + 1))
    size_errors: dict[int, Any] = {}
    for page_number in expected_pages:
        size = info["sizes"].get(page_number)
        rotation = info["rotations"].get(page_number)
        if (
            size is None
            or rotation != 0
            or abs(size[0] - LETTER_WIDTH_POINTS)
            > PAGE_SIZE_TOLERANCE_POINTS
            or abs(size[1] - LETTER_HEIGHT_POINTS)
            > PAGE_SIZE_TOLERANCE_POINTS
        ):
            size_errors[page_number] = {
                "size_points": size,
                "rotation": rotation,
            }
    checks.append(
        check(
            "letter_portrait_geometry",
            not size_errors,
            expected={
                "width_points": LETTER_WIDTH_POINTS,
                "height_points": LETTER_HEIGHT_POINTS,
                "rotation": 0,
                "tolerance_points": PAGE_SIZE_TOLERANCE_POINTS,
            },
            actual=("all pages" if not size_errors else size_errors),
        )
    )

    box_errors: list[dict[str, Any]] = []
    required_boxes = ("MediaBox", "CropBox", "BleedBox", "TrimBox", "ArtBox")
    for page_number in expected_pages:
        page_boxes = info["boxes"].get(page_number, {})
        media = page_boxes.get("MediaBox")
        if media is None:
            box_errors.append(
                {"page": page_number, "error": "missing MediaBox"}
            )
            continue
        for box_name in required_boxes:
            candidate = page_boxes.get(box_name)
            if candidate is None:
                box_errors.append(
                    {"page": page_number, "error": f"missing {box_name}"}
                )
            elif not box_is_valid_and_contained(candidate, media):
                box_errors.append(
                    {
                        "page": page_number,
                        "error": f"unsafe {box_name}",
                        "box": candidate,
                        "media_box": media,
                    }
                )
    checks.append(
        check(
            "safe_pdf_page_boxes",
            not box_errors,
            expected=(
                "nondegenerate Media/Crop/Bleed/Trim/Art boxes contained in "
                "each page MediaBox"
            ),
            actual=("safe" if not box_errors else box_errors[:24]),
        )
    )

    pdffonts = find_poppler_tool("pdffonts")
    fonts: list[dict[str, Any]] | None = None
    font_provider: str | None = None
    font_error: str | None = None
    if pdffonts:
        font_result = run_tool([pdffonts, str(path)])
        if font_result.returncode != 0:
            font_error = font_result.stderr.strip() or "pdffonts failed"
        else:
            fonts = parse_pdffonts(font_result.stdout)
            font_provider = "Poppler pdffonts"

    if fonts is None:
        fonts, pypdf_error = audit_fonts_with_pypdf(path)
        if fonts is not None:
            font_provider = "pypdf recursive /Resources audit"
        else:
            errors = [item for item in (font_error, pypdf_error) if item]
            font_error = "; ".join(errors)

    if fonts is None:
        checks.append(
            not_checked(
                "embedded_fonts",
                font_error or "Neither pdffonts nor pypdf is available.",
                expected="every referenced font embedded",
            )
        )
    else:
        unembedded = [font["name"] for font in fonts if not font["embedded"]]
        checks.append(
            check(
                "embedded_fonts",
                bool(fonts) and not unembedded,
                expected="one or more fonts, all embedded",
                actual={
                    "provider": font_provider,
                    "font_count": len(fonts),
                    "unembedded": unembedded,
                    "fonts": [font["name"] for font in fonts],
                },
                detail=(
                    "The pypdf fallback recursively inspects page, Form XObject, "
                    "and pattern resources, including Type 0 descendant font "
                    "descriptors and /FontFile, /FontFile2, /FontFile3 streams."
                ),
            )
        )
        result["font_audit_provider"] = font_provider
        result["fonts"] = fonts

    pdftoppm = find_poppler_tool("pdftoppm")
    if not pdftoppm:
        checks.append(
            not_checked(
                "nonblank_pages",
                "Poppler pdftoppm is unavailable.",
                expected="no visually blank pages",
            )
        )
        checks.append(
            not_checked(
                "content_safe_margin",
                "Poppler pdftoppm is unavailable.",
                expected=f"at least {safe_margin_points:g} points",
            )
        )
    else:
        try:
            raster = audit_raster_pages(
                path,
                page_count=page_count,
                pdftoppm=pdftoppm,
                safe_margin_points=safe_margin_points,
            )
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
            checks.append(
                check(
                    "pdf_raster_preflight",
                    False,
                    expected="successful low-resolution raster preflight",
                    actual=f"{type(exc).__name__}: {exc}",
                )
            )
        else:
            checks.append(
                check(
                    "nonblank_pages",
                    not raster["blank_pages"],
                    expected="no visually blank pages",
                    actual={"blank_pages": raster["blank_pages"]},
                    detail=(
                        f"Rendered all pages at {RASTER_DPI} dpi and measured "
                        "painted pixels."
                    ),
                )
            )
            checks.append(
                check(
                    "content_safe_margin",
                    not raster["safe_margin_violations"],
                    expected=f"at least {safe_margin_points:g} points on every edge",
                    actual={
                        "violation_count": len(
                            raster["safe_margin_violations"]
                        ),
                        "violations": raster["safe_margin_violations"][:24],
                    },
                    detail=(
                        "Conservative raster bounding-box check; review intended "
                        "bleeds separately if this edition later adds them."
                    ),
                )
            )
            result["raster_preflight"] = raster

    result.update(
        {
            "status": section_status(checks),
            "page_count": page_count,
            "page_sizes_points": {
                str(page): list(size) for page, size in info["sizes"].items()
            },
        }
    )
    return result


def serialize_checks(section: dict[str, Any]) -> dict[str, Any]:
    copied = dict(section)
    copied["checks"] = [asdict(item) for item in section.get("checks", [])]
    return copied


def validate_delivery(
    musicxml: Path,
    pdf: Path | None,
    *,
    provenance_dir: Path | None = DEFAULT_PROVENANCE_DIR,
    safe_margin_points: float = DEFAULT_SAFE_MARGIN_POINTS,
    final_delivery: bool = False,
) -> dict[str, Any]:
    musicxml_result = validate_musicxml(musicxml)
    provenance_result = validate_provenance(
        provenance_dir,
        lyric_content_hash=musicxml_result.get("lyric_content_hash"),
    )
    pdf_result = validate_pdf(pdf, safe_margin_points=safe_margin_points)

    all_checks = [
        *musicxml_result.get("checks", []),
        *provenance_result.get("checks", []),
        *pdf_result.get("checks", []),
    ]
    automated_status = section_status(all_checks)
    if automated_status == "failed":
        status = "failed"
    elif automated_status == "incomplete":
        status = "incomplete"
    elif not final_delivery:
        status = "candidate_passed"
    else:
        status = "passed"
    final_delivery_pass = status == "passed"

    counts = Counter(item.status for item in all_checks)
    return {
        "schema_version": 1,
        "validator": "Operations/Scripts/validate_fall2026_performer_score.py",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "delivery_intent": "final" if final_delivery else "candidate",
        "status": status,
        "automated_status": automated_status,
        "final_delivery_pass": final_delivery_pass,
        "inputs": {
            "musicxml": display_path(musicxml),
            "pdf": None if pdf is None else display_path(pdf),
            "provenance_dir": (
                None if provenance_dir is None else display_path(provenance_dir)
            ),
        },
        "expected": {
            "parts": len(EXPECTED_PART_IDS),
            "part_ids": list(EXPECTED_PART_IDS),
            "measures_per_part": EXPECTED_MEASURES_PER_PART,
            "note_elements": EXPECTED_NOTE_COUNT,
            "lyric_anchors": EXPECTED_LYRIC_ANCHORS,
            "fall_replacements": EXPECTED_FALL_REPLACEMENTS,
            "musical_fingerprint": EXPECTED_FINGERPRINT,
            "lyric_content_hash": EXPECTED_LYRIC_CONTENT_HASH,
            "lyric_placement_distribution": EXPECTED_PLACEMENT_DISTRIBUTION,
            "third_lane_anchor_count": EXPECTED_THIRD_LANE_COUNT,
            "third_lane_anchor_hash": EXPECTED_THIRD_LANE_HASH,
            "page_size_points": [LETTER_WIDTH_POINTS, LETTER_HEIGHT_POINTS],
            "page_count_divisor": 4,
            "safe_margin_points": safe_margin_points,
        },
        "summary": {
            "passed_checks": counts.get("pass", 0),
            "failed_checks": counts.get("fail", 0),
            "not_checked_checks": counts.get("not_checked", 0),
        },
        "musicxml": serialize_checks(musicxml_result),
        "provenance": serialize_checks(provenance_result),
        "pdf": serialize_checks(pdf_result),
        "limitations": [
            (
                "This validator proves MusicXML semantics and mechanical PDF "
                "preflight conditions; it cannot prove collision-free engraving, "
                "typographic quality, or performer readability. Retain the staged "
                "full-page and 100-percent visual audit as separate evidence."
            ),
            (
                "A final-delivery pass requires both final artifacts and the "
                "explicit --final-delivery assertion."
            ),
        ],
    }


def compact_json(value: Any, limit: int = 180) -> str:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if len(rendered) <= limit:
        return rendered
    return rendered[: limit - 3] + "..."


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Fall 2026 Performer-Score Final-Delivery Validation",
        "",
        f"**Status:** `{report['status']}`",
        "",
        f"**Final-delivery pass:** `{'YES' if report['final_delivery_pass'] else 'NO'}`",
        "",
        "## Inputs",
        "",
        f"- MusicXML: `{report['inputs']['musicxml']}`",
        f"- PDF: `{report['inputs']['pdf'] or 'not supplied'}`",
        f"- Provenance: `{report['inputs']['provenance_dir'] or 'not checked'}`",
        "",
    ]
    for title, key in (
        ("MusicXML", "musicxml"),
        ("Fall text and provenance", "provenance"),
        ("PDF preflight", "pdf"),
    ):
        lines.extend(
            [
                f"## {title}",
                "",
                "| Check | Status | Expected | Actual |",
                "| --- | --- | --- | --- |",
            ]
        )
        for item in report[key]["checks"]:
            lines.append(
                "| {name} | {status} | {expected} | {actual} |".format(
                    name=item["name"].replace("|", "\\|"),
                    status=item["status"],
                    expected=compact_json(item["expected"]).replace("|", "\\|"),
                    actual=compact_json(item["actual"]).replace("|", "\\|"),
                )
            )
        lines.append("")

    lines.extend(["## Scope limitation", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.append("")
    return "\n".join(lines)


def write_report(path: Path, content: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite without --force: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Fall 2026 performer-score MusicXML and PDF delivery artifacts."
    )
    parser.add_argument("--musicxml", type=Path, required=True)
    parser.add_argument("--pdf", type=Path)
    parser.add_argument(
        "--provenance-dir",
        type=Path,
        default=DEFAULT_PROVENANCE_DIR,
    )
    parser.add_argument(
        "--skip-provenance",
        action="store_true",
        help="Leave the 388-replacement provenance check incomplete.",
    )
    parser.add_argument(
        "--safe-margin-points",
        type=float,
        default=DEFAULT_SAFE_MARGIN_POINTS,
    )
    parser.add_argument(
        "--final-delivery",
        action="store_true",
        help=(
            "Assert that the supplied XML and PDF are the intended final artifacts. "
            "Without this flag a clean run is reported only as candidate_passed."
        ),
    )
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--report-md", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.safe_margin_points < 0:
        parser.error("--safe-margin-points must be nonnegative")

    report = validate_delivery(
        args.musicxml,
        args.pdf,
        provenance_dir=None if args.skip_provenance else args.provenance_dir,
        safe_margin_points=args.safe_margin_points,
        final_delivery=args.final_delivery,
    )
    rendered_json = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.report_json:
        write_report(args.report_json, rendered_json, force=args.force)
    if args.report_md:
        write_report(args.report_md, markdown_report(report), force=args.force)
    print(rendered_json, end="")
    if report["final_delivery_pass"]:
        return 0
    if report["status"] == "failed":
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
