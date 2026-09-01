#!/usr/bin/env python3
"""Render the shell-fitted V36 choir with strictly note-gated decoration."""

from __future__ import annotations

import argparse
import json
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageDraw

from build_v36_decorative_light_texture import DEFAULT_OUTPUT, sha256
from render_v36_decorative_light_review_video import DecorativeEngine, mix_color
from render_v36_four_row_choir_decorative_light_review_video import EnsembleSeat
from render_v36_four_row_choir_decorative_light_review_video import (
    CONDUCTOR_X,
    CONDUCTOR_Y,
)
from render_v36_light_chorus_review_video import (
    DEFAULT_ACTIVITY_PATH,
    _centered_text,
    load_review_timeline,
)
from render_v36_lyric_light_review_video import render_video
from render_v36_shell_fitted_four_row_choir_review_video import (
    REPO_ROOT,
    ShellFittedFourRowChoirLyricRenderer,
    ShellFittedFourRowChoirStageRenderer,
)


GATING_SCHEMA = "v36-strict-note-gated-decoration-policy-1"


class StrictNoteGatedStageRenderer(ShellFittedFourRowChoirStageRenderer):
    """Allow visual energy only while the seat's logical lane is sounding."""

    def _build_base(self) -> Image.Image:
        image = super()._build_base()
        draw = ImageDraw.Draw(image)
        footer_top = round(self.height * 0.895)
        footer_bottom = round(self.height * 0.955)
        draw.rectangle(
            (0, footer_top, self.width, footer_bottom), fill=(8, 11, 24)
        )
        _centered_text(
            draw,
            (self.width // 2, round(self.height * 0.915)),
            "strict note gate · texture only inside sounding intervals · review only",
            self.small_font,
            (128, 138, 154),
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
        if not states[seat.lane_key]:
            return 0.0
        return self.engine.brightness(
            seat.lane_key,
            seat.lane_replica,
            True,
            seconds,
        )

    def seat_sparkle(
        self,
        seat: EnsembleSeat,
        states: dict[str, bool],
        seconds: float,
    ) -> float:
        if seat.chorus == "shadow":
            return 0.0
        assert seat.lane_key is not None and seat.lane_replica is not None
        if not states[seat.lane_key]:
            return 0.0
        return max(
            self.engine.sparkle_strength(
                seat.lane_key, seat.lane_replica, seconds
            ),
            self.engine.ending_sparkle(
                seat.lane_key, seat.lane_replica, seconds
            ),
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
            assert seat.lane_replica is not None
            x = round(self.width * seat.normalized_x)
            y = round(self.height * seat.normalized_y)
            color = self.engine.point_color(value, seconds, seat.lane_replica)
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
            sparkle = self.seat_sparkle(seat, states, seconds)
            if sparkle > 0.5:
                ray = round(radius * (1.7 + 1.8 * sparkle))
                ray_color = mix_color(color, (255, 255, 255), sparkle)
                draw.line((x - ray, y, x + ray, y), fill=ray_color, width=1)
                draw.line((x, y - ray, x, y + ray), fill=ray_color, width=1)

        conductor_x = round(self.width * CONDUCTOR_X)
        conductor_y = round(self.height * CONDUCTOR_Y)
        conductor_radius = max(7, round(10 * self.scale))
        draw.ellipse(
            (
                conductor_x - conductor_radius,
                conductor_y - conductor_radius,
                conductor_x + conductor_radius,
                conductor_y + conductor_radius,
            ),
            fill=(7, 10, 17),
            outline=(148, 126, 73),
            width=max(1, round(2 * self.scale)),
        )
        conductor_inner = max(2, conductor_radius // 3)
        draw.ellipse(
            (
                conductor_x - conductor_inner,
                conductor_y - conductor_inner,
                conductor_x + conductor_inner,
                conductor_y + conductor_inner,
            ),
            fill=(3, 5, 9),
        )
        _centered_text(
            draw,
            (
                conductor_x,
                conductor_y + conductor_radius + round(5 * self.scale),
            ),
            "CONDUCTOR",
            self.small_font,
            (148, 126, 73),
        )


class StrictNoteGatedLyricRenderer(ShellFittedFourRowChoirLyricRenderer):
    def __init__(
        self, timeline: object, width: int, height: int, texture_path: Path
    ) -> None:
        super().__init__(timeline, width, height, texture_path)
        self.base_renderer = StrictNoteGatedStageRenderer(
            timeline, width, height, texture_path
        )
        self.engine: DecorativeEngine = self.base_renderer.engine


def gating_payload(renderer: StrictNoteGatedStageRenderer) -> dict[str, object]:
    return {
        "schemaVersion": GATING_SCHEMA,
        "artifactType": "review-only-strict-note-gating-policy",
        "status": "presentation-policy-not-runtime-topology",
        "runtimeEligible": False,
        "sourceActivity": {
            "path": str(renderer.timeline.activity_path.relative_to(REPO_ROOT)),
            "activitySha256": renderer.timeline.activity_sha256,
            "intervalCount": sum(
                len(lane.intervals) for lane in renderer.timeline.lanes
            ),
        },
        "logicalLaneKeys": list(renderer.timeline.stage_order),
        "gateRule": "A Light seat emits brightness, halo, and sparkle only while its mapped logical lane's V36 note activity is true.",
        "inactiveLaneOutput": {
            "brightness": 0.0,
            "halo": False,
            "sparkle": False,
        },
        "activeLaneDecoration": "Existing deterministic flicker, glitter, variable-speed glow, m104 behavior, and ending glimmer are retained but clipped to the lane's sounding intervals.",
        "intervalBoundaryRule": "start-inclusive and end-exclusive, inherited from the canonical V36 activity timeline",
        "layoutSha256": renderer.layout_sha256,
        "physicalTopologyEncoded": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activity", type=Path, default=DEFAULT_ACTIVITY_PATH)
    parser.add_argument("--texture", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--score-origin-seconds", type=Fraction, required=True)
    parser.add_argument("--duration-seconds", type=Fraction, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preview-output", type=Path)
    parser.add_argument("--preview-seconds", type=Fraction, default=Fraction(0))
    parser.add_argument("--policy-output", type=Path)
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
    renderer = StrictNoteGatedLyricRenderer(
        timeline, args.width, args.height, args.texture
    )
    result: dict[str, object] = {
        "texturePath": str(args.texture.resolve()),
        "textureSha256": sha256(args.texture),
        "layoutSha256": renderer.base_renderer.layout_sha256,
        "gatingSchema": GATING_SCHEMA,
    }
    if args.policy_output:
        if args.policy_output.exists():
            raise FileExistsError(
                f"Refusing to overwrite policy artifact: {args.policy_output}"
            )
        args.policy_output.parent.mkdir(parents=True, exist_ok=True)
        args.policy_output.write_text(
            json.dumps(gating_payload(renderer.base_renderer), indent=2) + "\n",
            encoding="utf-8",
        )
        result["policy"] = {
            "path": str(args.policy_output.resolve()),
            "sha256": sha256(args.policy_output),
        }
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
    if not args.policy_output and not args.preview_output and not args.output:
        raise ValueError("Supply --policy-output, --preview-output, and/or --output")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
