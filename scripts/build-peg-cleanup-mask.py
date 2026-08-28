"""Build a conservative, fixed tabletop-dirt mask from several peg-video frames.

The mask is intentionally limited to small, static, high-contrast marks on the
bright table mat.  A mark must recur at the same image location in multiple
frames; moving robots and task objects therefore do not enter the mask.
"""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


def luminance(rgb: np.ndarray) -> np.ndarray:
    return rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722


def candidate_mask(path: Path) -> tuple[np.ndarray, np.ndarray]:
    image = Image.open(path).convert("RGB")
    rgb = np.asarray(image, dtype=np.float32) / 255.0
    return candidate_mask_from_rgb(rgb), rgb


def candidate_mask_from_rgb(rgb: np.ndarray) -> np.ndarray:
    image = Image.fromarray(np.clip(rgb * 255, 0, 255).astype(np.uint8), mode="RGB")
    # A broad local mean describes the underlying mat without reacting to its
    # fine woven texture.  This is deliberately stricter than a local-detail
    # detector: normal mat weave must remain untouched.
    median = np.asarray(image.filter(ImageFilter.BoxBlur(9)), dtype=np.float32) / 255.0

    lum = luminance(rgb)
    local_lum = luminance(median)
    local_chroma = median.max(axis=2) - median.min(axis=2)
    dark_fraction = np.asarray(
        Image.fromarray(((lum < 0.35) * 255).astype(np.uint8), mode="L").filter(
            ImageFilter.BoxBlur(20)
        ),
        dtype=np.float32,
    ) / 255.0

    # Restrict detection to the neutral, bright table mat.  The top rail/wall,
    # wooden fixture, black robots, cables, and camera are rejected locally.
    table_like = (local_lum > 0.54) & (local_chroma < 0.18) & (dark_fraction < 0.075)
    rows = np.arange(rgb.shape[0])[:, None]
    table_like &= rows >= 165

    dark_mark = (lum < 0.42) & ((local_lum - lum) > 0.18)
    blue_mark = (
        ((rgb[..., 2] - rgb[..., 0]) > 0.10)
        & ((rgb[..., 2] - rgb[..., 1]) > 0.05)
        & (rgb[..., 2] > 0.28)
    )
    return table_like & (dark_mark | blue_mark)


def keep_small_components(mask: np.ndarray, max_area: int = 320) -> np.ndarray:
    """Keep only compact marks; reject object edges and broad shadows."""
    height, width = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    output = np.zeros_like(mask, dtype=bool)
    ys, xs = np.nonzero(mask)

    for sy, sx in zip(ys.tolist(), xs.tolist()):
        if seen[sy, sx]:
            continue
        queue: deque[tuple[int, int]] = deque([(sy, sx)])
        seen[sy, sx] = True
        component: list[tuple[int, int]] = []
        while queue:
            y, x = queue.popleft()
            component.append((y, x))
            for ny in range(max(0, y - 1), min(height, y + 2)):
                for nx in range(max(0, x - 1), min(width, x + 2)):
                    if mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((ny, nx))
        if 1 <= len(component) <= max_area:
            cy, cx = zip(*component)
            output[np.asarray(cy), np.asarray(cx)] = True
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--overlay", type=Path, required=True)
    parser.add_argument("--plate", type=Path, required=True)
    parser.add_argument("--stain-mask", type=Path, required=True)
    parser.add_argument("--correction", type=Path, required=True)
    parser.add_argument("--stain-overlay", type=Path, required=True)
    args = parser.parse_args()

    frame_paths = sorted(args.frames.glob("*.png"))
    if len(frame_paths) < 3:
        raise SystemExit("At least three reference frames are required")

    candidates = []
    reference = None
    frame_rgbs: list[np.ndarray] = []
    for path in frame_paths:
        candidate, rgb = candidate_mask(path)
        candidates.append(candidate)
        frame_rgbs.append(rgb)
        if reference is None:
            reference = rgb

    votes = np.stack(candidates).sum(axis=0)

    # The temporal median exposes fixed table marks even when an arm occludes
    # them in one or two samples.  The compact-component rule still rejects
    # foreground silhouettes and fixture edges.
    plate = np.median(np.stack(frame_rgbs), axis=0)
    plate_marks = keep_small_components(candidate_mask_from_rgb(plate))
    stable = keep_small_components((votes >= 2) | plate_marks)

    # Expand by four pixels so compressed fringes around each mark are repaired.
    binary = Image.fromarray((stable * 255).astype(np.uint8), mode="L")
    binary = binary.filter(ImageFilter.MaxFilter(9))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    binary.save(args.output)

    # Median compositing provides a background reference for detecting when a
    # moving arm/object occludes a dirt location.  It is used only as a gate;
    # its pixels are never inserted into the final video.
    Image.fromarray(np.clip(plate * 255, 0, 255).astype(np.uint8)).save(args.plate)

    # Low-frequency stain correction.  Select the brightest observed sample at
    # each pixel to suppress moving arm shadows, then estimate only broad dark
    # deviations from the surrounding mat.  The correction is additive, so the
    # original woven texture and high-frequency evidence remain intact.
    frame_stack = np.stack(frame_rgbs)
    lum_stack = np.stack([luminance(frame) for frame in frame_rgbs])
    brightest_index = np.argmax(lum_stack, axis=0)
    yy, xx = np.indices(brightest_index.shape)
    bright_plate = frame_stack[brightest_index, yy, xx]
    bright_image = Image.fromarray(np.clip(bright_plate * 255, 0, 255).astype(np.uint8), mode="RGB")
    local_rgb = np.asarray(bright_image.filter(ImageFilter.BoxBlur(28)), dtype=np.float32) / 255.0
    target_rgb = np.asarray(bright_image.filter(ImageFilter.BoxBlur(170)), dtype=np.float32) / 255.0
    local_lum = luminance(local_rgb)
    target_lum = luminance(target_rgb)
    local_chroma = local_rgb.max(axis=2) - local_rgb.min(axis=2)
    broad_dark_fraction = np.asarray(
        Image.fromarray(((luminance(bright_plate) < 0.38) * 255).astype(np.uint8), mode="L").filter(
            ImageFilter.BoxBlur(28)
        ),
        dtype=np.float32,
    ) / 255.0

    stain_strength = np.clip((target_lum - local_lum - 0.018) / 0.075, 0.0, 1.0)
    rows = np.arange(stain_strength.shape[0])[:, None]
    valid_stain = (
        (rows >= 165)
        & (local_lum > 0.47)
        & (local_chroma < 0.16)
        & (broad_dark_fraction < 0.065)
    )
    stain_strength *= valid_stain
    stain_strength = np.asarray(
        Image.fromarray(np.clip(stain_strength * 255, 0, 255).astype(np.uint8), mode="L").filter(
            ImageFilter.GaussianBlur(8)
        ),
        dtype=np.float32,
    ) / 255.0
    stain_strength *= 0.62

    # Full correction value; the soft stain mask controls how much is applied.
    additive = np.clip(target_lum - local_lum, 0.0, 0.095)
    correction = np.repeat(
        np.clip(128.0 + additive[..., None] * 255.0, 0, 255), 3, axis=2
    ).astype(np.uint8)
    stain_mask_u8 = np.clip(stain_strength * 255, 0, 255).astype(np.uint8)
    Image.fromarray(stain_mask_u8, mode="L").save(args.stain_mask)
    Image.fromarray(correction, mode="RGB").save(args.correction)

    stain_overlay = reference.copy()
    stain_overlay[..., 0] = np.clip(stain_overlay[..., 0] + stain_strength * 0.36, 0, 1)
    stain_overlay[..., 1] *= 1.0 - stain_strength * 0.62
    stain_overlay[..., 2] *= 1.0 - stain_strength * 0.62
    Image.fromarray(np.clip(stain_overlay * 255, 0, 255).astype(np.uint8)).save(args.stain_overlay)

    mask = np.asarray(binary, dtype=np.float32) / 255.0
    assert reference is not None
    overlay = reference.copy()
    overlay[..., 0] = np.where(mask > 0, 1.0, overlay[..., 0])
    overlay[..., 1] = np.where(mask > 0, overlay[..., 1] * 0.18, overlay[..., 1])
    overlay[..., 2] = np.where(mask > 0, overlay[..., 2] * 0.18, overlay[..., 2])
    Image.fromarray(np.clip(overlay * 255, 0, 255).astype(np.uint8)).save(args.overlay)

    covered = int((mask > 0).sum())
    total = int(mask.size)
    print(f"frames={len(frame_paths)} mask_pixels={covered} coverage={covered / total:.5%}")


if __name__ == "__main__":
    main()
