"""Render deterministic StereoPatch PNG identity assets and a hero mockup."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "brand"
QA = ROOT / ".qa" / "brand"

INK = "#252925"
INK_STRONG = "#111411"
SECONDARY = "#626862"
PAGE = "#FCFCF8"
SURFACE = "#F3F3F0"
BORDER = "#CDD2CB"
DIVIDER = "#E1E4DF"
BLUE = "#8298CB"
BLUE_DARK = "#6F86BF"
YELLOW = "#E2D275"
YELLOW_DARK = "#B6A343"
SAGE = "#759586"
SAGE_DARK = "#607F70"

SERIF = Path(r"C:\Windows\Fonts\SitkaVF.ttf")
SERIF_ITALIC = Path(r"C:\Windows\Fonts\SitkaVF-Italic.ttf")
SANS = ROOT / "public" / "fonts" / "SourceSans3-Regular.ttf"
SANS_SEMI = ROOT / "public" / "fonts" / "SourceSans3-Semibold.ttf"


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def draw_grid(draw: ImageDraw.ImageDraw, x: int, y: int, cell: int, gap: int,
              fill: str, outline: str, radius: int, width: int) -> tuple[int, int, int, int]:
    for row in range(2):
        for col in range(2):
            x0 = x + col * (cell + gap)
            y0 = y + row * (cell + gap)
            draw.rounded_rectangle(
                (x0, y0, x0 + cell, y0 + cell),
                radius=radius,
                fill=fill,
                outline=outline,
                width=width,
            )
    side = cell * 2 + gap
    return x, y, x + side, y + side


def draw_mark(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0) -> tuple[int, int, int, int]:
    s = lambda value: round(value * scale)
    cell, gap = s(52), s(12)
    radius, outline = s(9), max(2, s(3))
    blue_box = draw_grid(draw, x, y + s(24), cell, gap, BLUE, BLUE_DARK, radius, outline)
    yellow_box = draw_grid(draw, x, y + s(172), cell, gap, YELLOW, YELLOW_DARK, radius, outline)

    token_x, token_y, token_size = x + s(244), y + s(105), s(142)
    # Two quiet registration routes; no arrowheads, glow, or network-diagram clutter.
    route_width = max(2, s(4))
    draw.line(
        (blue_box[2] + s(15), (blue_box[1] + blue_box[3]) // 2,
         token_x - s(18), token_y + s(44)),
        fill=BLUE_DARK,
        width=route_width,
    )
    draw.line(
        (yellow_box[2] + s(15), (yellow_box[1] + yellow_box[3]) // 2,
         token_x - s(18), token_y + token_size - s(44)),
        fill=YELLOW_DARK,
        width=route_width,
    )
    draw.rounded_rectangle(
        (token_x, token_y, token_x + token_size, token_y + token_size),
        radius=s(20),
        fill=BLUE,
        outline=SAGE_DARK,
        width=max(3, s(6)),
    )
    corner = s(34)
    pad = s(15)
    draw.rounded_rectangle(
        (
            token_x + token_size - corner - pad,
            token_y + token_size - corner - pad,
            token_x + token_size - pad,
            token_y + token_size - pad,
        ),
        radius=s(6),
        fill=YELLOW,
        outline=YELLOW_DARK,
        width=max(2, s(3)),
    )
    # Registration tick: the shared address, not a decorative sparkle.
    tick = s(16)
    cx, cy = token_x + token_size // 2, token_y + token_size // 2
    draw.line((cx - tick, cy, cx + tick, cy), fill=SAGE_DARK, width=max(2, s(3)))
    draw.line((cx, cy - tick, cx, cy + tick), fill=SAGE_DARK, width=max(2, s(3)))
    return x, y, token_x + token_size, y + s(320)


def render_wordmark() -> Image.Image:
    canvas = Image.new("RGBA", (3200, 640), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw_mark(draw, 64, 126, 1.18)

    text_y = 112
    stereo_font = font(SERIF, 338)
    patch_font = font(SERIF_ITALIC, 338)
    text_x = 590
    draw.text((text_x, text_y), "Stereo", font=stereo_font, fill=INK_STRONG, anchor="la")
    stereo_width = draw.textlength("Stereo", font=stereo_font)
    draw.text(
        (text_x + round(stereo_width) - 5, text_y),
        "Patch",
        font=patch_font,
        fill=SAGE_DARK,
        anchor="la",
    )
    return canvas


def render_mark_square() -> Image.Image:
    canvas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw_mark(draw, 62, 122, 2.25)
    return canvas


def render_teaser_lockup(wordmark: Image.Image) -> Image.Image:
    canvas = Image.new("RGBA", (3200, 1000), (0, 0, 0, 0))
    mark = wordmark.resize((2880, 576), Image.Resampling.LANCZOS)
    canvas.alpha_composite(mark, (160, 72))
    draw = ImageDraw.Draw(canvas)
    draw.line((640, 690, 2560, 690), fill=DIVIDER, width=3)
    claim_font = font(SERIF_ITALIC, 102)
    draw.text(
        (1600, 790),
        "Geometry, where the policy already looks.",
        font=claim_font,
        fill=INK,
        anchor="mm",
    )
    return canvas


def render_design_board(wordmark: Image.Image, lockup: Image.Image) -> Image.Image:
    board = Image.new("RGB", (2400, 1500), PAGE)
    draw = ImageDraw.Draw(board)
    label = font(SANS_SEMI, 34)
    meta = font(SANS, 29)
    draw.text((120, 92), "STEREOPATCH · IDENTITY SYSTEM", font=label, fill=SECONDARY)
    draw.text((2280, 92), "ACADEMIC / WEB / TEASER", font=label, fill=SECONDARY, anchor="ra")
    draw.line((120, 148, 2280, 148), fill=DIVIDER, width=3)

    main = wordmark.resize((2080, 416), Image.Resampling.LANCZOS)
    board.paste(main, (160, 220), main)
    draw.text((1200, 685), "MASTER HORIZONTAL WORDMARK", font=meta, fill=SECONDARY, anchor="ma")

    draw.rounded_rectangle((120, 775, 2280, 1350), radius=28, fill="#F6F4EF", outline=BORDER, width=3)
    teaser = lockup.resize((1920, 600), Image.Resampling.LANCZOS)
    board.paste(teaser, (240, 740), teaser)
    draw.text((120, 1430), "Mechanism encoded in the mark: semantic patches + metric geometry → fused token", font=meta, fill=SECONDARY)
    return board


def render_hero_mockup(wordmark: Image.Image) -> Image.Image | None:
    source = ROOT / ".qa" / "screenshots" / "desktop-hero.png"
    if not source.exists():
        return None
    image = Image.open(source).convert("RGB")
    draw = ImageDraw.Draw(image)
    # Replace only the current kicker/title region; retain the real website evidence below.
    draw.rectangle((38, 95, 945, 474), fill=PAGE)
    brand = wordmark.resize((800, 160), Image.Resampling.LANCZOS)
    image.paste(brand, (44, 116), brand)
    claim_regular = font(SERIF, 61)
    claim_italic = font(SERIF_ITALIC, 61)
    draw.text((50, 307), "Geometry, where the policy", font=claim_regular, fill=INK_STRONG)
    draw.text((50, 375), "already looks.", font=claim_italic, fill=SAGE_DARK)
    return image


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)
    wordmark = render_wordmark()
    lockup = render_teaser_lockup(wordmark)
    render_mark_square().save(OUT / "stereopatch-mark-v1.png")
    wordmark.save(OUT / "stereopatch-wordmark-horizontal-v1.png")
    lockup.save(OUT / "stereopatch-lockup-teaser-v1.png")
    render_design_board(wordmark, lockup).save(QA / "stereopatch-brand-board-v1.png")
    hero = render_hero_mockup(wordmark)
    if hero is not None:
        hero.save(QA / "stereopatch-hero-mockup-v1.png")


if __name__ == "__main__":
    main()
