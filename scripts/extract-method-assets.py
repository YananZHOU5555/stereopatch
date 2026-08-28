from pathlib import Path

from PIL import Image, ImageEnhance


PROJECT = Path(__file__).resolve().parents[1]
SOURCE = Path(
    r"E:\OneDrive\文档\ICRA27\papers\StereoPatch\figures\source\stereopatch_dashboard_episode005.png"
)
OUTPUT = PROJECT / "public" / "media" / "figures"


def main() -> None:
    dashboard = Image.open(SOURCE).convert("RGB")
    rgb = dashboard.crop((17, 145, 416, 345))
    depth = dashboard.crop((417, 145, 816, 345))

    rgb = ImageEnhance.Contrast(ImageEnhance.Brightness(rgb).enhance(1.05)).enhance(1.05)
    depth = ImageEnhance.Contrast(depth).enhance(1.08)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    rgb.save(OUTPUT / "top-rgb.png", optimize=True)
    depth.save(OUTPUT / "depth-map.png", optimize=True)


if __name__ == "__main__":
    main()
