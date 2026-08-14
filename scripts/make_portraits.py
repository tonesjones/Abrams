"""Resize Imagine art into Deadlock Abrams UI portrait slots with alpha."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

SESSION = Path(
    r"C:\Users\Owner\.grok\sessions\C%3A%5CTestCode%5CAbrams\019fe34f-a791-76b1-a53a-c9039a574e66\images"
)
OUT = Path(r"C:\TestCode\Abrams\sully_textures")
OUT.mkdir(parents=True, exist_ok=True)

# Prefer edited portrait for main card; critical for crit card; gloat from main smiling
CARD = SESSION / "2.jpg"
if not CARD.exists():
    CARD = SESSION / "1.jpg"
GLOAT = SESSION / "3.jpg"
CRIT = SESSION / "4.jpg"


def remove_near_black_bg(img: Image.Image, threshold: int = 28) -> Image.Image:
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if r <= threshold and g <= threshold and b <= threshold:
                pixels[x, y] = (r, g, b, 0)
    return img


def fit_card(src: Path, size: tuple[int, int], out_name: str) -> None:
    im = Image.open(src).convert("RGBA")
    # Crop center to target aspect
    tw, th = size
    target_aspect = tw / th
    w, h = im.size
    aspect = w / h
    if aspect > target_aspect:
        new_w = int(h * target_aspect)
        left = (w - new_w) // 2
        im = im.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target_aspect)
        top = (h - new_h) // 2
        im = im.crop((0, top, w, top + new_h))
    im = im.resize(size, Image.Resampling.LANCZOS)
    im = remove_near_black_bg(im)
    out = OUT / out_name
    im.save(out, format="PNG", compress_level=6)
    print(f"saved {out} {im.size} {im.mode}")


def main() -> None:
    fit_card(CARD, (280, 380), "bull_card_psd.png")
    fit_card(GLOAT if GLOAT.exists() else CARD, (280, 380), "bull_card_gloat_psd.png")
    fit_card(CRIT if CRIT.exists() else CARD, (280, 380), "bull_card_critical_psd.png")
    fit_card(CARD, (128, 128), "bull_sm_psd.png")
    fit_card(CARD, (120, 200), "bull_vertical_psd.png")
    print("DONE portraits")


if __name__ == "__main__":
    main()
