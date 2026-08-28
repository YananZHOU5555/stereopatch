"""Prepare the paper's canonical Method figure for the project page.

The exported paper figure contains two neutral matte colours: pure white and
the warm-white module fill ``#F4F4F1``.  A border-connected flood fill is not
sufficient because arrows and module outlines enclose large matte islands.

This script therefore removes both matte colours everywhere except inside the
three embedded RGB/depth evidence frames.  Pixels close to a matte colour are
de-matted with deterministic colour-to-alpha reconstruction, avoiding a pale
fringe on the warm project-page background.  All scientific structure and all
pixels in the protected evidence frames remain byte-identical to the paper PNG.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT.parent
    / "papers"
    / "StereoPatch"
    / "figures"
    / "export"
    / "fig2_stereopatch_token_construction.png"
)
OUTPUT = ROOT / "public" / "media" / "method" / "stereopatch-method-transparent.png"

EXPECTED_SIZE = (3874, 1728)

# Half-open pixel coordinates in the canonical 3874 x 1728 paper export.
# Each region includes a small margin around the black image border so no white
# table, robot, or depth-map evidence can be mistaken for the canvas matte.
PROTECTED_EVIDENCE_ROIS = (
    (452, 219, 863, 428),  # RGB image
    (57, 484, 670, 662),  # top-view stereo pair
    (452, 805, 863, 1014),  # metric depth map
)

# (matte RGB, maximum L-infinity colour distance eligible for de-matting)
MATTE_KEYS = (
    ((255, 255, 255), 18.0),
    ((244, 244, 241), 8.0),
)


def _colour_to_alpha(colours: np.ndarray, matte: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Recover minimal alpha and foreground RGB for colours composited on matte."""

    below_matte = colours < matte
    lower_denominator = np.where(matte > 0, matte, 1.0)
    upper_denominator = np.where(matte < 255, 255.0 - matte, 1.0)
    per_channel_alpha = np.where(
        below_matte,
        (matte - colours) / lower_denominator,
        (colours - matte) / upper_denominator,
    )
    alpha = np.clip(np.max(per_channel_alpha, axis=1), 0.0, 1.0)

    foreground = np.zeros_like(colours)
    visible = alpha > 1e-6
    foreground[visible] = (
        colours[visible] - (1.0 - alpha[visible, None]) * matte
    ) / alpha[visible, None]
    foreground = np.clip(np.rint(foreground), 0, 255).astype(np.uint8)
    return alpha, foreground


def main() -> None:
    source_image = Image.open(SOURCE).convert("RGBA")
    if source_image.size != EXPECTED_SIZE:
        raise ValueError(
            f"Unexpected Method figure size {source_image.size}; "
            f"protected ROIs are registered to {EXPECTED_SIZE}."
        )

    source = np.asarray(source_image, dtype=np.uint8)
    output = source.copy()
    height, width = source.shape[:2]
    source_rgb = source[:, :, :3].astype(np.float32)

    protected = np.zeros((height, width), dtype=bool)
    for left, top, right, bottom in PROTECTED_EVIDENCE_ROIS:
        protected[top:bottom, left:right] = True

    best_distance = np.full((height, width), np.inf, dtype=np.float32)
    best_key = np.full((height, width), -1, dtype=np.int8)

    # Assign each non-evidence pixel to its nearest eligible matte colour.
    for key_index, (key_rgb, radius) in enumerate(MATTE_KEYS):
        matte = np.asarray(key_rgb, dtype=np.float32)
        distance = np.max(np.abs(source_rgb - matte), axis=2)
        take = (distance <= radius) & (distance < best_distance) & ~protected
        best_distance[take] = distance[take]
        best_key[take] = key_index

    processed = np.zeros((height, width), dtype=bool)
    for key_index, (key_rgb, _radius) in enumerate(MATTE_KEYS):
        selected = best_key == key_index
        if not np.any(selected):
            continue

        matte = np.asarray(key_rgb, dtype=np.float32)
        alpha, foreground = _colour_to_alpha(source_rgb[selected], matte)
        output[selected, :3] = foreground
        output[selected, 3] = np.rint(
            alpha * source[selected, 3].astype(np.float32)
        ).astype(np.uint8)
        processed |= selected

    # Deterministic scientific-asset QA.
    if not np.array_equal(output[protected], source[protected]):
        raise AssertionError("Protected RGB/depth evidence pixels changed.")

    opaque_key_residuals: dict[tuple[int, int, int], int] = {}
    for key_rgb, _radius in MATTE_KEYS:
        key = np.asarray(key_rgb, dtype=np.uint8)
        source_key_pixels = np.all(source[:, :, :3] == key, axis=2) & ~protected
        if np.any(output[source_key_pixels, 3] != 0):
            raise AssertionError(f"Matte key {key_rgb} was not fully transparent.")
        opaque_key_residuals[key_rgb] = int(
            np.count_nonzero(
                np.all(output[:, :, :3] == key, axis=2)
                & (output[:, :, 3] == 255)
                & ~protected
            )
        )
        if opaque_key_residuals[key_rgb] != 0:
            raise AssertionError(f"Opaque matte-key residual remains for {key_rgb}.")

    source_min = source[:, :, :3].min(axis=2)
    source_chroma = source[:, :, :3].max(axis=2) - source_min
    structural = ((source_min < 220) | (source_chroma > 25)) & ~protected
    structural_unchanged = np.all(output == source, axis=2) & structural
    if np.count_nonzero(structural_unchanged) != np.count_nonzero(structural):
        raise AssertionError("A clear structural pixel changed during matte removal.")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(output, mode="RGBA").save(OUTPUT, optimize=True)

    alpha = output[:, :, 3]
    print(
        f"prepared {OUTPUT} ({width}x{height}; "
        f"{np.count_nonzero(processed):,} pixels de-matted)"
    )
    print(
        "QA: protected evidence byte-identical; "
        f"opaque matte residuals={opaque_key_residuals}; "
        f"structural pixels unchanged="
        f"{np.count_nonzero(structural_unchanged):,}/"
        f"{np.count_nonzero(structural):,}; "
        f"alpha0={np.count_nonzero(alpha == 0):,}, "
        f"partial={np.count_nonzero((alpha > 0) & (alpha < 255)):,}, "
        f"opaque={np.count_nonzero(alpha == 255):,}"
    )


if __name__ == "__main__":
    main()
