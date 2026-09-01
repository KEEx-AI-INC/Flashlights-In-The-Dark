#!/usr/bin/env python3
"""Build a score-derived WordBuilder cue sheet without changing notation.

The cue sheet preserves every printed lyric syllable and its measure/onset so
EastWest WordBuilder programming can be reviewed against the 12-page cast.
It deliberately leaves phonetic substitutions to the audible Opus pass.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def lyric_token(lyric: ET.Element) -> str:
    text = clean_text("".join(lyric.findtext("text", default="")))
    syllabic = lyric.findtext("syllabic", default="single")
    if not text:
        return ""
    if syllabic in {"begin", "middle"}:
        return f"{text}-"
    if syllabic == "end":
        return f"-{text}"
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--csv", dest="csv_path", type=Path, required=True)
    parser.add_argument("--json", dest="json_path", type=Path, required=True)
    args = parser.parse_args()

    root = ET.parse(args.source).getroot()
    part_names = {
        item.attrib["id"]: clean_text(item.findtext("part-name"))
        for item in root.findall("./part-list/score-part")
    }
    rows: list[dict[str, object]] = []

    for part in root.findall("part"):
        part_id = part.attrib["id"]
        onset = 0
        divisions = 1
        for measure_index, measure in enumerate(part.findall("measure"), start=1):
            measure_onset = onset
            cursor = 0
            for note in measure.findall("note"):
                if note.find("chord") is None:
                    note_onset = cursor
                else:
                    note_onset = max(0, cursor - int(note.findtext("duration", default="0")))
                duration = int(note.findtext("duration", default="0"))
                for lyric in note.findall("lyric"):
                    token = lyric_token(lyric)
                    if not token:
                        continue
                    rows.append(
                        {
                            "part_id": part_id,
                            "staff": part_names.get(part_id, part_id),
                            "measure": measure_index,
                            "onset_divisions": note_onset,
                            "absolute_divisions": measure_onset + note_onset,
                            "line": lyric.attrib.get("number", "1"),
                            "placement": lyric.attrib.get("placement", ""),
                            "syllabic": lyric.findtext("syllabic", default="single"),
                            "engraved_syllable": clean_text(lyric.findtext("text")),
                            "wordbuilder_token": token,
                            "extend": "yes" if lyric.find("extend") is not None else "",
                            "duration_divisions": duration,
                        }
                    )
                if note.find("chord") is None:
                    cursor += duration
            onset += max(cursor, 0)

    args.csv_path.parent.mkdir(parents=True, exist_ok=True)
    with args.csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    per_staff = defaultdict(list)
    for row in rows:
        per_staff[str(row["staff"])].append(row)
    payload = {
        "source": str(args.source),
        "purpose": "Review sheet for manual EastWest WordBuilder entry and audition.",
        "rules": [
            "Enter wordbuilder_token in score order for each staff and lyric line.",
            "Retain hyphenated continuations exactly; an initial hyphen marks a carried syllable.",
            "Use phonetic substitutions only after an Opus audition proves they improve intelligibility.",
        ],
        "staffs": per_staff,
        "summary": {"staff_count": len(per_staff), "lyric_events": len(rows)},
    }
    args.json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} lyric events across {len(per_staff)} staves.")


if __name__ == "__main__":
    main()
