#!/usr/bin/env python3
"""Prepare a layout-clean MusicXML import for the Fall 2026 Dorico edition.

The validated lyric/music source remains authoritative.  This preparation
removes Finale-specific casting and absolute positioning, establishes a
performer-readable Letter-page scale, restores unambiguous ensemble names, and
repairs only demonstrable prose-direction defects.  Notes, rhythms, measures,
lyrics, dynamics, and cue timing are otherwise left untouched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


DOCTYPE = (
    '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
    '"http://www.musicxml.org/dtds/partwise.dtd">'
)

POSITION_ATTRIBUTES = {
    "default-x",
    "default-y",
    "relative-x",
    "relative-y",
    "letter-spacing",
    "line-height",
    "rotation",
}

FONT_ATTRIBUTES = {"font-family", "font-size"}

PART_NAMES = {
    "P1": ("Soprano S", "Sop. S"),
    "P2": ("Alto S", "Alto S"),
    "P3": ("Baritone S", "Bar. S"),
    "P4": ("Soprano L1/L2", "Sop. L1/L2"),
    "P5": ("Alto L1/L2", "Alto L1/L2"),
    "P6": ("Tenor/Bass L", "Ten./Bass L"),
}

PROSE_REPLACEMENTS = {
    "cacouphonous": "cacophonous",
    "musique concréte": "musique concrète",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def child(parent: ET.Element, tag: str) -> ET.Element:
    node = parent.find(tag)
    if node is None:
        node = ET.SubElement(parent, tag)
    return node


def set_text(parent: ET.Element, tag: str, value: str) -> ET.Element:
    node = child(parent, tag)
    node.text = value
    return node


def configure_defaults(root: ET.Element) -> None:
    defaults = child(root, "defaults")
    scaling = child(defaults, "scaling")
    set_text(scaling, "millimeters", "6.0")
    set_text(scaling, "tenths", "40")

    # Letter portrait at 6 mm per 40 tenths.
    page_layout = child(defaults, "page-layout")
    set_text(page_layout, "page-height", "1862.667")
    set_text(page_layout, "page-width", "1439.333")
    for margins in list(page_layout.findall("page-margins")):
        page_layout.remove(margins)

    # Mirrored margins: 19 mm inner, 14 mm outer, 15 mm top/bottom.
    odd = ET.SubElement(page_layout, "page-margins", {"type": "odd"})
    set_text(odd, "left-margin", "126.667")
    set_text(odd, "right-margin", "93.333")
    set_text(odd, "top-margin", "100")
    set_text(odd, "bottom-margin", "100")
    even = ET.SubElement(page_layout, "page-margins", {"type": "even"})
    set_text(even, "left-margin", "93.333")
    set_text(even, "right-margin", "126.667")
    set_text(even, "top-margin", "100")
    set_text(even, "bottom-margin", "100")

    for tag in ("system-layout", "staff-layout", "appearance", "music-font"):
        for node in list(defaults.findall(tag)):
            defaults.remove(node)

    word_font = child(defaults, "word-font")
    word_font.attrib.clear()
    word_font.set("font-family", "Academico")
    word_font.set("font-size", "10")
    lyric_font = child(defaults, "lyric-font")
    lyric_font.attrib.clear()
    lyric_font.set("font-family", "Academico")
    lyric_font.set("font-size", "10.5")


def configure_work_title(root: ET.Element) -> None:
    """Give Dorico an explicit project-level title on MusicXML import.

    Dorico otherwise derives the project title from the import filename and
    treats ``movement-title`` only as the flow title.  Keeping both titles
    explicit prevents an internal working filename from becoming page-one
    furniture.
    """

    work = root.find("work")
    if work is None:
        work = ET.Element("work")
        insertion_index = 0
        if root.find("movement-number") is not None:
            insertion_index = list(root).index(root.find("movement-number"))
        elif root.find("movement-title") is not None:
            insertion_index = list(root).index(root.find("movement-title"))
        root.insert(insertion_index, work)
    set_text(work, "work-title", "Flashlights in the Dark")


def configure_credits(root: ET.Element) -> int:
    removed = 0
    retained: list[ET.Element] = []
    for credit in list(root.findall("credit")):
        if credit.get("page") == "1":
            retained.append(credit)
        else:
            root.remove(credit)
            removed += 1

    specs = {
        "Set in 2076": ("719.667", "1810", "11", "center", "top"),
        "Flashlights in the Dark": ("719.667", "1735", "26", "center", "top"),
        "Commissioned by the Philharmonic Chorus of Madison": (
            "719.667",
            "1645",
            "10.5",
            "center",
            "top",
        ),
        "Jon D. Nelson": ("1300", "1575", "11", "right", "top"),
        "© 2025": ("719.667", "55", "9", "center", "bottom"),
    }
    for credit in retained:
        words = credit.find("credit-words")
        if words is None or (words.text or "") not in specs:
            continue
        x, y, size, justify, valign = specs[words.text or ""]
        words.attrib.clear()
        words.set("default-x", x)
        words.set("default-y", y)
        words.set("font-family", "Academico")
        words.set("font-size", size)
        words.set("justify", justify)
        words.set("valign", valign)
    return removed


def configure_parts(root: ET.Element) -> tuple[int, int]:
    renamed = 0
    groups = 0
    part_list = root.find("part-list")
    if part_list is None:
        return renamed, groups

    active_group = 0
    for item in part_list:
        if item.tag == "part-group" and item.get("type") == "start":
            active_group += 1
            item.set("number", str(active_group))
            group_name = item.findtext("group-name", "")
            if active_group == 1 and group_name != "Shadow Chorus":
                set_text(item, "group-name", "Shadow Chorus")
            if active_group == 2 and group_name != "Light Chorus":
                set_text(item, "group-name", "Light Chorus")
            groups += 1
        elif item.tag == "part-group" and item.get("type") == "stop":
            item.set("number", str(active_group))
        elif item.tag == "score-part":
            part_id = item.get("id", "")
            if part_id not in PART_NAMES:
                continue
            full, short = PART_NAMES[part_id]
            set_text(item, "part-name", full)
            set_text(item, "part-abbreviation", short)
            for instrument in item.findall("score-instrument"):
                set_text(instrument, "instrument-name", full)
            renamed += 1
    return renamed, groups


def remove_legacy_layout(root: ET.Element) -> dict[str, int]:
    counters = {
        "print_elements_removed": 0,
        "position_attributes_removed": 0,
        "font_attributes_removed": 0,
        "measure_widths_removed": 0,
        "staff_line_changes": 0,
    }

    # Every imported print element encodes Finale page/system geometry.  Remove
    # them so Dorico can cast from rhythmic and lyric density.
    for measure in root.findall("./part/measure"):
        if "width" in measure.attrib:
            del measure.attrib["width"]
            counters["measure_widths_removed"] += 1
        for print_node in list(measure.findall("print")):
            measure.remove(print_node)
            counters["print_elements_removed"] += 1

    for element in root.iter():
        if element.tag != "credit-words":
            for attribute in POSITION_ATTRIBUTES:
                if attribute in element.attrib:
                    del element.attrib[attribute]
                    counters["position_attributes_removed"] += 1
            for attribute in FONT_ATTRIBUTES:
                if attribute in element.attrib:
                    del element.attrib[attribute]
                    counters["font_attributes_removed"] += 1
        if element.tag == "staff-lines" and element.text != "5":
            element.text = "5"
            counters["staff_line_changes"] += 1

    return counters


def repair_directions(root: ET.Element) -> list[dict[str, str]]:
    corrections: list[dict[str, str]] = []
    for part in root.findall("part"):
        part_id = part.get("id", "")
        for measure in part.findall("measure"):
            measure_number = measure.get("number", "")
            for direction_type in measure.findall("./direction/direction-type"):
                words_nodes = direction_type.findall("words")
                texts = [(node.text or "") for node in words_nodes]
                joined = "".join(texts)
                if joined == "rearticulate freely in aleatoric style":
                    first = words_nodes[0]
                    before = " + ".join(repr(text) for text in texts)
                    first.text = "rearticulate freely in aleatoric style"
                    first.set("font-style", "italic")
                    for extra in words_nodes[1:]:
                        direction_type.remove(extra)
                    corrections.append(
                        {
                            "measure": measure_number,
                            "part": part_id,
                            "before": before,
                            "after": first.text,
                            "reason": "Rejoined a word split across adjacent MusicXML words objects.",
                        }
                    )

            for words in measure.findall("./direction/direction-type/words"):
                before = words.text or ""
                after = before
                for wrong, right in PROSE_REPLACEMENTS.items():
                    after = after.replace(wrong, right)
                if after != before:
                    words.text = after
                    corrections.append(
                        {
                            "measure": measure_number,
                            "part": part_id,
                            "before": before,
                            "after": after,
                            "reason": "Corrected a demonstrable orthographic error in a prose direction.",
                        }
                    )
    return corrections


def write_musicxml(tree: ET.ElementTree, output: Path) -> None:
    ET.indent(tree, space="  ")
    body = ET.tostring(tree.getroot(), encoding="unicode", short_empty_elements=True)
    output.write_text(f"<?xml version='1.0' encoding='utf-8'?>\n{DOCTYPE}\n{body}\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    tree = ET.parse(args.source)
    root = tree.getroot()
    source_hash = sha256(args.source)

    configure_defaults(root)
    configure_work_title(root)
    repeated_credits_removed = configure_credits(root)
    players_renamed, groups_normalized = configure_parts(root)
    layout_counts = remove_legacy_layout(root)
    corrections = repair_directions(root)

    encoding = root.find("./identification/encoding")
    if encoding is not None:
        for support in list(encoding.findall("supports")):
            if support.get("attribute") in {"new-page", "new-system"}:
                encoding.remove(support)
        software = ET.SubElement(encoding, "software")
        software.text = "Flashlights Fall 2026 Dorico import preparation"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_musicxml(tree, args.output)
    report = {
        "source": str(args.source),
        "output": str(args.output),
        "source_sha256": source_hash,
        "output_sha256": sha256(args.output),
        "repeated_page_credits_removed": repeated_credits_removed,
        "players_renamed": players_renamed,
        "groups_normalized": groups_normalized,
        **layout_counts,
        "semantic_direction_corrections": corrections,
    }
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
