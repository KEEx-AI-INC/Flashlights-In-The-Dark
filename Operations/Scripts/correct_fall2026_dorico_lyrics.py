#!/usr/bin/env python3
"""Apply logged lyric corrections to the clean Fall 2026 Dorico MusicXML.

This is deliberately a second, independent transformation after
``prepare_fall2026_dorico_import.py``.  It repairs only demonstrable lyric
spelling, syllabic-state, and lane-routing defects.  It does not change notes,
rhythms, measures, cue timing, the extra ``though`` at measure 20, or uncertain
phrase punctuation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = (
    ROOT / "Engraving/Scores/FlashlightsInTheDark_Fall2026_DoricoClean.musicxml"
)
DEFAULT_OUTPUT = (
    ROOT
    / "Engraving/Scores/FlashlightsInTheDark_Fall2026_DoricoTextCorrected.musicxml"
)
DEFAULT_REPORT = (
    ROOT
    / "Engraving/Scores/Fall2026-Provenance/FlashlightsInTheDark_Fall2026_TextCorrectionReport.json"
)

DOCTYPE = (
    '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
    '"http://www.musicxml.org/dtds/partwise.dtd">'
)

EXPECTED_PARTS = ("P1", "P2", "P3", "P4", "P5", "P6")
EXPECTED_MEASURES_PER_PART = 151
EXPECTED_LYRIC_ANCHORS = 1376
LITERAL_ALEATORIC_DIRECTION = "rearticulate freely in aleatoric style"


@dataclass(frozen=True)
class LyricRef:
    part: str
    measure: str
    note_index: int
    lyric_index: int
    voice: str
    lyric: ET.Element

    def location(self) -> dict[str, Any]:
        return {
            "part": self.part,
            "measure": self.measure,
            "note_index": self.note_index,
            "lyric_index": self.lyric_index,
            "voice": self.voice,
            "lyric_number": self.lyric.get("number", "1"),
        }


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


def iter_lyric_refs(root: ET.Element) -> Iterable[LyricRef]:
    for part in root.findall("part"):
        part_id = part.get("id", "")
        for measure in part.findall("measure"):
            measure_number = measure.get("number", "")
            for note_index, note in enumerate(measure.findall("note"), start=1):
                voice = note.findtext("voice", default="")
                for lyric_index, lyric in enumerate(note.findall("lyric"), start=1):
                    yield LyricRef(
                        part=part_id,
                        measure=measure_number,
                        note_index=note_index,
                        lyric_index=lyric_index,
                        voice=voice,
                        lyric=lyric,
                    )


def lyric_snapshot(lyric: ET.Element) -> dict[str, Any]:
    extend = lyric.find("extend")
    return {
        "number": lyric.get("number", "1"),
        "placement": lyric.get("placement"),
        "syllabic": lyric.findtext("syllabic"),
        "text": lyric.findtext("text"),
        "extend": None if extend is None else extend.get("type"),
    }


def select_lyrics(
    root: ET.Element,
    *,
    part: str,
    measure: str,
    text: str | None = None,
    voice: str | None = None,
    number: str | None = None,
) -> list[LyricRef]:
    matches: list[LyricRef] = []
    for ref in iter_lyric_refs(root):
        if ref.part != part or ref.measure != str(measure):
            continue
        if text is not None and ref.lyric.findtext("text") != text:
            continue
        if voice is not None and ref.voice != str(voice):
            continue
        if number is not None and ref.lyric.get("number", "1") != str(number):
            continue
        matches.append(ref)
    return matches


def require_lyrics(
    root: ET.Element,
    *,
    count: int = 1,
    **selector: str,
) -> list[LyricRef]:
    matches = select_lyrics(root, **selector)
    if len(matches) != count:
        raise ValueError(
            f"Expected {count} lyric match(es) for {selector}, found {len(matches)}"
        )
    return matches


def set_syllabic(lyric: ET.Element, value: str | None) -> None:
    node = lyric.find("syllabic")
    if value is None:
        if node is not None:
            lyric.remove(node)
        return
    if node is None:
        node = ET.Element("syllabic")
        lyric.insert(0, node)
    node.text = value


def set_lyric_text(lyric: ET.Element, value: str | None) -> None:
    node = lyric.find("text")
    if value is None:
        if node is not None:
            lyric.remove(node)
        return
    if node is None:
        node = ET.Element("text")
        syllabic = lyric.find("syllabic")
        insertion_index = 1 if syllabic is not None else 0
        lyric.insert(insertion_index, node)
    node.text = value


def set_extend(lyric: ET.Element, value: str | None) -> None:
    node = lyric.find("extend")
    if value is None:
        if node is not None:
            lyric.remove(node)
        return
    if node is None:
        node = ET.SubElement(lyric, "extend")
    node.set("type", value)


def record_mutation(
    corrections: list[dict[str, Any]],
    ref: LyricRef,
    *,
    category: str,
    reason: str,
    mutate: Callable[[ET.Element], None],
) -> None:
    before = lyric_snapshot(ref.lyric)
    mutate(ref.lyric)
    after = lyric_snapshot(ref.lyric)
    if before == after:
        raise ValueError(f"No-op correction at {ref.location()}: {reason}")
    corrections.append(
        {
            **ref.location(),
            "category": category,
            "before": before,
            "after": after,
            "reason": reason,
        }
    )


def repair_love_melismas(
    root: ET.Element, corrections: list[dict[str, Any]]
) -> None:
    for part in ("P1", "P2", "P3"):
        first = require_lyrics(root, part=part, measure="18", text="lo")[0]
        last = require_lyrics(root, part=part, measure="19", text="ove")[0]
        stop_candidates = [
            ref
            for ref in select_lyrics(root, part=part, measure="18")
            if ref.lyric.findtext("text") is None
            and ref.lyric.find("extend") is not None
            and ref.lyric.find("extend").get("type") == "stop"
        ]
        if len(stop_candidates) != 1:
            raise ValueError(
                f"Expected one intervening love extender in {part} m18; "
                f"found {len(stop_candidates)}"
            )
        middle = stop_candidates[0]
        before = [
            {**ref.location(), "lyric": lyric_snapshot(ref.lyric)}
            for ref in (first, middle, last)
        ]

        set_lyric_text(first.lyric, "love")
        set_syllabic(first.lyric, "single")
        set_extend(first.lyric, "start")
        set_extend(middle.lyric, "continue")
        set_lyric_text(last.lyric, None)
        set_syllabic(last.lyric, None)
        set_extend(last.lyric, "stop")

        after = [
            {**ref.location(), "lyric": lyric_snapshot(ref.lyric)}
            for ref in (first, middle, last)
        ]
        corrections.append(
            {
                "part": part,
                "measure": "18-19",
                "category": "lyric_word_and_melisma",
                "before": before,
                "after": after,
                "reason": (
                    "Re-encoded the one-syllable word 'love' as one text anchor "
                    "with a continuous extender, without removing lyric anchors."
                ),
            }
        )


def repair_definite_spelling(
    root: ET.Element, corrections: list[dict[str, Any]]
) -> None:
    for part, measure in (
        ("P3", "51"),
        ("P4", "50"),
        ("P5", "50"),
        ("P6", "50"),
    ):
        ref = require_lyrics(root, part=part, measure=measure, text="ceed")[0]
        record_mutation(
            corrections,
            ref,
            category="lyric_spelling",
            reason="Corrected 'preceeding' to 'preceding' while retaining its note anchor.",
            mutate=lambda lyric: set_lyric_text(lyric, "ced"),
        )

    for part, count in (("P4", 2), ("P5", 1), ("P6", 1)):
        for ref in require_lyrics(
            root, part=part, measure="99", text="wear", count=count
        ):
            record_mutation(
                corrections,
                ref,
                category="lyric_spelling",
                reason="Corrected the exported 'wear-ry' spelling to 'wea-ry'.",
                mutate=lambda lyric: set_lyric_text(lyric, "wea"),
            )

    first = require_lyrics(root, part="P6", measure="103", text="(yours")[0]
    record_mutation(
        corrections,
        first,
        category="canonical_case_and_punctuation",
        reason="Matched the unambiguous captured Fall cue '(Yours too.)'.",
        mutate=lambda lyric: set_lyric_text(lyric, "(Yours"),
    )
    last = require_lyrics(root, part="P6", measure="103", text="too)", voice="1")[0]
    record_mutation(
        corrections,
        last,
        category="canonical_case_and_punctuation",
        reason="Matched the unambiguous captured Fall cue '(Yours too.)'.",
        mutate=lambda lyric: set_lyric_text(lyric, "too.)"),
    )

    for part in ("P4", "P5", "P6"):
        for measure in ("140", "141", "142", "144", "148", "149"):
            ref = require_lyrics(root, part=part, measure=measure, text="hmm")[0]
            record_mutation(
                corrections,
                ref,
                category="canonical_case_and_punctuation",
                reason="Matched the separately timed captured Fall cue 'Hmm.'.",
                mutate=lambda lyric: set_lyric_text(lyric, "Hmm."),
            )


def repair_definite_syllabification(
    root: ET.Element, corrections: list[dict[str, Any]]
) -> None:
    pairs = [
        *((part, "61", "shad", "ows", None) for part in ("P1", "P2", "P3", "P5", "P6")),
        ("P2", "67", "flash", "lights", None),
    ]
    for part, measure, first_text, last_text, voice in pairs:
        first = require_lyrics(
            root, part=part, measure=measure, text=first_text, **({"voice": voice} if voice else {})
        )[0]
        last = require_lyrics(
            root, part=part, measure=measure, text=last_text, **({"voice": voice} if voice else {})
        )[0]
        record_mutation(
            corrections,
            first,
            category="lyric_syllabification",
            reason=f"Marked the first syllable of '{first_text}{last_text}' consistently.",
            mutate=lambda lyric: set_syllabic(lyric, "begin"),
        )
        record_mutation(
            corrections,
            last,
            category="lyric_syllabification",
            reason=f"Marked the final syllable of '{first_text}{last_text}' consistently.",
            mutate=lambda lyric: set_syllabic(lyric, "end"),
        )

    dark = require_lyrics(root, part="P2", measure="68", text="dark")[0]
    ness = require_lyrics(root, part="P2", measure="69", text="ness")[0]
    record_mutation(
        corrections,
        dark,
        category="lyric_syllabification",
        reason="Marked 'dark-ness' as a two-syllable word.",
        mutate=lambda lyric: set_syllabic(lyric, "begin"),
    )
    record_mutation(
        corrections,
        ness,
        category="lyric_syllabification",
        reason="Marked 'dark-ness' as a two-syllable word.",
        mutate=lambda lyric: set_syllabic(lyric, "end"),
    )

    shin = require_lyrics(root, part="P5", measure="38", text="Shin", voice="2")[0]
    ing = require_lyrics(root, part="P5", measure="38", text="ing", voice="2")[0]
    record_mutation(
        corrections,
        shin,
        category="lyric_syllabification",
        reason="Marked voice 2 'Shin-ing' consistently.",
        mutate=lambda lyric: set_syllabic(lyric, "begin"),
    )
    record_mutation(
        corrections,
        ing,
        category="lyric_syllabification",
        reason="Marked voice 2 'Shin-ing' consistently.",
        mutate=lambda lyric: set_syllabic(lyric, "end"),
    )


def repair_lane_state(
    root: ET.Element, corrections: list[dict[str, Any]]
) -> None:
    # P4's lower flurries line begins in lyric line 1 and immediately jumps to
    # line 2.  Keep the complete lower line in the stable extra lane (line 2).
    flur = require_lyrics(
        root, part="P4", measure="54", text="flur", voice="2", number="1"
    )[0]
    record_mutation(
        corrections,
        flur,
        category="lyric_lane_and_state",
        reason="Moved the complete lower 'flur-ries' phrase into lyric line 2.",
        mutate=lambda lyric: (lyric.set("number", "2"), set_syllabic(lyric, "begin")),
    )
    ries = require_lyrics(
        root, part="P4", measure="54", text="ries", voice="2", number="2"
    )[0]
    record_mutation(
        corrections,
        ries,
        category="lyric_lane_and_state",
        reason="Closed the lower 'flur-ries' word in lyric line 2.",
        mutate=lambda lyric: set_syllabic(lyric, "end"),
    )

    # Keep P4's lower warmth phrase in the same extra lane selected at m98.
    for measure, text in (("100", "I'll"), ("102", "yours")):
        ref = require_lyrics(
            root, part="P4", measure=measure, text=text, voice="2", number="1"
        )[0]
        record_mutation(
            corrections,
            ref,
            category="lyric_lane_and_state",
            reason="Kept the lower warmth phrase in stable lyric line 2.",
            mutate=lambda lyric: lyric.set("number", "2"),
        )

    state_repairs = [
        ("P4", "100", "I'll", "2", "2", "single"),
        ("P4", "101", "ry", "1", "1", "end"),
        ("P5", "99", "wea", "2", "1", "begin"),
        ("P5", "99", "ry", "2", "1", "end"),
        ("P5", "100", "ry", "1", "1", "end"),
        ("P5", "100", "I'll", "2", "1", "single"),
        ("P5", "101", "ry", "1", "1", "end"),
        ("P6", "100", "I'll", "2", "1", "single"),
        ("P6", "101", "ry", "1", "1", "end"),
    ]
    for part, measure, text, voice, number, target in state_repairs:
        ref = require_lyrics(
            root,
            part=part,
            measure=measure,
            text=text,
            voice=voice,
            number=number,
        )[0]
        record_mutation(
            corrections,
            ref,
            category="lyric_lane_and_state",
            reason="Repaired an impossible begin/middle/end state within its stable voice lane.",
            mutate=lambda lyric, target=target: set_syllabic(lyric, target),
        )


def route_lyrics(root: ET.Element) -> dict[str, Any]:
    changed = 0
    by_part_voice: dict[str, dict[str, dict[str, int]]] = {}
    extra_lane_anchors = 0
    for ref in iter_lyric_refs(root):
        placement = "above" if ref.voice == "1" else "below"
        old = ref.lyric.get("placement")
        if old != placement:
            ref.lyric.set("placement", placement)
            changed += 1
        part_bucket = by_part_voice.setdefault(ref.part, {})
        voice_bucket = part_bucket.setdefault(
            ref.voice,
            {"anchors": 0, "above": 0, "below": 0},
        )
        voice_bucket["anchors"] += 1
        voice_bucket[placement] += 1
        if ref.voice != "1" and ref.lyric.get("number", "1") == "2":
            extra_lane_anchors += 1
    return {
        "placement_attributes_changed": changed,
        "rule": {
            "voice_1": "above",
            "voice_2_and_later": "below",
            "extra_lower_lane": "retain lyric number 2",
        },
        "extra_lower_lane_anchors": extra_lane_anchors,
        "by_part_and_voice": by_part_voice,
    }


def preserve_and_flag_aleatoric_wording(root: ET.Element) -> list[dict[str, Any]]:
    flags: list[dict[str, Any]] = []
    for part in root.findall("part"):
        part_id = part.get("id", "")
        for measure in part.findall("measure"):
            for direction_type in measure.findall("./direction/direction-type"):
                words_nodes = direction_type.findall("words")
                texts = [node.text or "" for node in words_nodes]
                joined = "".join(texts)
                if joined == LITERAL_ALEATORIC_DIRECTION:
                    if len(words_nodes) > 1:
                        words_nodes[0].text = LITERAL_ALEATORIC_DIRECTION
                        for extra in words_nodes[1:]:
                            direction_type.remove(extra)
                    flags.append(
                        {
                            "part": part_id,
                            "measure": measure.get("number", ""),
                            "preserved": LITERAL_ALEATORIC_DIRECTION,
                            "status": "editorial_ambiguity_flagged",
                            "note": (
                                "Preserved the literal rea + rticulate concatenation; "
                                "did not substitute 'articulate'."
                            ),
                        }
                    )
                elif any("articulate freely in aleatoric style" in text for text in texts):
                    raise ValueError(
                        f"Unexpected aleatoric wording in {part_id} m{measure.get('number')}: {texts}"
                    )
    if len(flags) != 5:
        raise ValueError(f"Expected five aleatoric ambiguity flags, found {len(flags)}")
    return flags


def semantic_payload(element: ET.Element) -> Any:
    if element.tag == "lyric":
        return None
    children = []
    for child in element:
        payload = semantic_payload(child)
        if payload is not None:
            children.append(payload)
    text = (element.text or "").strip()
    return [element.tag, sorted(element.attrib.items()), text, children]


def musical_semantic_fingerprint(root: ET.Element) -> str:
    return hash_json(semantic_payload(root))


def lyric_anchor_payload(root: ET.Element) -> list[list[Any]]:
    return [
        [ref.part, ref.measure, ref.note_index, ref.lyric_index, ref.voice]
        for ref in iter_lyric_refs(root)
    ]


def score_shape(root: ET.Element) -> dict[str, Any]:
    parts = root.findall("part")
    measure_counts = {
        part.get("id", ""): len(part.findall("measure")) for part in parts
    }
    return {
        "part_ids": [part.get("id", "") for part in parts],
        "measure_counts": measure_counts,
        "note_count": len(root.findall("./part/measure/note")),
        "lyric_anchor_count": len(list(iter_lyric_refs(root))),
        "lyric_text_count": sum(
            1 for ref in iter_lyric_refs(root) if ref.lyric.find("text") is not None
        ),
    }


def assert_expected_input(shape: dict[str, Any]) -> None:
    if tuple(shape["part_ids"]) != EXPECTED_PARTS:
        raise ValueError(f"Unexpected parts: {shape['part_ids']}")
    if set(shape["measure_counts"].values()) != {EXPECTED_MEASURES_PER_PART}:
        raise ValueError(f"Unexpected measure counts: {shape['measure_counts']}")
    if shape["lyric_anchor_count"] != EXPECTED_LYRIC_ANCHORS:
        raise ValueError(
            f"Expected {EXPECTED_LYRIC_ANCHORS} lyric anchors; "
            f"found {shape['lyric_anchor_count']}"
        )


def syllabic_state_issues(root: ET.Element) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    open_words: dict[tuple[str, str, str], dict[str, Any]] = {}
    for ref in iter_lyric_refs(root):
        text = ref.lyric.findtext("text")
        syllabic = ref.lyric.findtext("syllabic")
        if not text or not syllabic:
            continue
        key = (ref.part, ref.voice, ref.lyric.get("number", "1"))
        opened = open_words.get(key)
        issue = None
        if syllabic == "begin":
            if opened is not None:
                issue = "begin_while_word_open"
            open_words[key] = {**ref.location(), "text": text}
        elif syllabic == "middle":
            if opened is None:
                issue = "middle_without_begin"
        elif syllabic == "end":
            if opened is None:
                issue = "end_without_begin"
            open_words.pop(key, None)
        elif syllabic == "single" and opened is not None:
            issue = "single_before_end"
            open_words.pop(key, None)
        if issue:
            issues.append({**ref.location(), "text": text, "issue": issue})
    return issues


def write_musicxml(tree: ET.ElementTree, output: Path) -> None:
    ET.indent(tree, space="  ")
    body = ET.tostring(tree.getroot(), encoding="unicode", short_empty_elements=True)
    output.write_text(
        f"<?xml version='1.0' encoding='utf-8'?>\n{DOCTYPE}\n{body}\n",
        encoding="utf-8",
    )


def transform(source: Path, output: Path, report_path: Path) -> dict[str, Any]:
    tree = ET.parse(source)
    root = tree.getroot()
    before_shape = score_shape(root)
    assert_expected_input(before_shape)
    before_anchor_payload = lyric_anchor_payload(root)
    before_anchor_hash = hash_json(before_anchor_payload)
    before_semantic_hash = musical_semantic_fingerprint(root)

    corrections: list[dict[str, Any]] = []
    repair_love_melismas(root, corrections)
    repair_definite_spelling(root, corrections)
    repair_definite_syllabification(root, corrections)
    repair_lane_state(root, corrections)
    routing = route_lyrics(root)
    ambiguity_flags = preserve_and_flag_aleatoric_wording(root)

    preserved_through = require_lyrics(
        root, part="P1", measure="20", text="though", count=1
    )[0]
    preserved_items = [
        {
            **preserved_through.location(),
            "text": "though",
            "status": "preserved_for_editorial_review",
            "reason": "Explicitly excluded from this definite-correction pass.",
        },
        {
            "status": "preserved_for_editorial_review",
            "scope": "uncertain phrase punctuation",
            "reason": "No punctuation beyond the captured '(Yours too.)' and 'Hmm.' cues was changed.",
        },
    ]

    after_shape = score_shape(root)
    after_anchor_payload = lyric_anchor_payload(root)
    after_semantic_hash = musical_semantic_fingerprint(root)
    if after_shape["lyric_anchor_count"] != EXPECTED_LYRIC_ANCHORS:
        raise ValueError("Lyric anchor count changed during correction")
    if before_anchor_payload != after_anchor_payload:
        raise ValueError("Lyric anchor locations changed during correction")
    if before_semantic_hash != after_semantic_hash:
        raise ValueError("Non-lyric score semantics changed during correction")

    output.parent.mkdir(parents=True, exist_ok=True)
    write_musicxml(tree, output)
    roundtrip_root = ET.parse(output).getroot()
    roundtrip_shape = score_shape(roundtrip_root)
    roundtrip_anchor_hash = hash_json(lyric_anchor_payload(roundtrip_root))
    roundtrip_semantic_hash = musical_semantic_fingerprint(roundtrip_root)

    placement_errors = [
        ref.location()
        for ref in iter_lyric_refs(roundtrip_root)
        if ref.lyric.get("placement")
        != ("above" if ref.voice == "1" else "below")
    ]
    remaining_states = syllabic_state_issues(roundtrip_root)
    expected_cross_voice_handoffs = [
        {
            "part": "P5",
            "measure": "11",
            "word": "A-rise!",
            "from_voice": "1",
            "to_voice": "2",
        },
        {
            "part": "P6",
            "measure": "43",
            "word": "au-tumn",
            "from_voice": "1",
            "to_voice": "2",
        },
    ]

    validation = {
        "passed": (
            roundtrip_shape["lyric_anchor_count"] == EXPECTED_LYRIC_ANCHORS
            and roundtrip_anchor_hash == before_anchor_hash
            and roundtrip_semantic_hash == before_semantic_hash
            and not placement_errors
        ),
        "source_shape": before_shape,
        "output_shape": roundtrip_shape,
        "lyric_anchor_hash_before": before_anchor_hash,
        "lyric_anchor_hash_after": roundtrip_anchor_hash,
        "lyric_anchor_locations_match": roundtrip_anchor_hash == before_anchor_hash,
        "musical_semantic_fingerprint_before": before_semantic_hash,
        "musical_semantic_fingerprint_after": roundtrip_semantic_hash,
        "musical_semantics_match": roundtrip_semantic_hash == before_semantic_hash,
        "placement_errors": placement_errors,
        "remaining_per_voice_syllabic_state_issues": remaining_states,
        "cross_voice_handoffs_preserved": expected_cross_voice_handoffs,
    }
    if not validation["passed"]:
        raise ValueError(f"Post-write validation failed: {validation}")

    report = {
        "source": display_path(source),
        "output": display_path(output),
        "source_sha256": sha256(source),
        "output_sha256": sha256(output),
        "correction_count": len(corrections),
        "corrections": corrections,
        "lyric_routing": routing,
        "ambiguity_flags": ambiguity_flags,
        "preserved_review_items": preserved_items,
        "validation": validation,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    report = transform(args.source, args.output, args.report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
