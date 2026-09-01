#!/usr/bin/env python3
"""Render the V36 decorative review as a mixed Light/Shadow ensemble."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageDraw

from build_v36_decorative_light_texture import DEFAULT_OUTPUT, sha256
from render_v36_decorative_light_review_video import (
    DecorativeEngine,
    TexturedStageRenderer,
    hash01,
    mix_color,
)
from render_v36_light_chorus_review_video import (
    DEFAULT_ACTIVITY_PATH,
    _centered_text,
    _timecode,
    load_review_timeline,
)
from render_v36_lyric_light_review_video import LyricStageRenderer, render_video


REPO_ROOT = Path(__file__).resolve().parents[2]
LAYOUT_SCHEMA = "v36-mixed-light-shadow-ensemble-layout-1"
LAYOUT_SEED = 36084242
ROW_COUNT = 7
COLUMN_COUNT = 12
LIGHTS_PER_ROW = 6
DEFAULT_LAYOUT_OUTPUT = (
    REPO_ROOT
    / "Visual-Production/Review-Renders/V36-Note-Synchronous-Review-2026-08-30/Manifests"
    / "FlashlightsInTheDark_v36_MixedLightShadowEnsembleLayout_2026-08-30.json"
)


@dataclass(frozen=True)
class EnsembleSeat:
    row: int
    column: int
    normalized_x: float
    normalized_y: float
    chorus: str
    lane_key: str | None
    lane_replica: int | None


def _layout_hash(seats: tuple[EnsembleSeat, ...]) -> str:
    encoded = json.dumps(
        [asdict(seat) for seat in seats],
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_mixed_ensemble_layout(
    stage_order: tuple[str, ...],
) -> tuple[EnsembleSeat, ...]:
    if len(stage_order) != LIGHTS_PER_ROW:
        raise ValueError("Mixed ensemble requires the six canonical Light lanes")
    seats: list[EnsembleSeat] = []
    for row in range(ROW_COUNT):
        row_seed = LAYOUT_SEED + row * 4099
        ranked_columns = sorted(
            range(COLUMN_COUNT),
            key=lambda column: hash01(row_seed, column + row * COLUMN_COUNT),
        )
        light_columns = sorted(ranked_columns[:LIGHTS_PER_ROW])
        lane_by_column = {
            column: stage_order[index]
            for index, column in enumerate(light_columns)
        }
        for column in range(COLUMN_COUNT):
            base_x = 0.095 + 0.81 * column / (COLUMN_COUNT - 1)
            jitter_x = (hash01(row_seed + 17, column) - 0.5) * 0.014
            base_y = 0.31 + 0.057 * row
            arch_drop = 0.035 * abs((column - 5.5) / 5.5)
            jitter_y = (hash01(row_seed + 31, column) - 0.5) * 0.012
            lane_key = lane_by_column.get(column)
            seats.append(
                EnsembleSeat(
                    row=row,
                    column=column,
                    normalized_x=round(base_x + jitter_x, 6),
                    normalized_y=round(base_y + arch_drop + jitter_y, 6),
                    chorus="light" if lane_key is not None else "shadow",
                    lane_key=lane_key,
                    lane_replica=row if lane_key is not None else None,
                )
            )
    return tuple(seats)


def layout_payload(stage_order: tuple[str, ...]) -> dict[str, object]:
    seats = build_mixed_ensemble_layout(stage_order)
    light_seats = [seat for seat in seats if seat.chorus == "light"]
    shadow_seats = [seat for seat in seats if seat.chorus == "shadow"]
    return {
        "schemaVersion": LAYOUT_SCHEMA,
        "artifactType": "review-only-mixed-light-shadow-ensemble-layout",
        "status": "presentation-layout-not-runtime-topology",
        "runtimeEligible": False,
        "seed": LAYOUT_SEED,
        "rowCount": ROW_COUNT,
        "columnCount": COLUMN_COUNT,
        "lightCircleCount": len(light_seats),
        "shadowCircleCount": len(shadow_seats),
        "shadowBehavior": "permanently dark",
        "lightLaneOrder": list(stage_order),
        "assignmentPolicy": "Each row contains six deterministically selected Light seats and six Shadow seats. Sorting the selected Light seats left-to-right assigns the canonical lane order while interleaving both choruses.",
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


class MixedEnsembleStageRenderer(TexturedStageRenderer):
    def __init__(
        self, timeline: object, width: int, height: int, texture_path: Path
    ) -> None:
        super().__init__(timeline, width, height, texture_path)
        self.seats = build_mixed_ensemble_layout(timeline.stage_order)
        self.layout_sha256 = _layout_hash(self.seats)

    def _build_base(self) -> Image.Image:
        image = super()._build_base()
        draw = ImageDraw.Draw(image)
        radius = max(4, round(6 * self.scale))
        legend_y = round(self.height * 0.245)
        shadow_x = round(self.width * 0.29)
        light_x = round(self.width * 0.56)
        draw.ellipse(
            (
                shadow_x - radius,
                legend_y - radius,
                shadow_x + radius,
                legend_y + radius,
            ),
            fill=(5, 7, 13),
            outline=(48, 56, 72),
            width=max(1, round(self.scale)),
        )
        draw.text(
            (shadow_x + round(14 * self.scale), legend_y - round(8 * self.scale)),
            "SHADOW CHORUS · permanently dark",
            font=self.small_font,
            fill=(117, 127, 145),
        )
        draw.ellipse(
            (
                light_x - radius,
                legend_y - radius,
                light_x + radius,
                legend_y + radius,
            ),
            fill=(255, 238, 183),
            outline=(255, 255, 242),
            width=max(1, round(self.scale)),
        )
        draw.text(
            (light_x + round(14 * self.scale), legend_y - round(8 * self.scale)),
            "LIGHT CHORUS · note + texture",
            font=self.small_font,
            fill=(223, 202, 145),
        )
        lane_labels = ("Sop-L1", "Sop-L2", "Ten-L", "Bass-L", "Alto-L2", "Alto-L1")
        label_y = round(self.height * 0.735)
        for index, label in enumerate(lane_labels):
            x = round(self.width * (0.10 + 0.80 * index / (len(lane_labels) - 1)))
            _centered_text(
                draw,
                (x, label_y),
                label,
                self.small_font,
                (111, 120, 137),
            )
        _centered_text(
            draw,
            (self.width // 2, label_y + round(18 * self.scale)),
            "general Light Chorus progression",
            self.small_font,
            (78, 87, 103),
        )
        return image

    def seat_brightness(
        self,
        seat: EnsembleSeat,
        states: dict[str, bool],
        seconds: float,
    ) -> float:
        if seat.chorus == "shadow":
            return 0.0
        assert seat.lane_key is not None and seat.lane_replica is not None
        return self.engine.brightness(
            seat.lane_key,
            seat.lane_replica,
            states[seat.lane_key],
            seconds,
        )

    def _draw_ensemble(
        self,
        image: Image.Image,
        states: dict[str, bool],
        seconds: float,
    ) -> None:
        radius = max(5, round(8 * self.scale))
        brightness = {
            (seat.row, seat.column): self.seat_brightness(seat, states, seconds)
            for seat in self.seats
        }
        glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        for seat in self.seats:
            if seat.chorus != "light":
                continue
            value = brightness[(seat.row, seat.column)]
            if value < 0.09:
                continue
            x = round(self.width * seat.normalized_x)
            y = round(self.height * seat.normalized_y)
            color = self.engine.point_color(value, seconds, seat.lane_replica or 0)
            glow_radius = round(radius * (2.0 + 2.2 * value))
            glow_draw.ellipse(
                (
                    x - glow_radius,
                    y - glow_radius,
                    x + glow_radius,
                    y + glow_radius,
                ),
                fill=(*color, round(9 + 50 * value)),
            )
        image.paste(Image.alpha_composite(image.convert("RGBA"), glow).convert("RGB"))
        draw = ImageDraw.Draw(image)

        # Dark seats are redrawn after all halos so their centers never illuminate.
        for seat in self.seats:
            if seat.chorus != "shadow":
                continue
            x = round(self.width * seat.normalized_x)
            y = round(self.height * seat.normalized_y)
            draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                fill=(5, 7, 13),
                outline=(48, 56, 72),
                width=max(1, round(self.scale)),
            )
            inner = max(2, radius // 3)
            draw.ellipse(
                (x - inner, y - inner, x + inner, y + inner),
                fill=(2, 3, 7),
            )

        for seat in self.seats:
            if seat.chorus != "light":
                continue
            assert seat.lane_key is not None and seat.lane_replica is not None
            value = brightness[(seat.row, seat.column)]
            x = round(self.width * seat.normalized_x)
            y = round(self.height * seat.normalized_y)
            color = self.engine.point_color(value, seconds, seat.lane_replica)
            fill = mix_color((14, 18, 29), color, value)
            outline = mix_color((65, 73, 89), (255, 252, 229), value)
            draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                fill=fill,
                outline=outline,
                width=max(1, round((1 + value) * self.scale)),
            )
            if value > 0.72:
                inner = max(2, radius // 3)
                inner_fill = mix_color(
                    color, (255, 255, 255), (value - 0.72) / 0.28
                )
                draw.ellipse(
                    (x - inner, y - inner, x + inner, y + inner),
                    fill=inner_fill,
                )
            sparkle = max(
                self.engine.sparkle_strength(
                    seat.lane_key, seat.lane_replica, seconds
                ),
                self.engine.ending_sparkle(
                    seat.lane_key, seat.lane_replica, seconds
                ),
            )
            if sparkle > 0.5:
                ray = round(radius * (1.7 + 1.8 * sparkle))
                ray_color = mix_color(color, (255, 255, 255), sparkle)
                draw.line((x - ray, y, x + ray, y), fill=ray_color, width=1)
                draw.line((x, y - ray, x, y + ray), fill=ray_color, width=1)

    def render_frame(self, elapsed_seconds: Fraction) -> Image.Image:
        self.current_seconds = float(elapsed_seconds)
        image = self.base.copy()
        draw = ImageDraw.Draw(image)
        margin = round(self.width * 0.055)
        annotation, meter = self._score_annotation(elapsed_seconds)
        draw.text(
            (margin, round(self.height * 0.16)),
            _timecode(elapsed_seconds),
            font=self.detail_font,
            fill=(185, 194, 208),
        )
        annotation_box = draw.textbbox((0, 0), annotation, font=self.detail_font)
        draw.text(
            (
                self.width - margin - (annotation_box[2] - annotation_box[0]),
                round(self.height * 0.16),
            ),
            annotation,
            font=self.detail_font,
            fill=(185, 194, 208),
        )
        meter_box = draw.textbbox((0, 0), meter, font=self.small_font)
        draw.text(
            (
                self.width - margin - (meter_box[2] - meter_box[0]),
                round(self.height * 0.205),
            ),
            meter,
            font=self.small_font,
            fill=(103, 113, 131),
        )
        states = self.timeline.lane_states_at_audio_time(elapsed_seconds)
        self._draw_ensemble(image, states, self.current_seconds)

        progress_left = margin
        progress_right = self.width - margin
        progress_y = round(self.height * 0.875)
        draw = ImageDraw.Draw(image)
        draw.line(
            (progress_left, progress_y, progress_right, progress_y),
            fill=(48, 56, 72),
            width=max(2, round(3 * self.scale)),
        )
        ratio = min(
            1.0,
            max(0.0, float(elapsed_seconds / self.timeline.output_duration_seconds)),
        )
        playhead_x = round(progress_left + (progress_right - progress_left) * ratio)
        draw.line(
            (progress_left, progress_y, playhead_x, progress_y),
            fill=(188, 166, 110),
            width=max(2, round(3 * self.scale)),
        )
        playhead_radius = max(3, round(5 * self.scale))
        draw.ellipse(
            (
                playhead_x - playhead_radius,
                progress_y - playhead_radius,
                playhead_x + playhead_radius,
                progress_y + playhead_radius,
            ),
            fill=(255, 238, 191),
        )
        return image


class MixedEnsembleLyricRenderer(LyricStageRenderer):
    def __init__(
        self, timeline: object, width: int, height: int, texture_path: Path
    ) -> None:
        super().__init__(timeline, width, height)
        self.base_renderer = MixedEnsembleStageRenderer(
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
    renderer = MixedEnsembleLyricRenderer(
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
