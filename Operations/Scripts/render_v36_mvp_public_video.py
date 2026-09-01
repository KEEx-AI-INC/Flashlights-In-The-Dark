#!/usr/bin/env python3
"""Render the privacy-safe V36 minimum-viable light-show review.

The renderer uses only anonymous score-derived seat geometry. It visualizes the
nominal 30-primary + 6-hot-reserve plan without simulating failures: 15
right-side Light routes before measure 104, an all-dark handoff, then 12
left-side Shadow routes and 12 right-side Light routes. Every visual emission
is clipped to the assigned V36 lane's sounding intervals.
"""

from __future__ import annotations

import argparse
import json
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageDraw

from build_v36_decorative_light_texture import sha256
from render_v36_decorative_light_review_video import DecorativeEngine, mix_color
from render_v36_four_row_choir_decorative_light_review_video import EnsembleSeat
from render_v36_light_chorus_review_video import (
    DEFAULT_ACTIVITY_PATH,
    _centered_text,
    _font,
    load_review_timeline,
)
from render_v36_lyric_light_review_video import LyricStageRenderer, render_video
from render_v36_strict_note_gated_light_review_video import StrictNoteGatedStageRenderer


SHADOW_TO_TEXTURE_LANE = {
    "soprano_s": "soprano_l1",
    "alto_s": "alto_l1",
    "baritone_s": "bass_l",
}


class ShadowActivity:
    def __init__(self, path: Path) -> None:
        self.path = path.resolve()
        self.sha256 = sha256(self.path)
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("schemaVersion") != "v36-shadow-chorus-note-activity-1":
            raise ValueError("Unexpected Shadow activity schema")
        self.intervals: dict[str, tuple[tuple[Fraction, Fraction, bool], ...]] = {}
        for group in payload.get("groups", []):
            self.intervals[str(group["key"])] = tuple(
                (
                    Fraction(str(item["start"]["cumulativeQuarter"])),
                    Fraction(str(item["end"]["cumulativeQuarter"])),
                    item["state"] == "on",
                )
                for item in group["activityIntervals"]
            )
        if set(self.intervals) != set(SHADOW_TO_TEXTURE_LANE):
            raise ValueError(f"Unexpected Shadow lanes: {sorted(self.intervals)}")

    def state(self, lane_key: str, quarter: Fraction | None) -> bool:
        if quarter is None:
            return False
        for start, end, is_on in self.intervals[lane_key]:
            if start <= quarter < end:
                return is_on
        return False


class PublicMVPStageRenderer(StrictNoteGatedStageRenderer):
    def __init__(
        self,
        timeline: object,
        width: int,
        height: int,
        texture_path: Path,
        topology_path: Path,
        shadow_activity_path: Path,
    ) -> None:
        super().__init__(timeline, width, height, texture_path)
        self.topology_path = topology_path.resolve()
        self.topology_sha256 = sha256(self.topology_path)
        self.topology = json.loads(self.topology_path.read_text(encoding="utf-8"))
        self.shadow_activity = ShadowActivity(shadow_activity_path)
        if self.topology.get("schemaVersion") != "v36-36-phone-topology-1":
            raise ValueError("Unexpected topology schema")
        counts = self.topology.get("counts", {})
        if counts.get("singers") != 59:
            raise ValueError("Expected 59 anonymous singer positions")
        if (
            counts.get("registeredEndpoints") != 36
            or counts.get("primaryEndpoints") != 30
            or counts.get("reserveEndpoints") != 6
        ):
            raise ValueError("Expected 30 primary and 6 reserve endpoints")
        self.phase_boundary_seconds = Fraction(
            str(self.topology["phaseBoundary"]["audioSeconds"])
        )
        self.first_shared_attack_seconds = Fraction(
            str(self.topology["phaseBoundary"]["firstSharedAttackAudioSeconds"])
        )
        self.endpoints_by_position = {
            item["homePositionId"]: item for item in self.topology["endpoints"]
        }
        self.routes_by_position = {
            item["homePositionId"]: item for item in self.topology["routes"]
        }
        self.seats = tuple(
            EnsembleSeat(
                int(item["row"]) - 1,
                int(item["column"]) - 1,
                float(item["normalized_x"]),
                float(item["normalized_y"]),
                str(item["chorus"]),
                item.get("lane_key"),
                None,
            )
            for item in self.topology["seatGeometry"]
        )
        if len(self.seats) != 59:
            raise ValueError("Topology seat geometry is incomplete")
        self.phone_font = _font(max(7, round(8 * self.scale)), bold=True)

    @staticmethod
    def _position_id(seat: EnsembleSeat) -> str:
        return f"r{seat.row + 1}c{seat.column + 1}"

    def _phase_key(self, seconds: Fraction) -> str | None:
        if seconds < self.phase_boundary_seconds:
            return "beforeM104"
        if seconds < self.first_shared_attack_seconds:
            return None
        return "fromM104"

    def _route_state(
        self,
        route: dict,
        phase_key: str | None,
        light_states: dict[str, bool],
        quarter: Fraction | None,
    ) -> tuple[bool, str | None, int | None]:
        if phase_key is None:
            return False, None, None
        phase = route["phases"][phase_key]
        if not phase["artisticallyEligible"]:
            return False, None, None
        lane_key = str(phase["laneKey"])
        replica = int(phase["laneReplica"])
        if route["side"] == "left":
            return self.shadow_activity.state(lane_key, quarter), lane_key, replica
        return bool(light_states.get(lane_key, False)), lane_key, replica

    @staticmethod
    def _texture_lane(lane_key: str) -> str:
        return SHADOW_TO_TEXTURE_LANE.get(lane_key, lane_key)

    def _build_base(self) -> Image.Image:
        image = super()._build_base()
        draw = ImageDraw.Draw(image)
        margin = round(self.width * 0.055)
        draw.rectangle(
            (
                margin - 4,
                round(self.height * 0.045),
                round(self.width * 0.91),
                round(self.height * 0.115),
            ),
            fill=(4, 6, 15),
        )
        draw.text(
            (margin, round(self.height * 0.055)),
            "FLASHLIGHTS IN THE DARK · V36 · MINIMUM-VIABLE LIGHT-SHOW DRAFT",
            font=self.title_font,
            fill=(230, 235, 243),
        )
        return image

    def _draw_phone_marker(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        radius: int,
        role: str,
        active: bool,
    ) -> None:
        outline = (59, 179, 205) if role == "reserve" else (93, 112, 145)
        if active:
            outline = (255, 247, 215)
        inset = max(2, radius // 3)
        draw.rounded_rectangle(
            (x - inset, y - radius - 5, x + inset, y - radius + 3),
            radius=1,
            fill=(5, 9, 17),
            outline=outline,
            width=1,
        )
        if role == "reserve":
            _centered_text(draw, (x, y - radius - 16), "R", self.phone_font, outline)

    def _draw_ensemble(
        self,
        image: Image.Image,
        light_states: dict[str, bool],
        seconds: float,
    ) -> None:
        elapsed = Fraction(str(seconds))
        quarter = self.timeline.quarter_at_audio_time(elapsed)
        phase_key = self._phase_key(elapsed)
        radius = max(5, round(8 * self.scale))
        seat_values: dict[str, tuple[float, str | None, int | None]] = {}
        for seat in self.seats:
            position_id = self._position_id(seat)
            endpoint = self.endpoints_by_position.get(position_id)
            route = self.routes_by_position.get(position_id)
            if endpoint is None or endpoint["role"] == "reserve" or route is None:
                seat_values[position_id] = (0.0, None, None)
                continue
            sounding, lane_key, replica = self._route_state(
                route, phase_key, light_states, quarter
            )
            if not sounding or lane_key is None or replica is None:
                seat_values[position_id] = (0.0, lane_key, replica)
                continue
            value = self.engine.brightness(
                self._texture_lane(lane_key), replica, True, seconds
            )
            seat_values[position_id] = (value, lane_key, replica)

        glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        for seat in self.seats:
            position_id = self._position_id(seat)
            value, lane_key, replica = seat_values[position_id]
            if value < 0.09 or lane_key is None or replica is None:
                continue
            x = round(self.width * seat.normalized_x)
            y = round(self.height * seat.normalized_y)
            color = self.engine.point_color(value, seconds, replica)
            glow_radius = round(radius * (2.0 + 2.2 * value))
            glow_draw.ellipse(
                (x - glow_radius, y - glow_radius, x + glow_radius, y + glow_radius),
                fill=(*color, round(9 + 50 * value)),
            )
        image.paste(Image.alpha_composite(image.convert("RGBA"), glow).convert("RGB"))
        draw = ImageDraw.Draw(image)

        for seat in self.seats:
            position_id = self._position_id(seat)
            endpoint = self.endpoints_by_position.get(position_id)
            value, lane_key, replica = seat_values[position_id]
            x = round(self.width * seat.normalized_x)
            y = round(self.height * seat.normalized_y)
            if value > 0 and lane_key is not None and replica is not None:
                color = self.engine.point_color(value, seconds, replica)
                fill = mix_color((14, 18, 29), color, value)
                outline = mix_color((65, 73, 89), (255, 252, 229), value)
            else:
                fill = (5, 7, 13)
                if endpoint is None:
                    outline = (34, 40, 54)
                elif endpoint["role"] == "reserve":
                    outline = (43, 113, 132)
                else:
                    outline = (63, 72, 90)
            draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                fill=fill,
                outline=outline,
                width=max(1, round((1 + value) * self.scale)),
            )
            if value > 0.72 and replica is not None:
                color = self.engine.point_color(value, seconds, replica)
                inner = max(2, radius // 3)
                draw.ellipse(
                    (x - inner, y - inner, x + inner, y + inner),
                    fill=mix_color(color, (255, 255, 255), (value - 0.72) / 0.28),
                )
            if value > 0.5 and lane_key is not None and replica is not None:
                sparkle = max(
                    self.engine.sparkle_strength(
                        self._texture_lane(lane_key), replica, seconds
                    ),
                    self.engine.ending_sparkle(
                        self._texture_lane(lane_key), replica, seconds
                    ),
                )
                if sparkle > 0.5:
                    ray = round(radius * (1.7 + 1.8 * sparkle))
                    ray_color = mix_color(
                        self.engine.point_color(value, seconds, replica),
                        (255, 255, 255),
                        sparkle,
                    )
                    draw.line((x - ray, y, x + ray, y), fill=ray_color, width=1)
                    draw.line((x, y - ray, x, y + ray), fill=ray_color, width=1)
            if endpoint is not None:
                self._draw_phone_marker(
                    draw, x, y, radius, str(endpoint["role"]), value > 0
                )

        conductor_x = round(self.width * 0.50)
        conductor_y = round(self.height * 0.705)
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
        _centered_text(
            draw,
            (conductor_x, conductor_y + conductor_radius + 4),
            "CONDUCTOR",
            self.phone_font,
            (148, 126, 73),
        )
        operator_x = round(self.width * 0.59)
        operator_y = round(self.height * 0.705)
        laptop_w, laptop_h = round(25 * self.scale), round(15 * self.scale)
        draw.rounded_rectangle(
            (
                operator_x - laptop_w,
                operator_y - laptop_h,
                operator_x + laptop_w,
                operator_y + laptop_h,
            ),
            radius=3,
            fill=(10, 17, 28),
            outline=(81, 169, 196),
            width=2,
        )
        draw.line(
            (
                operator_x - laptop_w - 4,
                operator_y + laptop_h + 3,
                operator_x + laptop_w + 4,
                operator_y + laptop_h + 3,
            ),
            fill=(81, 169, 196),
            width=2,
        )
        _centered_text(
            draw,
            (operator_x, operator_y + laptop_h + 5),
            "TECH OPERATOR · MacBook control",
            self.phone_font,
            (81, 169, 196),
        )


class PublicMVPLyricRenderer(LyricStageRenderer):
    def __init__(
        self,
        timeline: object,
        width: int,
        height: int,
        texture_path: Path,
        topology_path: Path,
        shadow_activity_path: Path,
    ) -> None:
        super().__init__(timeline, width, height)
        self.base_renderer = PublicMVPStageRenderer(
            timeline,
            width,
            height,
            texture_path,
            topology_path,
            shadow_activity_path,
        )
        self.engine: DecorativeEngine = self.base_renderer.engine

    def render_frame(self, elapsed_seconds: Fraction) -> Image.Image:
        image = self.base_renderer.render_frame(elapsed_seconds)
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        panels = {"shadow": (42, 548, 627, 665), "light": (653, 548, 1238, 665)}
        for box in panels.values():
            odraw.rounded_rectangle(
                box,
                radius=10,
                fill=(10, 13, 23, 232),
                outline=(68, 78, 98, 225),
                width=1,
            )
        odraw.rectangle(
            (0, 666, self.width, self.height),
            fill=(5, 8, 17, 246),
            outline=(48, 58, 76, 255),
            width=1,
        )
        image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(image)
        draw.text((62, 555), "SHADOW CHORUS", font=self.title_font, fill=(224, 229, 239))
        draw.text((673, 555), "LIGHT CHORUS", font=self.title_font, fill=(255, 224, 145))
        row_y = {"Soprano": 583, "Alto": 613, "Baritone": 643, "Tenor/Bass": 643}
        quarter = self.timeline.quarter_at_audio_time(elapsed_seconds)
        for row, starts, segments in self.row_data:
            x_label, x_text, max_width = (
                (62, 174, 430) if row.module == "shadow" else (673, 790, 425)
            )
            y = row_y[row.label]
            draw.text((x_label, y), row.label, font=self.label_font, fill=(165, 175, 192))
            text = self._active_text(starts, segments, quarter)
            if text:
                display, font = self._fit_text(draw, text, max_width)
                draw.text(
                    (x_text, y - 3),
                    display,
                    font=font,
                    fill=(242, 245, 250)
                    if row.module == "shadow"
                    else (255, 244, 208),
                )
        key_font = _font(
            max(8, round(10 * min(self.width / 1280, self.height / 720))),
            bold=True,
        )
        phase = self.base_renderer._phase_key(elapsed_seconds)
        phase_text = (
            "PRE-M104 · 15 RIGHT-SIDE LIGHT ROUTES"
            if phase == "beforeM104"
            else "M104 HANDOFF · ALL PHONES DARK"
            if phase is None
            else "POST-M104 · 12 LEFT SHADOW + 12 RIGHT LIGHT ROUTES"
        )
        _centered_text(
            draw,
            (self.width // 2, 671),
            f"{phase_text}    PHONE □ · primary    R · connected hot reserve, normally dark",
            key_font,
            (171, 181, 197),
        )
        _centered_text(
            draw,
            (self.width // 2, 696),
            "STRICT NOTE GATE · light and texture only while the assigned V36 chorus lane is sounding · review only",
            key_font,
            (132, 143, 160),
        )
        return image


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--shadow-activity", type=Path, required=True)
    parser.add_argument("--activity", type=Path, default=DEFAULT_ACTIVITY_PATH)
    parser.add_argument("--texture", type=Path, required=True)
    parser.add_argument("--score-origin-seconds", type=Fraction, required=True)
    parser.add_argument("--duration-seconds", type=Fraction, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preview-output", type=Path)
    parser.add_argument("--preview-seconds", type=Fraction, default=Fraction(0))
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
    renderer = PublicMVPLyricRenderer(
        timeline,
        args.width,
        args.height,
        args.texture,
        args.topology,
        args.shadow_activity,
    )
    base = renderer.base_renderer
    result = {
        "runtimeEligible": False,
        "privacySafe": True,
        "singerCount": 59,
        "registeredPhoneCount": 36,
        "primaryPhoneCount": 30,
        "hotReserveCount": 6,
        "topologySha256": base.topology_sha256,
        "topologyManifestSha256": base.topology["manifestSha256"],
        "lightActivitySha256": timeline.activity_sha256,
        "shadowActivitySha256": base.shadow_activity.sha256,
        "measure104BoundarySeconds": str(base.phase_boundary_seconds),
        "firstPostHandoffAttackSeconds": str(base.first_shared_attack_seconds),
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
    if not args.preview_output and not args.output:
        raise ValueError("Supply --preview-output and/or --output")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
