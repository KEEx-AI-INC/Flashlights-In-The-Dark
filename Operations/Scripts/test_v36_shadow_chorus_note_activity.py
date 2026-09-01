#!/usr/bin/env python3
"""Focused invariants for V36 Shadow Chorus note activity."""

from __future__ import annotations

import json
import sys
import unittest
from fractions import Fraction
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import build_v36_shadow_chorus_note_activity as builder  # noqa: E402


ARTIFACT = (
    REPO_ROOT
    / "Engraving/Score-Study/FlashlightsInTheDark_v36_ShadowChorusNoteActivity.json"
)


class V36ShadowChorusNoteActivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.checked_in = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        cls.generated = builder.build_artifact()

    def test_checked_in_artifact_is_deterministic(self) -> None:
        self.assertEqual(self.checked_in, self.generated)
        self.assertEqual(self.checked_in["source"]["measureCount"], 141)
        self.assertEqual(self.checked_in["source"]["scoreSpanQuarter"], "535")
        self.assertFalse(self.checked_in["runtimeEligible"])

    def test_three_logical_lanes_and_all_source_noteheads(self) -> None:
        groups = self.checked_in["groups"]
        self.assertEqual(
            [(item["key"], item["sourcePartId"]) for item in groups],
            [("soprano_s", "P1"), ("alto_s", "P2"), ("baritone_s", "P3")],
        )
        source_segments = sum(
            event["sourceSegmentCount"]
            for group in groups
            for event in group["noteEvents"]
        )
        self.assertEqual(source_segments, 763)
        self.assertEqual(self.checked_in["validation"]["sourceNoteheadCount"], 763)

    def test_baritone_voice_two_is_provenance_only_binary_or(self) -> None:
        baritone = next(group for group in self.checked_in["groups"] if group["key"] == "baritone_s")
        supplemental = [event for event in baritone["noteEvents"] if event["sourceVoice"] == "2"]
        self.assertEqual(len(supplemental), 4)
        self.assertEqual(sum(item["sourceSegmentCount"] for item in supplemental), 6)
        primary_spans = {
            (item["start"]["cumulativeQuarter"], item["end"]["cumulativeQuarter"])
            for item in baritone["noteEvents"]
            if item["sourceVoice"] == "1"
        }
        self.assertTrue(
            all(
                (item["start"]["cumulativeQuarter"], item["end"]["cumulativeQuarter"])
                in primary_spans
                for item in supplemental
            )
        )
        self.assertEqual(baritone["stateAggregation"]["mode"], "binary-logical-or")

    def test_unmatched_alto_tie_is_capped_at_incompatible_pitch(self) -> None:
        resolutions = self.checked_in["tieResolutions"]
        self.assertEqual(len(resolutions), 1)
        item = resolutions[0]
        self.assertEqual(item["sourceId"], "P2-m110-v1-n0198")
        self.assertEqual(item["writtenPitch"], "Ab4")
        self.assertEqual(item["nextWrittenPitch"], "G4")
        self.assertEqual(item["encodedEnd"]["cumulativeQuarter"], "411")

    def test_all_shadow_lanes_are_off_in_m104_redistribution_window(self) -> None:
        for group in self.checked_in["groups"]:
            covering = [
                item
                for item in group["activityIntervals"]
                if Fraction(item["start"]["cumulativeQuarter"]) <= Fraction(381)
                and Fraction(item["end"]["cumulativeQuarter"]) >= Fraction(382)
            ]
            self.assertEqual(len(covering), 1, group["key"])
            self.assertEqual(covering[0]["state"], "off", group["key"])

    def test_no_cue_or_grace_notes_are_inferred(self) -> None:
        self.assertEqual(self.checked_in["validation"]["cueNoteCount"], 0)
        self.assertEqual(self.checked_in["validation"]["graceNoteCount"], 0)
        self.assertEqual(self.checked_in["unresolvedSourceWarnings"], [])


if __name__ == "__main__":
    unittest.main()
