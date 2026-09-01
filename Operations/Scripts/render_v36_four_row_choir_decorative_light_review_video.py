#!/usr/bin/env python3
"""Render the V36 review as a four-row windowed choir plus conductor."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageDraw

from build_v36_decorative_light_texture import DEFAULT_OUTPUT, sha256
from render_v36_decorative_light_review_video import (
    DecorativeEngine,
    TexturedStageRenderer,
    hash01,
)
from render_v36_light_chorus_review_video import (
    DEFAULT_ACTIVITY_PATH,
    _centered_text,
    load_review_timeline,
)
from render_v36_lyric_light_review_video import LyricStageRenderer, render_video
from render_v36_mixed_ensemble_decorative_light_review_video import (
    EnsembleSeat,
    MixedEnsembleStageRenderer,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
LAYOUT_SCHEMA = "v36-four-row-windowed-choir-layout-1"
LAYOUT_SEED = 36043004
ROW_COUNT = 4
COLUMN_COUNT = 15
ROW_LIGHT_COUNTS = (8, 7, 8, 7)
SPOT_SPACING_X = 0.056
EVEN_ROW_START_X = 0.094
WINDOW_OFFSET_X = SPOT_SPACING_X / 2
ROW_CENTER_Y = (0.31, 0.405, 0.50, 0.595)
CURVE_DEPTH = 0.055
CONDUCTOR_X = 0.5
CONDUCTOR_Y = 0.705
DEFAULT_LAYOUT_OUTPUT = (
    REPO_ROOT
    / "Visual-Production/Review-Renders/V36-Note-Synchronous-Review-2026-08-30/Manifests"
    / "FlashlightsInTheDark_v36_FourRowChoirLayout_2026-08-30.json"
)


def _lane_sequence_for_row(
    stage_order: tuple[str, ...], row: int
) -> tuple[str, ...]:
    extra_lanes_by_row = ((0, 5), (1,), (2, 3), (4,))
    sequence: list[str] = []
    for lane_index, lane_key in enumerate(stage_order):
        sequence.extend(
            [lane_key] * (2 if lane_index in extra_lanes_by_row[row] else 1)
        )
    if len(sequence) != ROW_LIGHT_COUNTS[row]:
        raise ValueError("Four-row lane distribution is inconsistent")
    return tuple(sequence)


def _row_position(row: int, column: int) -> tuple[float, float]:
    row_seed = LAYOUT_SEED + row * 4099
    offset = WINDOW_OFFSET_X if row % 2 else 0.0
    base_x = EVEN_ROW_START_X + SPOT_SPACING_X * column + offset
    jitter_x = (hash01(row_seed + 17, column) - 0.5) * 0.008
    x = base_x + jitter_x
    normalized_shell_distance = (x - 0.5) / 0.42
    curve_drop = CURVE_DEPTH * normalized_shell_distance**2
    jitter_y = (hash01(row_seed + 31, column) - 0.5) * 0.006
    y = ROW_CENTER_Y[row] + curve_drop + jitter_y
    return round(x, 6), round(y, 6)


def build_four_row_layout(
    stage_order: tuple[str, ...],
) -> tuple[EnsembleSeat, ...]:
    if len(stage_order) != 6:
        raise ValueError("Four-row choir requires the six canonical Light lanes")
    lane_replica = {lane_key: 0 for lane_key in stage_order}
    seats: list[EnsembleSeat] = []
    for row in range(ROW_COUNT):
        row_seed = LAYOUT_SEED + row * 4099
        ranked_columns = sorted(
            range(COLUMN_COUNT),
            key=lambda column: hash01(row_seed, column + row * COLUMN_COUNT),
        )
        light_columns = sorted(ranked_columns[: ROW_LIGHT_COUNTS[row]])
        sequence = _lane_sequence_for_row(stage_order, row)
        lane_by_column = dict(zip(light_columns, sequence))
        for column in range(COLUMN_COUNT):
            lane_key = lane_by_column.get(column)
            replica = None
            if lane_key is not None:
                replica = lane_replica[lane_key]
                lane_replica[lane_key] += 1
            x, y = _row_position(row, column)
            seats.append(
                EnsembleSeat(
                    row=row,
                    column=column,
                    normalized_x=x,
                    normalized_y=y,
                    chorus="light" if lane_key is not None else "shadow",
                    lane_key=lane_key,
                    lane_replica=replica,
                )
            )
    if set(lane_replica.values()) != {5}:
        raise ValueError(f"Expected five Light spots per lane: {lane_replica}")
    return tuple(seats)


def _layout_hash(seats: tuple[EnsembleSeat, ...]) -> str:
    encoded = json.dumps(
        [asdict(seat) for seat in seats],
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def layout_payload(stage_order: tuple[str, ...]) -> dict[str, object]:
    seats = build_four_row_layout(stage_order)
    light_seats = [seat for seat in seats if seat.chorus == "light"]
    shadow_seats = [seat for seat in seats if seat.chorus == "shadow"]
    return {
        "schemaVersion": LAYOUT_SCHEMA,
        "artifactType": "review-only-four-row-windowed-choir-layout",
        "status": "presentation-layout-not-runtime-topology",
        "runtimeEligible": False,
        "seed": LAYOUT_SEED,
        "rowCount": ROW_COUNT,
        "spotsPerRow": COLUMN_COUNT,
        "rowLightCounts": list(ROW_LIGHT_COUNTS),
        "lightCircleCount": len(light_seats),
        "shadowCircleCount": len(shadow_seats),
        "conductorSpotCount": 1,
        "lightSpotsPerLogicalLane": {
            lane_key: sum(seat.lane_key == lane_key for seat in light_seats)
            for lane_key in stage_order
        },
        "lightLaneOrder": list(stage_order),
        "rowWindowOffsetsInSpotUnits": [0.0, 0.5, 0.0, 0.5],
        "curvePolicy": "Each row follows a parallel shallow parabola with its highest point at center, matching the background shell's center-high arch.",
        "shadowBehavior": "permanently dark",
        "conductor": {
            "normalizedX": CONDUCTOR_X,
            "normalizedY": CONDUCTOR_Y,
            "behavior": "neutral permanently dark presentation marker",
            "includedInChorusCounts": False,
        },
        "physicalTopologyEncoded": False,
        "layoutSha256": _layout_hash(seats),
        "seats": [asdict(seat) for seat in seats],
    }


def write_layout(path: Path, stage_order: tuple[str, ...]) -> dict[str, object]:
    path = path.resolve()
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite layout artifact: {path}")
    payload = layout_payload(stage_order)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return {"path": str(path), "sha256": sha256(path), **payload}


class FourRowChoirStageRenderer(MixedEnsembleStageRenderer):
    def __init__(
        self, timeline: object, width: int, height: int, texture_path: Path
    ) -> None:
        super().__init__(timeline, width, height, texture_path)
        self.seats = build_four_row_layout(timeline.stage_order)
        self.layout_sha256 = _layout_hash(self.seats)

    def _build_base(self) -> Image.Image:
        image = TexturedStageRenderer._build_base(self)
        draw = ImageDraw.Draw(image)
        margin = round(self.width * 0.055)
        header_y = round(self.height * 0.055)
        draw.rectangle(
            (
                margin - round(4 * self.scale),
                header_y - round(5 * self.scale),
                round(self.width * 0.76),
                round(self.height * 0.115),
            ),
            fill=(4, 6, 15),
        )
        draw.text(
            (margin, header_y),
            "FLASHLIGHTS IN THE DARK  ·  V36 CHOIR LIGHT REVIEW",
            font=self.title_font,
            fill=(230, 235, 243),
        )

        guide_color = (24, 31, 46)
        for row in range(ROW_COUNT):
            points = []
            for sample in range(81):
                column = 14 * sample / 80
                offset = WINDOW_OFFSET_X if row % 2 else 0.0
                x01 = EVEN_ROW_START_X + SPOT_SPACING_X * column + offset
                shell_distance = (x01 - 0.5) / 0.42
                y01 = ROW_CENTER_Y[row] + CURVE_DEPTH * shell_distance**2
                points.append((round(self.width * x01), round(self.height * y01)))
            draw.line(points, fill=guide_color, width=max(1, round(self.scale)))

        radius = max(4, round(6 * self.scale))
        legend_y = round(self.height * 0.23)
        legend = (
            (0.245, (5, 7, 13), (48, 56, 72), "SHADOW · dark"),
            (0.455, (255, 238, 183), (255, 255, 242), "LIGHT · note + texture"),
            (0.72, (7, 10, 17), (148, 126, 73), "CONDUCTOR · marker"),
        )
        for x_ratio, fill, outline, label in legend:
            x = round(self.width * x_ratio)
            draw.ellipse(
                (x - radius, legend_y - radius, x + radius, legend_y + radius),
                fill=fill,
                outline=outline,
                width=max(1, round(self.scale)),
            )
            draw.text(
                (x + round(13 * self.scale), legend_y - round(8 * self.scale)),
                label,
                font=self.small_font,
                fill=outline,
            )
        _centered_text(
            draw,
            (self.width // 2, round(self.height * 0.265)),
            "Light order left → right:  Sop-L1 · Sop-L2 · Ten-L · Bass-L · Alto-L2 · Alto-L1",
            self.small_font,
            (94, 103, 120),
        )
        return image

    def _draw_ensemble(
        self,
        image: Image.Image,
        states: dict[str, bool],
        seconds: float,
    ) -> None:
        super()._draw_ensemble(image, states, seconds)
        draw = ImageDraw.Draw(image)
        x = round(self.width * CONDUCTOR_X)
        y = round(self.height * CONDUCTOR_Y)
        radius = max(7, round(10 * self.scale))
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=(7, 10, 17),
            outline=(148, 126, 73),
            width=max(1, round(2 * self.scale)),
        )
        inner = max(2, radius // 3)
        draw.ellipse(
            (x - inner, y - inner, x + inner, y + inner),
            fill=(3, 5, 9),
        )
        _centered_text(
            draw,
            (x, y + radius + round(5 * self.scale)),
            "CONDUCTOR",
            self.small_font,
            (148, 126, 73),
        )


class FourRowChoirLyricRenderer(LyricStageRenderer):
    def __init__(
        self, timeline: object, width: int, height: int, texture_path: Path
    ) -> None:
        super().__init__(timeline, width, height)
        self.base_renderer = FourRowChoirStageRenderer(
            timeline, width, height, texture_path
        )
        self.engine: DecorativeEngine = self.base_renderer.engine


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activity", type=Path, default=DEFAULT_ACTIVITY_PATH)
    parser.add_argument("--texture", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--score-origin-seconds", type=Fraction, required=True)
    parser.add_argument("--duration-seconds", type=Fraction, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preview-output", type=Path)
    parser.add_argument("--preview-seconds", type=Fraction, default=Fraction(0))
    parser.add_argument("--layout-output", type=Path)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--crf", type=int, default=18)
    parser.add_argument("--preset", default="medium")
    args = parser.parse_args()
    timeline = load_review_timeline(
        args.activity,
        score_origin_seconds=args.score_origin_seconds,
        output_duration_seconds=args.duration_seconds,
    )
    renderer = FourRowChoirLyricRenderer(
        timeline, args.width, args.height, args.texture
    )
    result: dict[str, object] = {
        "texturePath": str(args.texture.resolve()),
        "textureSha256": sha256(args.texture),
        "layoutSha256": renderer.base_renderer.layout_sha256,
        "lightCircleCount": sum(
            seat.chorus == "light" for seat in renderer.base_renderer.seats
        ),
        "shadowCircleCount": sum(
            seat.chorus == "shadow" for seat in renderer.base_renderer.seats
        ),
        "conductorSpotCount": 1,
    }
    if args.layout_output:
        result["layoutArtifact"] = write_layout(
            args.layout_output, timeline.stage_order
        )
    if args.preview_output:
        if args.preview_output.exists():
            raise FileExistsError(f"Refusing to overwrite preview: {args.preview_output}")
        args.preview_output.parent.mkdir(parents=True, exist_ok=True)
        renderer.render_frame(args.preview_seconds).save(args.preview_output, "PNG")
        result["preview"] = {
            "path": str(args.preview_output.resolve()),
            "sha256": sha256(args.preview_output),
            "atSeconds": str(args.preview_seconds),
        }
    if args.output:
        result["video"] = render_video(
            renderer, args.output, args.fps, args.crf, args.preset
        )
    if not args.layout_output and not args.preview_output and not args.output:
        raise ValueError("Supply --layout-output, --preview-output, and/or --output")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
