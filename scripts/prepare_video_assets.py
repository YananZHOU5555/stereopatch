"""Build browser-compatible 4K60 evidence videos at their final web speeds.

The two generalization masters receive 2x timestamp compression. The four task
masters are already edited at their intended 4x presentation speed, so they
receive no additional acceleration. Outputs are validated before replacing any
published asset.
"""

from __future__ import annotations

import argparse
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import imageio_ffmpeg


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path("E:/OneDrive/Desktop/StoreoPatch")
OUTPUT_ROOT = ROOT / "public" / "media" / "video-4k60"
FFMPEG = Path(imageio_ffmpeg.get_ffmpeg_exe())


@dataclass(frozen=True)
class Asset:
    key: str
    source: Path
    additional_speed: int
    poster_source_time: float


ASSETS = (
    # These generalization masters are presented at 2x on the website.
    Asset("placement", SOURCE_ROOT / "扔到桶" / "夹到桶-4K60 无音乐.mp4", 2, 108.5),
    Asset("picking", SOURCE_ROOT / "pick玩具" / "pick 玩具 4K60 无声音.mp4", 2, 74.5),
    # These task masters already encode the intended 4x presentation speed.
    Asset("peg", SOURCE_ROOT / "插销" / "插销 4K60 无音频.mp4", 1, 8.6),
    Asset("picnic", SOURCE_ROOT / "野餐袋" / "野餐袋 4K60- 无音乐.mp4", 1, 12.0),
    Asset("bowl", SOURCE_ROOT / "碗" / "碗 4k60.mp4", 1, 18.0),
    Asset("cup", SOURCE_ROOT / "夹杯子" / "夹杯子 4K60 无音频.mp4", 1, 7.2),
)


def metadata(path: Path) -> dict:
    frames = imageio_ffmpeg.read_frames(str(path), pix_fmt="rgb24", input_params=["-threads", "1"])
    result = next(frames)
    frames.close()
    return result


def run_with_progress(command: list[str], key: str) -> None:
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert process.stdout is not None
    last_second = -1
    diagnostics: list[str] = []
    for line in process.stdout:
        line = line.strip()
        diagnostics.append(line)
        if line.startswith("out_time="):
            timecode = line.removeprefix("out_time=")
            try:
                hours, minutes, seconds = timecode.split(":")
                current = int(hours) * 3600 + int(minutes) * 60 + int(float(seconds))
            except ValueError:
                continue
            if current == 0 or current - last_second >= 15:
                print(f"[{key}] encoded {timecode}", flush=True)
                last_second = current
    return_code = process.wait()
    if return_code:
        tail = "\n".join(diagnostics[-30:])
        raise RuntimeError(f"ffmpeg failed for {key} ({return_code})\n{tail}")


def prepare(asset: Asset) -> None:
    if not asset.source.exists():
        raise FileNotFoundError(asset.source)

    source_meta = metadata(asset.source)
    source_size = source_meta.get("size") or source_meta.get("source_size")
    source_fps = float(source_meta["fps"])
    source_duration = float(source_meta["duration"])
    if source_size != (3840, 2160) or abs(source_fps - 60.0) > 0.01:
        raise RuntimeError(f"{asset.key}: expected a 3840x2160/60 master, got {source_size}/{source_fps}")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    final_video = OUTPUT_ROOT / f"{asset.key}.mp4"
    partial_video = OUTPUT_ROOT / f".{asset.key}.partial.mp4"
    final_poster = OUTPUT_ROOT / f"{asset.key}.jpg"
    partial_poster = OUTPUT_ROOT / f".{asset.key}.partial.jpg"

    for stale in (partial_video, partial_poster):
        stale.unlink(missing_ok=True)

    filters = "fps=60,format=yuv420p"
    if asset.additional_speed != 1:
        filters = f"setpts=PTS/{asset.additional_speed},fps=60,format=yuv420p"

    command = [
        str(FFMPEG),
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-hwaccel",
        "cuda",
        "-i",
        str(asset.source),
        "-map",
        "0:v:0",
        "-an",
        "-vf",
        filters,
        "-c:v",
        "h264_nvenc",
        "-preset",
        "p6",
        "-tune",
        "hq",
        "-rc",
        "vbr",
        "-cq",
        "22",
        "-b:v",
        "0",
        "-profile:v",
        "high",
        "-level:v",
        "5.2",
        "-g",
        "120",
        "-bf",
        "3",
        "-spatial_aq",
        "1",
        "-temporal_aq",
        "1",
        "-rc-lookahead",
        "32",
        "-pix_fmt",
        "yuv420p",
        "-tag:v",
        "avc1",
        "-fps_mode",
        "cfr",
        "-movflags",
        "+faststart",
        "-progress",
        "pipe:1",
        "-nostats",
        str(partial_video),
    ]

    print(
        f"[{asset.key}] source {source_duration:.3f}s with {asset.additional_speed}x additional speed -> expected {source_duration / asset.additional_speed:.3f}s",
        flush=True,
    )
    run_with_progress(command, asset.key)

    output_meta = metadata(partial_video)
    output_size = output_meta.get("size") or output_meta.get("source_size")
    output_fps = float(output_meta["fps"])
    output_duration = float(output_meta["duration"])
    expected_duration = source_duration / asset.additional_speed
    if output_size != (3840, 2160):
        raise RuntimeError(f"{asset.key}: invalid output size {output_size}")
    if abs(output_fps - 60.0) > 0.01:
        raise RuntimeError(f"{asset.key}: invalid output fps {output_fps}")
    if abs(output_duration - expected_duration) > 0.08:
        raise RuntimeError(
            f"{asset.key}: duration {output_duration:.3f}s differs from expected {expected_duration:.3f}s"
        )

    poster_time = min(asset.poster_source_time / asset.additional_speed, max(0.0, output_duration - 0.1))
    poster_command = [
        str(FFMPEG),
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{poster_time:.3f}",
        "-i",
        str(partial_video),
        "-frames:v",
        "1",
        "-vf",
        "scale=1920:-2:flags=lanczos",
        "-q:v",
        "2",
        str(partial_poster),
    ]
    subprocess.run(poster_command, check=True)

    os.replace(partial_video, final_video)
    os.replace(partial_poster, final_poster)
    print(
        f"[{asset.key}] verified 3840x2160/60, {output_duration:.3f}s, {final_video.stat().st_size / 1048576:.1f} MiB",
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("keys", nargs="*", help="Optional asset keys; defaults to all six")
    arguments = parser.parse_args()
    selected = set(arguments.keys)
    unknown = selected.difference(asset.key for asset in ASSETS)
    if unknown:
        raise SystemExit(f"unknown asset keys: {', '.join(sorted(unknown))}")
    for asset in ASSETS:
        if not selected or asset.key in selected:
            prepare(asset)


if __name__ == "__main__":
    main()
