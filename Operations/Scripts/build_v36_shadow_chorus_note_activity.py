#!/usr/bin/env python3
"""Build the non-runtime V36 Shadow Chorus note-activity source artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import build_v36_light_chorus_note_activity as common


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCORE = (
    REPO_ROOT
    / "Engraving/Scores/FlashlightsInTheDark_v36_FinaleExport_2026-08-29.musicxml"
)
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "Engraving/Score-Study/FlashlightsInTheDark_v36_ShadowChorusNoteActivity.json"
)
EXPECTED_PART_NAMES = {
    "P1": "Soprano S",
    "P2": "Alto S",
    "P3": "Baritone S",
}
GROUPS = (
    {
        "key": "soprano_s",
        "label": "Soprano Shadow",
        "family": "soprano",
        "partId": "P1",
        "voices": ("1",),
    },
    {
        "key": "alto_s",
        "label": "Alto Shadow",
        "family": "alto",
        "partId": "P2",
        "voices": ("1",),
    },
    {
        "key": "baritone_s",
        "label": "Baritone Shadow",
        "family": "baritone",
        "partId": "P3",
        "voices": ("1", "2"),
    },
)
SHADOW_TIE_RESOLUTION = {
    "partId": "P2",
    "measure": 110,
    "voice": "1",
    "writtenPitch": "Ab4",
    "localStartQuarter": "7/2",
    "durationQuarter": "1/2",
    "nextMeasure": 111,
    "nextWrittenPitch": "G4",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_artifact(score_path: Path = DEFAULT_SCORE) -> dict[str, Any]:
    if sha256(score_path) != common.EXPECTED_SCORE_SHA256:
        raise ValueError("Refusing to derive Shadow activity from an unknown score")
    root = ET.parse(score_path).getroot()
    part_names = common._part_names(root)
    for part_id, expected_name in EXPECTED_PART_NAMES.items():
        if part_names.get(part_id) != expected_name:
            raise ValueError(
                f"Part mapping changed for {part_id}: {part_names.get(part_id)!r}"
            )

    parts = {part.attrib["id"]: part for part in root.findall("part")}
    reference_measures = common._build_measure_map(parts["P1"])
    if len(reference_measures) != common.EXPECTED_MEASURE_COUNT:
        raise ValueError("Unexpected V36 measure count")
    score_span = reference_measures[-1].start + reference_measures[-1].duration
    if score_span != common.EXPECTED_SCORE_SPAN:
        raise ValueError("Unexpected V36 nominal score span")

    extracted: dict[str, list[common.RawNote]] = {}
    inventory: dict[str, dict[str, Any]] = {}
    for part_id in EXPECTED_PART_NAMES:
        measures = common._build_measure_map(parts[part_id])
        if common._measure_signature(measures) != common._measure_signature(reference_measures):
            raise ValueError(f"Measure grid mismatch in {part_id}")
        extracted[part_id], inventory[part_id] = common._extract_part_notes(
            parts[part_id], measures
        )

    original_specs = common.TIE_RESOLUTION_SPECS
    common.TIE_RESOLUTION_SPECS = original_specs + (SHADOW_TIE_RESOLUTION,)
    try:
        groups: list[dict[str, Any]] = []
        tie_resolutions: list[dict[str, Any]] = []
        for spec in GROUPS:
            events: list[dict[str, Any]] = []
            for voice in spec["voices"]:
                voice_notes = [
                    note
                    for note in extracted[spec["partId"]]
                    if note.voice == voice
                ]
                voice_events, resolutions = common._merge_exact_ties(
                    voice_notes,
                    reference_measures,
                    f"{spec['key']}-v{voice}",
                )
                lane_role = (
                    "supplemental-divisi-same-lane"
                    if spec["partId"] == "P3" and voice == "2"
                    else "primary-voice"
                )
                for event in voice_events:
                    event["laneRole"] = lane_role
                events.extend(voice_events)
                tie_resolutions.extend(resolutions)
            events.sort(key=lambda item: (item["_start"], item["_end"], item["id"]))
            intervals = common._activity_intervals(
                events, reference_measures, score_span, spec["key"]
            )
            groups.append(
                {
                    "key": spec["key"],
                    "label": spec["label"],
                    "family": spec["family"],
                    "sourcePartId": spec["partId"],
                    "sourcePartName": EXPECTED_PART_NAMES[spec["partId"]],
                    "sourceVoices": [
                        {
                            "voice": voice,
                            "laneRole": (
                                "supplemental-divisi-same-lane"
                                if spec["partId"] == "P3" and voice == "2"
                                else "primary-voice"
                            ),
                        }
                        for voice in spec["voices"]
                    ],
                    "stateAggregation": {
                        "mode": "binary-logical-or",
                        "onWhen": "one-or-more-performed-note-events-are-sounding",
                        "simultaneousMultiplicity": "does-not-change-output-level",
                        "duplicateSpanHandling": "deduplicate-for-lane-state-only",
                        "provenanceHandling": "preserve-every-source-notehead",
                        "touchingEvents": "continuous-on-without-intermediate-off",
                        "outputStates": ["off", "on"],
                    },
                    "noteEvents": common._without_internal_fields(events),
                    "activityIntervals": common._without_internal_fields(intervals),
                }
            )
    finally:
        common.TIE_RESOLUTION_SPECS = original_specs

    baritone = next(group for group in groups if group["key"] == "baritone_s")
    supplemental = [
        event
        for event in baritone["noteEvents"]
        if event["sourceVoice"] == "2"
    ]
    supplemental_noteheads = sum(
        event["sourceSegmentCount"] for event in supplemental
    )
    if len(supplemental) != 4 or supplemental_noteheads != 6:
        raise ValueError(
            "Expected six P3 voice-2 source noteheads merged into four sounding "
            f"events, found {supplemental_noteheads} noteheads/{len(supplemental)} events"
        )
    primary_spans = {
        (
            event["start"]["cumulativeQuarter"],
            event["end"]["cumulativeQuarter"],
        )
        for event in baritone["noteEvents"]
        if event["sourceVoice"] == "1"
    }
    if any(
        (event["start"]["cumulativeQuarter"], event["end"]["cumulativeQuarter"])
        not in primary_spans
        for event in supplemental
    ):
        raise ValueError("P3 voice-2 divisi is no longer exactly concurrent with voice 1")

    payload: dict[str, Any] = {
        "schemaVersion": "v36-shadow-chorus-note-activity-1",
        "artifactType": "topology-independent-shadow-chorus-note-activity-source",
        "status": "authoring-source-not-runtime-ready",
        "runtimeEligible": False,
        "artisticRule": (
            "From measure 104 onward, a Shadow logical lane may illuminate only "
            "while one or more performed notes in its mapped V36 material sound."
        ),
        "source": {
            "path": common._repo_path(score_path),
            "sha256": common.EXPECTED_SCORE_SHA256,
            "scoreVersion": "V36",
            "measureCount": common.EXPECTED_MEASURE_COUNT,
            "scoreSpanQuarter": common._fraction_string(score_span),
            "generator": "Operations/Scripts/build_v36_shadow_chorus_note_activity.py",
        },
        "coordinateSystems": {
            "authoritativeHere": "V36 score measure/beat and cumulative-quarter coordinates",
            "performanceTime": "Not encoded; bind only to an approved conductor/audio playback clock",
        },
        "deploymentContract": {
            "topologyIndependent": True,
            "physicalPhoneCountEncoded": False,
            "replicationPolicy": "A logical lane may be replicated to assigned devices without brightness stacking",
            "strictGateRequired": True,
            "activePhase": "from V36 measure 104 only",
        },
        "semanticRoutingPolicies": {
            "rests": "off-state is explicit in activityIntervals",
            "ties": "merge only exact adjacent same-pitch starts/stops",
            "chordsAndDivisi": "binary OR; simultaneous notes do not increase brightness",
            "sharedUnisons": "deduplicate only in lane state; retain all source noteheads",
            "cueAndGraceNotes": "none occur in P1-P3",
        },
        "partInventory": [
            {
                "partId": part_id,
                "partName": EXPECTED_PART_NAMES[part_id],
                **inventory[part_id],
            }
            for part_id in ("P1", "P2", "P3")
        ],
        "groups": groups,
        "supplementalSourceVoices": [
            {
                "partId": "P3",
                "voice": "2",
                "assignedGroupKey": "baritone_s",
                "sourceNoteheadCount": supplemental_noteheads,
                "soundingEventCount": len(supplemental),
                "evidence": "Every event is exactly concurrent with a P3 voice-1 span",
                "laneEffect": "provenance only; binary lane output and brightness are unchanged",
            }
        ],
        "tieResolutions": tie_resolutions,
        "unresolvedSourceWarnings": [],
        "validation": {
            "logicalGroupCount": len(groups),
            "sourceNoteheadCount": sum(
                item["pitchedNoteheadCount"] for item in inventory.values()
            ),
            "activityCoversFullScore": all(
                group["activityIntervals"][0]["start"]["cumulativeQuarter"] == "0"
                and group["activityIntervals"][-1]["end"]["cumulativeQuarter"]
                == common._fraction_string(score_span)
                for group in groups
            ),
            "baritoneSupplementalDivisiEventCount": len(supplemental),
            "baritoneSupplementalDivisiSourceNoteheadCount": supplemental_noteheads,
            "unmatchedTieStartsResolved": len(tie_resolutions),
            "cueNoteCount": sum(item["cuePitchedNoteheadCount"] for item in inventory.values()),
            "graceNoteCount": sum(item["graceNoteCount"] for item in inventory.values()),
        },
    }
    if payload["validation"]["unmatchedTieStartsResolved"] != 1:
        raise ValueError("Expected exactly one conservative Shadow tie resolution")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score", type=Path, default=DEFAULT_SCORE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = build_artifact(args.score)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "sha256": sha256(args.output),
                **payload["validation"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
