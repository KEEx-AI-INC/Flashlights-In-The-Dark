#!/usr/bin/env python3
"""Render the canonical V36 six-lane note activity as a silent review video.

This is a review renderer, not a runtime manifest generator.  It reads the
topology-independent V36 activity source, derives the score tempo map from the
canonical Finale MusicXML, and places that score clock on an explicitly supplied
playback clock.  No legacy light choreography or physical phone count is used.

The generated H.264 file is intentionally silent so a separately verified mix
can be muxed without this renderer modifying or transcoding the source audio.
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ACTIVITY_PATH = (
    REPO_ROOT
    / "Engraving/Score-Study/FlashlightsInTheDark_v36_LightChorusNoteActivity.json"
)
EXPECTED_SCHEMA = "v36-light-chorus-note-activity-2"
EXPECTED_LANE_KEYS = (
    "soprano_l1",
    "soprano_l2",
    "tenor_l",
    "bass_l",
    "alto_l2",
    "alto_l1",
)


def _fraction(value: object) -> Fraction:
    return Fraction(str(value))


def _fraction_text(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _decimal_text(value: Fraction, places: int = 9) -> str:
    return f"{float(value):.{places}f}"


def _round_fraction_ms(value: Fraction) -> int:
    """Round a nonnegative exact millisecond value to nearest, half up."""

    if value < 0:
        raise ValueError("Playback milliseconds cannot be negative")
    return (value.numerator * 2 + value.denominator) // (2 * value.denominator)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


@dataclass(frozen=True)
class Measure:
    ordinal: int
    token: str
    number: int
    start_quarter: Fraction
    duration_quarter: Fraction
    beats: int
    beat_type: int

    @property
    def end_quarter(self) -> Fraction:
        return self.start_quarter + self.duration_quarter


@dataclass(frozen=True)
class ActivityInterval:
    source_id: str
    state: str
    start_quarter: Fraction
    end_quarter: Fraction
    duration_quarter: Fraction
    start_coordinate: dict[str, Any]
    end_coordinate: dict[str, Any]
    note_event_ids: tuple[str, ...]


@dataclass(frozen=True)
class Lane:
    key: str
    label: str
    intervals: tuple[ActivityInterval, ...]

    def state_at(self, quarter: Fraction) -> bool:
        if quarter < self.intervals[0].start_quarter:
            return False
        starts = [item.start_quarter for item in self.intervals]
        index = bisect.bisect_right(starts, quarter) - 1
        if index < 0:
            return False
        interval = self.intervals[index]
        return interval.state == "on" and quarter < interval.end_quarter


@dataclass(frozen=True)
class TempoEvent:
    start_quarter: Fraction
    quarter_bpm: Fraction


@dataclass(frozen=True)
class ScoreClock:
    events: tuple[TempoEvent, ...]
    score_span_quarter: Fraction

    def __post_init__(self) -> None:
        if not self.events or self.events[0].start_quarter != 0:
            raise ValueError("Tempo map must begin at score quarter 0")
        if any(item.quarter_bpm <= 0 for item in self.events):
            raise ValueError("Tempo values must be positive")
        if any(
            first.start_quarter >= second.start_quarter
            for first, second in zip(self.events, self.events[1:])
        ):
            raise ValueError("Tempo events must have strictly increasing positions")
        if self.events[-1].start_quarter >= self.score_span_quarter:
            raise ValueError("Last tempo event must occur before score end")

    def seconds_from_score_origin(self, quarter: Fraction) -> Fraction:
        if quarter < 0 or quarter > self.score_span_quarter:
            raise ValueError(
                f"Score quarter outside 0..{self.score_span_quarter}: {quarter}"
            )
        elapsed = Fraction(0)
        for index, event in enumerate(self.events):
            next_start = (
                self.events[index + 1].start_quarter
                if index + 1 < len(self.events)
                else self.score_span_quarter
            )
            if quarter <= event.start_quarter:
                break
            covered_end = min(quarter, next_start)
            elapsed += (
                (covered_end - event.start_quarter) * Fraction(60) / event.quarter_bpm
            )
            if quarter <= next_start:
                break
        return elapsed

    def quarter_at_seconds_from_origin(self, elapsed: Fraction) -> Fraction:
        if elapsed <= 0:
            return Fraction(0)
        cursor_seconds = Fraction(0)
        for index, event in enumerate(self.events):
            next_start = (
                self.events[index + 1].start_quarter
                if index + 1 < len(self.events)
                else self.score_span_quarter
            )
            segment_seconds = (
                (next_start - event.start_quarter) * Fraction(60) / event.quarter_bpm
            )
            if elapsed < cursor_seconds + segment_seconds:
                return event.start_quarter + (
                    (elapsed - cursor_seconds) * event.quarter_bpm / Fraction(60)
                )
            if elapsed == cursor_seconds + segment_seconds:
                return next_start
            cursor_seconds += segment_seconds
        return self.score_span_quarter


@dataclass(frozen=True)
class ReviewTimeline:
    activity_path: Path
    activity_sha256: str
    score_path: Path
    score_sha256: str
    measures: tuple[Measure, ...]
    lanes: tuple[Lane, ...]
    stage_order: tuple[str, ...]
    score_clock: ScoreClock
    score_origin_seconds: Fraction
    output_duration_seconds: Fraction
    binding_input: dict[str, str]

    @property
    def score_end_seconds(self) -> Fraction:
        return self.score_origin_seconds + self.score_clock.seconds_from_score_origin(
            self.score_clock.score_span_quarter
        )

    def quarter_at_audio_time(self, elapsed_seconds: Fraction) -> Fraction | None:
        relative = elapsed_seconds - self.score_origin_seconds
        score_duration = self.score_clock.seconds_from_score_origin(
            self.score_clock.score_span_quarter
        )
        if relative < 0 or relative >= score_duration:
            return None
        return self.score_clock.quarter_at_seconds_from_origin(relative)

    def lane_states_at_audio_time(self, elapsed_seconds: Fraction) -> dict[str, bool]:
        quarter = self.quarter_at_audio_time(elapsed_seconds)
        if quarter is None:
            return {lane.key: False for lane in self.lanes}
        return {lane.key: lane.state_at(quarter) for lane in self.lanes}

    def measure_at_quarter(self, quarter: Fraction) -> Measure:
        starts = [measure.start_quarter for measure in self.measures]
        index = bisect.bisect_right(starts, quarter) - 1
        return self.measures[max(0, min(index, len(self.measures) - 1))]


def _load_measures(payload: dict[str, Any]) -> tuple[Measure, ...]:
    measures = tuple(
        Measure(
            ordinal=int(item["ordinal"]),
            token=str(item["token"]),
            number=int(item["measure"]),
            start_quarter=_fraction(item["startQuarter"]),
            duration_quarter=_fraction(item["durationQuarter"]),
            beats=int(item["beats"]),
            beat_type=int(item["beatType"]),
        )
        for item in payload["scoreGrid"]["measures"]
    )
    if not measures or measures[0].start_quarter != 0:
        raise ValueError("Score grid must begin at quarter 0")
    cursor = Fraction(0)
    for expected_ordinal, measure in enumerate(measures, start=1):
        if measure.ordinal != expected_ordinal:
            raise ValueError("Score-grid ordinals are not contiguous")
        if measure.start_quarter != cursor:
            raise ValueError(
                f"Score-grid gap or overlap before measure {measure.token}"
            )
        cursor = measure.end_quarter
    score_span = _fraction(payload["source"]["scoreSpanQuarter"])
    if cursor != score_span:
        raise ValueError(f"Score-grid end {cursor} != source span {score_span}")
    return measures


def _load_lanes(payload: dict[str, Any], score_span: Fraction) -> tuple[Lane, ...]:
    groups = payload.get("groups", [])
    observed_keys = tuple(str(group["key"]) for group in groups)
    if observed_keys != EXPECTED_LANE_KEYS:
        raise ValueError(f"Unexpected V36 lane mapping/order: {observed_keys}")
    lanes: list[Lane] = []
    for group in groups:
        policy = group.get("stateAggregation", {})
        if (
            policy.get("mode") != "binary-logical-or"
            or policy.get("simultaneousMultiplicity") != "does-not-change-output-level"
            or policy.get("outputStates") != ["off", "on"]
        ):
            raise ValueError(f"Lane {group['key']} does not declare exact binary OR")
        intervals = tuple(
            ActivityInterval(
                source_id=str(item["id"]),
                state=str(item["state"]),
                start_quarter=_fraction(item["start"]["cumulativeQuarter"]),
                end_quarter=_fraction(item["end"]["cumulativeQuarter"]),
                duration_quarter=_fraction(item["durationQuarter"]),
                start_coordinate=dict(item["start"]),
                end_coordinate=dict(item["end"]),
                note_event_ids=tuple(
                    str(event_id) for event_id in item["noteEventIds"]
                ),
            )
            for item in group["activityIntervals"]
        )
        if not intervals:
            raise ValueError(f"Lane {group['key']} has no activity intervals")
        cursor = Fraction(0)
        for interval in intervals:
            if interval.state not in {"off", "on"}:
                raise ValueError(f"Lane {group['key']} contains non-binary state")
            if interval.start_quarter != cursor or interval.end_quarter <= cursor:
                raise ValueError(
                    f"Lane {group['key']} has a gap, overlap, or empty interval"
                )
            if (
                interval.end_quarter - interval.start_quarter
                != interval.duration_quarter
            ):
                raise ValueError(
                    f"Lane {group['key']} contains an inconsistent duration"
                )
            if interval.state == "off" and interval.note_event_ids:
                raise ValueError(
                    f"Lane {group['key']} has note-event IDs in an off interval"
                )
            cursor = interval.end_quarter
        if cursor != score_span:
            raise ValueError(f"Lane {group['key']} does not cover the full score")
        lanes.append(
            Lane(
                key=str(group["key"]),
                label=str(group["label"]),
                intervals=intervals,
            )
        )
    return tuple(lanes)


def _tempo_events_from_part(
    part: ET.Element,
    measures: tuple[Measure, ...],
) -> tuple[TempoEvent, ...]:
    xml_measures = part.findall("measure")
    if len(xml_measures) != len(measures):
        raise ValueError(
            f"Tempo-source part {part.attrib.get('id')} has {len(xml_measures)} measures; "
            f"expected {len(measures)}"
        )
    divisions: int | None = None
    events: list[TempoEvent] = []
    for xml_measure, measure in zip(xml_measures, measures):
        cursor_divisions = 0
        last_note_onset = 0
        for child in xml_measure:
            if child.tag == "attributes" and child.findtext("divisions"):
                divisions = int(child.findtext("divisions", "0"))
                if divisions <= 0:
                    raise ValueError("MusicXML divisions must be positive")
                continue
            if child.tag == "backup":
                cursor_divisions -= int(child.findtext("duration", "0"))
                continue
            if child.tag == "forward":
                cursor_divisions += int(child.findtext("duration", "0"))
                continue
            if child.tag == "note":
                if divisions is None:
                    raise ValueError("Timed MusicXML content precedes divisions")
                if child.find("grace") is not None:
                    continue
                duration = int(child.findtext("duration", "0"))
                if child.find("chord") is None:
                    last_note_onset = cursor_divisions
                    cursor_divisions += duration
                else:
                    _ = last_note_onset
                continue
            sounds: list[tuple[ET.Element, int]] = []
            if child.tag == "direction":
                sound = child.find("sound")
                offset = int(child.findtext("offset", "0"))
                if sound is not None:
                    sounds.append((sound, cursor_divisions + offset))
            elif child.tag == "sound":
                sounds.append((child, cursor_divisions))
            for sound, position_divisions in sounds:
                if "tempo" not in sound.attrib:
                    continue
                if divisions is None:
                    raise ValueError("Tempo event precedes MusicXML divisions")
                quarter = measure.start_quarter + Fraction(
                    position_divisions, divisions
                )
                events.append(
                    TempoEvent(
                        start_quarter=quarter,
                        quarter_bpm=_fraction(sound.attrib["tempo"]),
                    )
                )
    return tuple(events)


def _load_tempo_map(
    score_path: Path, measures: tuple[Measure, ...]
) -> tuple[TempoEvent, ...]:
    root = ET.parse(score_path).getroot()
    maps = [
        events
        for part in root.findall("part")
        if (events := _tempo_events_from_part(part, measures))
    ]
    if not maps:
        raise ValueError("Canonical MusicXML contains no playback tempo events")
    authority = maps[0]
    if any(events != authority for events in maps[1:]):
        raise ValueError("MusicXML parts disagree about the tempo map")
    deduplicated: list[TempoEvent] = []
    for event in authority:
        if deduplicated and event.start_quarter == deduplicated[-1].start_quarter:
            if event.quarter_bpm != deduplicated[-1].quarter_bpm:
                raise ValueError("Conflicting tempo values at one score position")
            continue
        deduplicated.append(event)
    return tuple(deduplicated)


def load_review_timeline(
    activity_path: Path = DEFAULT_ACTIVITY_PATH,
    *,
    score_origin_seconds: Fraction | None = None,
    anchor_quarter: Fraction | None = None,
    anchor_seconds: Fraction | None = None,
    output_duration_seconds: Fraction,
) -> ReviewTimeline:
    activity_path = activity_path.resolve()
    payload = json.loads(activity_path.read_text(encoding="utf-8"))
    if payload.get("schemaVersion") != EXPECTED_SCHEMA:
        raise ValueError(
            f"Expected {EXPECTED_SCHEMA}, found {payload.get('schemaVersion')}"
        )
    if payload.get("status") != "authoring-source-not-runtime-ready":
        raise ValueError("V36 activity source is not marked non-runtime")
    if (
        payload.get("validation", {}).get("legacyRuntimeArtifactsUsedAsInputs")
        is not False
    ):
        raise ValueError("V36 source does not exclude legacy runtime choreography")
    if (
        payload.get("validation", {}).get("activityIntervalsExplicitlyCoverScore")
        is not True
    ):
        raise ValueError("V36 source does not assert full-score activity coverage")

    measures = _load_measures(payload)
    score_span = _fraction(payload["source"]["scoreSpanQuarter"])
    lanes = _load_lanes(payload, score_span)
    stage_order = tuple(
        str(item) for item in payload["mappingProvenance"]["stageOrder"]
    )
    if stage_order != EXPECTED_LANE_KEYS:
        raise ValueError(f"Unexpected canonical stage order: {stage_order}")

    source_path_value = Path(payload["source"]["path"])
    score_path = (
        source_path_value
        if source_path_value.is_absolute()
        else REPO_ROOT / source_path_value
    ).resolve()
    score_sha256 = _sha256(score_path)
    if score_sha256 != payload["source"]["sha256"]:
        raise ValueError(
            "Canonical MusicXML checksum does not match activity provenance"
        )
    score_clock = ScoreClock(_load_tempo_map(score_path, measures), score_span)

    direct_binding = score_origin_seconds is not None
    anchor_binding = anchor_quarter is not None or anchor_seconds is not None
    if direct_binding == anchor_binding:
        raise ValueError(
            "Supply exactly one binding: score origin, or anchor quarter + time"
        )
    if direct_binding:
        assert score_origin_seconds is not None
        resolved_origin = score_origin_seconds
        binding_input = {
            "kind": "score-origin",
            "scoreQuarter": "0",
            "audioSeconds": _fraction_text(score_origin_seconds),
        }
    else:
        if anchor_quarter is None or anchor_seconds is None:
            raise ValueError(
                "Anchor binding requires both anchor quarter and anchor seconds"
            )
        if not 0 <= anchor_quarter <= score_span:
            raise ValueError("Anchor quarter lies outside the canonical V36 score")
        resolved_origin = anchor_seconds - score_clock.seconds_from_score_origin(
            anchor_quarter
        )
        binding_input = {
            "kind": "score-coordinate-anchor",
            "scoreQuarter": _fraction_text(anchor_quarter),
            "audioSeconds": _fraction_text(anchor_seconds),
        }
    if resolved_origin < 0:
        raise ValueError("Resolved score origin precedes playback time zero")
    if output_duration_seconds <= 0:
        raise ValueError("Output duration must be positive")

    timeline = ReviewTimeline(
        activity_path=activity_path,
        activity_sha256=_sha256(activity_path),
        score_path=score_path,
        score_sha256=score_sha256,
        measures=measures,
        lanes=lanes,
        stage_order=stage_order,
        score_clock=score_clock,
        score_origin_seconds=resolved_origin,
        output_duration_seconds=output_duration_seconds,
        binding_input=binding_input,
    )
    if timeline.score_end_seconds > output_duration_seconds:
        raise ValueError(
            "Output ends before the tempo-mapped V36 score endpoint: "
            f"{_decimal_text(timeline.score_end_seconds)} > "
            f"{_decimal_text(output_duration_seconds)}"
        )
    return timeline


def _font(
    size: int, *, bold: bool = False
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("/System/Library/Fonts/SFNS.ttf"),
        Path("/System/Library/Fonts/SFNSRounded.ttf"),
        Path("/System/Library/Fonts/Helvetica.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
        if bold
        else Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            return ImageFont.truetype(
                str(candidate),
                size=size,
                index=1 if bold and candidate.suffix == ".ttc" else 0,
            )
        except OSError:
            continue
    return ImageFont.load_default()


def _centered_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
) -> None:
    box = draw.textbbox((0, 0), text, font=font)
    draw.text((xy[0] - (box[2] - box[0]) / 2, xy[1]), text, font=font, fill=fill)


def _timecode(seconds: Fraction) -> str:
    value = max(0.0, float(seconds))
    minutes = int(value // 60)
    remaining = value - minutes * 60
    return f"{minutes:02d}:{remaining:05.2f}"


class StageRenderer:
    """Draw a neutral stage view in which every point mirrors one lane state."""

    def __init__(self, timeline: ReviewTimeline, width: int, height: int) -> None:
        if width < 320 or height < 180 or width % 2 or height % 2:
            raise ValueError("Dimensions must be even and at least 320x180")
        self.timeline = timeline
        self.width = width
        self.height = height
        scale = min(width / 1280.0, height / 720.0)
        self.scale = scale
        self.title_font = _font(max(16, round(28 * scale)), bold=True)
        self.label_font = _font(max(12, round(20 * scale)), bold=True)
        self.detail_font = _font(max(10, round(14 * scale)))
        self.small_font = _font(max(9, round(12 * scale)))
        self.base = self._build_base()

    def _build_base(self) -> Image.Image:
        image = Image.new("RGB", (self.width, self.height), (4, 6, 14))
        draw = ImageDraw.Draw(image)
        for y in range(self.height):
            ratio = y / max(1, self.height - 1)
            color = (
                round(4 + 4 * ratio),
                round(6 + 5 * ratio),
                round(14 + 12 * ratio),
            )
            draw.line((0, y, self.width, y), fill=color)

        margin = round(self.width * 0.055)
        header_y = round(self.height * 0.055)
        draw.text(
            (margin, header_y),
            "FLASHLIGHTS IN THE DARK  ·  V36 LIGHT CHORUS REVIEW",
            font=self.title_font,
            fill=(230, 235, 243),
        )
        draw.line(
            (
                margin,
                round(self.height * 0.14),
                self.width - margin,
                round(self.height * 0.14),
            ),
            fill=(48, 56, 74),
            width=max(1, round(self.scale)),
        )

        # A restrained proscenium and riser arc; these are presentation only.
        arch_box = (
            round(self.width * 0.055),
            round(self.height * 0.17),
            round(self.width * 0.945),
            round(self.height * 1.03),
        )
        draw.arc(
            arch_box, 192, 348, fill=(35, 43, 61), width=max(1, round(2 * self.scale))
        )
        draw.line(
            (
                round(self.width * 0.08),
                round(self.height * 0.79),
                round(self.width * 0.92),
                round(self.height * 0.79),
            ),
            fill=(30, 38, 54),
            width=max(1, round(2 * self.scale)),
        )
        footer = "six logical lanes · binary OR · repeated points mirror one lane state"
        _centered_text(
            draw,
            (self.width // 2, round(self.height * 0.915)),
            footer,
            self.small_font,
            (128, 138, 154),
        )
        return image

    def _group_centers(self) -> dict[str, tuple[int, int]]:
        normalized_x = (0.115, 0.265, 0.415, 0.585, 0.735, 0.885)
        normalized_y = (0.66, 0.52, 0.44, 0.44, 0.52, 0.66)
        return {
            key: (round(self.width * x), round(self.height * y))
            for key, x, y in zip(self.timeline.stage_order, normalized_x, normalized_y)
        }

    def _draw_light_bank(
        self,
        image: Image.Image,
        center: tuple[int, int],
        label: str,
        on: bool,
    ) -> None:
        draw = ImageDraw.Draw(image)
        radius = max(5, round(10 * self.scale))
        spread_x = max(18, round(30 * self.scale))
        spread_y = max(16, round(25 * self.scale))
        point_offsets = (
            (-spread_x, -spread_y),
            (0, -spread_y),
            (spread_x, -spread_y),
            (-round(spread_x * 1.5), spread_y),
            (-round(spread_x * 0.5), spread_y),
            (round(spread_x * 0.5), spread_y),
            (round(spread_x * 1.5), spread_y),
        )
        if on:
            glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow)
            for dx, dy in point_offsets:
                x, y = center[0] + dx, center[1] + dy
                glow_radius = radius * 3
                glow_draw.ellipse(
                    (
                        x - glow_radius,
                        y - glow_radius,
                        x + glow_radius,
                        y + glow_radius,
                    ),
                    fill=(255, 220, 124, 24),
                )
            image.paste(
                Image.alpha_composite(image.convert("RGBA"), glow).convert("RGB")
            )
            draw = ImageDraw.Draw(image)

        for dx, dy in point_offsets:
            x, y = center[0] + dx, center[1] + dy
            if on:
                draw.ellipse(
                    (x - radius, y - radius, x + radius, y + radius),
                    fill=(255, 248, 214),
                    outline=(255, 255, 245),
                    width=max(1, round(2 * self.scale)),
                )
                inner = max(2, radius // 3)
                draw.ellipse(
                    (x - inner, y - inner, x + inner, y + inner),
                    fill=(255, 255, 255),
                )
            else:
                draw.ellipse(
                    (x - radius, y - radius, x + radius, y + radius),
                    fill=(18, 23, 34),
                    outline=(72, 80, 96),
                    width=max(1, round(self.scale)),
                )
        label_y = center[1] + spread_y + radius + round(12 * self.scale)
        _centered_text(
            draw, (center[0], label_y), label, self.label_font, (221, 226, 235)
        )
        _centered_text(
            draw,
            (center[0], label_y + round(27 * self.scale)),
            "ON" if on else "off",
            self.small_font,
            (255, 227, 151) if on else (96, 106, 124),
        )

    def _score_annotation(self, elapsed_seconds: Fraction) -> tuple[str, str]:
        if elapsed_seconds < self.timeline.score_origin_seconds:
            return "V36 lead-in", "score begins at m1 beat 1"
        if elapsed_seconds >= self.timeline.score_end_seconds:
            return "V36 score complete", "playback tail"
        quarter = self.timeline.quarter_at_audio_time(elapsed_seconds)
        assert quarter is not None
        measure = self.timeline.measure_at_quarter(quarter)
        local_quarter = quarter - measure.start_quarter
        beat = Fraction(1) + local_quarter / Fraction(4, measure.beat_type)
        beat_value = float(beat)
        beat_text = (
            str(round(beat_value))
            if abs(beat_value - round(beat_value)) < 0.005
            else f"{beat_value:.2f}"
        )
        return (
            f"V36 · m{measure.token} · beat {beat_text}",
            f"{measure.beats}/{measure.beat_type}",
        )

    def render_frame(self, elapsed_seconds: Fraction) -> Image.Image:
        image = self.base.copy()
        draw = ImageDraw.Draw(image)
        margin = round(self.width * 0.055)
        annotation, meter = self._score_annotation(elapsed_seconds)
        draw.text(
            (margin, round(self.height * 0.16)),
            _timecode(elapsed_seconds),
            font=self.detail_font,
            fill=(185, 194, 208),
        )
        annotation_box = draw.textbbox((0, 0), annotation, font=self.detail_font)
        draw.text(
            (
                self.width - margin - (annotation_box[2] - annotation_box[0]),
                round(self.height * 0.16),
            ),
            annotation,
            font=self.detail_font,
            fill=(185, 194, 208),
        )
        meter_box = draw.textbbox((0, 0), meter, font=self.small_font)
        draw.text(
            (
                self.width - margin - (meter_box[2] - meter_box[0]),
                round(self.height * 0.205),
            ),
            meter,
            font=self.small_font,
            fill=(103, 113, 131),
        )

        states = self.timeline.lane_states_at_audio_time(elapsed_seconds)
        centers = self._group_centers()
        lane_map = {lane.key: lane for lane in self.timeline.lanes}
        for key in self.timeline.stage_order:
            self._draw_light_bank(image, centers[key], lane_map[key].label, states[key])

        progress_left = margin
        progress_right = self.width - margin
        progress_y = round(self.height * 0.875)
        draw.line(
            (progress_left, progress_y, progress_right, progress_y),
            fill=(48, 56, 72),
            width=max(2, round(3 * self.scale)),
        )
        ratio = min(
            1.0,
            max(0.0, float(elapsed_seconds / self.timeline.output_duration_seconds)),
        )
        playhead_x = round(progress_left + (progress_right - progress_left) * ratio)
        draw.line(
            (progress_left, progress_y, playhead_x, progress_y),
            fill=(188, 166, 110),
            width=max(2, round(3 * self.scale)),
        )
        playhead_radius = max(3, round(5 * self.scale))
        draw.ellipse(
            (
                playhead_x - playhead_radius,
                progress_y - playhead_radius,
                playhead_x + playhead_radius,
                progress_y + playhead_radius,
            ),
            fill=(255, 238, 191),
        )
        return image


def _run(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def probe_video(path: Path) -> dict[str, Any]:
    output = _run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=index,codec_type,codec_name,width,height,pix_fmt,r_frame_rate",
            "-of",
            "json",
            str(path),
        ]
    )
    return json.loads(output)


def render_video(
    timeline: ReviewTimeline,
    output_path: Path,
    *,
    width: int = 1280,
    height: int = 720,
    fps: int = 30,
    crf: int = 18,
    preset: str = "medium",
) -> dict[str, Any]:
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing video: {output_path}")
    if fps <= 0 or fps > 120:
        raise ValueError("FPS must be between 1 and 120")
    if not 0 <= crf <= 51:
        raise ValueError("CRF must be between 0 and 51")
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    renderer = StageRenderer(timeline, width, height)
    frame_count = math.ceil(float(timeline.output_duration_seconds) * fps)
    command = [
        ffmpeg,
        "-v",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s:v",
        f"{width}x{height}",
        "-r",
        str(fps),
        "-i",
        "pipe:0",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        preset,
        "-crf",
        str(crf),
        "-pix_fmt",
        "yuv420p",
        "-threads",
        "1",
        "-movflags",
        "+faststart",
        "-frames:v",
        str(frame_count),
        str(output_path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert process.stdin is not None
    try:
        for frame_index in range(frame_count):
            frame_time = Fraction(frame_index, fps)
            process.stdin.write(renderer.render_frame(frame_time).tobytes())
        process.stdin.close()
        return_code = process.wait()
    except BaseException:
        process.kill()
        process.wait()
        raise
    if return_code != 0:
        raise RuntimeError(f"ffmpeg exited with status {return_code}")
    probe = probe_video(output_path)
    streams = probe.get("streams", [])
    video_streams = [item for item in streams if item.get("codec_type") == "video"]
    audio_streams = [item for item in streams if item.get("codec_type") == "audio"]
    if len(video_streams) != 1 or audio_streams:
        raise ValueError("Review render must contain exactly one silent video stream")
    stream = video_streams[0]
    if (
        stream.get("codec_name") != "h264"
        or stream.get("pix_fmt") != "yuv420p"
        or int(stream.get("width", 0)) != width
        or int(stream.get("height", 0)) != height
    ):
        raise ValueError(f"Unexpected encoded stream: {stream}")
    return {
        "path": str(output_path.resolve()),
        "sha256": _sha256(output_path),
        "bytes": output_path.stat().st_size,
        "frameCount": frame_count,
        "probe": probe,
    }


def write_previews(
    renderer: StageRenderer,
    preview_dir: Path,
    times: Iterable[Fraction],
) -> list[dict[str, Any]]:
    preview_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    seen: set[Fraction] = set()
    for index, frame_time in enumerate(times, start=1):
        if frame_time in seen:
            continue
        seen.add(frame_time)
        safe_time = min(
            max(Fraction(0), frame_time),
            renderer.timeline.output_duration_seconds,
        )
        path = (
            preview_dir / f"v36-light-review-{index:02d}-{float(safe_time):010.3f}s.png"
        )
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite preview: {path}")
        renderer.render_frame(safe_time).save(path, format="PNG")
        results.append(
            {
                "path": str(path.resolve()),
                "atSeconds": _fraction_text(safe_time),
                "sha256": _sha256(path),
            }
        )
    return results


def timeline_metadata(timeline: ReviewTimeline) -> dict[str, Any]:
    score_duration = timeline.score_clock.seconds_from_score_origin(
        timeline.score_clock.score_span_quarter
    )
    activity_intervals: list[dict[str, Any]] = []
    for lane in timeline.lanes:
        for interval in lane.intervals:
            playback_start_seconds = (
                timeline.score_origin_seconds
                + timeline.score_clock.seconds_from_score_origin(interval.start_quarter)
            )
            playback_end_seconds = (
                timeline.score_origin_seconds
                + timeline.score_clock.seconds_from_score_origin(interval.end_quarter)
            )
            start_ms = playback_start_seconds * 1000
            end_ms = playback_end_seconds * 1000
            activity_intervals.append(
                {
                    "sourceIntervalId": interval.source_id,
                    "laneKey": lane.key,
                    "laneLabel": lane.label,
                    "state": interval.state,
                    "score": {
                        "start": interval.start_coordinate,
                        "end": interval.end_coordinate,
                        "durationQuarter": _fraction_text(interval.duration_quarter),
                    },
                    "playback": {
                        "startMsExact": _fraction_text(start_ms),
                        "startMsRounded": _round_fraction_ms(start_ms),
                        "endMsExact": _fraction_text(end_ms),
                        "endMsRounded": _round_fraction_ms(end_ms),
                        "durationMsExact": _fraction_text(end_ms - start_ms),
                        "durationMsRounded": _round_fraction_ms(end_ms - start_ms),
                    },
                    "noteEventIds": list(interval.note_event_ids),
                }
            )
    return {
        "schemaVersion": "v36-light-chorus-review-timeline-1",
        "artifactType": "non-runtime-review-visualization-binding",
        "runtimeEligible": False,
        "activitySource": {
            "path": _repo_path(timeline.activity_path),
            "sha256": timeline.activity_sha256,
            "schemaVersion": EXPECTED_SCHEMA,
        },
        "scoreSource": {
            "path": _repo_path(timeline.score_path),
            "sha256": timeline.score_sha256,
            "scoreSpanQuarter": _fraction_text(timeline.score_clock.score_span_quarter),
        },
        "bindingInput": timeline.binding_input,
        "resolvedClock": {
            "authority": "supplied-review-playback-clock",
            "scoreOriginSeconds": _fraction_text(timeline.score_origin_seconds),
            "scoreOriginSecondsDecimal": _decimal_text(timeline.score_origin_seconds),
            "tempoMap": [
                {
                    "startQuarter": _fraction_text(item.start_quarter),
                    "quarterBpm": _fraction_text(item.quarter_bpm),
                }
                for item in timeline.score_clock.events
            ],
            "tempoMappedScoreDurationSeconds": _fraction_text(score_duration),
            "tempoMappedScoreDurationSecondsDecimal": _decimal_text(score_duration),
            "scoreEndSeconds": _fraction_text(timeline.score_end_seconds),
            "scoreEndSecondsDecimal": _decimal_text(timeline.score_end_seconds),
            "outputDurationSeconds": _fraction_text(timeline.output_duration_seconds),
            "outputDurationSecondsDecimal": _decimal_text(
                timeline.output_duration_seconds
            ),
        },
        "visualPolicy": {
            "laneKeys": list(timeline.stage_order),
            "state": "exact-binary-logical-or-from-source-activity-intervals",
            "chordAndDivisiBrightnessStacking": False,
            "replicatedPointsPerLane": 7,
            "replicatedPointsArePresentationOnly": True,
            "legacyChoreographyUsed": False,
            "physicalTopologyEncoded": False,
        },
        "playbackBoundActivity": {
            "status": "non-runtime-review-only",
            "intervalCount": len(activity_intervals),
            "intervals": activity_intervals,
            "outsideScoreAllOff": [
                {
                    "region": "playback-lead-in",
                    "stateForAllLanes": "off",
                    "startMsExact": "0",
                    "startMsRounded": 0,
                    "endMsExact": _fraction_text(timeline.score_origin_seconds * 1000),
                    "endMsRounded": _round_fraction_ms(
                        timeline.score_origin_seconds * 1000
                    ),
                },
                {
                    "region": "playback-tail",
                    "stateForAllLanes": "off",
                    "startMsExact": _fraction_text(timeline.score_end_seconds * 1000),
                    "startMsRounded": _round_fraction_ms(
                        timeline.score_end_seconds * 1000
                    ),
                    "endMsExact": _fraction_text(
                        timeline.output_duration_seconds * 1000
                    ),
                    "endMsRounded": _round_fraction_ms(
                        timeline.output_duration_seconds * 1000
                    ),
                },
            ],
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activity", type=Path, default=DEFAULT_ACTIVITY_PATH)
    binding = parser.add_mutually_exclusive_group(required=True)
    binding.add_argument("--score-origin-seconds", type=_fraction)
    binding.add_argument("--anchor-seconds", type=_fraction)
    parser.add_argument(
        "--anchor-quarter",
        type=_fraction,
        help="Cumulative V36 quarter position paired with --anchor-seconds",
    )
    parser.add_argument("--duration-seconds", type=_fraction, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--metadata-output", type=Path)
    parser.add_argument(
        "--binding-output",
        type=Path,
        help="Write the deterministic non-runtime playback-bound interval JSON",
    )
    parser.add_argument("--preview-dir", type=Path)
    parser.add_argument("--preview-at", action="append", type=_fraction, default=[])
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--crf", type=int, default=18)
    parser.add_argument("--preset", default="medium")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate inputs and print deterministic timeline metadata without rendering",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.anchor_seconds is not None and args.anchor_quarter is None:
        raise SystemExit("--anchor-seconds requires --anchor-quarter")
    if args.anchor_seconds is None and args.anchor_quarter is not None:
        raise SystemExit("--anchor-quarter requires --anchor-seconds")
    timeline = load_review_timeline(
        args.activity,
        score_origin_seconds=args.score_origin_seconds,
        anchor_quarter=args.anchor_quarter,
        anchor_seconds=args.anchor_seconds,
        output_duration_seconds=args.duration_seconds,
    )
    metadata = timeline_metadata(timeline)
    if args.check and (args.output or args.preview_dir or args.metadata_output):
        raise SystemExit(
            "--check does not write video, previews, or video provenance; "
            "use --binding-output for deterministic interval JSON"
        )
    if args.binding_output is not None:
        if args.binding_output.exists():
            raise FileExistsError(
                f"Refusing to overwrite playback binding: {args.binding_output}"
            )
        args.binding_output.parent.mkdir(parents=True, exist_ok=True)
        args.binding_output.write_text(
            json.dumps(metadata, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
    if args.check:
        json.dump(metadata, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if args.output is None:
        raise SystemExit("--output is required unless --check is used")
    if args.metadata_output is not None and args.metadata_output.exists():
        raise FileExistsError(f"Refusing to overwrite metadata: {args.metadata_output}")

    if args.preview_dir is not None:
        preview_times = args.preview_at or [
            Fraction(0),
            timeline.score_origin_seconds,
            timeline.score_origin_seconds + Fraction(4) * Fraction(60, 102),
            timeline.score_origin_seconds
            + timeline.score_clock.seconds_from_score_origin(Fraction(116)),
            (timeline.score_origin_seconds + timeline.score_end_seconds) / 2,
            max(Fraction(0), timeline.score_end_seconds - Fraction(1, 10)),
            max(Fraction(0), timeline.output_duration_seconds - Fraction(1, 10)),
        ]
        renderer = StageRenderer(timeline, args.width, args.height)
        metadata["previews"] = write_previews(renderer, args.preview_dir, preview_times)

    metadata["video"] = render_video(
        timeline,
        args.output,
        width=args.width,
        height=args.height,
        fps=args.fps,
        crf=args.crf,
        preset=args.preset,
    )
    if args.metadata_output is not None:
        args.metadata_output.parent.mkdir(parents=True, exist_ok=True)
        args.metadata_output.write_text(
            json.dumps(metadata, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
