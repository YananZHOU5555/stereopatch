"""Remove every dirt-mask pixel that is ever occupied by moving content.

The resulting mask is time invariant.  It is intentionally conservative: if a
robot, gripper, cable, task object, or strong moving shadow reaches a location
in any frame, that location is never repaired in the final video.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


def read_exact(stream, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--mask", type=Path, required=True)
    parser.add_argument("--plate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--table-mask", type=Path, required=True)
    parser.add_argument("--clean-plate", type=Path, required=True)
    parser.add_argument("--overlay", type=Path, required=True)
    parser.add_argument("--motion-map", type=Path, required=True)
    parser.add_argument("--ffmpeg", type=Path, required=True)
    parser.add_argument("--scan-width", type=int, default=480)
    parser.add_argument("--scan-height", type=int, default=270)
    args = parser.parse_args()

    plate_image = Image.open(args.plate).convert("RGB")
    full_width, full_height = plate_image.size
    dirt_mask_image = Image.open(args.mask).convert("L")
    dirt_mask = np.asarray(dirt_mask_image) > 0

    scan_size = (args.scan_width, args.scan_height)
    plate_low_image = plate_image.resize(scan_size, Image.Resampling.BOX).filter(
        ImageFilter.BoxBlur(3)
    )
    plate_low = np.asarray(plate_low_image, dtype=np.int16)

    command = [
        str(args.ffmpeg),
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(args.video),
        "-vf",
        f"scale={args.scan_width}:{args.scan_height}:flags=area",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-",
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdout is not None
    frame_bytes = args.scan_width * args.scan_height * 3
    maximum_difference = np.zeros((args.scan_height, args.scan_width), dtype=np.uint8)
    frame_count = 0

    while True:
        raw = read_exact(process.stdout, frame_bytes)
        if not raw:
            break
        if len(raw) != frame_bytes:
            process.kill()
            raise RuntimeError("Truncated raw frame from ffmpeg")
        frame = np.frombuffer(raw, dtype=np.uint8).reshape(
            args.scan_height, args.scan_width, 3
        )
        frame_low = np.asarray(
            Image.fromarray(frame, mode="RGB").filter(ImageFilter.BoxBlur(3)),
            dtype=np.int16,
        )
        difference = np.max(np.abs(frame_low - plate_low), axis=2).astype(np.uint8)
        maximum_difference = np.maximum(maximum_difference, difference)
        frame_count += 1

    stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"ffmpeg frame scan failed ({return_code}): {stderr}")

    # A 15-pixel low-resolution dilation corresponds to a 60-pixel safety
    # margin at 1080p, protecting object edges and motion blur.
    ever_foreground_low = Image.fromarray(
        ((maximum_difference > 34) * 255).astype(np.uint8), mode="L"
    ).filter(ImageFilter.MaxFilter(15))
    ever_foreground = np.asarray(
        ever_foreground_low.resize((full_width, full_height), Image.Resampling.NEAREST)
    ) > 0

    # Remove static non-table structures as well.  Unlike individual dirt
    # specks, a robot/fixture creates a high dark-pixel fraction in a broad
    # neighbourhood.
    plate = np.asarray(plate_image, dtype=np.float32) / 255.0
    plate_lum = plate[..., 0] * 0.2126 + plate[..., 1] * 0.7152 + plate[..., 2] * 0.0722
    dark_fraction = np.asarray(
        Image.fromarray(((plate_lum < 0.38) * 255).astype(np.uint8), mode="L").filter(
            ImageFilter.BoxBlur(24)
        ),
        dtype=np.float32,
    ) / 255.0
    static_structure = dark_fraction > 0.065

    table_mask = dirt_mask & ~static_structure
    safe_mask = table_mask & ~ever_foreground
    Image.fromarray((table_mask * 255).astype(np.uint8), mode="L").save(args.table_mask)

    # Construct the fixed repair plate locally.  Median replacement cannot pull
    # content across distant mask islands, unlike a logo-removal filter applied
    # to hundreds of scattered points.
    plate_u8 = np.asarray(plate_image, dtype=np.uint8)
    local_median = np.asarray(
        plate_image.filter(ImageFilter.MedianFilter(21)), dtype=np.uint8
    )
    clean_plate = plate_u8.copy()
    clean_plate[table_mask] = local_median[table_mask]
    Image.fromarray(clean_plate, mode="RGB").save(args.clean_plate)
    safe_image = Image.fromarray((safe_mask * 255).astype(np.uint8), mode="L")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    safe_image.save(args.output)
    Image.fromarray(maximum_difference, mode="L").resize(
        (full_width, full_height), Image.Resampling.NEAREST
    ).save(args.motion_map)

    overlay = np.asarray(plate_image, dtype=np.float32) / 255.0
    overlay[..., 0] = np.where(safe_mask, 1.0, overlay[..., 0])
    overlay[..., 1] = np.where(safe_mask, overlay[..., 1] * 0.15, overlay[..., 1])
    overlay[..., 2] = np.where(safe_mask, overlay[..., 2] * 0.15, overlay[..., 2])
    Image.fromarray(np.clip(overlay * 255, 0, 255).astype(np.uint8)).save(args.overlay)

    original_pixels = int(dirt_mask.sum())
    table_pixels = int(table_mask.sum())
    safe_pixels = int(safe_mask.sum())
    print(
        f"frames={frame_count} original_mask_pixels={original_pixels} "
        f"table_mask_pixels={table_pixels} table_retained={table_pixels / max(original_pixels, 1):.2%} "
        f"always_safe_pixels={safe_pixels} always_safe_retained={safe_pixels / max(original_pixels, 1):.2%}"
    )


if __name__ == "__main__":
    main()
