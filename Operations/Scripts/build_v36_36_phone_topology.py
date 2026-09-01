#!/usr/bin/env python3
"""Build the anonymous, non-runtime V36 36-phone stage topology.

The private roster is used only to recover chorus/lane membership.  Names are
never copied into the generated artifact.  Every committed identity is a
stable row/column position, endpoint id, or musical route id.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "Show-Control/Topology/FlashlightsInTheDark_v36_36PhoneTopology.json"
)
TOPOLOGY_SEED = 20260831
ROW_COUNTS = (14, 15, 15, 15)
ROW_START_X = (0.150, 0.175, 0.150, 0.175)
SPACING_X = 0.050
ROW_SHELL_INSET = (0.11, 0.18, 0.25, 0.32)
SHELL_CENTER_X = 0.5
SHELL_CENTER_Y = 0.60
SHELL_RADIUS_X = 0.445
SHELL_RADIUS_Y = 0.43
M104_START_SECONDS = "298.6276862745"
M104_FIRST_ATTACK_SECONDS = "299.4610196078"
SCORE_SHA256 = "251aa4e216ac7bcd0716aaf8efd09a4a7fd259ffaeae1384ba384648ed70e216"
LIGHT_ACTIVITY_SHA256 = "8965e556771ddf72ce01a64af9a03c10df2b9503d85023328e782469e98d21e7"

LIGHT_LANE_ORDER = (
    "soprano_l1",
    "soprano_l2",
    "tenor_l",
    "bass_l",
    "alto_l2",
    "alto_l1",
)
LIGHT_PRIMARY_QUOTAS = {
    "soprano_l1": 2,
    "soprano_l2": 2,
    "tenor_l": 3,
    "bass_l": 3,
    "alto_l2": 3,
    "alto_l1": 2,
}
LIGHT_POST_M104_QUOTAS = {lane: 2 for lane in LIGHT_LANE_ORDER}
SHADOW_LANE_ORDER = ("soprano_s", "alto_s", "baritone_s")
SHADOW_PRIMARY_QUOTAS = {lane: 5 for lane in SHADOW_LANE_ORDER}
SHADOW_POST_M104_QUOTAS = {lane: 4 for lane in SHADOW_LANE_ORDER}
PRIMARY_ROW_QUOTAS = (3, 4, 4, 4)
POST_M104_ROW_QUOTAS = (3, 3, 3, 3)


@dataclass(frozen=True)
class Seat:
    position_id: str
    row: int
    column: int
    normalized_x: float
    normalized_y: float
    side: str
    chorus: str
    lane_key: str


def shell_y(x: float) -> float:
    unit_x = (x - SHELL_CENTER_X) / SHELL_RADIUS_X
    if abs(unit_x) > 1:
        raise ValueError(f"Position x={x} lies outside the stage shell")
    return SHELL_CENTER_Y - SHELL_RADIUS_Y * math.sqrt(1 - unit_x**2)


def _shadow_lane(row: int, column: int) -> str:
    if row == 0:
        if column <= 2:
            return "soprano_s"
        if column <= 4:
            return "alto_s"
        if column <= 6:
            return "baritone_s"
    else:
        if column <= 1:
            return "soprano_s"
        if column <= 3:
            return "alto_s"
        if column <= 6:
            return "baritone_s"
    raise ValueError(f"Unexpected Shadow seat r{row + 1}c{column + 1}")


def load_anonymous_seats(roster_path: Path) -> tuple[Seat, ...]:
    payload = json.loads(roster_path.read_text(encoding="utf-8"))
    rows = payload.get("rows")
    if not isinstance(rows, list) or tuple(map(len, rows)) != ROW_COUNTS:
        raise ValueError(f"Expected anonymous row shape {ROW_COUNTS}")

    seats: list[Seat] = []
    for row_index, row in enumerate(rows):
        for column, record in enumerate(row):
            chorus = record.get("chorus")
            if chorus not in {"shadow", "light"}:
                raise ValueError(f"Invalid chorus at r{row_index + 1}c{column + 1}")
            if column < 7 and chorus != "shadow":
                raise ValueError("The approved roster must keep Shadow on the left")
            if column >= 7 and chorus != "light":
                raise ValueError("The approved roster must keep Light on the right")
            lane_key = (
                _shadow_lane(row_index, column)
                if chorus == "shadow"
                else str(record.get("laneKey") or "")
            )
            valid_lanes = SHADOW_LANE_ORDER if chorus == "shadow" else LIGHT_LANE_ORDER
            if lane_key not in valid_lanes:
                raise ValueError(
                    f"Invalid lane at r{row_index + 1}c{column + 1}: {lane_key!r}"
                )
            x = ROW_START_X[row_index] + SPACING_X * column
            y = shell_y(x) + ROW_SHELL_INSET[row_index]
            seats.append(
                Seat(
                    position_id=f"r{row_index + 1}c{column + 1}",
                    row=row_index + 1,
                    column=column + 1,
                    normalized_x=round(x, 6),
                    normalized_y=round(y, 6),
                    side="left" if chorus == "shadow" else "right",
                    chorus=chorus,
                    lane_key=lane_key,
                )
            )

    if len(seats) != 59:
        raise ValueError("Expected exactly 59 anonymous singer positions")
    if sum(seat.chorus == "shadow" for seat in seats) != 28:
        raise ValueError("Expected exactly 28 Shadow positions")
    if sum(seat.chorus == "light" for seat in seats) != 31:
        raise ValueError("Expected exactly 31 Light positions")
    return tuple(seats)


def _distance_squared(left: Seat, right: Seat) -> float:
    return round(
        (left.normalized_x - right.normalized_x) ** 2
        + (left.normalized_y - right.normalized_y) ** 2,
        12,
    )


def _selection_score(selected: tuple[Seat, ...], coverage: tuple[Seat, ...]) -> tuple[float, float, float]:
    pair_distances = [
        _distance_squared(left, right)
        for left, right in itertools.combinations(selected, 2)
    ]
    minimum_pair = min(pair_distances) if pair_distances else 0.0
    maximum_coverage = max(
        min(_distance_squared(candidate, chosen) for chosen in selected)
        for candidate in coverage
    )
    return minimum_pair, -maximum_coverage, round(sum(pair_distances), 12)


def _tie_hash(kind: str, seats: Iterable[Seat]) -> str:
    ids = ",".join(sorted(seat.position_id for seat in seats))
    return hashlib.sha256(f"{TOPOLOGY_SEED}|{kind}|{ids}".encode()).hexdigest()


def select_grouped_positions(
    seats: tuple[Seat, ...],
    group_quotas: dict[str, int],
    row_quotas: tuple[int, int, int, int],
    kind: str,
) -> tuple[Seat, ...]:
    options: list[tuple[str, list[tuple[Seat, ...]]]] = []
    for group, quota in group_quotas.items():
        members = tuple(seat for seat in seats if seat.lane_key == group)
        if len(members) < quota:
            raise ValueError(f"Not enough {group} seats for quota {quota}")
        options.append((group, list(itertools.combinations(members, quota))))
    options.sort(key=lambda item: len(item[1]))

    best: tuple[Seat, ...] | None = None
    best_score: tuple[float, float, float] | None = None
    best_tie: str | None = None

    def visit(index: int, chosen: tuple[Seat, ...], row_counts: list[int]) -> None:
        nonlocal best, best_score, best_tie
        if any(count > row_quotas[row] for row, count in enumerate(row_counts)):
            return
        if index == len(options):
            if tuple(row_counts) != row_quotas:
                return
            ordered = tuple(sorted(chosen, key=lambda seat: (seat.row, seat.column)))
            score = _selection_score(ordered, seats)
            tie = _tie_hash(kind, ordered)
            if (
                best is None
                or score > best_score
                or (score == best_score and tie < best_tie)
            ):
                best, best_score, best_tie = ordered, score, tie
            return
        _, combos = options[index]
        for combo in combos:
            next_counts = row_counts.copy()
            for seat in combo:
                next_counts[seat.row - 1] += 1
            visit(index + 1, chosen + combo, next_counts)

    visit(0, (), [0, 0, 0, 0])
    if best is None:
        raise ValueError(f"No deterministic {kind} selection satisfies all quotas")
    return best


def select_reserves(
    shadow_seats: tuple[Seat, ...],
    light_seats: tuple[Seat, ...],
    shadow_primaries: tuple[Seat, ...],
    light_primaries: tuple[Seat, ...],
) -> tuple[Seat, ...]:
    primary_ids = {seat.position_id for seat in shadow_primaries + light_primaries}

    def options(side_seats: tuple[Seat, ...]) -> list[tuple[Seat, ...]]:
        candidates = [seat for seat in side_seats if seat.position_id not in primary_ids]
        return [
            combo
            for combo in itertools.combinations(candidates, 3)
            if len({seat.row for seat in combo}) == 3
        ]

    shadow_options = options(shadow_seats)
    light_options = options(light_seats)
    best: tuple[Seat, ...] | None = None
    best_score: tuple[float, float, float] | None = None
    best_tie: str | None = None
    for left in shadow_options:
        for right in light_options:
            combined = tuple(sorted(left + right, key=lambda seat: (seat.row, seat.column)))
            if {seat.row for seat in combined} != {1, 2, 3, 4}:
                continue
            pair_distances = [
                _distance_squared(a, b) for a, b in itertools.combinations(combined, 2)
            ]
            coverage = max(
                max(
                    min(_distance_squared(primary, reserve) for reserve in left)
                    for primary in shadow_primaries
                ),
                max(
                    min(_distance_squared(primary, reserve) for reserve in right)
                    for primary in light_primaries
                ),
            )
            score = (
                min(pair_distances),
                -coverage,
                round(sum(pair_distances), 12),
            )
            tie = _tie_hash("reserve", combined)
            if (
                best is None
                or score > best_score
                or (score == best_score and tie < best_tie)
            ):
                best, best_score, best_tie = combined, score, tie
    if best is None:
        raise ValueError("No reserve layout satisfies spatial constraints")
    return best


def _manifest_hash(payload: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def build_topology(roster_path: Path) -> dict[str, object]:
    seats = load_anonymous_seats(roster_path)
    shadow = tuple(seat for seat in seats if seat.side == "left")
    light = tuple(seat for seat in seats if seat.side == "right")
    shadow_primary = select_grouped_positions(
        shadow, SHADOW_PRIMARY_QUOTAS, PRIMARY_ROW_QUOTAS, "shadow-primary"
    )
    light_primary = select_grouped_positions(
        light, LIGHT_PRIMARY_QUOTAS, PRIMARY_ROW_QUOTAS, "light-primary"
    )
    shadow_post = select_grouped_positions(
        shadow_primary,
        SHADOW_POST_M104_QUOTAS,
        POST_M104_ROW_QUOTAS,
        "shadow-post-m104",
    )
    light_post = select_grouped_positions(
        light_primary,
        LIGHT_POST_M104_QUOTAS,
        POST_M104_ROW_QUOTAS,
        "light-post-m104",
    )
    reserves = select_reserves(shadow, light, shadow_primary, light_primary)

    selected_phone_seats = tuple(
        sorted(shadow_primary + light_primary + reserves, key=lambda seat: (seat.row, seat.column))
    )
    endpoint_by_position = {
        seat.position_id: f"endpoint-{index:02d}"
        for index, seat in enumerate(selected_phone_seats, start=1)
    }
    reserve_ids = {seat.position_id for seat in reserves}
    shadow_post_ids = {seat.position_id for seat in shadow_post}
    light_post_ids = {seat.position_id for seat in light_post}

    endpoints: list[dict[str, object]] = []
    for seat in selected_phone_seats:
        endpoints.append(
            {
                "endpointId": endpoint_by_position[seat.position_id],
                "homePositionId": seat.position_id,
                "side": seat.side,
                "role": "reserve" if seat.position_id in reserve_ids else "primary",
                "normallyDark": seat.position_id in reserve_ids,
            }
        )

    primary_seats = tuple(
        sorted(shadow_primary + light_primary, key=lambda seat: (seat.side, seat.row, seat.column))
    )
    routes: list[dict[str, object]] = []
    lane_replica: dict[tuple[str, str], int] = {}
    for side in ("left", "right"):
        side_seats = [seat for seat in primary_seats if seat.side == side]
        for index, seat in enumerate(side_seats, start=1):
            route_id = f"route-{side}-{index:02d}"
            pre_active = side == "right"
            post_active = (
                seat.position_id in shadow_post_ids
                if side == "left"
                else seat.position_id in light_post_ids
            )
            phases: dict[str, object] = {}
            for phase, active in (("beforeM104", pre_active), ("fromM104", post_active)):
                key = (phase, seat.lane_key)
                replica = lane_replica.get(key, 0) if active else None
                if active:
                    lane_replica[key] = int(replica) + 1
                phases[phase] = {
                    "artisticallyEligible": active,
                    "laneKey": seat.lane_key if active else None,
                    "laneReplica": replica,
                }
            routes.append(
                {
                    "routeId": route_id,
                    "homePositionId": seat.position_id,
                    "defaultEndpointId": endpoint_by_position[seat.position_id],
                    "side": side,
                    "phases": phases,
                    "strictNoteGateRequired": True,
                    "mayBecomeReserveWhenInactive": False,
                }
            )

    reserve_rank = {
        position_id: rank
        for rank, position_id in enumerate(
            sorted(
                reserve_ids,
                key=lambda value: hashlib.sha256(
                    f"{TOPOLOGY_SEED}|reserve-rank|{value}".encode()
                ).hexdigest(),
            ),
            start=1,
        )
    }
    for endpoint in endpoints:
        if endpoint["role"] == "reserve":
            endpoint["reservePriorityRank"] = reserve_rank[endpoint["homePositionId"]]

    payload: dict[str, object] = {
        "schemaVersion": "v36-36-phone-topology-1",
        "artifactType": "anonymous-v36-primary-and-hot-reserve-topology",
        "status": "rehearsal-foundation-not-runtime-ready",
        "runtimeEligible": False,
        "seed": TOPOLOGY_SEED,
        "source": {
            "scorePath": "Engraving/Scores/FlashlightsInTheDark_v36_FinaleExport_2026-08-29.musicxml",
            "scoreSha256": SCORE_SHA256,
            "lightActivityPath": "Engraving/Score-Study/FlashlightsInTheDark_v36_LightChorusNoteActivity.json",
            "lightActivitySha256": LIGHT_ACTIVITY_SHA256,
            "privateRosterRetained": False,
            "performerNamesEncoded": False,
        },
        "counts": {
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
        "phaseBoundary": {
            "measure": 104,
            "cumulativeQuarter": "381",
            "audioSeconds": M104_START_SECONDS,
            "firstSharedAttackCumulativeQuarter": "382",
            "firstSharedAttackAudioSeconds": M104_FIRST_ATTACK_SECONDS,
            "globalDarkWindowMilliseconds": "833.3333333",
            "eventOrdering": [
                "panic-latch",
                "deactivate-and-release-old-phase-routes",
                "activate-new-phase-routes-dark",
                "resolve-deferred-health-and-failover",
                "apply-note-gates-at-first-attack",
            ],
        },
        "automaticTakeoverPolicy": {
            "sameSideOnly": True,
            "crossSideRequiresOperatorConfirmation": True,
            "candidateSort": [
                "squaredDistance",
                "reservePriorityRank",
                "homePositionId",
                "endpointId",
            ],
            "inactivePrimaryMayActAsReserve": False,
        },
        "selectionPolicy": {
            "primaryRowQuotasPerSide": list(PRIMARY_ROW_QUOTAS),
            "postM104RowQuotasPerSide": list(POST_M104_ROW_QUOTAS),
            "lightPrimaryLaneQuotas": LIGHT_PRIMARY_QUOTAS,
            "lightPostM104LaneQuotas": LIGHT_POST_M104_QUOTAS,
            "shadowPrimaryLaneQuotas": SHADOW_PRIMARY_QUOTAS,
            "shadowPostM104LaneQuotas": SHADOW_POST_M104_QUOTAS,
            "reserveConstraints": {
                "distinctRowsPerSide": 3,
                "allFourRowsRepresentedGlobally": True,
                "objective": [
                    "maximize-minimum-pair-distance",
                    "minimize-worst-same-side-primary-distance",
                    "maximize-total-pair-distance",
                    "seeded-sha256-tie-break",
                ],
            },
        },
        "seatGeometry": [asdict(seat) for seat in seats],
        "endpoints": endpoints,
        "routes": routes,
        "validation": {
            "allIdsAnonymous": True,
            "allReserveEndpointsNormallyDark": True,
            "allRoutesHaveOneDefaultPrimary": True,
            "noPrimaryBecomesReserveWhenPhaseInactive": True,
            "reserveSides": {
                side: sum(
                    endpoint["role"] == "reserve" and endpoint["side"] == side
                    for endpoint in endpoints
                )
                for side in ("left", "right")
            },
        },
    }
    payload["manifestSha256"] = _manifest_hash(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--roster",
        type=Path,
        required=True,
        help="Private 59-singer roster JSON; names are read but never emitted",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = build_topology(args.roster)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output.resolve()), **payload["counts"], "manifestSha256": payload["manifestSha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
