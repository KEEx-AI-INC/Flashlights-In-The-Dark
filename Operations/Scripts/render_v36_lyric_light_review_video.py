#!/usr/bin/env python3
"""Render the V36 light review with score-synchronous chorus lyric modules."""

from __future__ import annotations

import argparse
import bisect
import json
import math
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageDraw

from build_v36_review_lyrics import ROWS, extract_lyric_spans, row_segments, sha256
from render_v36_light_chorus_review_video import (
    DEFAULT_ACTIVITY_PATH,
    StageRenderer,
    _font,
    load_review_timeline,
    probe_video,
)


class LyricStageRenderer:
    def __init__(self, timeline: object, width: int, height: int) -> None:
        self.timeline = timeline
        self.width = width
        self.height = height
        self.base_renderer = StageRenderer(timeline, width, height)
        scale = min(width / 1280.0, height / 720.0)
        self.title_font = _font(max(14, round(19 * scale)), bold=True)
        self.label_font = _font(max(13, round(17 * scale)), bold=True)
        self.lyric_font = _font(max(15, round(21 * scale)), bold=True)
        spans = extract_lyric_spans(timeline.score_path, timeline.measures)
        self.row_data: list[tuple[object, list[Fraction], list[tuple[Fraction, Fraction, str]]]] = []
        for row in ROWS:
            segments = row_segments(row, spans)
            self.row_data.append((row, [item[0] for item in segments], segments))

    def _active_text(self, starts: list[Fraction], segments: list[tuple[Fraction, Fraction, str]], quarter: Fraction | None) -> str:
        if quarter is None or not starts:
            return ""
        index = bisect.bisect_right(starts, quarter) - 1
        if index < 0:
            return ""
        start, end, text = segments[index]
        return text if start <= quarter < end else ""

    def _fit_text(self, draw: ImageDraw.ImageDraw, text: str, max_width: int):
        font = self.lyric_font
        if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
            return text, font
        smaller = _font(max(13, round(17 * min(self.width / 1280.0, self.height / 720.0))), bold=True)
        if draw.textbbox((0, 0), text, font=smaller)[2] <= max_width:
            return text, smaller
        shortened = text
        while shortened and draw.textbbox((0, 0), shortened + "…", font=smaller)[2] > max_width:
            shortened = shortened[:-1]
        return shortened.rstrip() + "…", smaller

    def render_frame(self, elapsed_seconds: Fraction) -> Image.Image:
        image = self.base_renderer.render_frame(elapsed_seconds)
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        panels = {"shadow": (42, 570, 627, 708), "light": (653, 570, 1238, 708)}
        radius = max(8, round(12 * min(self.width / 1280.0, self.height / 720.0)))
        for box in panels.values():
            odraw.rounded_rectangle(box, radius=radius, fill=(10, 13, 23, 232), outline=(68, 78, 98, 225), width=1)
        image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(image)
        draw.text((62, 581), "SHADOW CHORUS", font=self.title_font, fill=(224, 229, 239))
        draw.text((673, 581), "LIGHT CHORUS", font=self.title_font, fill=(255, 224, 145))
        row_y = {"Soprano": 610, "Alto": 646, "Baritone": 682, "Tenor/Bass": 682}
        quarter = self.timeline.quarter_at_audio_time(elapsed_seconds)
        for row, starts, segments in self.row_data:
            x_label, x_text, max_width = (62, 174, 430) if row.module == "shadow" else (673, 790, 425)
            y = row_y[row.label]
            draw.text((x_label, y), row.label, font=self.label_font, fill=(165, 175, 192))
            text = self._active_text(starts, segments, quarter)
            if text:
                display, font = self._fit_text(draw, text, max_width)
                fill = (242, 245, 250) if row.module == "shadow" else (255, 244, 208)
                draw.text((x_text, y - 3), display, font=font, fill=fill)
        return image


def render_video(renderer: LyricStageRenderer, output: Path, fps: int, crf: int, preset: str) -> dict[str, object]:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing video: {output}")
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required")
    output.parent.mkdir(parents=True, exist_ok=True)
    frame_count = math.ceil(float(renderer.timeline.output_duration_seconds) * fps)
    command = [
        ffmpeg, "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s:v", f"{renderer.width}x{renderer.height}", "-r", str(fps), "-i", "pipe:0",
        "-an", "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
        "-pix_fmt", "yuv420p", "-threads", "1", "-movflags", "+faststart",
        "-frames:v", str(frame_count), str(output),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert process.stdin is not None
    try:
        for frame_index in range(frame_count):
            process.stdin.write(renderer.render_frame(Fraction(frame_index, fps)).tobytes())
        process.stdin.close()
        return_code = process.wait()
    except BaseException:
        process.kill()
        process.wait()
        raise
    if return_code:
        raise RuntimeError(f"ffmpeg exited with status {return_code}")
    probe = probe_video(output)
    stream = probe["streams"][0]
    if stream.get("codec_name") != "h264" or stream.get("pix_fmt") != "yuv420p":
        raise ValueError(f"Unexpected output stream: {stream}")
    return {"path": str(output.resolve()), "sha256": sha256(output), "frameCount": frame_count, "probe": probe}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activity", type=Path, default=DEFAULT_ACTIVITY_PATH)
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
    renderer = LyricStageRenderer(timeline, args.width, args.height)
    result: dict[str, object] = {
        "scoreSha256": timeline.score_sha256,
        "activitySha256": timeline.activity_sha256,
        "rowCount": len(renderer.row_data),
    }
    if args.preview_output:
        if args.preview_output.exists():
            raise FileExistsError(f"Refusing to overwrite preview: {args.preview_output}")
        args.preview_output.parent.mkdir(parents=True, exist_ok=True)
        renderer.render_frame(args.preview_seconds).save(args.preview_output, "PNG")
        result["preview"] = {"path": str(args.preview_output.resolve()), "sha256": sha256(args.preview_output)}
    if args.output:
        result["video"] = render_video(renderer, args.output, args.fps, args.crf, args.preset)
    if not args.preview_output and not args.output:
        raise ValueError("Supply --preview-output and/or --output")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
