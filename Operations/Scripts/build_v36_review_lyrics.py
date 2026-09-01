#!/usr/bin/env python3
"""Build review-only ASS lyric modules from the canonical V36 MusicXML.

The output places Shadow Chorus lyrics in a lower-left module and Light Chorus
lyrics in a lower-right module.  Timing uses the same score clock and playback
anchor as the V36 note-synchronous light review.  This does not create runtime
cues or alter the authored light activity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterable

from render_v36_light_chorus_review_video import DEFAULT_ACTIVITY_PATH, load_review_timeline


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class LyricSpan:
    part_id: str
    voice: str
    lyric_number: str
    text: str
    start_quarter: Fraction
    end_quarter: Fraction
    source_measure: str


@dataclass(frozen=True)
class DisplayRow:
    module: str
    label: str
    role_sources: tuple[tuple[str, tuple[tuple[str, str], ...]], ...]


ROWS = (
    DisplayRow("shadow", "Soprano", (("", (("P1", "1"),)),)),
    DisplayRow("shadow", "Alto", (("", (("P2", "1"),)),)),
    DisplayRow("shadow", "Baritone", (("", (("P3", "1"), ("P3", "2"))),)),
    DisplayRow("light", "Soprano", (("L1", (("P4", "1"), ("P4", "3"))), ("L2", (("P4", "2"),)))),
    DisplayRow("light", "Alto", (("L1", (("P5", "1"),)), ("L2", (("P5", "2"),)))),
    DisplayRow("light", "Tenor/Bass", (("Ten", (("P6", "1"),)), ("Bass", (("P6", "2"),)))),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def syllable_text(text: str, syllabic: str | None) -> str:
    if syllabic == "begin":
        return f"{text}–"
    if syllabic == "middle":
        return f"–{text}–"
    if syllabic == "end":
        return f"–{text}"
    return text


def extract_lyric_spans(score_path: Path, measures: Iterable[object]) -> list[LyricSpan]:
    root = ET.parse(score_path).getroot()
    measure_grid = tuple(measures)
    spans: list[LyricSpan] = []
    open_extensions: dict[tuple[str, str, str], int] = {}

    for part in root.findall("part"):
        part_id = part.get("id", "")
        xml_measures = part.findall("measure")
        if len(xml_measures) != len(measure_grid):
            raise ValueError(f"{part_id} measure count disagrees with V36 grid")
        divisions: int | None = None
        for xml_measure, measure in zip(xml_measures, measure_grid):
            cursor = 0
            last_onset = 0
            for child in xml_measure:
                if child.tag == "attributes" and child.findtext("divisions"):
                    divisions = int(child.findtext("divisions", "0"))
                    if divisions <= 0:
                        raise ValueError("MusicXML divisions must be positive")
                    continue
                if child.tag == "backup":
                    cursor -= int(child.findtext("duration", "0"))
                    continue
                if child.tag == "forward":
                    cursor += int(child.findtext("duration", "0"))
                    continue
                if child.tag != "note" or child.find("grace") is not None:
                    continue
                if divisions is None:
                    raise ValueError("Timed note precedes MusicXML divisions")
                duration = int(child.findtext("duration", "0"))
                onset = last_onset if child.find("chord") is not None else cursor
                if child.find("chord") is None:
                    last_onset = onset
                    cursor += duration
                if child.find("rest") is not None or duration <= 0:
                    continue
                voice = child.findtext("voice", "1")
                start = measure.start_quarter + Fraction(onset, divisions)
                end = start + Fraction(duration, divisions)
                for lyric in child.findall("lyric"):
                    number = lyric.get("number", "1")
                    key = (part_id, voice, number)
                    raw_text = lyric.findtext("text")
                    extend = lyric.find("extend")
                    extend_type = extend.get("type", "continue") if extend is not None else None
                    if raw_text:
                        if key in open_extensions:
                            open_extensions.pop(key)
                        spans.append(
                            LyricSpan(
                                part_id=part_id,
                                voice=voice,
                                lyric_number=number,
                                text=syllable_text(raw_text, lyric.findtext("syllabic")),
                                start_quarter=start,
                                end_quarter=end,
                                source_measure=xml_measure.get("number", ""),
                            )
                        )
                        if extend_type in {"start", "continue"}:
                            open_extensions[key] = len(spans) - 1
                    elif extend is not None and key in open_extensions:
                        index = open_extensions[key]
                        spans[index].end_quarter = max(spans[index].end_quarter, end)
                        if extend_type == "stop":
                            open_extensions.pop(key)
    if open_extensions:
        unresolved = ", ".join("/".join(key) for key in sorted(open_extensions))
        raise ValueError(f"Unclosed MusicXML lyric extensions: {unresolved}")
    return spans


def active_texts(
    spans: list[LyricSpan], sources: tuple[tuple[str, str], ...], quarter: Fraction
) -> list[str]:
    values: list[str] = []
    for span in spans:
        if (span.part_id, span.voice) not in sources:
            continue
        if span.start_quarter <= quarter < span.end_quarter and span.text not in values:
            values.append(span.text)
    return values


def row_segments(row: DisplayRow, spans: list[LyricSpan]) -> list[tuple[Fraction, Fraction, str]]:
    relevant = [
        span
        for span in spans
        if any((span.part_id, span.voice) in sources for _, sources in row.role_sources)
    ]
    boundaries = sorted({value for span in relevant for value in (span.start_quarter, span.end_quarter)})
    segments: list[tuple[Fraction, Fraction, str]] = []
    for start, end in zip(boundaries, boundaries[1:]):
        if end <= start:
            continue
        midpoint = (start + end) / 2
        role_values: list[tuple[str, str]] = []
        for role, sources in row.role_sources:
            text = " / ".join(active_texts(relevant, sources, midpoint))
            if text:
                role_values.append((role, text))
        if not role_values:
            continue
        if len(row.role_sources) == 1 or (len(role_values) > 1 and len({v for _, v in role_values}) == 1):
            display = role_values[0][1]
        else:
            display = "   ·   ".join(f"{role}: {value}" for role, value in role_values)
        if segments and segments[-1][1] == start and segments[-1][2] == display:
            previous = segments[-1]
            segments[-1] = (previous[0], end, display)
        else:
            segments.append((start, end, display))
    return segments


def ass_time(seconds: Fraction) -> str:
    centiseconds = max(0, round(float(seconds) * 100))
    hours, remainder = divmod(centiseconds, 360000)
    minutes, remainder = divmod(remainder, 6000)
    secs, cs = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"


def ass_escape(text: str) -> str:
    return text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")


def build_ass(timeline: object, spans: list[LyricSpan]) -> tuple[str, dict[str, object]]:
    end = ass_time(timeline.output_duration_seconds)
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ModuleTitle,Helvetica,19,&H00EDE8D9,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: RowLabel,Helvetica,17,&H00AEB7C6,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Lyric,Helvetica,22,&H00FFFFFF,&H00FFFFFF,&H00201A0E,&H00000000,-1,0,0,0,100,100,0,0,1,1.2,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events: list[str] = []
    # Opaque-enough lower-corner panels, drawn beneath all text.
    for x1, x2 in ((42, 627), (653, 1238)):
        shape = f"{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&H17130B&\\1a&H18&}}m {x1} 570 l {x2} 570 l {x2} 708 l {x1} 708"
        events.append(f"Dialogue: 0,0:00:00.00,{end},Lyric,,0,0,0,,{shape}")
    events.extend(
        [
            f"Dialogue: 1,0:00:00.00,{end},ModuleTitle,,0,0,0,,{{\\pos(62,582)}}SHADOW CHORUS",
            f"Dialogue: 1,0:00:00.00,{end},ModuleTitle,,0,0,0,,{{\\pos(673,582)}}LIGHT CHORUS",
        ]
    )
    row_y = {"Soprano": 613, "Alto": 649, "Baritone": 685, "Tenor/Bass": 685}
    segment_count = 0
    for row in ROWS:
        x_label, x_lyric = (62, 174) if row.module == "shadow" else (673, 790)
        y = row_y[row.label]
        events.append(
            f"Dialogue: 1,0:00:00.00,{end},RowLabel,,0,0,0,,{{\\pos({x_label},{y})}}{row.label}"
        )
        for start_q, end_q, text in row_segments(row, spans):
            start = timeline.score_origin_seconds + timeline.score_clock.seconds_from_score_origin(start_q)
            finish = timeline.score_origin_seconds + timeline.score_clock.seconds_from_score_origin(end_q)
            events.append(
                f"Dialogue: 2,{ass_time(start)},{ass_time(finish)},Lyric,,0,0,0,,{{\\pos({x_lyric},{y - 2})}}{ass_escape(text)}"
            )
            segment_count += 1
    metadata = {
        "schemaVersion": "v36-review-lyrics-1",
        "artifactType": "review-only-lyric-overlay-source",
        "runtimeEligible": False,
        "scoreSource": {"path": str(timeline.score_path.relative_to(REPO_ROOT)), "sha256": timeline.score_sha256},
        "activitySource": {"path": str(timeline.activity_path.relative_to(REPO_ROOT)), "sha256": timeline.activity_sha256},
        "scoreOriginSeconds": str(timeline.score_origin_seconds),
        "outputDurationSeconds": str(timeline.output_duration_seconds),
        "sourceLyricSpanCount": len(spans),
        "displaySegmentCount": segment_count,
        "modules": {
            "lowerLeft": {"chorus": "Shadow", "rows": ["Soprano", "Alto", "Baritone"], "sourceParts": ["P1", "P2", "P3"]},
            "lowerRight": {"chorus": "Light", "rows": ["Soprano", "Alto", "Tenor/Bass"], "sourceParts": ["P4", "P5", "P6"], "divisiDisplay": "role-qualified when simultaneous texts differ"}
        },
        "lyricPolicy": {
            "source": "MusicXML lyric elements on performed pitched notes",
            "syllabicMarkers": "en dash marks begin, middle, and end syllables",
            "extensions": "sustain the displayed syllable through MusicXML extend stop",
            "rests": "blank",
            "simultaneousDuplicates": "deduplicated for display only",
            "scoreTextChanged": False
        }
    }
    return header + "\n".join(events) + "\n", metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activity", type=Path, default=DEFAULT_ACTIVITY_PATH)
    parser.add_argument("--score-origin-seconds", type=Fraction, required=True)
    parser.add_argument("--duration-seconds", type=Fraction, required=True)
    parser.add_argument("--ass-output", type=Path, required=True)
    parser.add_argument("--metadata-output", type=Path, required=True)
    args = parser.parse_args()
    timeline = load_review_timeline(
        args.activity,
        score_origin_seconds=args.score_origin_seconds,
        output_duration_seconds=args.duration_seconds,
    )
    spans = extract_lyric_spans(timeline.score_path, timeline.measures)
    ass, metadata = build_ass(timeline, spans)
    args.ass_output.parent.mkdir(parents=True, exist_ok=True)
    args.metadata_output.parent.mkdir(parents=True, exist_ok=True)
    if args.ass_output.exists() or args.metadata_output.exists():
        raise FileExistsError("Refusing to overwrite an existing lyric artifact")
    args.ass_output.write_text(ass, encoding="utf-8")
    metadata["assOutput"] = str(args.ass_output.resolve())
    metadata["assSha256"] = sha256(args.ass_output)
    args.metadata_output.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
