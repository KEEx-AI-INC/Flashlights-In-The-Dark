#!/usr/bin/env python3
"""Render the validated Fall 2026 lyric-correction JSON as a reviewable log."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = (
    REPO_ROOT
    / "Engraving/Scores/Fall2026-Provenance/"
    "FlashlightsInTheDark_Fall2026_TextCorrectionReport.json"
)
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "Documentation/Project-Management/FALL_2026_LYRIC_CORRECTIONS.md"
)


def _escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _lyric_state(lyric: dict[str, Any]) -> str:
    text = lyric.get("text")
    bits = [f"text={text!r}" if text is not None else "text=<none>"]
    for key in ("syllabic", "extend", "number", "placement"):
        value = lyric.get(key)
        if value is not None:
            bits.append(f"{key}={value}")
    return ", ".join(bits)


def _state(correction: dict[str, Any], side: str) -> str:
    value = correction[side]
    if isinstance(value, list):
        rendered = []
        for anchor in value:
            location = (
                f"m{anchor['measure']} n{anchor['note_index']} "
                f"v{anchor['voice']} l{anchor['lyric_number']}"
            )
            rendered.append(f"{location}: {_lyric_state(anchor['lyric'])}")
        return "; ".join(rendered)
    location = (
        f"m{correction['measure']} n{correction['note_index']} "
        f"v{correction['voice']} l{correction['lyric_number']}"
    )
    return f"{location}: {_lyric_state(value)}"


def build(source: Path, output: Path) -> None:
    report = json.loads(source.read_text(encoding="utf-8"))
    corrections = report["corrections"]
    if report["correction_count"] != len(corrections):
        raise ValueError("Correction count does not match the correction list")

    categories = Counter(item["category"] for item in corrections)
    lines = [
        "# Fall 2026 Lyric Correction Inventory",
        "",
        "This is the human-readable companion to the validated machine report",
        f"`{source.relative_to(REPO_ROOT)}`. It enumerates all lyric-semantic",
        "normalizations made before the Dorico import. The later direction and",
        "duplicate-object corrections remain in",
        "`Documentation/Project-Management/FALL_2026_ENGRAVING_CORRECTIONS.md`.",
        "",
        "## Provenance and scope",
        "",
        f"- Source MusicXML SHA-256: `{report['source_sha256']}`",
        f"- Corrected MusicXML SHA-256: `{report['output_sha256']}`",
        f"- Enumerated lyric corrections: **{len(corrections)}**",
        "- Musical semantics and all lyric-anchor locations were preserved, as",
        "  recorded by the validation block in the machine report.",
        "- Authority: the validated Fall 2026 import and approved editorial",
        "  normalization pass. The absent canonical Assembly source remains a",
        "  provenance limitation; ambiguous wording was preserved for review.",
        "",
        "Category totals:",
        "",
    ]
    for category, count in sorted(categories.items()):
        lines.append(f"- {category.replace('_', ' ')}: {count}")

    lines.extend(
        [
            "",
            "## Complete correction ledger",
            "",
            "| Measure | Part | Category | Before | After | Rationale |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for correction in corrections:
        row = [
            correction["measure"],
            correction["part"],
            correction["category"].replace("_", " "),
            _state(correction, "before"),
            _state(correction, "after"),
            correction["reason"],
        ]
        lines.append("| " + " | ".join(_escape(item) for item in row) + " |")

    lines.extend(
        [
            "",
            "## Preserved ambiguities and review items",
            "",
        ]
    )
    for item in report.get("ambiguity_flags", []):
        lines.append(
            f"- {item['part']} m.{item['measure']}: `{item['preserved']}` — "
            f"{item['note']}"
        )
    for item in report.get("preserved_review_items", []):
        if "part" in item:
            lines.append(
                f"- {item['part']} m.{item['measure']}: `{item.get('text', '')}` — "
                f"{item['reason']}"
            )
        else:
            lines.append(f"- {item['scope']}: {item['reason']}")

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.source.resolve(), args.output.resolve())
    print(args.output.resolve())


if __name__ == "__main__":
    main()
