"""Generate logo.ico from logo.png for Windows exe/installer."""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PNG = ROOT / "assets" / "logo.png"
ICO = ROOT / "assets" / "logo.ico"


def main() -> None:
    if not PNG.exists():
        print(f"Missing {PNG}")
        return
    img = Image.open(PNG).convert("RGBA")
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(ICO, format="ICO", sizes=sizes)
    print(f"Created {ICO}")


if __name__ == "__main__":
    main()
