#!/usr/bin/env python3
"""Build deterministic review-only decoration for the V36 note light show."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from fractions import Fraction
from pathlib import Path

import numpy as np

from render_v36_light_chorus_review_video import (
    DEFAULT_ACTIVITY_PATH,
    _fraction_text,
    load_review_timeline,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "v36-decorative-light-texture-1"
DEFAULT_AUDIO = (
    REPO_ROOT
    / "Visual-Production/Review-Renders/V36-Note-Synchronous-Review-2026-08-30/Audio"
    / "FlashlightsInTheDark_v36_ElectronicsMinus3dB_FinalePiano_PrimerHalfBeatCorrection_ReviewMix_2026-08-30.wav"
)
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "Visual-Production/Review-Renders/V36-Note-Synchronous-Review-2026-08-30/Manifests"
    / "FlashlightsInTheDark_v36_DecorativeTexture_Authoring_2026-08-30.json"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def decode_mono(path: Path, sample_rate: int = 2000) -> np.ndarray:
    payload = subprocess.check_output(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            "-f",
            "f32le",
            "-",
        ]
    )
    return np.frombuffer(payload, dtype="<f4").astype(np.float64)


def dynamics_envelope(
    audio_path: Path,
    *,
    duration_seconds: Fraction,
    score_start_seconds: Fraction,
    score_end_seconds: Fraction,
) -> tuple[list[dict[str, object]], dict[str, float]]:
    sample_rate = 2000
    frames_per_second = 10
    block = sample_rate // frames_per_second
    audio = decode_mono(audio_path, sample_rate)
    expected = round(float(duration_seconds) * sample_rate)
    if abs(len(audio) - expected) > 2:
        raise ValueError(f"Audio sample count {len(audio)} does not match duration")
    count = len(audio) // block
    rms = np.sqrt(np.mean(audio[: count * block].reshape(count, block) ** 2, axis=1) + 1e-12)
    dbfs = 20 * np.log10(rms + 1e-12)
    # A one-second Hann smoother tracks musical density without chasing each attack.
    kernel = np.hanning(11)
    kernel /= kernel.sum()
    smoothed = np.convolve(dbfs, kernel, mode="same")
    score_slice = smoothed[
        max(0, int(float(score_start_seconds) * frames_per_second)) :
        min(len(smoothed), math.ceil(float(score_end_seconds) * frames_per_second))
    ]
    # Audited active-score P20/P80 references from this exact normal-primer mix.
    quiet_reference = -25.935
    loud_reference = -18.976
    loudness = np.clip(
        (smoothed - quiet_reference) / (loud_reference - quiet_reference), 0, 1
    )
    quietness = 1 - loudness
    perturbation = 0.08 + 0.78 * quietness**1.4
    points = [
        {
            "timeMs": index * 100,
            "rmsDbfs": round(float(smoothed[index]), 3),
            "loudness01": round(float(loudness[index]), 4),
            "quietness01": round(float(quietness[index]), 4),
            "perturbationMix01": round(float(perturbation[index]), 4),
        }
        for index in range(len(smoothed))
    ]
    return points, {
        "quietReferenceDbfsP20": round(quiet_reference, 3),
        "loudReferenceDbfsP80": round(loud_reference, 3),
        "observedP20Dbfs": round(float(np.quantile(score_slice, 0.20)), 3),
        "observedMedianDbfs": round(float(np.quantile(score_slice, 0.50)), 3),
        "observedP80Dbfs": round(float(np.quantile(score_slice, 0.80)), 3),
        "observedMinimumDbfs": round(float(np.min(score_slice)), 3),
        "observedMaximumDbfs": round(float(np.max(score_slice)), 3),
    }


def measure_boundary(timeline: object, number: int) -> tuple[Fraction, Fraction]:
    measure = next(item for item in timeline.measures if item.number == number)
    start = timeline.score_origin_seconds + timeline.score_clock.seconds_from_score_origin(
        measure.start_quarter
    )
    end = timeline.score_origin_seconds + timeline.score_clock.seconds_from_score_origin(
        measure.end_quarter
    )
    return start, end


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activity", type=Path, default=DEFAULT_ACTIVITY_PATH)
    parser.add_argument("--audio", type=Path, default=DEFAULT_AUDIO)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite authored texture: {output}")
    timeline = load_review_timeline(
        args.activity,
        score_origin_seconds=Fraction(20313, 2125),
        output_duration_seconds=Fraction(2641, 6),
    )
    envelope, dynamics = dynamics_envelope(
        args.audio.resolve(),
        duration_seconds=timeline.output_duration_seconds,
        score_start_seconds=timeline.score_origin_seconds,
        score_end_seconds=timeline.score_end_seconds,
    )
    m96_start, _ = measure_boundary(timeline, 96)
    m104_start, _ = measure_boundary(timeline, 104)
    m111_start, _ = measure_boundary(timeline, 111)
    m131_start, _ = measure_boundary(timeline, 131)
    m133_start, _ = measure_boundary(timeline, 133)
    m137_start, _ = measure_boundary(timeline, 137)
    m138_start, m138_end = measure_boundary(timeline, 138)
    m140_start, _ = measure_boundary(timeline, 140)
    m104_measure = next(item for item in timeline.measures if item.number == 104)
    m104_shared_attack = (
        timeline.score_origin_seconds
        + timeline.score_clock.seconds_from_score_origin(
            m104_measure.start_quarter + Fraction(1)
        )
    )
    m133_chandelier = (
        timeline.score_origin_seconds
        + timeline.score_clock.seconds_from_score_origin(
            next(item for item in timeline.measures if item.number == 133).start_quarter
            + Fraction(3)
        )
    )
    m138_late_peak = m138_start + (m138_end - m138_start) * Fraction(3, 4)
    tail_glimmer_end = min(timeline.output_duration_seconds, Fraction("430.473104"))
    payload = {
        "schemaVersion": SCHEMA,
        "artifactType": "authored-v36-review-only-decorative-light-texture",
        "status": "authoring-source-not-runtime-ready",
        "runtimeEligible": False,
        "artisticRule": {
            "foundation": "V36 Light Chorus note activity remains the direct-response layer.",
            "normalBehavior": "Seeded flicker and glow ramps decorate every logical lane and arbitrary replica without encoding a physical phone count.",
            "quietBehavior": "At low audio level, decoration may heavily obscure the binary on/off silhouette by independently illuminating rests and dimming sounding points.",
            "loudBehavior": "At high audio level, perturbation recedes so sounding-versus-resting note activity reads clearly.",
            "brightnessStacking": False,
            "legacyChoreographyUsed": False,
        },
        "sources": {
            "noteActivity": {
                "path": repo_path(timeline.activity_path),
                "sha256": timeline.activity_sha256,
            },
            "score": {
                "path": repo_path(timeline.score_path),
                "sha256": timeline.score_sha256,
            },
            "dynamicsAudio": {
                "path": repo_path(args.audio),
                "sha256": sha256(args.audio),
                "description": "Corrected piano alignment, normal half-beat primer tones, electronics reduced 3 dB.",
                "durationSeconds": str(timeline.output_duration_seconds),
            },
        },
        "clock": {
            "scoreOriginSeconds": _fraction_text(timeline.score_origin_seconds),
            "scoreEndSeconds": _fraction_text(timeline.score_end_seconds),
            "outputDurationSeconds": _fraction_text(timeline.output_duration_seconds),
            "tempoMap": [
                {
                    "startQuarter": _fraction_text(event.start_quarter),
                    "quarterBpm": _fraction_text(event.quarter_bpm),
                }
                for event in timeline.score_clock.events
            ],
        },
        "topologyPolicy": {
            "logicalLaneKeys": list(timeline.stage_order),
            "replication": "For any nonnegative replica index, derive stable phases and rates from lane key, replica index, and seed.",
            "reviewSampling": "The review renderer samples seven presentation points per lane; this count is not part of the authored field.",
        },
        "randomPolicy": {
            "mode": "deterministic-seeded-continuous-value-noise",
            "seed": 360104141,
            "differentSpeedBandsHz": {
                "slowGlow": [0.06, 0.22],
                "mediumFlutter": [0.35, 1.3],
                "fastFlicker": [2.4, 5.8],
                "glitter": [3.5, 6.0],
                "endingPinprick": [0.3, 1.4],
            },
            "deterministicRegenerationRequired": True,
        },
        "dynamicsPolicy": {
            **dynamics,
            "analysisFramesPerSecond": 10,
            "smoothingSeconds": 1.0,
            "perturbationAtQuietReference": 0.86,
            "perturbationAtLoudReference": 0.08,
            "interpolation": "linear between envelope samples",
        },
        "specialSections": {
            "glitterApproachTo104": {
                "startMeasure": 96,
                "endAtMeasure": 104,
                "startSeconds": _fraction_text(m96_start),
                "endSeconds": _fraction_text(m104_start),
                "curve": "quadratic density and intensity increase",
                "behavior": "Rare dust begins in the all-rest m96, then independent gold-white micro-sparks grow denser through m103 while loudness caps their per-point masking near the ff arrival.",
            },
            "measure104UnifiedGlow": {
                "startMeasure": 104,
                "firstSharedAttackQuarter": "382",
                "firstSharedAttackSeconds": _fraction_text(m104_shared_attack),
                "endBeforeMeasure": 111,
                "startSeconds": _fraction_text(m104_start),
                "endSeconds": _fraction_text(m111_start),
                "behavior": "All lanes and arbitrary field samples share a warm preglow from the m104 downbeat, bloom together at the six-lane q382 entrance, then breathe in exact synchrony through m110 before the m111 subito mp.",
                "cycleSeconds": 8.333333333,
                "minimumBrightness": 0.08,
                "maximumBrightness": 0.96,
            },
            "endingGlimmer": {
                "seedStartMeasure": 131,
                "chandelierDirectionMeasure": 133,
                "intensifyMeasure": 138,
                "seedStartSeconds": _fraction_text(m131_start),
                "homePhraseStartSeconds": _fraction_text(m133_start),
                "chandelierDirectionSeconds": _fraction_text(m133_chandelier),
                "swellStartSeconds": _fraction_text(m137_start),
                "swellPeakSeconds": _fraction_text(m138_late_peak),
                "diminishToPppSeconds": _fraction_text(m140_start),
                "scoreEndSeconds": _fraction_text(timeline.score_end_seconds),
                "tailFadeEndSeconds": _fraction_text(tail_glimmer_end),
                "behavior": "Point-sparks seed the m131-132 hinge, then the written m133 q3 sound-chandelier direction opens a calm pearl-gold field of slow glows and sparse pinpricks. It swells modestly at m137-138, dims through m140 ppp, and reaches black at the measured audio-decay endpoint.",
            },
        },
        "dynamicsEnvelope": envelope,
        "validationRequirements": {
            "brightnessAlwaysWithinZeroAndOne": True,
            "deterministicAcrossRegeneration": True,
            "quietPerturbationGreaterThanLoudPerturbation": True,
            "measure104AllLanesSynchronized": True,
            "glitterIncreasesIntoMeasure104": True,
            "endingTailReachesBlack": True,
            "runtimeManifestGenerated": False,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(output), "sha256": sha256(output), "envelopePoints": len(envelope)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
