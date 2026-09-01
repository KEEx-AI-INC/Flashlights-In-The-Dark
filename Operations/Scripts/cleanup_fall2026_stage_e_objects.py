#!/usr/bin/env python3
"""Apply the conservative Stage E engraving-object cleanup to MusicXML.

This pass starts from the validated Dorico-normalized Fall 2026 source.  It
removes only confirmed duplicate ensemble directions and redundant first-page
credit objects whose content already has a semantic MusicXML metadata source.
It deliberately leaves chord-symbol spacing to Dorico because MusicXML has no
safe minimum-gap control and the existing ``harmony/offset`` values are timing
anchors, not cosmetic offsets.
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
    normalized_score_fingerprint,
    validate_score_shape,
)
from normalize_fall2026_dorico_engraving import (
    staff_line_payload,
    validate_casting,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = (
    ROOT
    / "Engraving/Scores/Fall2026-Provenance/FlashlightsInTheDark_Fall2026_DoricoNormalized.musicxml"
)
DEFAULT_OUTPUT = (
    ROOT
    / "Engraving/Scores/Fall2026-Provenance/FlashlightsInTheDark_Fall2026_StageEClean.musicxml"
)
DEFAULT_REPORT = (
    ROOT
    / "Engraving/Scores/Fall2026-Provenance/FlashlightsInTheDark_Fall2026_StageECleanupReport.json"
)
NORMALIZATION_REPORT = (
    ROOT
    / "Engraving/Scores/Fall2026-Provenance/FlashlightsInTheDark_Fall2026_DoricoNormalizationReport.json"
)

DOCTYPE = (
    '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
    '"http://www.musicxml.org/dtds/partwise.dtd">'
)

EXPECTED_NOTE_COUNT = 2787
EXPECTED_FALL_REPLACEMENTS = 388
ALEATORIC_TEXT = "rearticulate freely in aleatoric style"

# The repeated passage described editorially as "m126-ish" is located at
# MusicXML measure 130.  P1 is the top staff and therefore retains the single
# printable ensemble direction at both confirmed locations.
ALEATORIC_DUPLICATE_RULES: dict[int, dict[str, tuple[str, ...] | str]] = {
    115: {"retain": "P1", "remove": ("P2",)},
    130: {"retain": "P1", "remove": ("P2", "P3")},
}

REDUNDANT_CREDIT_ROLES = {
    "Flashlights in the Dark": {
        "role": "title",
        "metadata_paths": ("work/work-title", "movement-title"),
    },
    "Jon D. Nelson": {
        "role": "composer",
        "metadata_paths": ("identification/creator[@type='composer']",),
    },
    "© 2025": {
        "role": "copyright",
        "metadata_paths": ("identification/rights",),
    },
}

APPROVED_UNIQUE_CREDITS = {
    "Set in 2076": "subtitle",
    "Commissioned by the Philharmonic Chorus of Madison": "commission",
}

POSITION_ATTRIBUTES = ("default-x", "default-y", "relative-x", "relative-y")


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


def semantic_element(element: ET.Element) -> dict[str, Any]:
    """Return a whitespace-insensitive, attribute-exact element payload."""
    text = element.text
    if text is not None and not text.strip():
        text = None
    return {
        "tag": element.tag,
        "attributes": dict(sorted(element.attrib.items())),
        "text": text,
        "children": [semantic_element(child) for child in element],
    }


def element_signature(element: ET.Element) -> str:
    return hash_json(semantic_element(element))


def verify_provenance_chain(source: Path) -> dict[str, Any]:
    report = load_json(NORMALIZATION_REPORT)
    source_hash = sha256(source)
    validation = report.get("validation", {})
    provenance = report.get("provenance", {})
    if report.get("output_sha256") != source_hash:
        raise ValueError("Source does not match the Dorico normalization report")
    if not validation.get("passed"):
        raise ValueError("Dorico normalization report is not validated")
    if validation.get("note_count") != EXPECTED_NOTE_COUNT:
        raise ValueError("Normalization report does not record 2,787 notes")
    if validation.get("lyric_anchor_count") != EXPECTED_LYRIC_ANCHORS:
        raise ValueError("Normalization report does not record 1,376 lyric anchors")
    if provenance.get("fall_replacements") != EXPECTED_FALL_REPLACEMENTS:
        raise ValueError("Normalization provenance does not record 388 replacements")
    if not provenance.get("reports_chain"):
        raise ValueError("Normalization provenance chain is not complete")
    return {
        "normalized_source_sha256": source_hash,
        "normalization_report_sha256": sha256(NORMALIZATION_REPORT),
        "fall_replacements": EXPECTED_FALL_REPLACEMENTS,
        "reports_chain": True,
    }


def part_name_map(root: ET.Element) -> dict[str, str]:
    return {
        part.get("id", ""): part.findtext("part-name", "")
        for part in root.findall("./part-list/score-part")
    }


def find_measure(root: ET.Element, part_id: str, measure_number: int) -> ET.Element:
    part = root.find(f"./part[@id='{part_id}']")
    if part is None:
        raise ValueError(f"Missing part {part_id}")
    measure = part.find(f"./measure[@number='{measure_number}']")
    if measure is None:
        raise ValueError(f"Missing {part_id} measure {measure_number}")
    return measure


def words_texts(direction: ET.Element) -> tuple[str, ...]:
    return tuple(
        "".join(words.itertext())
        for words in direction.findall("./direction-type/words")
    )


def is_pure_words_direction(direction: ET.Element, text: str) -> bool:
    direction_types = direction.findall("direction-type")
    if len(direction_types) != 1:
        return False
    direction_type = direction_types[0]
    children = list(direction_type)
    if len(children) != 1 or children[0].tag != "words":
        return False
    if "".join(children[0].itertext()) != text:
        return False
    return all(child.tag in {"direction-type", "offset", "staff"} for child in direction)


def find_word_directions(
    root: ET.Element, part_id: str, measure_number: int, text: str
) -> list[tuple[int, ET.Element]]:
    measure = find_measure(root, part_id, measure_number)
    return [
        (index, direction)
        for index, direction in enumerate(measure.findall("direction"), start=1)
        if words_texts(direction) == (text,)
    ]


def consolidate_aleatoric_directions(root: ET.Element) -> list[dict[str, Any]]:
    parts = [part.get("id", "") for part in root.findall("part")]
    if not parts or parts[0] != "P1":
        raise ValueError("P1 must be the top staff before consolidating directions")
    names = part_name_map(root)
    removals: list[dict[str, Any]] = []

    for measure_number, rule in ALEATORIC_DUPLICATE_RULES.items():
        retained_part = str(rule["retain"])
        removed_parts = tuple(rule["remove"])
        expected_parts = {retained_part, *removed_parts}
        actual_parts = {
            part_id
            for part_id in parts
            if find_word_directions(root, part_id, measure_number, ALEATORIC_TEXT)
        }
        if actual_parts != expected_parts:
            raise ValueError(
                f"Unexpected {ALEATORIC_TEXT!r} distribution at measure "
                f"{measure_number}: {sorted(actual_parts)}"
            )

        retained = find_word_directions(
            root, retained_part, measure_number, ALEATORIC_TEXT
        )
        if len(retained) != 1:
            raise ValueError(
                f"Expected one retained direction in {retained_part} m{measure_number}"
            )
        retained_index, retained_direction = retained[0]
        if not is_pure_words_direction(retained_direction, ALEATORIC_TEXT):
            raise ValueError("Retained aleatoric direction contains other semantics")
        if retained_direction.get("placement") != "above":
            raise ValueError("Retained aleatoric direction is not above the top staff")
        retained_signature = element_signature(retained_direction)

        for removed_part in removed_parts:
            matches = find_word_directions(
                root, removed_part, measure_number, ALEATORIC_TEXT
            )
            if len(matches) != 1:
                raise ValueError(
                    f"Expected one duplicate in {removed_part} m{measure_number}"
                )
            direction_index, direction = matches[0]
            if not is_pure_words_direction(direction, ALEATORIC_TEXT):
                raise ValueError(
                    f"Duplicate in {removed_part} m{measure_number} has other semantics"
                )
            signature = element_signature(direction)
            if signature != retained_signature:
                raise ValueError(
                    f"Duplicate in {removed_part} m{measure_number} is not exact"
                )
            if direction.find(".//sound") is not None:
                raise ValueError("Refusing to remove a direction that carries playback data")

            measure = find_measure(root, removed_part, measure_number)
            measure.remove(direction)
            removals.append(
                {
                    "text": ALEATORIC_TEXT,
                    "part": removed_part,
                    "part_name": names.get(removed_part, ""),
                    "measure": measure_number,
                    "direction_index_before_removal": direction_index,
                    "placement": direction.get("placement"),
                    "offset": direction.findtext("offset"),
                    "semantic_signature": signature,
                    "retained_part": retained_part,
                    "retained_part_name": names.get(retained_part, ""),
                    "retained_direction_index": retained_index,
                    "reason": (
                        "Exact duplicate of the ensemble-wide instruction; retained "
                        "once above the top staff."
                    ),
                }
            )

    return removals


def duplicate_word_clusters(root: ET.Element) -> list[dict[str, Any]]:
    clusters: dict[tuple[str, tuple[str, ...]], list[dict[str, Any]]] = defaultdict(list)
    names = part_name_map(root)
    for part in root.findall("part"):
        part_id = part.get("id", "")
        for measure in part.findall("measure"):
            for index, direction in enumerate(measure.findall("direction"), start=1):
                texts = words_texts(direction)
                if not texts:
                    continue
                clusters[(measure.get("number", ""), texts)].append(
                    {
                        "part": part_id,
                        "part_name": names.get(part_id, ""),
                        "direction_index": index,
                    }
                )

    result: list[dict[str, Any]] = []
    for (measure, texts), occurrences in sorted(
        clusters.items(), key=lambda item: (int(item[0][0]), item[0][1])
    ):
        if len({item["part"] for item in occurrences}) < 2:
            continue
        text = " | ".join(texts)
        normalized_texts = tuple(text.strip() for text in texts)
        if measure == "112" and normalized_texts == ("subito",):
            reason = (
                "Preserved on every staff: this is a performer-level dynamic-state "
                "instruction, not safely reducible to a system object."
            )
        elif measure == "7" and normalized_texts == ("listen for primer tone",):
            reason = (
                "Preserved on each Light staff as a performer-specific entrance cue."
            )
        else:
            reason = (
                "Preserved because the fragment is not unambiguously an "
                "ensemble-wide semantic direction."
            )
        result.append(
            {
                "measure": int(measure),
                "texts": list(texts),
                "display_text": text,
                "occurrences": occurrences,
                "action": "preserved",
                "reason": reason,
            }
        )
    return result


def metadata_credit_sources(root: ET.Element) -> dict[str, set[str]]:
    return {
        "title": {
            value
            for value in (
                root.findtext("./work/work-title"),
                root.findtext("movement-title"),
            )
            if value is not None
        },
        "composer": {
            creator.text or ""
            for creator in root.findall("./identification/creator")
            if creator.get("type") == "composer"
        },
        "copyright": {
            rights.text or "" for rights in root.findall("./identification/rights")
        },
    }


def credit_text(credit: ET.Element) -> str:
    return "\n".join(
        "".join(words.itertext()) for words in credit.findall("credit-words")
    )


def remove_redundant_page1_credits(
    root: ET.Element,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sources = metadata_credit_sources(root)
    removals: list[dict[str, Any]] = []
    retained: list[dict[str, Any]] = []
    credits = list(root.findall("credit"))
    for index, credit in enumerate(credits, start=1):
        text = credit_text(credit)
        page = credit.get("page")
        redundant = REDUNDANT_CREDIT_ROLES.get(text) if page == "1" else None
        if redundant is not None:
            role = str(redundant["role"])
            if text not in sources[role]:
                raise ValueError(
                    f"Credit {text!r} lacks its expected semantic metadata source"
                )
            root.remove(credit)
            removals.append(
                {
                    "page": 1,
                    "credit_index_before_removal": index,
                    "text": text,
                    "role": role,
                    "metadata_paths_retained": list(redundant["metadata_paths"]),
                    "semantic_signature": element_signature(credit),
                    "reason": (
                        "Removed redundant page-one credit furniture; Dorico can "
                        "populate this field from the retained semantic metadata."
                    ),
                }
            )
            continue

        role = APPROVED_UNIQUE_CREDITS.get(text)
        retained.append(
            {
                "page": int(page) if page and page.isdigit() else page,
                "text": text,
                "role": role or "unclassified",
                "metadata_path": "credit[@page='1']/credit-words",
                "semantic_signature": element_signature(credit),
                "reason": (
                    "Retained as the approved MusicXML path for unique subtitle or "
                    "commission metadata not duplicated by standard title fields."
                    if role
                    else "Retained because it is unique and not safely classifiable."
                ),
            }
        )

    remaining_page1 = {
        credit_text(credit)
        for credit in root.findall("credit")
        if credit.get("page") == "1"
    }
    if remaining_page1 != set(APPROVED_UNIQUE_CREDITS):
        raise ValueError(
            f"Unexpected retained page-one credit set: {sorted(remaining_page1)}"
        )
    if len(removals) != len(REDUNDANT_CREDIT_ROLES):
        raise ValueError("Expected exactly three redundant page-one credits")
    return removals, retained


def contextual_element_payload(
    root: ET.Element, tag: str
) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for part in root.findall("part"):
        part_id = part.get("id", "")
        for measure in part.findall("measure"):
            measure_number = measure.get("number", "")
            elements = measure.findall(f".//{tag}")
            for index, element in enumerate(elements, start=1):
                rows.append(
                    [part_id, measure_number, index, semantic_element(element)]
                )
    return rows


def top_level_measure_payload(
    root: ET.Element, tag: str
) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for part in root.findall("part"):
        part_id = part.get("id", "")
        for measure in part.findall("measure"):
            measure_number = measure.get("number", "")
            for index, element in enumerate(measure.findall(tag), start=1):
                rows.append(
                    [part_id, measure_number, index, semantic_element(element)]
                )
    return rows


def direction_counter(root: ET.Element) -> Counter[str]:
    result: Counter[str] = Counter()
    for part in root.findall("part"):
        part_id = part.get("id", "")
        for measure in part.findall("measure"):
            measure_number = measure.get("number", "")
            for direction in measure.findall("direction"):
                key = json.dumps(
                    [part_id, measure_number, semantic_element(direction)],
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                result[key] += 1
    return result


def metadata_payload(root: ET.Element) -> dict[str, Any]:
    return {
        "work": semantic_element(root.find("work")) if root.find("work") is not None else None,
        "movement_number": root.findtext("movement-number"),
        "movement_title": root.findtext("movement-title"),
        "identification": (
            semantic_element(root.find("identification"))
            if root.find("identification") is not None
            else None
        ),
    }


def harmony_label(harmony: ET.Element) -> str:
    root_step = harmony.findtext("./root/root-step", "")
    root_alter = harmony.findtext("./root/root-alter")
    kind = harmony.find("kind")
    kind_value = kind.text if kind is not None else ""
    kind_text = kind.get("text") if kind is not None else None
    bass_step = harmony.findtext("./bass/bass-step")
    bass_alter = harmony.findtext("./bass/bass-alter")
    return json.dumps(
        {
            "root_step": root_step,
            "root_alter": root_alter,
            "kind": kind_value,
            "kind_text": kind_text,
            "bass_step": bass_step,
            "bass_alter": bass_alter,
            "degrees": [
                {
                    "value": degree.findtext("degree-value"),
                    "alter": degree.findtext("degree-alter"),
                    "type": degree.findtext("degree-type"),
                }
                for degree in harmony.findall("degree")
            ],
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def audit_dense_harmony(root: ET.Element) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    unsafe_position_attributes: list[dict[str, Any]] = []
    for part in root.findall("part"):
        part_id = part.get("id", "")
        for measure in part.findall("measure"):
            measure_number = int(measure.get("number", "0"))
            if not 93 <= measure_number <= 97:
                continue
            for index, harmony in enumerate(measure.findall("harmony"), start=1):
                for element in harmony.iter():
                    for attribute in POSITION_ATTRIBUTES:
                        if attribute in element.attrib:
                            unsafe_position_attributes.append(
                                {
                                    "part": part_id,
                                    "measure": measure_number,
                                    "harmony_index": index,
                                    "element": element.tag,
                                    "attribute": attribute,
                                    "value": element.get(attribute),
                                }
                            )
                records.append(
                    {
                        "part": part_id,
                        "measure": measure_number,
                        "harmony_index": index,
                        "identity": harmony_label(harmony),
                        "offset": harmony.findtext("offset"),
                        "semantic_signature": element_signature(harmony),
                    }
                )

    return {
        "measure_range": [93, 97],
        "harmony_count": len(records),
        "harmonies": records,
        "unsafe_local_position_attributes": unsafe_position_attributes,
        "musicxml_changes": [],
        "action": "dorico_only",
        "reason": (
            "MusicXML provides no safe minimum-gap or collision-avoidance control "
            "for this chord-symbol run. Existing harmony offsets are rhythmic "
            "anchors; changing them would change timing. Retain every harmony "
            "identity and offset, then adjust chord-symbol/note spacing in Dorico."
        ),
    }


def assert_aleatoric_result(root: ET.Element) -> None:
    for measure_number, rule in ALEATORIC_DUPLICATE_RULES.items():
        for part in root.findall("part"):
            part_id = part.get("id", "")
            count = len(
                find_word_directions(root, part_id, measure_number, ALEATORIC_TEXT)
            )
            expected = 1 if part_id == rule["retain"] else 0
            if count != expected:
                raise ValueError(
                    f"Aleatoric direction result mismatch in {part_id} "
                    f"m{measure_number}: {count}"
                )


def write_musicxml(tree: ET.ElementTree, output: Path) -> None:
    ET.indent(tree, space="  ")
    body = ET.tostring(tree.getroot(), encoding="unicode", short_empty_elements=True)
    output.write_text(
        f"<?xml version='1.0' encoding='utf-8'?>\n{DOCTYPE}\n{body}\n",
        encoding="utf-8",
    )


def refuse_overwrite(paths: Iterable[Path], force: bool) -> None:
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
    refuse_overwrite((output, report_path), force)
    provenance = verify_provenance_chain(source) if verify_chain else None

    tree = ET.parse(source)
    root = tree.getroot()
    source_state = validate_score_shape(root)
    if normalized_score_fingerprint(root) != EXPECTED_STRUCTURE_FINGERPRINT:
        raise ValueError("Source does not match the canonical musical fingerprint")
    if len(root.findall("./part/measure/note")) != EXPECTED_NOTE_COUNT:
        raise ValueError("Source note count is not 2,787")
    if len(root.findall(".//lyric")) != EXPECTED_LYRIC_ANCHORS:
        raise ValueError("Source lyric-anchor count is not 1,376")

    notes_before = top_level_measure_payload(root, "note")
    lyrics_before = contextual_element_payload(root, "lyric")
    dynamics_before = contextual_element_payload(root, "dynamics")
    harmonies_before = top_level_measure_payload(root, "harmony")
    directions_before = direction_counter(root)
    metadata_before = metadata_payload(root)
    staff_lines_before = staff_line_payload(root)
    casting_before = validate_casting(root)
    harmony_audit_before = audit_dense_harmony(root)

    if not staff_lines_before or any(row[2] != "5" for row in staff_lines_before):
        raise ValueError("Source contains a non-five-line staff override")
    if harmony_audit_before["unsafe_local_position_attributes"]:
        raise ValueError("Dense harmony passage unexpectedly contains local offsets")

    direction_removals = consolidate_aleatoric_directions(root)
    credit_removals, retained_credits = remove_redundant_page1_credits(root)
    preserved_duplicate_clusters = duplicate_word_clusters(root)
    assert_aleatoric_result(root)

    notes_after = top_level_measure_payload(root, "note")
    lyrics_after = contextual_element_payload(root, "lyric")
    dynamics_after = contextual_element_payload(root, "dynamics")
    harmonies_after = top_level_measure_payload(root, "harmony")
    directions_after = direction_counter(root)
    metadata_after = metadata_payload(root)
    staff_lines_after = staff_line_payload(root)
    casting_after = validate_casting(root)
    output_state = validate_score_shape(root)
    harmony_audit_after = audit_dense_harmony(root)

    expected_directions_after = directions_before.copy()
    for removal in direction_removals:
        key_payload = [
            removal["part"],
            str(removal["measure"]),
            semantic_element(
                find_word_directions(
                    root,
                    str(removal["retained_part"]),
                    int(removal["measure"]),
                    ALEATORIC_TEXT,
                )[0][1]
            ),
        ]
        key_payload[0] = removal["part"]
        key = json.dumps(
            key_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        expected_directions_after[key] -= 1
        if expected_directions_after[key] == 0:
            del expected_directions_after[key]

    invariant_checks = {
        "score_shape_match": source_state == output_state,
        "canonical_structure_matches": (
            output_state["structure_fingerprint"] == EXPECTED_STRUCTURE_FINGERPRINT
        ),
        "notes_exact": notes_before == notes_after,
        "lyrics_text_attributes_and_placement_exact": lyrics_before == lyrics_after,
        "dynamics_exact": dynamics_before == dynamics_after,
        "harmonies_exact": harmonies_before == harmonies_after,
        "harmony_dense_passage_exact": harmony_audit_before == harmony_audit_after,
        "direction_changes_exactly_logged": (
            directions_after == expected_directions_after
        ),
        "semantic_metadata_exact": metadata_before == metadata_after,
        "five_line_overrides_exact": staff_lines_before == staff_lines_after,
        "casting_breaks_exact": casting_before == casting_after,
    }
    if not all(invariant_checks.values()):
        raise ValueError(f"Stage E in-memory invariants failed: {invariant_checks}")

    output.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    write_musicxml(tree, output)
    reparsed = ET.parse(output).getroot()
    assert_aleatoric_result(reparsed)

    roundtrip_state = validate_score_shape(reparsed)
    roundtrip_checks = {
        "score_shape_match": roundtrip_state == source_state,
        "note_count_exact": len(reparsed.findall("./part/measure/note"))
        == EXPECTED_NOTE_COUNT,
        "lyric_anchor_count_exact": len(reparsed.findall(".//lyric"))
        == EXPECTED_LYRIC_ANCHORS,
        "canonical_structure_matches": (
            roundtrip_state["structure_fingerprint"]
            == EXPECTED_STRUCTURE_FINGERPRINT
        ),
        "notes_exact": top_level_measure_payload(reparsed, "note") == notes_before,
        "lyrics_text_attributes_and_placement_exact": (
            contextual_element_payload(reparsed, "lyric") == lyrics_before
        ),
        "dynamics_exact": (
            contextual_element_payload(reparsed, "dynamics") == dynamics_before
        ),
        "harmonies_exact": (
            top_level_measure_payload(reparsed, "harmony") == harmonies_before
        ),
        "direction_changes_exactly_logged": (
            direction_counter(reparsed) == expected_directions_after
        ),
        "semantic_metadata_exact": metadata_payload(reparsed) == metadata_before,
        "five_line_overrides_exact": (
            staff_line_payload(reparsed) == staff_lines_before
        ),
        "casting_breaks_exact": validate_casting(reparsed) == casting_before,
        "fall_replacements_preserved": (
            provenance is None
            or provenance["fall_replacements"] == EXPECTED_FALL_REPLACEMENTS
        ),
    }
    validation_passed = all(
        value if isinstance(value, bool) else True
        for value in roundtrip_checks.values()
    )
    if not validation_passed:
        raise ValueError(f"Stage E round-trip validation failed: {roundtrip_checks}")

    ambiguity_flags = [
        {
            "code": "REPEATED_PASSAGE_LOCATION_RESOLVED",
            "requested_description": "m126-ish repeated passage",
            "musicxml_measure": 130,
            "action": "Consolidated at the actual encoded location, measure 130.",
        },
        {
            "code": "HARMONY_SPACING_DORICO_ONLY",
            "measures": [93, 94, 95, 96, 97],
            "action": harmony_audit_after["reason"],
        },
    ]

    validation = {
        "passed": validation_passed,
        "part_ids": roundtrip_state["part_ids"],
        "measure_counts": roundtrip_state["measure_counts"],
        "note_count": len(reparsed.findall("./part/measure/note")),
        "lyric_anchor_count": len(reparsed.findall(".//lyric")),
        "fall_replacement_count": EXPECTED_FALL_REPLACEMENTS,
        "structure_fingerprint": roundtrip_state["structure_fingerprint"],
        **roundtrip_checks,
        "note_payload_hash_before": hash_json(notes_before),
        "note_payload_hash_after": hash_json(
            top_level_measure_payload(reparsed, "note")
        ),
        "lyric_payload_hash_before": hash_json(lyrics_before),
        "lyric_payload_hash_after": hash_json(
            contextual_element_payload(reparsed, "lyric")
        ),
        "dynamics_payload_hash_before": hash_json(dynamics_before),
        "dynamics_payload_hash_after": hash_json(
            contextual_element_payload(reparsed, "dynamics")
        ),
        "harmony_payload_hash_before": hash_json(harmonies_before),
        "harmony_payload_hash_after": hash_json(
            top_level_measure_payload(reparsed, "harmony")
        ),
        "casting": casting_before,
    }

    report = {
        "stage": "E",
        "source": display_path(source),
        "output": display_path(output),
        "source_sha256": sha256(source),
        "output_sha256": sha256(output),
        "provenance": provenance,
        "ensemble_direction_cleanup": {
            "exact_wording_preserved": ALEATORIC_TEXT,
            "retained_locations": [
                {"part": "P1", "part_name": "Soprano S", "measure": measure}
                for measure in sorted(ALEATORIC_DUPLICATE_RULES)
            ],
            "removed_duplicate_count": len(direction_removals),
            "removed_duplicates": direction_removals,
            "other_exact_cross_part_clusters": preserved_duplicate_clusters,
        },
        "page1_credit_cleanup": {
            "removed_redundant_count": len(credit_removals),
            "removed_redundant": credit_removals,
            "retained_unique_count": len(retained_credits),
            "retained_unique": retained_credits,
        },
        "harmony_spacing_audit": harmony_audit_after,
        "ambiguity_flags": ambiguity_flags,
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
        args.source,
        args.output,
        args.report,
        force=args.force,
        verify_chain=True,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
