"""Render the StereoPatch stereo-disparity wordmark and paper-ready PNG lockups."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "brand"

SANS_SEMI = ROOT / "src" / "assets" / "fonts" / "SourceSans3-Semibold.ttf"
SERIF = ROOT / "src" / "assets" / "fonts" / "Newsreader-Variable.ttf"
MONO = Path(r"C:\Windows\Fonts\consola.ttf")

INK = "#111111"
SECONDARY = "#626862"
PAPER = "#FCFCF8"
DIVIDER = "#D8D6CD"
BLUE = "#8298CB"
YELLOW = "#E2D275"
SAGE = "#607F70"


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def tracked_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    face: ImageFont.FreeTypeFont,
    fill: str,
    tracking: int,
) -> int:
    x, y = xy
    start = x
    for glyph in text:
        draw.text((x, y), glyph, font=face, fill=fill)
        x += round(draw.textlength(glyph, font=face)) + tracking
    return x - start - tracking


def fused_patch(draw: ImageDraw.ImageDraw, x: int, y: int, size: int) -> None:
    outline = max(1, round(size * 0.045))
    draw.rounded_rectangle(
        (x, y, x + size, y + size),
        radius=max(2, round(size * 0.18)),
        fill=BLUE,
        outline=SAGE,
        width=outline,
    )
    corner = round(size * 0.30)
    pad = round(size * 0.10)
    draw.rounded_rectangle(
        (x + size - corner - pad, y + size - corner - pad, x + size - pad, y + size - pad),
        radius=max(1, round(size * 0.04)),
        fill=YELLOW,
    )


def custom_wordmark(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    size: int,
) -> tuple[int, int, int, int]:
    """Draw one exact wordmark: stereo disparity on Stereo, a fused patch in P."""
    x, y = xy
    face = font(SANS_SEMI, size)
    depth = max(1, round(size * 0.017))

    # Paired, restrained disparity edges. The black front face remains dominant.
    draw.text((x - depth, y + depth // 2), "Stereo", font=face, fill=BLUE)
    draw.text((x + depth, y - depth // 2), "Stereo", font=face, fill=YELLOW)
    draw.text((x, y), "Stereo", font=face, fill=INK)

    stereo_width = round(draw.textlength("Stereo", font=face))
    patch_x = x + stereo_width
    draw.text((patch_x, y), "Patch", font=face, fill=INK)

    # The counter of the capital P becomes the policy-facing fused patch.
    token_size = max(5, round(size * 0.112))
    fused_patch(
        draw,
        patch_x + round(size * 0.245),
        y + round(size * 0.155),
        token_size,
    )
    word_width = stereo_width + round(draw.textlength("Patch", font=face))
    return x, y, x + word_width, y + size


def render_wordmark() -> Image.Image:
    image = Image.new("RGBA", (3200, 620), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    custom_wordmark(draw, (100, 72), 390)
    return image


def render_title_rail(scale: int = 2) -> Image.Image:
    width, height = 2040 * scale, 168 * scale
    image = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(image)
    mono = font(MONO, 15 * scale)
    claim = font(SERIF, 45 * scale)

    left = 52 * scale
    tracked_text(
        draw,
        (left, 14 * scale),
        "DUAL-FOUNDATION · RGB-INDEXED GEOMETRY",
        mono,
        SECONDARY,
        max(1, scale),
    )
    right_meta = "DINOv3 × DeFM · ACT / DP"
    right_meta_width = round(draw.textlength(right_meta, font=mono))
    draw.text((width - 52 * scale - right_meta_width, 15 * scale), right_meta, font=mono, fill=SECONDARY)

    custom_wordmark(draw, (left, 45 * scale), 86 * scale)
    divider_x = 676 * scale
    draw.line((divider_x, 58 * scale, divider_x, 132 * scale), fill=DIVIDER, width=scale)
    draw.text(
        (716 * scale, 66 * scale),
        "Geometry, where the policy already looks.",
        font=claim,
        fill=INK,
    )
    draw.line((0, height - scale, width, height - scale), fill=DIVIDER, width=scale)
    return image


def render_teaser_composite(rail: Image.Image) -> Image.Image | None:
    figure_path = ROOT / "public" / "media" / "figures" / "teaser-task-suite.png"
    if not figure_path.exists():
        return None
    figure = Image.open(figure_path).convert("RGB")
    if figure.size != (2040, 1512):
        figure = figure.resize((2040, 1512), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (2040, 1680), PAPER)
    canvas.paste(rail, (0, 0))
    canvas.paste(figure, (0, 168))
    return canvas


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    render_wordmark().save(OUT / "stereopatch-wordmark-v3.png")

    rail_2x = render_title_rail(scale=2)
    rail_2x.save(OUT / "stereopatch-title-rail-teaser-v3.png", dpi=(300, 300))
    rail = rail_2x.resize((2040, 168), Image.Resampling.LANCZOS)
    rail.save(OUT / "stereopatch-title-rail-teaser-2040-v3.png", dpi=(300, 300))

    composite = render_teaser_composite(rail)
    if composite is not None:
        composite.save(OUT / "stereopatch-teaser-with-title-v3.png", dpi=(300, 300))


if __name__ == "__main__":
    main()
