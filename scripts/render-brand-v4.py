"""Render the final StereoPatch wireframe-depth wordmark and paper-title PNGs."""

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
STEREO_BLUE = "#C6CFDF"
STEREO_STONE = "#C0BDAD"
DIVIDER = "#D8D6CD"
ROBOT_BLUE = "#C7DBE8"
ROBOT_BLUE_DEEP = "#5E8BA1"
ROBOT_OUTLINE = "#8EAFBE"
ROBOT_FACE = "#FFFEFA"
ROBOT_FACE_OUTLINE = "#B2C4CB"
ROBOT_EYE = "#20272B"


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


def patch_counter_polygon(patch_x: int, y: int, size: int) -> list[tuple[int, int]]:
    x0 = patch_x + round(size * 0.225)
    y0 = y + round(size * 0.145)
    width = round(size * 0.195)
    height = round(size * 0.165)
    return [
        (x0, y0),
        (x0 + width, y0),
        (x0 + width, y0 + round(height * 0.68)),
        (x0 + round(width * 0.76), y0 + round(height * 0.68)),
        (x0 + round(width * 0.76), y0 + height),
        (x0, y0 + height),
    ]


def custom_wordmark(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    size: int,
    cutout_fill: str | tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    x, y = xy
    face = font(SANS_SEMI, size)
    blue_x = max(2, round(size * 0.030))
    blue_y = max(1, round(size * 0.024))
    stone_x = max(1, round(size * 0.017))
    stone_y = max(1, round(size * 0.004))

    # Two soft, crisp paper layers create spatial depth without blur.
    draw.text(
        (x - blue_x, y + blue_y),
        "Stereo",
        font=face,
        fill=STEREO_BLUE,
    )
    draw.text(
        (x - stone_x, y + stone_y),
        "Stereo",
        font=face,
        fill=STEREO_STONE,
    )
    draw.text((x, y), "Stereo", font=face, fill=INK)

    stereo_width = round(draw.textlength("Stereo", font=face))
    patch_x = x + stereo_width
    p_advance = round(draw.textlength("P", font=face))
    p_gap = round(size * 0.025)
    draw.text((patch_x + p_advance + p_gap, y), "atch", font=face, fill=INK)

    # A custom black P keeps the glyph intact while rounding the bowl into a robot head.
    stem_x = patch_x + round(size * 0.025)
    stem_y = y + round(size * 0.504)
    stem_w = round(size * 0.130)
    stem_h = round(size * 0.496)
    draw.rounded_rectangle(
        (stem_x, stem_y, stem_x + stem_w, stem_y + stem_h),
        radius=max(2, round(size * 0.035)),
        fill=INK,
    )
    head_x = patch_x + round(size * 0.025)
    head_y = y + round(size * 0.344)
    head_w = round(size * 0.580)
    head_h = round(size * 0.370)
    draw.rounded_rectangle(
        (head_x, head_y, head_x + head_w, head_y + head_h),
        radius=max(3, round(size * 0.160)),
        fill=INK,
    )

    counter_x = patch_x + round(size * 0.190)
    counter_y = y + round(size * 0.420)
    counter_w = round(size * 0.305)
    counter_h = round(size * 0.205)
    draw.rounded_rectangle(
        (counter_x, counter_y, counter_x + counter_w, counter_y + counter_h),
        radius=max(2, round(size * 0.064)),
        fill=cutout_fill,
    )

    eye_w = max(3, round(size * 0.052))
    eye_h = max(5, round(size * 0.080))
    eye_y = counter_y + round(counter_h * 0.31)
    for eye_x in (counter_x + round(counter_w * 0.24), counter_x + round(counter_w * 0.59)):
        draw.rounded_rectangle(
            (eye_x, eye_y, eye_x + eye_w, eye_y + eye_h),
            radius=max(2, round(eye_w * 0.48)),
            fill="#111111",
        )
        glint = max(1, round(size * 0.006))
        draw.ellipse(
            (eye_x + round(eye_w * 0.22), eye_y + round(eye_h * 0.14),
             eye_x + round(eye_w * 0.22) + glint, eye_y + round(eye_h * 0.14) + glint),
            fill=ROBOT_FACE,
        )
    word_width = stereo_width + round(draw.textlength("Patch", font=face))
    return x, y, x + word_width, y + size


def render_wordmark() -> Image.Image:
    image = Image.new("RGBA", (3200, 620), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    custom_wordmark(draw, (120, 72), 390, (0, 0, 0, 0))
    bbox = image.getbbox()
    if bbox is None:
        return image
    padding = 24
    left = max(0, bbox[0] - padding)
    top = max(0, bbox[1] - padding)
    right = min(image.width, bbox[2] + padding)
    bottom = min(image.height, bbox[3] + padding)
    return image.crop((left, top, right, bottom))


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
    meta_width = round(draw.textlength(right_meta, font=mono))
    draw.text((width - 52 * scale - meta_width, 15 * scale), right_meta, font=mono, fill=SECONDARY)

    custom_wordmark(draw, (left, 45 * scale), 86 * scale, PAPER)
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
    path = ROOT / "public" / "media" / "figures" / "teaser-task-suite.png"
    if not path.exists():
        return None
    figure = Image.open(path).convert("RGB")
    if figure.size != (2040, 1512):
        figure = figure.resize((2040, 1512), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (2040, 1680), PAPER)
    canvas.paste(rail, (0, 0))
    canvas.paste(figure, (0, 168))
    return canvas


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    wordmark = render_wordmark()
    wordmark.save(OUT / "stereopatch-wordmark-v13.png", dpi=(300, 300))
    wordmark.save(OUT / "StereoPatch-wordmark-only.png", dpi=(300, 300))
    rail_2x = render_title_rail(scale=2)
    rail_2x.save(OUT / "stereopatch-title-rail-teaser-v13.png", dpi=(300, 300))
    rail = rail_2x.resize((2040, 168), Image.Resampling.LANCZOS)
    rail.save(OUT / "stereopatch-title-rail-teaser-2040-v13.png", dpi=(300, 300))
    composite = render_teaser_composite(rail)
    if composite is not None:
        composite.save(OUT / "stereopatch-teaser-with-title-v13.png", dpi=(300, 300))


if __name__ == "__main__":
    main()
