"""Prepare provenance-preserving evidence assets for the project page.

The script copies the paper's exact simulation/protocol imagery and removes only
edge-connected near-white canvas from the two RQ3 composites. Pixels inside the
photographic panels are never globally keyed, so white robot-table regions stay
intact.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path
import shutil
import sys

import numpy as np
from matplotlib import colormaps
from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
PAPER = Path("E:/OneDrive/文档/ICRA27/papers/StereoPatch")
EXPORT = PAPER / "figures" / "export"
SIM_SOURCE = PAPER / "figures" / "source" / "sim_benchmarks"
PUBLIC = ROOT / "public" / "media"
PAPER_SOURCE = PAPER / "figures" / "source"

sys.path.insert(0, str(PAPER_SOURCE))
from build_rq4_visual_depth_strip import (  # noqa: E402
    DEPTH_Y,
    RGB_Y,
    crop_row,
    neutralize_rgb_background,
)


SIMULATION_ASSETS = (
    "robomimic_tool_hang.png",
    "robomimic_square.png",
    "robomimic_transport.png",
    "robofactory_lift_barrier.png",
    "robofactory_camera_alignment.png",
    "robofactory_three_robot_stack.png",
    "behavior_open_door.png",
    "behavior_turn_on_radio.png",
)


def copy_exact(source: Path, destination: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def edge_connected_canvas(source: Path, destination: Path) -> None:
    """Make only edge-connected neutral pixels transparent.

    A strict seed threshold prevents the flood fill from entering the light
    table surfaces inside the photographs. A two-pixel neutral fringe is then
    feathered to avoid a white matte around labels on the warm web canvas.
    """

    image = Image.open(source).convert("RGBA")
    width, height = image.size
    pixels = image.load()
    visited = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    def is_seed(x: int, y: int) -> bool:
        red, green, blue, _ = pixels[x, y]
        return min(red, green, blue) >= 248 and max(red, green, blue) - min(red, green, blue) <= 5

    def enqueue(x: int, y: int) -> None:
        index = y * width + x
        if visited[index] or not is_seed(x, y):
            return
        visited[index] = 1
        queue.append((x, y))

    for x in range(width):
        enqueue(x, 0)
        enqueue(x, height - 1)
    for y in range(height):
        enqueue(0, y)
        enqueue(width - 1, y)

    while queue:
        x, y = queue.popleft()
        if x:
            enqueue(x - 1, y)
        if x + 1 < width:
            enqueue(x + 1, y)
        if y:
            enqueue(x, y - 1)
        if y + 1 < height:
            enqueue(x, y + 1)

    canvas = Image.new("L", (width, height), 0)
    canvas.putdata(visited)
    fringe = canvas.filter(ImageFilter.MaxFilter(5))
    canvas_data = canvas.load()
    fringe_data = fringe.load()

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if canvas_data[x, y]:
                pixels[x, y] = (red, green, blue, 0)
            elif fringe_data[x, y] and min(red, green, blue) > 230 and max(red, green, blue) - min(red, green, blue) <= 10:
                luminance = (red + green + blue) / 3
                softened = round(max(0, min(255, (248 - luminance) * 255 / 18)))
                pixels[x, y] = (red, green, blue, min(alpha, softened))

    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, optimize=True)


def build_depth_ambiguity_tiles() -> None:
    """Export native evidence tiles so labels stay crisp in responsive HTML.

    The crop, RGB background-only correction, ordering, and height pixels are
    shared with the paper builder.  Only the composite typography is moved to
    semantic HTML; no evidence pixels or measured values are regenerated.
    """

    source = Image.open(PAPER_SOURCE / "rq4_patch_depth" / "rgb_height_action.png").convert("RGB")
    destination = PUBLIC / "figures" / "depth-ambiguity"
    destination.mkdir(parents=True, exist_ok=True)

    rgb_tiles = [neutralize_rgb_background(tile) for tile in crop_row(source, RGB_Y)]
    height_tiles = crop_row(source, DEPTH_Y)
    ids = ("4", "3", "2", "1")
    for panel_id, rgb_tile, height_tile in zip(ids, rgb_tiles, height_tiles):
        rgb_tile.save(destination / f"rgb-{panel_id}.png", optimize=True)
        height_tile.save(destination / f"height-{panel_id}.png", optimize=True)

    samples = colormaps["turbo"](np.linspace(1.0, 0.0, 512))[:, :3]
    scale = np.uint8(np.clip(np.round(samples[:, None, :] * 255.0), 0, 255))
    scale = np.repeat(scale, 24, axis=1)
    Image.fromarray(scale).save(destination / "turbo-0-160.png", optimize=True)


def main() -> None:
    for name in SIMULATION_ASSETS:
        copy_exact(SIM_SOURCE / name, PUBLIC / "simulation" / name)

    copy_exact(EXPORT / "position_protocols_pi.png", PUBLIC / "figures" / "position-protocols.png")
    copy_exact(EXPORT / "rq2_data_efficiency.png", PUBLIC / "figures" / "rq2-data-efficiency.png")

    edge_connected_canvas(
        EXPORT / "rq4_visual_depth_ambiguity_strip.png",
        PUBLIC / "figures" / "depth-ambiguity-transparent.png",
    )
    edge_connected_canvas(
        EXPORT / "signed_contact_failures_cleaned.png",
        PUBLIC / "figures" / "contact-outcomes-transparent.png",
    )
    build_depth_ambiguity_tiles()


if __name__ == "__main__":
    main()
