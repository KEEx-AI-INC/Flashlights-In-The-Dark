#!/usr/bin/env python3
"""Build the non-runtime V36 Light Chorus note-activity source artifact.

The artifact uses exact score coordinates only.  It deliberately contains no
playback timestamps, trigger IDs, brightness curves, or runtime profile data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCORE_PATH = (
    REPO_ROOT
    / "Engraving/Scores/FlashlightsInTheDark_v36_FinaleExport_2026-08-29.musicxml"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "Engraving/Score-Study/FlashlightsInTheDark_v36_LightChorusNoteActivity.json"
)
EXPECTED_SCORE_SHA256 = (
    "251aa4e216ac7bcd0716aaf8efd09a4a7fd259ffaeae1384ba384648ed70e216"
)
EXPECTED_MEASURE_COUNT = 141
EXPECTED_SCORE_SPAN = Fraction(535)
EXPECTED_LIGHT_PART_NAMES = {
    "P4": "Soprano L1, L2",
    "P5": "Alto L1, L2",
    "P6": "Tenor/Bass L",
}


@dataclass(frozen=True)
class GroupSpec:
    key: str
    label: str
    part_id: str
    voice: str
    family: str


GROUP_SPECS = (
    GroupSpec("soprano_l1", "Sop-L1", "P4", "1", "soprano"),
    GroupSpec("soprano_l2", "Sop-L2", "P4", "2", "soprano"),
    GroupSpec("tenor_l", "Ten-L", "P6", "1", "tenor_bass"),
    GroupSpec("bass_l", "Bass-L", "P6", "2", "tenor_bass"),
    GroupSpec("alto_l2", "Alto-L2", "P5", "2", "alto"),
    GroupSpec("alto_l1", "Alto-L1", "P5", "1", "alto"),
)

# Finale exported this upper P4 divisi as voice 3 under the "top line sop solo"
# direction.  Every source and tie-merged span exactly matches P4 voice 1, so it
# shares soprano_l1 and contributes provenance without a seventh lane or level.
SUPPLEMENTAL_VOICE_SPECS = (
    {
        "partId": "P4",
        "voice": "3",
        "label": "Soprano supplemental divisi",
        "assignedGroupKey": "soprano_l1",
        "mappingStatus": "assigned-supplemental-divisi-same-lane",
        "laneRole": "supplemental-divisi-same-lane",
    },
)

# The four <cue/> flags are full-size, positive-duration opposing-stem unison
# onsets in the rendered score.  Each exactly duplicates the simultaneous
# primary voice before the voices divide, so the visible score establishes it
# as performed material.  Preserve the source flag without inferring why Finale
# emitted it.
CUE_RESOLUTION_SPECS = (
    {
        "partId": "P6",
        "measure": 10,
        "voice": "2",
        "writtenPitch": "C#3",
        "localStartQuarter": "0",
        "durationQuarter": "1/3",
        "assignedGroupKey": "bass_l",
        "matchedPrimaryVoice": "1",
        "renderedEvidence": (
            "Full-size opposing-stem shared onset carrying lyric 'we' into the "
            "independent voice-2 phrase 'we are the light'."
        ),
    },
    {
        "partId": "P5",
        "measure": 25,
        "voice": "2",
        "writtenPitch": "G#4",
        "localStartQuarter": "3/4",
        "durationQuarter": "1/4",
        "assignedGroupKey": "alto_l2",
        "matchedPrimaryVoice": "1",
        "renderedEvidence": (
            "Full-size opposing-stem shared 'at' onset before the two alto "
            "voices divide on 'last'."
        ),
    },
    {
        "partId": "P4",
        "measure": 97,
        "voice": "2",
        "writtenPitch": "E5",
        "localStartQuarter": "2",
        "durationQuarter": "3/2",
        "assignedGroupKey": "soprano_l2",
        "matchedPrimaryVoice": "1",
        "renderedEvidence": (
            "Full-size opposing-stem shared 'Should' onset before the "
            "independent voice-2 continuation."
        ),
    },
    {
        "partId": "P5",
        "measure": 98,
        "voice": "2",
        "writtenPitch": "Fb4",
        "localStartQuarter": "0",
        "durationQuarter": "1",
        "assignedGroupKey": "alto_l2",
        "matchedPrimaryVoice": "1",
        "renderedEvidence": (
            "Full-size opposing-stem shared 'hands' onset before the two "
            "alto voices divide on 'grow'."
        ),
    },
)

TIE_RESOLUTION_SPECS = (
    {
        "partId": "P4",
        "measure": 69,
        "voice": "1",
        "writtenPitch": "D#5",
        "localStartQuarter": "7/2",
        "durationQuarter": "1/2",
        "nextMeasure": 70,
        "nextWrittenPitch": "D5",
    },
    {
        "partId": "P4",
        "measure": 134,
        "voice": "1",
        "writtenPitch": "B#3",
        "localStartQuarter": "3",
        "durationQuarter": "1",
        "nextMeasure": 135,
        "nextWrittenPitch": "B3",
    },
    {
        "partId": "P5",
        "measure": 108,
        "voice": "1",
        "writtenPitch": "Bb4",
        "localStartQuarter": "2",
        "durationQuarter": "4",
        "nextMeasure": 109,
        "nextWrittenPitch": "Ab4",
    },
    {
        "partId": "P6",
        "measure": 99,
        "voice": "2",
        "writtenPitch": "A3",
        "localStartQuarter": "2",
        "durationQuarter": "2",
        "nextMeasure": 100,
        "nextWrittenPitch": "Bb3",
    },
)


@dataclass(frozen=True)
class MeasureInfo:
    ordinal: int
    token: str
    number: int
    start: Fraction
    duration: Fraction
    beats: int
    beat_type: int


@dataclass(frozen=True)
class RawNote:
    source_id: str
    part_id: str
    voice: str
    measure_ordinal: int
    measure_token: str
    measure_number: int
    start: Fraction
    end: Fraction
    local_start: Fraction
    duration: Fraction
    pitch: str
    midi: int
    chord_member: bool
    cue: bool
    tie_start: bool
    tie_stop: bool


def _cue_resolution_for(note: RawNote) -> dict[str, Any] | None:
    if not note.cue:
        return None
    matches = [
        spec
        for spec in CUE_RESOLUTION_SPECS
        if spec["partId"] == note.part_id
        and spec["measure"] == note.measure_number
        and spec["voice"] == note.voice
        and spec["writtenPitch"] == note.pitch
        and Fraction(spec["localStartQuarter"]) == note.local_start
        and Fraction(spec["durationQuarter"]) == note.duration
    ]
    if len(matches) != 1:
        raise ValueError(
            "Canonical V36 cue-flag inventory changed at "
            f"{note.part_id} M{note.measure_number} v{note.voice} {note.pitch}"
        )
    return matches[0]


def _is_performed(note: RawNote) -> bool:
    return not note.cue or _cue_resolution_for(note) is not None


def _performance_disposition(note: RawNote) -> str:
    return "performed-shared-unison" if note.cue else "performed"


def _tie_resolution_for(note: RawNote) -> dict[str, Any] | None:
    matches = [
        spec
        for spec in TIE_RESOLUTION_SPECS
        if spec["partId"] == note.part_id
        and spec["measure"] == note.measure_number
        and spec["voice"] == note.voice
        and spec["writtenPitch"] == note.pitch
        and Fraction(spec["localStartQuarter"]) == note.local_start
        and Fraction(spec["durationQuarter"]) == note.duration
    ]
    if len(matches) > 1:
        raise ValueError(f"Duplicate tie-resolution spec for {note.source_id}")
    return matches[0] if matches else None


def _fraction_string(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _parse_measure_number(token: str) -> int:
    match = re.match(r"^(\d+)", token.strip())
    if match is None:
        raise ValueError(f"Measure token has no numeric base: {token!r}")
    return int(match.group(1))


def _parse_beats(raw: str) -> int:
    pieces = raw.replace(" ", "").split("+")
    try:
        return sum(int(piece) for piece in pieces)
    except ValueError as exc:
        raise ValueError(f"Unsupported MusicXML beats value: {raw!r}") from exc


def _repo_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def _pitch_payload(note: ET.Element) -> tuple[str, int]:
    pitch = note.find("pitch")
    if pitch is None:
        raise ValueError("Expected a pitched note")
    step = pitch.findtext("step")
    octave_text = pitch.findtext("octave")
    if step is None or octave_text is None:
        raise ValueError("Incomplete MusicXML pitch")
    alter = int(pitch.findtext("alter", "0"))
    octave = int(octave_text)
    accidental = {-2: "bb", -1: "b", 0: "", 1: "#", 2: "##"}.get(
        alter, f"({alter:+d})"
    )
    semitone = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}[step]
    midi = (octave + 1) * 12 + semitone + alter
    return f"{step}{accidental}{octave}", midi


def _part_names(root: ET.Element) -> dict[str, str]:
    return {
        score_part.attrib["id"]: (score_part.findtext("part-name") or "").strip()
        for score_part in root.findall("./part-list/score-part")
    }


def _build_measure_map(part: ET.Element) -> list[MeasureInfo]:
    beats = 4
    beat_type = 4
    start = Fraction(0)
    result: list[MeasureInfo] = []
    for ordinal, measure in enumerate(part.findall("measure"), start=1):
        token = measure.attrib.get("number", str(ordinal))
        time = measure.find("./attributes/time")
        if time is not None:
            beats_text = time.findtext("beats")
            beat_type_text = time.findtext("beat-type")
            if beats_text is None or beat_type_text is None:
                raise ValueError(f"Incomplete time signature at {part.attrib['id']} {token}")
            beats = _parse_beats(beats_text)
            beat_type = int(beat_type_text)
        duration = Fraction(beats * 4, beat_type)
        result.append(
            MeasureInfo(
                ordinal=ordinal,
                token=token,
                number=_parse_measure_number(token),
                start=start,
                duration=duration,
                beats=beats,
                beat_type=beat_type,
            )
        )
        start += duration
    return result


def _measure_signature(measures: Iterable[MeasureInfo]) -> list[tuple[str, Fraction, int, int]]:
    return [(item.token, item.duration, item.beats, item.beat_type) for item in measures]


def _coordinate(value: Fraction, measures: list[MeasureInfo]) -> dict[str, Any]:
    score_end = measures[-1].start + measures[-1].duration
    if value == score_end:
        return {
            "kind": "score-end",
            "afterMeasureOrdinal": measures[-1].ordinal,
            "afterMeasureToken": measures[-1].token,
            "cumulativeQuarter": _fraction_string(value),
        }
    for measure in measures:
        if measure.start <= value < measure.start + measure.duration:
            local = value - measure.start
            beat = Fraction(1) + local / Fraction(4, measure.beat_type)
            return {
                "kind": "measure-beat",
                "measureOrdinal": measure.ordinal,
                "measureToken": measure.token,
                "measure": measure.number,
                "beat": _fraction_string(beat),
                "meter": f"{measure.beats}/{measure.beat_type}",
                "localQuarter": _fraction_string(local),
                "cumulativeQuarter": _fraction_string(value),
            }
    raise ValueError(f"Score coordinate outside encoded span: {value}")


def _extract_part_notes(
    part: ET.Element,
    measures: list[MeasureInfo],
) -> tuple[list[RawNote], dict[str, Any]]:
    part_id = part.attrib["id"]
    current_divisions: int | None = None
    raw_notes: list[RawNote] = []
    voice_note_counters: dict[str, int] = {}
    observed_voices: set[str] = set()
    rest_count = 0
    hidden_rest_count = 0
    cue_note_count = 0
    grace_count = 0
    encoded_extents: list[Fraction] = []

    xml_measures = part.findall("measure")
    if len(xml_measures) != len(measures):
        raise ValueError(
            f"{part_id} has {len(xml_measures)} measures, expected {len(measures)}"
        )

    for measure, measure_info in zip(xml_measures, measures):
        attributes = measure.find("attributes")
        if attributes is not None and attributes.findtext("divisions"):
            current_divisions = int(attributes.findtext("divisions", "0"))
        if current_divisions is None or current_divisions <= 0:
            raise ValueError(f"No positive divisions value before {part_id} {measure_info.token}")

        position = 0
        max_position = 0
        last_note_onset = 0
        seen_timed_item = False

        for child in measure:
            if child.tag == "attributes":
                new_divisions_text = child.findtext("divisions")
                if new_divisions_text:
                    new_divisions = int(new_divisions_text)
                    if seen_timed_item and new_divisions != current_divisions:
                        raise ValueError(
                            f"Mid-measure divisions change is unsupported at {part_id} "
                            f"{measure_info.token}"
                        )
                    current_divisions = new_divisions
                continue
            if child.tag == "backup":
                position -= int(child.findtext("duration", "0"))
                if position < 0:
                    raise ValueError(f"Negative cursor at {part_id} {measure_info.token}")
                seen_timed_item = True
                continue
            if child.tag == "forward":
                position += int(child.findtext("duration", "0"))
                max_position = max(max_position, position)
                seen_timed_item = True
                continue
            if child.tag != "note":
                continue

            seen_timed_item = True
            if child.find("grace") is not None:
                grace_count += 1
                raise ValueError(
                    f"Grace note requires an explicit visibility policy at "
                    f"{part_id} {measure_info.token}"
                )
            duration_divisions = int(child.findtext("duration", "0"))
            if duration_divisions <= 0:
                raise ValueError(f"Non-positive note duration at {part_id} {measure_info.token}")
            is_chord = child.find("chord") is not None
            onset_divisions = last_note_onset if is_chord else position
            local_start = Fraction(onset_divisions, current_divisions)
            duration = Fraction(duration_divisions, current_divisions)
            max_position = max(max_position, onset_divisions + duration_divisions)

            if child.find("rest") is not None:
                rest_count += 1
                if child.attrib.get("print-object") == "no":
                    hidden_rest_count += 1
            else:
                voice = child.findtext("voice", "1")
                observed_voices.add(voice)
                voice_note_counters[voice] = voice_note_counters.get(voice, 0) + 1
                pitch, midi = _pitch_payload(child)
                is_cue = child.find("cue") is not None
                if is_cue:
                    cue_note_count += 1
                tie_types = {tie.attrib.get("type", "") for tie in child.findall("tie")}
                source_id = (
                    f"{part_id}-m{measure_info.ordinal:03d}-v{voice}-"
                    f"n{voice_note_counters[voice]:04d}"
                )
                raw_notes.append(
                    RawNote(
                        source_id=source_id,
                        part_id=part_id,
                        voice=voice,
                        measure_ordinal=measure_info.ordinal,
                        measure_token=measure_info.token,
                        measure_number=measure_info.number,
                        start=measure_info.start + local_start,
                        end=measure_info.start + local_start + duration,
                        local_start=local_start,
                        duration=duration,
                        pitch=pitch,
                        midi=midi,
                        chord_member=is_chord,
                        cue=is_cue,
                        tie_start="start" in tie_types,
                        tie_stop="stop" in tie_types,
                    )
                )

            if not is_chord:
                last_note_onset = position
                position += duration_divisions

        extent = Fraction(max_position, current_divisions)
        encoded_extents.append(extent)
        if extent != measure_info.duration:
            raise ValueError(
                f"Encoded extent mismatch at {part_id} {measure_info.token}: "
                f"{_fraction_string(extent)} != {_fraction_string(measure_info.duration)}"
            )

    return raw_notes, {
        "observedVoices": sorted(observed_voices, key=lambda item: int(item)),
        "pitchedNoteheadCount": len(raw_notes),
        "nonCuePitchedNoteheadCount": sum(not note.cue for note in raw_notes),
        "cuePitchedNoteheadCount": cue_note_count,
        "restElementCount": rest_count,
        "hiddenRestElementCount": hidden_rest_count,
        "chordMemberCount": sum(note.chord_member for note in raw_notes),
        "graceNoteCount": grace_count,
        "encodedMeasureCount": len(encoded_extents),
    }


def _segment_payload(note: RawNote, measures: list[MeasureInfo]) -> dict[str, Any]:
    return {
        "sourceId": note.source_id,
        "sourcePartId": note.part_id,
        "sourceMeasureOrdinal": note.measure_ordinal,
        "sourceMeasureToken": note.measure_token,
        "sourceMeasure": note.measure_number,
        "sourceVoice": note.voice,
        "start": _coordinate(note.start, measures),
        "end": _coordinate(note.end, measures),
        "durationQuarter": _fraction_string(note.duration),
        "writtenPitch": note.pitch,
        "midi": note.midi,
        "chordMember": note.chord_member,
        "sourceCueFlag": note.cue,
        "performanceDisposition": _performance_disposition(note),
        "tieStart": note.tie_start,
        "tieStop": note.tie_stop,
    }


def _merge_exact_ties(
    notes: list[RawNote],
    measures: list[MeasureInfo],
    event_prefix: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Merge only adjacent, same-pitch ties with an explicit start and stop."""

    ordered = sorted(
        notes,
        key=lambda note: (
            note.start,
            note.end,
            note.voice,
            note.midi,
            note.pitch,
            note.source_id,
        ),
    )
    by_id = {note.source_id: note for note in ordered}
    incoming: dict[str, str] = {}
    outgoing: dict[str, str] = {}

    for current in ordered:
        if not current.tie_stop:
            continue
        candidates = [
            previous
            for previous in ordered
            if previous.part_id == current.part_id
            and previous.voice == current.voice
            and previous.pitch == current.pitch
            and previous.end == current.start
            and previous.tie_start
            and previous.source_id not in outgoing
        ]
        if len(candidates) == 1:
            previous = candidates[0]
            outgoing[previous.source_id] = current.source_id
            incoming[current.source_id] = previous.source_id

    resolutions: list[dict[str, Any]] = []
    for note in ordered:
        if note.tie_start and note.source_id not in outgoing:
            spec = _tie_resolution_for(note)
            if spec is None:
                raise ValueError(f"Unresolved unmatched tie start: {note.source_id}")
            adjacent = [
                candidate
                for candidate in ordered
                if candidate.part_id == note.part_id
                and candidate.voice == note.voice
                and candidate.start == note.end
                and candidate.measure_number == spec["nextMeasure"]
                and candidate.pitch == spec["nextWrittenPitch"]
            ]
            if len(adjacent) != 1 or adjacent[0].pitch == note.pitch:
                raise ValueError(
                    "Tie-resolution continuation changed for "
                    f"{note.source_id}: {[item.source_id for item in adjacent]}"
                )
            next_note = adjacent[0]
            resolutions.append(
                {
                    "kind": "capped-at-encoded-end-different-pitch-continuation",
                    "sourceId": note.source_id,
                    "partId": note.part_id,
                    "voice": note.voice,
                    "writtenPitch": note.pitch,
                    "at": _coordinate(note.start, measures),
                    "encodedEnd": _coordinate(note.end, measures),
                    "encodedDurationQuarter": _fraction_string(note.duration),
                    "nextSourceId": next_note.source_id,
                    "nextWrittenPitch": next_note.pitch,
                    "nextStart": _coordinate(next_note.start, measures),
                    "gapQuarter": "0",
                    "resolution": (
                        "Cap the old pitch at its encoded end and begin the adjacent "
                        "different pitch as a separate event. Binary lane OR leaves no "
                        "off transition at the shared boundary."
                    ),
                }
            )
        if note.tie_stop and note.source_id not in incoming:
            raise ValueError(f"Unresolved unmatched tie stop: {note.source_id}")

    chains: list[list[RawNote]] = []
    for note in ordered:
        if note.source_id in incoming:
            continue
        chain = [note]
        cursor = note
        while cursor.source_id in outgoing:
            cursor = by_id[outgoing[cursor.source_id]]
            chain.append(cursor)
        chains.append(chain)

    events: list[dict[str, Any]] = []
    for index, chain in enumerate(chains, start=1):
        first = chain[0]
        last = chain[-1]
        event_id = f"{event_prefix}-note-{index:04d}"
        events.append(
            {
                "id": event_id,
                "partId": first.part_id,
                "sourceVoice": first.voice,
                "writtenPitch": first.pitch,
                "midi": first.midi,
                "start": _coordinate(first.start, measures),
                "end": _coordinate(last.end, measures),
                "durationQuarter": _fraction_string(last.end - first.start),
                "sourceSegmentCount": len(chain),
                "tiedContinuation": len(chain) > 1,
                "sourceSegments": [_segment_payload(item, measures) for item in chain],
                "_start": first.start,
                "_end": last.end,
            }
        )
    return events, resolutions


def _activity_intervals(
    events: list[dict[str, Any]],
    measures: list[MeasureInfo],
    score_span: Fraction,
    group_key: str,
) -> list[dict[str, Any]]:
    ordered = sorted(events, key=lambda item: (item["_start"], item["_end"], item["id"]))
    merged: list[dict[str, Any]] = []
    for event in ordered:
        if not merged or event["_start"] > merged[-1]["end"]:
            merged.append(
                {
                    "start": event["_start"],
                    "end": event["_end"],
                    "noteEventIds": [event["id"]],
                }
            )
        else:
            merged[-1]["end"] = max(merged[-1]["end"], event["_end"])
            merged[-1]["noteEventIds"].append(event["id"])

    intervals: list[dict[str, Any]] = []
    cursor = Fraction(0)
    interval_index = 1
    for item in merged:
        if cursor < item["start"]:
            intervals.append(
                {
                    "id": f"{group_key}-activity-{interval_index:04d}",
                    "state": "off",
                    "start": _coordinate(cursor, measures),
                    "end": _coordinate(item["start"], measures),
                    "durationQuarter": _fraction_string(item["start"] - cursor),
                    "noteEventIds": [],
                    "_start": cursor,
                    "_end": item["start"],
                }
            )
            interval_index += 1
        intervals.append(
            {
                "id": f"{group_key}-activity-{interval_index:04d}",
                "state": "on",
                "start": _coordinate(item["start"], measures),
                "end": _coordinate(item["end"], measures),
                "durationQuarter": _fraction_string(item["end"] - item["start"]),
                "noteEventIds": item["noteEventIds"],
                "_start": item["start"],
                "_end": item["end"],
            }
        )
        interval_index += 1
        cursor = item["end"]
    if cursor < score_span:
        intervals.append(
            {
                "id": f"{group_key}-activity-{interval_index:04d}",
                "state": "off",
                "start": _coordinate(cursor, measures),
                "end": _coordinate(score_span, measures),
                "durationQuarter": _fraction_string(score_span - cursor),
                "noteEventIds": [],
                "_start": cursor,
                "_end": score_span,
            }
        )
    return intervals


def _without_internal_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_internal_fields(item)
            for key, item in value.items()
            if not key.startswith("_")
        }
    if isinstance(value, list):
        return [_without_internal_fields(item) for item in value]
    return value


def _source_metadata(root: ET.Element) -> dict[str, Any]:
    identification = root.find("identification")
    encoding = identification.find("encoding") if identification is not None else None
    software = encoding.findtext("software") if encoding is not None else None
    encoding_date = encoding.findtext("encoding-date") if encoding is not None else None
    work_title = root.findtext("./work/work-title")
    movement_title = root.findtext("movement-title")
    return {
        "workTitle": (work_title or movement_title or "").strip(),
        "musicXmlVersion": root.attrib.get("version"),
        "encodingSoftware": software,
        "encodingDate": encoding_date,
    }


def _measure_grid_payload(measures: list[MeasureInfo]) -> dict[str, Any]:
    return {
        "unit": "nominal-quarter-note",
        "measures": [
            {
                "ordinal": measure.ordinal,
                "token": measure.token,
                "measure": measure.number,
                "startQuarter": _fraction_string(measure.start),
                "durationQuarter": _fraction_string(measure.duration),
                "beats": measure.beats,
                "beatType": measure.beat_type,
                "meter": f"{measure.beats}/{measure.beat_type}",
            }
            for measure in measures
        ],
    }


def build_artifact(score_path: Path = DEFAULT_SCORE_PATH) -> dict[str, Any]:
    score_path = score_path.resolve()
    source_bytes = score_path.read_bytes()
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    if source_sha256 != EXPECTED_SCORE_SHA256:
        raise ValueError(
            "V36 note activity requires the canonical V36 Finale export: "
            f"expected SHA-256 {EXPECTED_SCORE_SHA256}, got {source_sha256} "
            f"for {score_path}"
        )
    root = ET.fromstring(source_bytes)
    parts = {part.attrib["id"]: part for part in root.findall("part")}
    part_names = _part_names(root)
    missing_parts = sorted({spec.part_id for spec in GROUP_SPECS} - set(parts))
    if missing_parts:
        raise ValueError(f"Missing mapped Light Chorus parts: {missing_parts}")

    reference_part = next(iter(parts.values()))
    measures = _build_measure_map(reference_part)
    reference_signature = _measure_signature(measures)
    score_span = measures[-1].start + measures[-1].duration
    if len(measures) != EXPECTED_MEASURE_COUNT or score_span != EXPECTED_SCORE_SPAN:
        raise ValueError(
            "Canonical V36 score-shape invariant changed: "
            f"measures={len(measures)}, span={_fraction_string(score_span)}"
        )
    observed_light_part_names = {
        part_id: part_names.get(part_id, "") for part_id in EXPECTED_LIGHT_PART_NAMES
    }
    if observed_light_part_names != EXPECTED_LIGHT_PART_NAMES:
        raise ValueError(
            "Canonical V36 Light Chorus part names changed: "
            f"{observed_light_part_names}"
        )
    for part_id in sorted({spec.part_id for spec in GROUP_SPECS}):
        candidate = _build_measure_map(parts[part_id])
        if _measure_signature(candidate) != reference_signature:
            raise ValueError(f"Meter map differs for mapped part {part_id}")

    extracted: dict[str, list[RawNote]] = {}
    part_inventory: list[dict[str, Any]] = []
    for part_id in sorted({spec.part_id for spec in GROUP_SPECS}):
        notes, inventory = _extract_part_notes(parts[part_id], measures)
        extracted[part_id] = notes
        part_inventory.append(
            {
                "partId": part_id,
                "partName": part_names.get(part_id, ""),
                **inventory,
                "performedPitchedNoteheadCount": sum(
                    _is_performed(note) for note in notes
                ),
                "sourceCueFlaggedPerformedCount": sum(
                    note.cue and _is_performed(note) for note in notes
                ),
                "excludedPitchedNoteheadCount": sum(
                    not _is_performed(note) for note in notes
                ),
            }
        )

    primary_voice_map = {(spec.part_id, spec.voice): spec for spec in GROUP_SPECS}
    supplemental_voice_map = {
        (item["partId"], item["voice"]): item for item in SUPPLEMENTAL_VOICE_SPECS
    }
    observed_voice_keys = {
        (note.part_id, note.voice)
        for notes in extracted.values()
        for note in notes
    }
    covered_voice_keys = set(primary_voice_map) | set(supplemental_voice_map)
    if observed_voice_keys != covered_voice_keys:
        raise ValueError(
            "Light Chorus voice inventory changed: "
            f"observed={sorted(observed_voice_keys)} covered={sorted(covered_voice_keys)}"
        )

    group_payloads: list[dict[str, Any]] = []
    primary_events_by_group: dict[str, list[dict[str, Any]]] = {}
    primary_notes_by_group: dict[str, list[RawNote]] = {}
    tie_resolutions: list[dict[str, Any]] = []
    for spec in GROUP_SPECS:
        raw_notes = [
            note
            for note in extracted[spec.part_id]
            if note.voice == spec.voice and _is_performed(note)
        ]
        events, resolutions = _merge_exact_ties(raw_notes, measures, spec.key)
        for event in events:
            event["laneRole"] = "primary-voice-proxy"
        primary_events_by_group[spec.key] = events
        primary_notes_by_group[spec.key] = raw_notes
        tie_resolutions.extend(resolutions)
        group_payloads.append(
            {
                "key": spec.key,
                "label": spec.label,
                "family": spec.family,
                "sourcePartId": spec.part_id,
                "sourcePartName": part_names.get(spec.part_id, ""),
                "primarySourceVoice": spec.voice,
                "sourceVoices": [
                    {"voice": spec.voice, "laneRole": "primary-voice-proxy"}
                ],
                "mappingConfidence": "verified-logical-voice-proxy",
                "stateAggregation": {
                    "mode": "binary-logical-or",
                    "onWhen": "one-or-more-performed-note-events-are-sounding",
                    "simultaneousMultiplicity": "does-not-change-output-level",
                    "duplicateSpanHandling": "deduplicate-for-lane-state-only",
                    "provenanceHandling": "preserve-every-source-notehead",
                    "touchingEvents": "continuous-on-without-intermediate-off",
                    "outputStates": ["off", "on"],
                },
                "noteEvents": events,
            }
        )

    supplemental_payloads: list[dict[str, Any]] = []
    group_by_key = {group["key"]: group for group in group_payloads}
    for supplemental in SUPPLEMENTAL_VOICE_SPECS:
        raw_notes = [
            note
            for note in extracted[supplemental["partId"]]
            if note.voice == supplemental["voice"] and _is_performed(note)
        ]
        prefix = (
            f"{supplemental['assignedGroupKey']}-supplemental-v"
            f"{supplemental['voice']}"
        )
        events, resolutions = _merge_exact_ties(raw_notes, measures, prefix)
        if resolutions:
            raise ValueError("Unexpected tie-resolution case in supplemental P4 voice 3")
        for event in events:
            event["laneRole"] = supplemental["laneRole"]

        coverage_notes = primary_notes_by_group[supplemental["assignedGroupKey"]]
        raw_matches = {
            note.source_id: sorted(
                candidate.source_id
                for candidate in coverage_notes
                if candidate.start == note.start and candidate.end == note.end
            )
            for note in raw_notes
        }
        if any(not matches for matches in raw_matches.values()):
            raise ValueError("P4 voice 3 no longer exactly matches P4 voice 1 spans")
        coverage_events = primary_events_by_group[supplemental["assignedGroupKey"]]
        event_matches = {
            event["id"]: sorted(
                candidate["id"]
                for candidate in coverage_events
                if candidate["_start"] == event["_start"]
                and candidate["_end"] == event["_end"]
            )
            for event in events
        }
        if any(not matches for matches in event_matches.values()):
            raise ValueError("P4 voice 3 merged spans no longer match P4 voice 1")

        target_group = group_by_key[supplemental["assignedGroupKey"]]
        target_group["sourceVoices"].append(
            {"voice": supplemental["voice"], "laneRole": supplemental["laneRole"]}
        )
        target_group["noteEvents"].extend(events)
        supplemental_payloads.append(
            {
                **supplemental,
                "partName": part_names.get(supplemental["partId"], ""),
                "visibilityRule": (
                    "Assign to the existing soprano lane. Exact concurrence with its "
                    "primary voice adds source provenance but binary OR prevents a new "
                    "lane or an output-level increase."
                ),
                "sourcePitchedNoteheadCount": len(raw_notes),
                "soundingEventCount": len(events),
                "exactPrimaryRawSpanMatchCount": len(raw_matches),
                "exactPrimaryEventSpanMatchCount": len(event_matches),
                "allSpansExactlyConcurrent": True,
                "sourceIds": [note.source_id for note in raw_notes],
                "noteEventIds": [event["id"] for event in events],
                "matchingPrimarySourceIds": raw_matches,
                "matchingPrimaryNoteEventIds": event_matches,
            }
        )

    for group in group_payloads:
        events = group["noteEvents"]
        intervals = _activity_intervals(events, measures, score_span, group["key"])
        group["activityIntervals"] = intervals
        primary_segments = sum(
            event["sourceSegmentCount"]
            for event in events
            if event["laneRole"] == "primary-voice-proxy"
        )
        supplemental_segments = sum(
            event["sourceSegmentCount"]
            for event in events
            if event["laneRole"] == "supplemental-divisi-same-lane"
        )
        group["summary"] = {
            "performedSourcePitchedNoteheadCount": primary_segments
            + supplemental_segments,
            "primarySourcePitchedNoteheadCount": primary_segments,
            "supplementalSourcePitchedNoteheadCount": supplemental_segments,
            "chordMemberCount": sum(
                segment["chordMember"]
                for event in events
                for segment in event["sourceSegments"]
            ),
            "soundingEventCount": len(events),
            "laneStateDistinctSpanCount": len(
                {(event["_start"], event["_end"]) for event in events}
            ),
            "tiedSoundingEventCount": sum(
                event["sourceSegmentCount"] > 1 for event in events
            ),
            "onIntervalCount": sum(
                interval["state"] == "on" for interval in intervals
            ),
            "offIntervalCount": sum(
                interval["state"] == "off" for interval in intervals
            ),
            "soundingQuarter": _fraction_string(
                sum(
                    (
                        interval["_end"] - interval["_start"]
                        for interval in intervals
                        if interval["state"] == "on"
                    ),
                    Fraction(0),
                )
            ),
        }

    source_to_event: dict[str, tuple[str, str]] = {}
    for group in group_payloads:
        for event in group["noteEvents"]:
            for segment in event["sourceSegments"]:
                source_to_event[segment["sourceId"]] = (group["key"], event["id"])

    cue_notes = sorted(
        (note for notes in extracted.values() for note in notes if note.cue),
        key=lambda note: (note.start, note.part_id, int(note.voice), note.source_id),
    )
    if len(cue_notes) != len(CUE_RESOLUTION_SPECS):
        raise ValueError("Canonical V36 cue-flag count changed")
    cue_flag_resolutions: list[dict[str, Any]] = []
    for note in cue_notes:
        spec = _cue_resolution_for(note)
        assert spec is not None
        primary_matches = [
            candidate
            for candidate in extracted[note.part_id]
            if candidate.voice == spec["matchedPrimaryVoice"]
            and not candidate.cue
            and candidate.start == note.start
            and candidate.end == note.end
            and candidate.pitch == note.pitch
        ]
        if len(primary_matches) != 1:
            raise ValueError(f"Cue-flag shared-unison evidence changed: {note.source_id}")
        assigned_group, event_id = source_to_event[note.source_id]
        if assigned_group != spec["assignedGroupKey"]:
            raise ValueError(f"Cue-flag lane assignment changed: {note.source_id}")
        cue_flag_resolutions.append(
            {
                "sourceId": note.source_id,
                "disposition": "performed-shared-unison",
                "assignedGroupKey": assigned_group,
                "noteEventId": event_id,
                "matchedPrimarySourceId": primary_matches[0].source_id,
                "matchedPrimaryVoice": spec["matchedPrimaryVoice"],
                "exactStartEndPitchMatch": True,
                "musicXmlEvidence": (
                    "Positive duration with type size full; cue flag retained as "
                    "source provenance rather than treated as a rest."
                ),
                "renderedScoreEvidence": spec["renderedEvidence"],
                **_segment_payload(note, measures),
            }
        )

    for resolution in tie_resolutions:
        resolution["assignedGroupKey"] = source_to_event[resolution["sourceId"]][0]
        resolution["sourceNoteEventId"] = source_to_event[resolution["sourceId"]][1]
        resolution["nextNoteEventId"] = source_to_event[resolution["nextSourceId"]][1]
    tie_resolutions.sort(
        key=lambda item: (
            item["partId"],
            int(item["voice"]),
            Fraction(item["at"]["cumulativeQuarter"]),
            item["sourceId"],
        )
    )
    if len(tie_resolutions) != len(TIE_RESOLUTION_SPECS):
        raise ValueError("Canonical V36 unmatched-tie inventory changed")

    source_info = _source_metadata(root)
    payload: dict[str, Any] = {
        "schemaVersion": "v36-light-chorus-note-activity-2",
        "artifactType": "score-derived-light-chorus-note-activity",
        "status": "authoring-source-not-runtime-ready",
        "artisticRule": {
            "statement": (
                "Each performed Light Chorus note is visibly represented: a logical lane is "
                "on while any assigned note is sounding and off when none is sounding."
            ),
            "aggregation": "binary-logical-or-by-six-logical-vocal-lanes",
            "tiePolicy": (
                "Merge only adjacent same-pitch segments with agreeing explicit tie markup. "
                "Cap the four verified pitch-changing connectors at encoded boundaries and "
                "keep the lane continuously on when the next note begins there."
            ),
            "chordAndDivisiPolicy": (
                "Preserve every source notehead; simultaneous notes and duplicate spans are "
                "binary-OR lane-state inputs and never increase output level."
            ),
            "restPolicy": (
                "Off intervals explicitly cover every score span in which a lane has no "
                "assigned sounding event."
            ),
            "cuePolicy": (
                "The four cue-flagged notes are full-size performed shared-unison onsets in "
                "V36. Include them while retaining the cue flag in provenance."
            ),
        },
        "source": {
            "path": _repo_path(score_path),
            "sha256": source_sha256,
            "scoreVersion": "V36",
            "measureCount": len(measures),
            "scoreSpanQuarter": _fraction_string(score_span),
            **source_info,
            "generator": _repo_path(Path(__file__)),
        },
        "coordinateSystems": {
            "score": {
                "authority": "canonical-v36-musicxml-notation-grid",
                "unit": "nominal-quarter-note",
                "encoding": "exact-reduced-rational-string",
                "status": "annotation-and-authoring-source",
            },
            "performance": {
                "authorityRequired": "approved-conductor-audio-playback-clock",
                "status": "unbound",
                "note": (
                    "No score coordinate in this artifact is an approved playback timestamp."
                ),
            },
        },
        "deploymentContract": {
            "logicalLaneCount": len(GROUP_SPECS),
            "logicalLaneKeys": [spec.key for spec in GROUP_SPECS],
            "authoringTopology": "independent-of-physical-endpoints",
            "runtimeAssignmentRequired": True,
            "replicationRule": (
                "At runtime, copy each lane's identical binary state to every endpoint "
                "assigned to that lane."
            ),
            "endpointVariation": "none-in-this-artistic-source",
            "physicalPopulation": "runtime-deployment-concern-not-stored-here",
        },
        "scoreGrid": _measure_grid_payload(measures),
        "mappingProvenance": {
            "stageOrder": [spec.key for spec in GROUP_SPECS],
            "verifiedLogicalMappingSources": [
                "Operations/Scripts/build_trigger_point_light_show.py",
                "Software/Conductor-MacOS/FlashlightsInTheDark_MacOS/Model/EventRecipe.swift",
                "Software/Singer-Client/lib/model/client_state.dart",
            ],
            "legacyDeploymentLayoutsExcludedFromAuthoringInputs": [
                "Software/Conductor-MacOS/FlashlightsInTheDark_MacOS/Model/LightStaffStageLayout.swift",
                "Software/Singer-Client/lib/model/client_state.dart",
            ],
            "interpretationBoundary": (
                "A separately encoded voice remains on its verified lane. Compressed "
                "single-voice notation is not fanned out to an absent voice."
            ),
        },
        "semanticRoutingPolicies": [
            {
                "kind": "supplemental-soprano-divisi",
                "source": "P4 voice 3",
                "handling": (
                    "Assign to soprano_l1 because all source and tie-merged spans exactly "
                    "coincide with P4 voice 1; preserve both provenances and use one binary state."
                ),
            },
            {
                "kind": "chords-and-divisi",
                "handling": (
                    "Keep every pitch in its explicitly encoded lane; aggregate simultaneous "
                    "activity with binary OR and no output-level stacking."
                ),
            },
            {
                "kind": "compressed-single-voice-material",
                "handling": (
                    "Keep it on the encoded voice's lane; do not infer routing to an absent "
                    "voice from texture or legacy choreography."
                ),
            },
            {
                "kind": "source-cue-flags",
                "handling": (
                    "Include the four verified performed shared-unison onsets; do not use the "
                    "cue flag alone as evidence that a singer is silent."
                ),
            },
        ],
        "partInventory": part_inventory,
        "groups": group_payloads,
        "supplementalSourceVoices": supplemental_payloads,
        "cueFlagResolutions": cue_flag_resolutions,
        "tieResolutions": tie_resolutions,
        "excludedSourceNotes": [],
        "unresolvedSourceWarnings": [],
        "validation": {
            "mappedGroupCount": len(GROUP_SPECS),
            "mappedPrimaryVoiceCount": len(GROUP_SPECS),
            "supplementalSourceVoiceCount": len(SUPPLEMENTAL_VOICE_SPECS),
            "allObservedLightVoicesInventoried": True,
            "allSupplementalSpansExactlyConcurrent": True,
            "allCueFlagsResolvedAsPerformed": True,
            "allUnmatchedTieStartsResolved": True,
            "activityIntervalsExplicitlyCoverScore": True,
            "legacyRuntimeArtifactsUsedAsInputs": False,
            "runtimeTimingPresent": False,
            "physicalEndpointAssignmentsPresent": False,
        },
    }
    cleaned = _without_internal_fields(payload)
    validate_artifact(cleaned)
    return cleaned


def _fraction_from_string(raw: str) -> Fraction:
    return Fraction(raw)


def _coordinate_fraction(coordinate: dict[str, Any]) -> Fraction:
    return _fraction_from_string(coordinate["cumulativeQuarter"])


def validate_artifact(payload: dict[str, Any]) -> None:
    if payload.get("schemaVersion") != "v36-light-chorus-note-activity-2":
        raise ValueError("Unexpected V36 note-activity schema version")
    if payload.get("status") != "authoring-source-not-runtime-ready":
        raise ValueError("V36 note activity must remain non-runtime")
    if payload["coordinateSystems"]["performance"]["status"] != "unbound":
        raise ValueError("Performance coordinates must remain unbound")

    deployment = payload["deploymentContract"]
    expected_lane_keys = [spec.key for spec in GROUP_SPECS]
    if (
        deployment["logicalLaneCount"] != len(GROUP_SPECS)
        or deployment["logicalLaneKeys"] != expected_lane_keys
        or deployment["authoringTopology"] != "independent-of-physical-endpoints"
        or deployment["runtimeAssignmentRequired"] is not True
        or deployment["endpointVariation"] != "none-in-this-artistic-source"
        or deployment["physicalPopulation"]
        != "runtime-deployment-concern-not-stored-here"
    ):
        raise ValueError("Topology-independent deployment contract changed")

    source = payload["source"]
    if source["sha256"] != EXPECTED_SCORE_SHA256:
        raise ValueError("Artifact does not name the canonical V36 score hash")
    if source["measureCount"] != EXPECTED_MEASURE_COUNT:
        raise ValueError("Artifact does not name the canonical V36 measure count")
    score_span = _fraction_from_string(source["scoreSpanQuarter"])
    if score_span != EXPECTED_SCORE_SPAN:
        raise ValueError("Artifact does not name the canonical V36 score span")

    score_grid = payload["scoreGrid"]
    if score_grid["unit"] != "nominal-quarter-note":
        raise ValueError("Unexpected score-grid unit")
    grid_measures = score_grid["measures"]
    if len(grid_measures) != EXPECTED_MEASURE_COUNT:
        raise ValueError("Score grid has the wrong measure count")
    measure_by_ordinal: dict[int, dict[str, Any]] = {}
    grid_cursor = Fraction(0)
    for expected_ordinal, measure in enumerate(grid_measures, start=1):
        ordinal = measure["ordinal"]
        start = _fraction_from_string(measure["startQuarter"])
        duration = _fraction_from_string(measure["durationQuarter"])
        beats = int(measure["beats"])
        beat_type = int(measure["beatType"])
        if ordinal != expected_ordinal or ordinal in measure_by_ordinal:
            raise ValueError("Score-grid ordinals are not consecutive")
        if start != grid_cursor or duration <= 0:
            raise ValueError(f"Invalid score-grid extent at measure {ordinal}")
        if duration != Fraction(beats * 4, beat_type):
            raise ValueError(f"Meter duration mismatch at measure {ordinal}")
        if measure["meter"] != f"{beats}/{beat_type}":
            raise ValueError(f"Meter label mismatch at measure {ordinal}")
        measure_by_ordinal[ordinal] = measure
        grid_cursor += duration
    if grid_cursor != score_span:
        raise ValueError("Score grid does not reach the declared score span")

    def validate_coordinate(coordinate: dict[str, Any]) -> None:
        cumulative = _coordinate_fraction(coordinate)
        if coordinate["kind"] == "score-end":
            final_measure = grid_measures[-1]
            if (
                cumulative != score_span
                or coordinate["afterMeasureOrdinal"] != final_measure["ordinal"]
                or coordinate["afterMeasureToken"] != final_measure["token"]
            ):
                raise ValueError("Invalid score-end coordinate")
            return
        if coordinate["kind"] != "measure-beat":
            raise ValueError(f"Unknown score-coordinate kind: {coordinate['kind']}")
        measure = measure_by_ordinal.get(coordinate["measureOrdinal"])
        if measure is None:
            raise ValueError("Coordinate names an unknown measure ordinal")
        if (
            coordinate["measureToken"] != measure["token"]
            or coordinate["measure"] != measure["measure"]
            or coordinate["meter"] != measure["meter"]
        ):
            raise ValueError("Coordinate measure annotation disagrees with score grid")
        local = _fraction_from_string(coordinate["localQuarter"])
        start = _fraction_from_string(measure["startQuarter"])
        duration = _fraction_from_string(measure["durationQuarter"])
        if not (0 <= local < duration) or cumulative != start + local:
            raise ValueError("Coordinate local and cumulative offsets disagree")
        expected_beat = Fraction(1) + local / Fraction(4, measure["beatType"])
        if _fraction_from_string(coordinate["beat"]) != expected_beat:
            raise ValueError("Coordinate notated beat disagrees with score grid")

    forbidden_keys = {
        "atMs",
        "durationMs",
        "availableWindowMs",
        "triggerId",
        "cueId",
        "keyframes",
        "brightness",
        "intensity",
        "lightShowManifest",
        "legacyRuntimeTopologyReference",
        "slots",
        "slot",
        "legacySlot",
        "seatNumber",
        "deviceCount",
        "phoneCount",
    }

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            overlap = forbidden_keys.intersection(value)
            if overlap:
                raise ValueError(f"Runtime fields are forbidden: {sorted(overlap)}")
            if "kind" in value and "cumulativeQuarter" in value:
                validate_coordinate(value)
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)

    def validate_duration(item: dict[str, Any], label: str) -> None:
        start = _coordinate_fraction(item["start"])
        end = _coordinate_fraction(item["end"])
        if end <= start or _fraction_from_string(item["durationQuarter"]) != end - start:
            raise ValueError(f"Duration mismatch in {label}")

    seen_source_ids: set[str] = set()
    source_segments: dict[str, dict[str, Any]] = {}
    source_locations: dict[str, tuple[str, str]] = {}

    def validate_event(
        event: dict[str, Any],
        expected_part_id: str,
        expected_roles: dict[str, str],
        group_key: str,
    ) -> None:
        validate_duration(event, event["id"])
        expected_role = expected_roles.get(event["sourceVoice"])
        if event["partId"] != expected_part_id or expected_role is None:
            raise ValueError(f"Event routing provenance mismatch in {event['id']}")
        if event["laneRole"] != expected_role:
            raise ValueError(f"Event lane role mismatch in {event['id']}")
        segments = event["sourceSegments"]
        if len(segments) != event["sourceSegmentCount"] or not segments:
            raise ValueError(f"Segment count mismatch in {event['id']}")
        if event["tiedContinuation"] != (len(segments) > 1):
            raise ValueError(f"Tie-continuation flag mismatch in {event['id']}")
        for segment in segments:
            validate_duration(segment, segment["sourceId"])
            if segment["sourceId"] in seen_source_ids:
                raise ValueError(f"Duplicate source note {segment['sourceId']}")
            seen_source_ids.add(segment["sourceId"])
            source_segments[segment["sourceId"]] = segment
            source_locations[segment["sourceId"]] = (group_key, event["id"])
            if (
                segment["sourcePartId"] != expected_part_id
                or segment["sourceVoice"] != event["sourceVoice"]
                or segment["writtenPitch"] != event["writtenPitch"]
                or segment["midi"] != event["midi"]
            ):
                raise ValueError(f"Source-segment provenance mismatch in {event['id']}")
            if segment["sourceCueFlag"]:
                if segment["performanceDisposition"] != "performed-shared-unison":
                    raise ValueError(f"Cue disposition mismatch in {event['id']}")
            elif segment["performanceDisposition"] != "performed":
                raise ValueError(f"Performance disposition mismatch in {event['id']}")
        if (
            _coordinate_fraction(segments[0]["start"])
            != _coordinate_fraction(event["start"])
            or _coordinate_fraction(segments[-1]["end"])
            != _coordinate_fraction(event["end"])
        ):
            raise ValueError(f"Segment extent mismatch in {event['id']}")
        if len(segments) > 1:
            for left, right in zip(segments, segments[1:]):
                if left["writtenPitch"] != right["writtenPitch"]:
                    raise ValueError(f"Pitch-changing tie in {event['id']}")
                if _coordinate_fraction(left["end"]) != _coordinate_fraction(
                    right["start"]
                ):
                    raise ValueError(f"Non-contiguous tie in {event['id']}")
                if not left["tieStart"] or not right["tieStop"]:
                    raise ValueError(f"Tie markup mismatch in {event['id']}")

    groups = payload["groups"]
    if [group["key"] for group in groups] != expected_lane_keys:
        raise ValueError("Six-group stage order changed")
    for group, spec in zip(groups, GROUP_SPECS):
        expected_source_voices = [
            {"voice": spec.voice, "laneRole": "primary-voice-proxy"}
        ]
        if spec.key == "soprano_l1":
            expected_source_voices.append(
                {
                    "voice": "3",
                    "laneRole": "supplemental-divisi-same-lane",
                }
            )
        expected_aggregation = {
            "mode": "binary-logical-or",
            "onWhen": "one-or-more-performed-note-events-are-sounding",
            "simultaneousMultiplicity": "does-not-change-output-level",
            "duplicateSpanHandling": "deduplicate-for-lane-state-only",
            "provenanceHandling": "preserve-every-source-notehead",
            "touchingEvents": "continuous-on-without-intermediate-off",
            "outputStates": ["off", "on"],
        }
        if (
            group["key"] != spec.key
            or group["label"] != spec.label
            or group["family"] != spec.family
            or group["sourcePartId"] != spec.part_id
            or group["primarySourceVoice"] != spec.voice
            or group["sourceVoices"] != expected_source_voices
            or group["mappingConfidence"] != "verified-logical-voice-proxy"
            or group["stateAggregation"] != expected_aggregation
        ):
            raise ValueError(f"Six-group mapping changed at {spec.key}")
        expected_roles = {
            item["voice"]: item["laneRole"] for item in expected_source_voices
        }
        events = group["noteEvents"]
        intervals = group["activityIntervals"]
        event_by_id = {event["id"]: event for event in events}
        represented_ids: list[str] = []
        if len(event_by_id) != len(events):
            raise ValueError(f"Duplicate note event ID in {group['key']}")
        if not intervals:
            raise ValueError(f"No activity intervals in {group['key']}")
        if _coordinate_fraction(intervals[0]["start"]) != 0:
            raise ValueError(f"{group['key']} activity does not start at score zero")
        if _coordinate_fraction(intervals[-1]["end"]) != score_span:
            raise ValueError(f"{group['key']} activity does not reach score end")
        previous_end = Fraction(0)
        previous_state: str | None = None
        for interval in intervals:
            start = _coordinate_fraction(interval["start"])
            end = _coordinate_fraction(interval["end"])
            validate_duration(interval, interval["id"])
            if interval["state"] not in {"on", "off"}:
                raise ValueError(f"Non-binary activity state in {group['key']}")
            if start != previous_end or end <= start:
                raise ValueError(f"Invalid activity coverage in {group['key']}")
            if previous_state == interval["state"]:
                raise ValueError(f"Unmerged activity states in {group['key']}")
            if interval["state"] == "off" and interval["noteEventIds"]:
                raise ValueError(f"Off interval has note events in {group['key']}")
            if interval["state"] == "on" and not interval["noteEventIds"]:
                raise ValueError(f"On interval lacks note events in {group['key']}")
            for event_id in interval["noteEventIds"]:
                if event_id not in event_by_id:
                    raise ValueError(f"Unknown note event {event_id}")
                event = event_by_id[event_id]
                event_start = _coordinate_fraction(event["start"])
                event_end = _coordinate_fraction(event["end"])
                if not (start <= event_start < event_end <= end):
                    raise ValueError(f"Event {event_id} falls outside its on interval")
                represented_ids.append(event_id)
            previous_end = end
            previous_state = interval["state"]
        if set(event_by_id) != set(represented_ids) or len(represented_ids) != len(
            event_by_id
        ):
            raise ValueError(f"Unrepresented note events in {group['key']}")

        expected_on_ranges: list[tuple[Fraction, Fraction]] = []
        for event in sorted(
            events,
            key=lambda item: (
                _coordinate_fraction(item["start"]),
                _coordinate_fraction(item["end"]),
                item["id"],
            ),
        ):
            event_start = _coordinate_fraction(event["start"])
            event_end = _coordinate_fraction(event["end"])
            if not expected_on_ranges or event_start > expected_on_ranges[-1][1]:
                expected_on_ranges.append((event_start, event_end))
            else:
                left, right = expected_on_ranges[-1]
                expected_on_ranges[-1] = (left, max(right, event_end))
        observed_on_ranges = [
            (
                _coordinate_fraction(interval["start"]),
                _coordinate_fraction(interval["end"]),
            )
            for interval in intervals
            if interval["state"] == "on"
        ]
        if observed_on_ranges != expected_on_ranges:
            raise ValueError(f"Activity union differs from note events in {group['key']}")

        for event in events:
            validate_event(event, spec.part_id, expected_roles, group["key"])

        summary = group["summary"]
        primary_segments = sum(
            event["sourceSegmentCount"]
            for event in events
            if event["laneRole"] == "primary-voice-proxy"
        )
        supplemental_segments = sum(
            event["sourceSegmentCount"]
            for event in events
            if event["laneRole"] == "supplemental-divisi-same-lane"
        )
        expected_summary_values = {
            "performedSourcePitchedNoteheadCount": primary_segments
            + supplemental_segments,
            "primarySourcePitchedNoteheadCount": primary_segments,
            "supplementalSourcePitchedNoteheadCount": supplemental_segments,
            "chordMemberCount": sum(
                segment["chordMember"]
                for event in events
                for segment in event["sourceSegments"]
            ),
            "soundingEventCount": len(events),
            "laneStateDistinctSpanCount": len(
                {
                    (
                        _coordinate_fraction(event["start"]),
                        _coordinate_fraction(event["end"]),
                    )
                    for event in events
                }
            ),
            "tiedSoundingEventCount": sum(
                event["sourceSegmentCount"] > 1 for event in events
            ),
            "onIntervalCount": sum(
                interval["state"] == "on" for interval in intervals
            ),
            "offIntervalCount": sum(
                interval["state"] == "off" for interval in intervals
            ),
            "soundingQuarter": _fraction_string(
                sum(
                    (
                        _coordinate_fraction(interval["end"])
                        - _coordinate_fraction(interval["start"])
                        for interval in intervals
                        if interval["state"] == "on"
                    ),
                    Fraction(0),
                )
            ),
        }
        if any(summary[key] != value for key, value in expected_summary_values.items()):
            raise ValueError(f"Group summary mismatch in {group['key']}")

    group_by_key = {group["key"]: group for group in groups}
    if len(payload["supplementalSourceVoices"]) != len(SUPPLEMENTAL_VOICE_SPECS):
        raise ValueError("Supplemental source-voice inventory changed")
    for supplemental, expected in zip(
        payload["supplementalSourceVoices"], SUPPLEMENTAL_VOICE_SPECS
    ):
        if any(supplemental[key] != value for key, value in expected.items()):
            raise ValueError("Supplemental source-voice mapping changed")
        coverage_group = group_by_key[supplemental["assignedGroupKey"]]
        supplemental_events = [
            event
            for event in coverage_group["noteEvents"]
            if event["laneRole"] == supplemental["laneRole"]
        ]
        supplemental_source_ids = [
            segment["sourceId"]
            for event in supplemental_events
            for segment in event["sourceSegments"]
        ]
        if (
            supplemental["allSpansExactlyConcurrent"] is not True
            or supplemental["sourceIds"] != supplemental_source_ids
            or supplemental["noteEventIds"]
            != [event["id"] for event in supplemental_events]
            or supplemental["sourcePitchedNoteheadCount"] != len(supplemental_source_ids)
            or supplemental["soundingEventCount"] != len(supplemental_events)
            or supplemental["exactPrimaryRawSpanMatchCount"]
            != len(supplemental_source_ids)
            or supplemental["exactPrimaryEventSpanMatchCount"]
            != len(supplemental_events)
        ):
            raise ValueError("Supplemental divisi inventory mismatch")
        for source_id, primary_ids in supplemental["matchingPrimarySourceIds"].items():
            source = source_segments[source_id]
            if not primary_ids:
                raise ValueError("Supplemental source span lacks primary match")
            for primary_id in primary_ids:
                primary = source_segments[primary_id]
                if (
                    primary["sourceVoice"] != coverage_group["primarySourceVoice"]
                    or _coordinate_fraction(primary["start"])
                    != _coordinate_fraction(source["start"])
                    or _coordinate_fraction(primary["end"])
                    != _coordinate_fraction(source["end"])
                ):
                    raise ValueError("Supplemental raw span match changed")
        event_by_id = {
            event["id"]: event for event in coverage_group["noteEvents"]
        }
        for event_id, primary_ids in supplemental[
            "matchingPrimaryNoteEventIds"
        ].items():
            event = event_by_id[event_id]
            if not primary_ids:
                raise ValueError("Supplemental event span lacks primary match")
            for primary_id in primary_ids:
                primary = event_by_id[primary_id]
                if (
                    primary["laneRole"] != "primary-voice-proxy"
                    or _coordinate_fraction(primary["start"])
                    != _coordinate_fraction(event["start"])
                    or _coordinate_fraction(primary["end"])
                    != _coordinate_fraction(event["end"])
                ):
                    raise ValueError("Supplemental event span match changed")

    if payload["excludedSourceNotes"]:
        raise ValueError("V36 performed source noteheads may not be silently excluded")
    if payload["unresolvedSourceWarnings"]:
        raise ValueError("V36 source policy still has unresolved warnings")

    cue_resolutions = payload["cueFlagResolutions"]
    cue_source_ids = {
        source_id
        for source_id, segment in source_segments.items()
        if segment["sourceCueFlag"]
    }
    if (
        len(cue_resolutions) != len(CUE_RESOLUTION_SPECS)
        or {item["sourceId"] for item in cue_resolutions} != cue_source_ids
    ):
        raise ValueError("Cue-flag resolution inventory changed")
    for resolution in cue_resolutions:
        source = source_segments[resolution["sourceId"]]
        primary = source_segments[resolution["matchedPrimarySourceId"]]
        location = source_locations[resolution["sourceId"]]
        if (
            resolution["disposition"] != "performed-shared-unison"
            or resolution["performanceDisposition"] != "performed-shared-unison"
            or resolution["sourceCueFlag"] is not True
            or resolution["exactStartEndPitchMatch"] is not True
            or resolution["assignedGroupKey"] != location[0]
            or resolution["noteEventId"] != location[1]
            or primary["sourcePartId"] != source["sourcePartId"]
            or primary["sourceVoice"] != resolution["matchedPrimaryVoice"]
            or primary["sourceCueFlag"] is not False
            or primary["writtenPitch"] != source["writtenPitch"]
            or _coordinate_fraction(primary["start"])
            != _coordinate_fraction(source["start"])
            or _coordinate_fraction(primary["end"])
            != _coordinate_fraction(source["end"])
        ):
            raise ValueError(f"Cue-flag evidence mismatch: {resolution['sourceId']}")

    expected_tie_specs = {
        (
            item["partId"],
            item["measure"],
            item["voice"],
            item["writtenPitch"],
            item["nextMeasure"],
            item["nextWrittenPitch"],
        )
        for item in TIE_RESOLUTION_SPECS
    }
    observed_tie_specs: set[tuple[Any, ...]] = set()
    if len(payload["tieResolutions"]) != len(TIE_RESOLUTION_SPECS):
        raise ValueError("Tie-resolution inventory changed")
    for resolution in payload["tieResolutions"]:
        source = source_segments[resolution["sourceId"]]
        next_source = source_segments[resolution["nextSourceId"]]
        boundary = _coordinate_fraction(resolution["encodedEnd"])
        group_key, source_event_id = source_locations[resolution["sourceId"]]
        next_group_key, next_event_id = source_locations[resolution["nextSourceId"]]
        observed_tie_specs.add(
            (
                source["sourcePartId"],
                source["sourceMeasure"],
                source["sourceVoice"],
                source["writtenPitch"],
                next_source["sourceMeasure"],
                next_source["writtenPitch"],
            )
        )
        on_ranges = [
            (
                _coordinate_fraction(interval["start"]),
                _coordinate_fraction(interval["end"]),
            )
            for interval in group_by_key[group_key]["activityIntervals"]
            if interval["state"] == "on"
        ]
        if (
            resolution["kind"]
            != "capped-at-encoded-end-different-pitch-continuation"
            or resolution["gapQuarter"] != "0"
            or resolution["partId"] != source["sourcePartId"]
            or resolution["voice"] != source["sourceVoice"]
            or resolution["writtenPitch"] != source["writtenPitch"]
            or resolution["nextWrittenPitch"] != next_source["writtenPitch"]
            or _coordinate_fraction(resolution["at"])
            != _coordinate_fraction(source["start"])
            or _fraction_from_string(resolution["encodedDurationQuarter"])
            != boundary - _coordinate_fraction(resolution["at"])
            or source["tieStart"] is not True
            or source["writtenPitch"] == next_source["writtenPitch"]
            or _coordinate_fraction(source["end"]) != boundary
            or _coordinate_fraction(next_source["start"]) != boundary
            or _coordinate_fraction(resolution["nextStart"]) != boundary
            or resolution["assignedGroupKey"] != group_key
            or next_group_key != group_key
            or resolution["sourceNoteEventId"] != source_event_id
            or resolution["nextNoteEventId"] != next_event_id
            or not any(left < boundary < right for left, right in on_ranges)
        ):
            raise ValueError(f"Tie-resolution evidence mismatch: {resolution['sourceId']}")
    if observed_tie_specs != expected_tie_specs:
        raise ValueError("Tie-resolution score contexts changed")

    performed_inventory = sum(
        item["performedPitchedNoteheadCount"] for item in payload["partInventory"]
    )
    if performed_inventory != len(seen_source_ids):
        raise ValueError("Performed Light Chorus notehead inventory is incomplete")


def _write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score", type=Path, default=DEFAULT_SCORE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate and compare with the checked-in artifact without writing.",
    )
    args = parser.parse_args(argv)

    payload = build_artifact(args.score)
    if args.check:
        if not args.output.exists():
            print(f"Missing artifact: {args.output}", file=sys.stderr)
            return 1
        existing = json.loads(args.output.read_text(encoding="utf-8"))
        validate_artifact(existing)
        if existing != payload:
            print(f"Artifact is stale: {args.output}", file=sys.stderr)
            return 1
        print(
            "V36 Light Chorus note activity is current: "
            f"{len(payload['groups'])} groups, "
            f"{sum(len(group['noteEvents']) for group in payload['groups'])} lane-assigned events"
        )
        return 0

    _write_payload(args.output, payload)
    print(
        f"Wrote {args.output}: {len(payload['groups'])} groups, "
        f"{sum(len(group['noteEvents']) for group in payload['groups'])} lane-assigned events, "
        f"{len(payload['cueFlagResolutions'])} cue flags resolved, "
        f"{len(payload['tieResolutions'])} unmatched tie starts resolved"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
