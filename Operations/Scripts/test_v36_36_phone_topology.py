#!/usr/bin/env python3
"""Focused invariants for the anonymous V36 36-phone topology."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from collections import Counter
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import build_v36_36_phone_topology as builder  # noqa: E402


ARTIFACT = (
    REPO_ROOT
    / "Show-Control/Topology/FlashlightsInTheDark_v36_36PhoneTopology.json"
)


class V3636PhoneTopologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    def test_manifest_hash_and_counts(self) -> None:
        unhashed = copy.deepcopy(self.payload)
        expected = unhashed.pop("manifestSha256")
        self.assertEqual(builder._manifest_hash(unhashed), expected)
        self.assertEqual(
            self.payload["counts"],
            {
                "singers": 59,
                "shadowSingers": 28,
                "lightSingers": 31,
                "registeredEndpoints": 36,
                "primaryEndpoints": 30,
                "reserveEndpoints": 6,
                "primaryPerSide": 15,
                "reservePerSide": 3,
                "eligibleBeforeM104": {"left": 0, "right": 15},
                "eligibleFromM104": {"left": 12, "right": 12},
            },
        )

    def test_endpoint_roles_and_route_ownership_are_disjoint(self) -> None:
        endpoints = self.payload["endpoints"]
        routes = self.payload["routes"]
        endpoint_ids = [item["endpointId"] for item in endpoints]
        route_ids = [item["routeId"] for item in routes]
        self.assertEqual(len(endpoint_ids), len(set(endpoint_ids)))
        self.assertEqual(len(route_ids), len(set(route_ids)))
        self.assertEqual(Counter(item["role"] for item in endpoints), {"primary": 30, "reserve": 6})
        default_owners = [item["defaultEndpointId"] for item in routes]
        self.assertEqual(len(default_owners), len(set(default_owners)))
        reserve_ids = {item["endpointId"] for item in endpoints if item["role"] == "reserve"}
        self.assertTrue(reserve_ids.isdisjoint(default_owners))
        self.assertTrue(
            all(item["normallyDark"] for item in endpoints if item["role"] == "reserve")
        )

    def test_lane_and_row_quotas(self) -> None:
        routes = self.payload["routes"]
        before = [
            route for route in routes if route["phases"]["beforeM104"]["artisticallyEligible"]
        ]
        after = [
            route for route in routes if route["phases"]["fromM104"]["artisticallyEligible"]
        ]
        self.assertEqual(Counter(route["side"] for route in before), {"right": 15})
        self.assertEqual(Counter(route["side"] for route in after), {"left": 12, "right": 12})
        self.assertEqual(
            Counter(route["phases"]["beforeM104"]["laneKey"] for route in before),
            builder.LIGHT_PRIMARY_QUOTAS,
        )
        self.assertEqual(
            Counter(
                route["phases"]["fromM104"]["laneKey"]
                for route in after
                if route["side"] == "right"
            ),
            builder.LIGHT_POST_M104_QUOTAS,
        )
        self.assertEqual(
            Counter(
                route["phases"]["fromM104"]["laneKey"]
                for route in after
                if route["side"] == "left"
            ),
            builder.SHADOW_POST_M104_QUOTAS,
        )

    def test_reserves_are_spatially_dispersed_and_same_side_balanced(self) -> None:
        endpoints = self.payload["endpoints"]
        reserves = [item for item in endpoints if item["role"] == "reserve"]
        self.assertEqual(Counter(item["side"] for item in reserves), {"left": 3, "right": 3})
        positions = {item["position_id"]: item for item in self.payload["seatGeometry"]}
        for side in ("left", "right"):
            rows = {
                positions[item["homePositionId"]]["row"]
                for item in reserves
                if item["side"] == side
            }
            self.assertEqual(len(rows), 3)
        self.assertEqual(
            {
                positions[item["homePositionId"]]["row"] for item in reserves
            },
            {1, 2, 3, 4},
        )

    def test_no_private_identity_or_device_identifier_is_encoded(self) -> None:
        forbidden_keys = {"displayName", "performerName", "deviceId", "udid", "ip"}

        def visit(value: object) -> None:
            if isinstance(value, dict):
                self.assertFalse(forbidden_keys.intersection(value))
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
        visit(self.payload)
        self.assertFalse(self.payload["source"]["performerNamesEncoded"])

    def test_m104_global_dark_window_and_order_are_frozen(self) -> None:
        boundary = self.payload["phaseBoundary"]
        self.assertEqual(boundary["audioSeconds"], "298.6276862745")
        self.assertEqual(boundary["firstSharedAttackAudioSeconds"], "299.4610196078")
        self.assertEqual(boundary["eventOrdering"][0], "panic-latch")
        self.assertEqual(boundary["eventOrdering"][-1], "apply-note-gates-at-first-attack")


if __name__ == "__main__":
    unittest.main()
