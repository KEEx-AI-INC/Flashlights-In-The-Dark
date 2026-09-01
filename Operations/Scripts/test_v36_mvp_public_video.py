#!/usr/bin/env python3
"""Focused contract checks for the privacy-safe V36 MVP renderer."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOPOLOGY = ROOT / "Show-Control/Topology/FlashlightsInTheDark_v36_36PhoneTopology.json"
RENDERER = Path(__file__).with_name("render_v36_mvp_public_video.py")


class PublicMVPContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.topology = json.loads(TOPOLOGY.read_text(encoding="utf-8"))

    def test_counts_and_privacy_boundary(self) -> None:
        counts = self.topology["counts"]
        self.assertEqual(counts["singers"], 59)
        self.assertEqual(counts["shadowSingers"], 28)
        self.assertEqual(counts["lightSingers"], 31)
        self.assertEqual(counts["registeredEndpoints"], 36)
        self.assertEqual(counts["primaryEndpoints"], 30)
        self.assertEqual(counts["reserveEndpoints"], 6)
        self.assertFalse(self.topology["runtimeEligible"])
        self.assertFalse(self.topology["source"]["performerNamesEncoded"])

    def test_m104_phase_contract(self) -> None:
        counts = self.topology["counts"]
        self.assertEqual(counts["eligibleBeforeM104"], {"left": 0, "right": 15})
        self.assertEqual(counts["eligibleFromM104"], {"left": 12, "right": 12})
        self.assertEqual(
            self.topology["phaseBoundary"]["globalDarkWindowMilliseconds"],
            "833.3333333",
        )

    def test_single_endpoint_and_route_ownership(self) -> None:
        endpoints = self.topology["endpoints"]
        self.assertEqual(len(endpoints), 36)
        self.assertEqual(len({item["endpointId"] for item in endpoints}), 36)
        self.assertEqual(len({item["homePositionId"] for item in endpoints}), 36)
        routes = self.topology["routes"]
        self.assertEqual(len(routes), 30)
        self.assertEqual(len({item["routeId"] for item in routes}), 30)
        self.assertEqual(len({item["homePositionId"] for item in routes}), 30)

    def test_renderer_contains_no_private_display_names(self) -> None:
        source = RENDERER.read_text(encoding="utf-8")
        self.assertNotIn("displayName", source)
        self.assertNotIn("performerName", source)
        self.assertIn('"CONDUCTOR"', source)
        self.assertIn('"TECH OPERATOR · MacBook control"', source)
        self.assertIn("StrictNoteGatedStageRenderer", source)


if __name__ == "__main__":
    unittest.main()
