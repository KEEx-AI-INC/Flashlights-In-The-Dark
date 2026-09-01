#!/usr/bin/env python3
"""Render the V36 note-responsive light show with deterministic decoration."""

from __future__ import annotations

import argparse
import bisect
import json
import math
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageDraw

from build_v36_decorative_light_texture import DEFAULT_OUTPUT, SCHEMA, sha256
from render_v36_light_chorus_review_video import (
    DEFAULT_ACTIVITY_PATH,
    StageRenderer,
    _centered_text,
    load_review_timeline,
)
from render_v36_lyric_light_review_video import LyricStageRenderer, render_video


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return min(high, max(low, value))


def smoothstep(value: float) -> float:
    value = clamp(value)
    return value * value * (3 - 2 * value)


def mix(a: float, b: float, amount: float) -> float:
    return a + (b - a) * amount


def mix_color(
    first: tuple[int, int, int], second: tuple[int, int, int], amount: float
) -> tuple[int, int, int]:
    return tuple(round(mix(a, b, clamp(amount))) for a, b in zip(first, second))


def hash01(seed: int, index: int) -> float:
    value = (seed ^ ((index + 0x9E3779B9) & 0xFFFFFFFF)) & 0xFFFFFFFF
    value ^= value >> 16
    value = (value * 0x7FEB352D) & 0xFFFFFFFF
    value ^= value >> 15
    value = (value * 0x846CA68B) & 0xFFFFFFFF
    value ^= value >> 16
    return value / 0xFFFFFFFF


def value_noise(seconds: float, frequency: float, seed: int) -> float:
    position = seconds * frequency
    left = math.floor(position)
    amount = smoothstep(position - left)
    return mix(hash01(seed, left), hash01(seed, left + 1), amount)


class DecorativeEngine:
    def __init__(self, texture_path: Path, timeline: object) -> None:
        self.path = texture_path.resolve()
        self.payload = json.loads(self.path.read_text(encoding="utf-8"))
        if self.payload.get("schemaVersion") != SCHEMA:
            raise ValueError("Unexpected decorative texture schema")
        if self.payload.get("status") != "authoring-source-not-runtime-ready":
            raise ValueError("Decorative texture must remain non-runtime")
        source = self.payload["sources"]["noteActivity"]
        if source["sha256"] != timeline.activity_sha256:
            raise ValueError("Texture and V36 note activity checksums disagree")
        lane_keys = tuple(self.payload["topologyPolicy"]["logicalLaneKeys"])
        if lane_keys != timeline.stage_order:
            raise ValueError("Texture lane order disagrees with V36 stage order")
        self.timeline = timeline
        self.score_origin = float(timeline.score_origin_seconds)
        self.seed = int(self.payload["randomPolicy"]["seed"])
        envelope = self.payload["dynamicsEnvelope"]
        self.envelope_times = [int(item["timeMs"]) / 1000 for item in envelope]
        self.perturbation = [float(item["perturbationMix01"]) for item in envelope]
        self.loudness = [float(item["loudness01"]) for item in envelope]
        sections = self.payload["specialSections"]
        self.glitter_start = float(Fraction(sections["glitterApproachTo104"]["startSeconds"]))
        self.glitter_end = float(Fraction(sections["glitterApproachTo104"]["endSeconds"]))
        self.unified_start = float(Fraction(sections["measure104UnifiedGlow"]["startSeconds"]))
        self.unified_attack = float(
            Fraction(sections["measure104UnifiedGlow"]["firstSharedAttackSeconds"])
        )
        self.unified_end = float(Fraction(sections["measure104UnifiedGlow"]["endSeconds"]))
        self.unified_cycle = float(sections["measure104UnifiedGlow"]["cycleSeconds"])
        self.unified_minimum = float(
            sections["measure104UnifiedGlow"]["minimumBrightness"]
        )
        self.unified_maximum = float(
            sections["measure104UnifiedGlow"]["maximumBrightness"]
        )
        ending = sections["endingGlimmer"]
        self.ending_start = float(Fraction(ending["seedStartSeconds"]))
        self.chandelier_start = float(Fraction(ending["chandelierDirectionSeconds"]))
        self.ending_swell_start = float(Fraction(ending["swellStartSeconds"]))
        self.ending_swell_peak = float(Fraction(ending["swellPeakSeconds"]))
        self.ending_diminish = float(Fraction(ending["diminishToPppSeconds"]))
        self.score_end = float(Fraction(ending["scoreEndSeconds"]))
        self.tail_end = float(Fraction(ending["tailFadeEndSeconds"]))
        self.speed_bands = self.payload["randomPolicy"]["differentSpeedBandsHz"]
        self.lane_index = {key: index for index, key in enumerate(lane_keys)}
        self.params: dict[tuple[str, int], dict[str, float | int]] = {}

    def _interpolate(self, values: list[float], seconds: float) -> float:
        if seconds <= self.envelope_times[0]:
            return values[0]
        if seconds >= self.envelope_times[-1]:
            return values[-1]
        index = bisect.bisect_right(self.envelope_times, seconds) - 1
        left_time = self.envelope_times[index]
        right_time = self.envelope_times[index + 1]
        amount = (seconds - left_time) / (right_time - left_time)
        return mix(values[index], values[index + 1], amount)

    def perturbation_at(self, seconds: float) -> float:
        return self._interpolate(self.perturbation, seconds)

    def loudness_at(self, seconds: float) -> float:
        return self._interpolate(self.loudness, seconds)

    def glitter_strength(self, seconds: float) -> float:
        if seconds < self.glitter_start or seconds >= self.glitter_end:
            return 0.0
        progress = (seconds - self.glitter_start) / (self.glitter_end - self.glitter_start)
        return smoothstep(progress) ** 1.4

    def unified_glow(self, seconds: float) -> float | None:
        if not self.unified_start <= seconds < self.unified_end:
            return None
        if seconds <= self.unified_attack:
            progress = (seconds - self.unified_start) / max(
                0.001, self.unified_attack - self.unified_start
            )
            return mix(
                self.unified_minimum,
                self.unified_maximum,
                smoothstep(progress),
            )
        phase = ((seconds - self.unified_attack) / self.unified_cycle) % 1.0
        breath = 0.5 + 0.5 * math.cos(2 * math.pi * phase)
        return mix(self.unified_minimum, self.unified_maximum, breath)

    def _band_value(self, band: str, unit: float) -> float:
        low, high = (float(item) for item in self.speed_bands[band])
        return mix(low, high, unit)

    def _point_params(self, lane_key: str, replica: int) -> dict[str, float | int]:
        key = (lane_key, replica)
        if key in self.params:
            return self.params[key]
        lane = self.lane_index[lane_key]
        base = lane * 1009 + replica * 9176
        params: dict[str, float | int] = {
            "seed": self.seed + lane * 65537 + replica * 4099,
            "slowHz": self._band_value("slowGlow", hash01(self.seed, base + 1)),
            "mediumHz": self._band_value("mediumFlutter", hash01(self.seed, base + 2)),
            "fastHz": self._band_value("fastFlicker", hash01(self.seed, base + 3)),
            "glitterHz": self._band_value("glitter", hash01(self.seed, base + 4)),
            "endingHz": self._band_value("endingPinprick", hash01(self.seed, base + 5)),
            "phase": hash01(self.seed, base + 6) * 2 * math.pi,
        }
        self.params[key] = params
        return params

    def sparkle_strength(self, lane_key: str, replica: int, seconds: float) -> float:
        approach = self.glitter_strength(seconds)
        if approach <= 0:
            return 0.0
        params = self._point_params(lane_key, replica)
        glitter = value_noise(
            seconds, float(params["glitterHz"]), int(params["seed"]) + 47
        )
        threshold = mix(0.992, 0.72, approach)
        return clamp((glitter - threshold) / max(0.001, 1 - threshold)) * approach

    def ending_swell(self, seconds: float) -> float:
        if seconds < self.ending_swell_start:
            return 0.0
        if seconds <= self.ending_swell_peak:
            return smoothstep(
                (seconds - self.ending_swell_start)
                / max(0.001, self.ending_swell_peak - self.ending_swell_start)
            )
        if seconds < self.ending_diminish:
            return 1.0 - smoothstep(
                (seconds - self.ending_swell_peak)
                / max(0.001, self.ending_diminish - self.ending_swell_peak)
            )
        return 0.0

    def ending_sparkle(self, lane_key: str, replica: int, seconds: float) -> float:
        if not self.ending_start <= seconds < self.tail_end:
            return 0.0
        params = self._point_params(lane_key, replica)
        entry = smoothstep(
            (seconds - self.ending_start)
            / max(0.001, self.chandelier_start - self.ending_start)
        )
        swell = self.ending_swell(seconds)
        noise = value_noise(
            seconds, float(params["endingHz"]), int(params["seed"]) + 83
        )
        threshold = mix(0.988, 0.88, 0.45 * entry + 0.55 * swell)
        return clamp((noise - threshold) / max(0.001, 1 - threshold))

    def brightness(
        self, lane_key: str, replica: int, note_on: bool, seconds: float
    ) -> float:
        if seconds < self.score_origin or seconds >= self.tail_end:
            return 0.0
        unified = self.unified_glow(seconds)
        if unified is not None:
            return unified
        params = self._point_params(lane_key, replica)
        seed = int(params["seed"])
        slow = 0.5 + 0.5 * math.sin(
            2 * math.pi * float(params["slowHz"]) * seconds + float(params["phase"])
        )
        medium = value_noise(seconds, float(params["mediumHz"]), seed + 11)
        fast = value_noise(seconds, float(params["fastHz"]), seed + 29)
        texture = clamp(0.06 + 0.38 * slow + 0.30 * medium + 0.30 * fast**2)
        direct = 1.0 if note_on else 0.0
        perturbation = self.perturbation_at(seconds)
        value = mix(direct, texture, perturbation)

        approach = self.glitter_strength(seconds)
        if approach:
            spark = self.sparkle_strength(lane_key, replica, seconds)
            loud_cap = mix(0.38, 0.11, self.loudness_at(seconds))
            value = mix(value, max(value, spark), approach * loud_cap)
            value = clamp(value + approach * loud_cap * 0.08 * slow)

        if seconds >= self.ending_start:
            if seconds >= self.tail_end:
                return 0.0
            entry = smoothstep(
                (seconds - self.ending_start)
                / max(0.001, self.chandelier_start - self.ending_start)
            )
            tail_fade = (
                1.0
                if seconds <= self.score_end
                else clamp((self.tail_end - seconds) / (self.tail_end - self.score_end))
            )
            swell = self.ending_swell(seconds)
            calm = 0.08 + (0.18 + 0.16 * swell) * slow
            glimmer = self.ending_sparkle(lane_key, replica, seconds)
            dazzling = max(calm, glimmer * mix(0.72, 0.98, swell))
            override_mix = mix(0.18, 0.78, entry)
            value = mix(value, dazzling, override_mix) * tail_fade
        return clamp(value)

    def point_color(self, brightness: float, seconds: float, replica: int) -> tuple[int, int, int]:
        normal = (255, 248, 214)
        approach = self.glitter_strength(seconds)
        if approach:
            return mix_color(normal, (255, 216, 116), approach * (0.55 + 0.45 * brightness))
        if self.unified_start <= seconds < self.unified_end:
            return mix_color((255, 173, 72), (255, 238, 174), brightness)
        if seconds >= self.ending_start:
            crystalline = (255, 255, 240) if replica % 3 == 0 else (255, 222, 138)
            return mix_color((225, 195, 125), crystalline, brightness)
        return normal


class TexturedStageRenderer(StageRenderer):
    def __init__(self, timeline: object, width: int, height: int, texture_path: Path) -> None:
        super().__init__(timeline, width, height)
        self.engine = DecorativeEngine(texture_path, timeline)
        self.current_seconds = 0.0
        self.label_to_key = {lane.label: lane.key for lane in timeline.lanes}

    def _build_base(self) -> Image.Image:
        image = super()._build_base()
        draw = ImageDraw.Draw(image)
        top = round(self.height * 0.895)
        bottom = round(self.height * 0.955)
        draw.rectangle((0, top, self.width, bottom), fill=(8, 11, 24))
        _centered_text(
            draw,
            (self.width // 2, round(self.height * 0.915)),
            "note-responsive foundation · deterministic decorative texture · review only",
            self.small_font,
            (128, 138, 154),
        )
        return image

    def render_frame(self, elapsed_seconds: Fraction) -> Image.Image:
        self.current_seconds = float(elapsed_seconds)
        return super().render_frame(elapsed_seconds)

    def _draw_light_bank(
        self,
        image: Image.Image,
        center: tuple[int, int],
        label: str,
        on: bool,
    ) -> None:
        draw = ImageDraw.Draw(image)
        radius = max(5, round(10 * self.scale))
        spread_x = max(18, round(30 * self.scale))
        spread_y = max(16, round(25 * self.scale))
        point_offsets = (
            (-spread_x, -spread_y),
            (0, -spread_y),
            (spread_x, -spread_y),
            (-round(spread_x * 1.5), spread_y),
            (-round(spread_x * 0.5), spread_y),
            (round(spread_x * 0.5), spread_y),
            (round(spread_x * 1.5), spread_y),
        )
        lane_key = self.label_to_key[label]
        brightnesses = [
            self.engine.brightness(lane_key, index, on, self.current_seconds)
            for index in range(len(point_offsets))
        ]
        glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        for index, ((dx, dy), brightness) in enumerate(zip(point_offsets, brightnesses)):
            if brightness < 0.09:
                continue
            x, y = center[0] + dx, center[1] + dy
            glow_radius = round(radius * (2.2 + brightness * 2.2))
            color = self.engine.point_color(brightness, self.current_seconds, index)
            glow_draw.ellipse(
                (x - glow_radius, y - glow_radius, x + glow_radius, y + glow_radius),
                fill=(*color, round(10 + 54 * brightness)),
            )
        image.paste(Image.alpha_composite(image.convert("RGBA"), glow).convert("RGB"))
        draw = ImageDraw.Draw(image)
        for index, ((dx, dy), brightness) in enumerate(zip(point_offsets, brightnesses)):
            x, y = center[0] + dx, center[1] + dy
            color = self.engine.point_color(brightness, self.current_seconds, index)
            fill = mix_color((14, 18, 29), color, brightness)
            outline = mix_color((62, 70, 86), (255, 252, 229), brightness)
            draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                fill=fill,
                outline=outline,
                width=max(1, round((1 + brightness) * self.scale)),
            )
            if brightness > 0.72:
                inner = max(2, radius // 3)
                inner_fill = mix_color(color, (255, 255, 255), (brightness - 0.72) / 0.28)
                draw.ellipse(
                    (x - inner, y - inner, x + inner, y + inner), fill=inner_fill
                )
            sparkle = max(
                self.engine.sparkle_strength(
                    lane_key, index, self.current_seconds
                ),
                self.engine.ending_sparkle(
                    lane_key, index, self.current_seconds
                ),
            )
            if sparkle > 0.5:
                ray = round(radius * (1.6 + 1.8 * sparkle))
                ray_color = mix_color(color, (255, 255, 255), sparkle)
                draw.line((x - ray, y, x + ray, y), fill=ray_color, width=1)
                draw.line((x, y - ray, x, y + ray), fill=ray_color, width=1)
        label_y = center[1] + spread_y + radius + round(12 * self.scale)
        _centered_text(draw, (center[0], label_y), label, self.label_font, (221, 226, 235))
        average = sum(brightnesses) / len(brightnesses)
        _centered_text(
            draw,
            (center[0], label_y + round(27 * self.scale)),
            f"texture · {average:.0%}",
            self.small_font,
            (255, 221, 140) if average > 0.55 else (112, 122, 140),
        )


class DecorativeLyricRenderer(LyricStageRenderer):
    def __init__(
        self, timeline: object, width: int, height: int, texture_path: Path
    ) -> None:
        super().__init__(timeline, width, height)
        self.base_renderer = TexturedStageRenderer(
            timeline, width, height, texture_path
        )
        self.engine = self.base_renderer.engine


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activity", type=Path, default=DEFAULT_ACTIVITY_PATH)
    parser.add_argument("--texture", type=Path, default=DEFAULT_OUTPUT)
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
    renderer = DecorativeLyricRenderer(
        timeline, args.width, args.height, args.texture
    )
    result: dict[str, object] = {
        "texturePath": str(args.texture.resolve()),
        "textureSha256": sha256(args.texture),
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
            "loudness01": renderer.engine.loudness_at(float(args.preview_seconds)),
            "perturbation01": renderer.engine.perturbation_at(float(args.preview_seconds)),
            "glitterStrength01": renderer.engine.glitter_strength(float(args.preview_seconds)),
            "unifiedGlow01": renderer.engine.unified_glow(float(args.preview_seconds)),
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
