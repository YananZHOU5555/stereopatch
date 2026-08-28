"""Render the approved StereoPatch editorial masthead as high-resolution PNGs."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "brand"

SOURCE_SANS_SEMIBOLD = ROOT / "src" / "assets" / "fonts" / "SourceSans3-Semibold.ttf"
NEWSREADER = ROOT / "src" / "assets" / "fonts" / "Newsreader-Variable.ttf"
MONO = Path(r"C:\Windows\Fonts\consola.ttf")

INK = "#111111"
SECONDARY = "#626862"
PAPER = "#FCFCF8"
DIVIDER = "#D8D6CD"
TOKEN_BLUE = "#8298CB"
TOKEN_YELLOW = "#E2D275"
TOKEN_OUTLINE = "#607F70"


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def draw_tracked_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    face: ImageFont.FreeTypeFont,
    fill: str,
    tracking: int,
) -> int:
    """Draw a short metadata label with deterministic tracking; return its width."""
    x, y = xy
    origin = x
    for character in text:
        draw.text((x, y), character, font=face, fill=fill)
        x += round(draw.textlength(character, font=face)) + tracking
    return x - origin - tracking


def draw_token(draw: ImageDraw.ImageDraw, x: int, y: int, size: int) -> None:
    radius = max(3, round(size * 0.13))
    outline = max(2, round(size * 0.025))
    draw.rounded_rectangle(
        (x, y, x + size, y + size),
        radius=radius,
        fill=TOKEN_BLUE,
        outline=TOKEN_OUTLINE,
        width=outline,
    )
    inset_size = round(size * 0.27)
    inset_pad = round(size * 0.11)
    draw.rounded_rectangle(
        (
            x + size - inset_size - inset_pad,
            y + size - inset_size - inset_pad,
            x + size - inset_pad,
            y + size - inset_pad,
        ),
        radius=max(1, round(size * 0.035)),
        fill=TOKEN_YELLOW,
    )


def render_wordmark() -> Image.Image:
    """Transparent master wordmark for slides, paper figures, and social cards."""
    image = Image.new("RGBA", (3200, 620), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    title_font = font(SOURCE_SANS_SEMIBOLD, 390)
    x, y = 100, 72
    draw.text((x, y), "StereoPatch", font=title_font, fill=INK)
    text_width = round(draw.textlength("StereoPatch", font=title_font))
    token_size = 108
    draw_token(draw, x + text_width + 48, 122, token_size)
    return image


def render_title_rail(scale: int = 2) -> Image.Image:
    """2040×168 logical-pixel paper title rail, rendered at 2× by default."""
    width, height = 2040 * scale, 168 * scale
    image = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(image)

    mono = font(MONO, 16 * scale)
    title = font(SOURCE_SANS_SEMIBOLD, 86 * scale)
    claim = font(NEWSREADER, 41 * scale)

    left = 52 * scale
    draw_tracked_text(
        draw,
        (left, 15 * scale),
        "DUAL-FOUNDATION · RGB-INDEXED GEOMETRY RETRIEVAL",
        mono,
        SECONDARY,
        max(1, round(0.9 * scale)),
    )
    draw.text((left, 47 * scale), "StereoPatch", font=title, fill=INK)
    title_width = round(draw.textlength("StereoPatch", font=title))
    token_size = 25 * scale
    draw_token(draw, left + title_width + 14 * scale, 59 * scale, token_size)

    claim_text = "Geometry, where the policy already looks."
    claim_width = round(draw.textlength(claim_text, font=claim))
    draw.text((width - 52 * scale - claim_width, 69 * scale), claim_text, font=claim, fill=INK)
    draw.line((0, height - scale, width, height - scale), fill=DIVIDER, width=scale)
    return image


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    render_wordmark().save(OUT / "stereopatch-wordmark-v2.png")
    rail_2x = render_title_rail(scale=2)
    rail_2x.save(OUT / "stereopatch-title-rail-teaser-v2.png", dpi=(300, 300))
    rail_2x.resize((2040, 168), Image.Resampling.LANCZOS).save(
        OUT / "stereopatch-title-rail-teaser-2040-v2.png",
        dpi=(300, 300),
    )


if __name__ == "__main__":
    main()
