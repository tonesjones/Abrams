"""Apply Sully-face UV + teal body recolors + portraits, then ready for VtexPacker."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance

SESSION = Path(
    r"C:\Users\Owner\.grok\sessions\C%3A%5CTestCode%5CAbrams\019fe34f-a791-76b1-a53a-c9039a574e66\images"
)
VANILLA = Path(r"C:\TestCode\Abrams\vanilla_clean\models\heroes_wip\abrams\materials")
OUT = Path(r"C:\TestCode\Abrams\sully_textures")
OUT.mkdir(parents=True, exist_ok=True)

# Teal palette matched to the Disney profile ref
SULLY_TEAL = np.array([45, 175, 185], dtype=np.float32)
SULLY_TEAL_DARK = np.array([20, 100, 115], dtype=np.float32)
SULLY_TEAL_LIGHT = np.array([110, 220, 215], dtype=np.float32)
SPOT_PURPLE = np.array([115, 70, 165], dtype=np.float32)
SPOT_PURPLE_DARK = np.array([65, 35, 100], dtype=np.float32)


def luminance(rgb: np.ndarray) -> np.ndarray:
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def make_spot_mask(h: int, w: int, seed: int, density: float = 0.11) -> np.ndarray:
    rng = np.random.default_rng(seed)
    mask = np.zeros((h, w), dtype=np.float32)
    n = max(int(density * (h * w) / (np.pi * 70**2)), 40)
    ys = rng.integers(0, h, size=n)
    xs = rng.integers(0, w, size=n)
    rs = rng.uniform(28, 150, size=n)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    for y, x, r in zip(ys, xs, rs):
        sx = float(r * rng.uniform(0.65, 1.35))
        sy = float(r * rng.uniform(0.65, 1.35))
        shear = float(rng.uniform(-0.25, 0.25))
        xd = (xx - x) + shear * (yy - y)
        yd = yy - y
        d = (xd / sx) ** 2 + (yd / sy) ** 2
        blob = np.clip(1.15 - d, 0, 1)
        blob = np.where(blob > 0.35, np.clip((blob - 0.15) / 0.85, 0, 1), blob * 0.4)
        mask = np.maximum(mask, np.power(np.clip(blob, 0, 1), 0.85).astype(np.float32))
    return np.clip(mask, 0, 1)


def fur_from_luminance(lum_n: np.ndarray) -> np.ndarray:
    t = np.clip((lum_n - 0.12) / 0.72, 0, 1)[..., None]
    t = t**0.85
    low = SULLY_TEAL_DARK[None, None, :] * (1 - t * 2) + SULLY_TEAL[None, None, :] * (t * 2)
    high = SULLY_TEAL[None, None, :] * (1 - (t - 0.5) * 2) + SULLY_TEAL_LIGHT[None, None, :] * (
        (t - 0.5) * 2
    )
    return np.where(t < 0.5, low, high)


def recolor_to_fur(img: Image.Image, seed: int, keep_leather: bool = False) -> Image.Image:
    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    h, w = arr.shape[:2]
    lum = luminance(arr)
    detail = (arr - lum[..., None]) * 0.35
    lum_n = np.clip((lum / 255.0 - 0.04) / 0.88, 0, 1)
    base = fur_from_luminance(lum_n)
    base = np.clip(base + detail * np.array([0.5, 1.0, 1.0]), 0, 255)
    spots = make_spot_mask(h, w, seed)
    valid = np.clip((lum - 6.0) / 20.0, 0, 1)
    spot_col = (
        SPOT_PURPLE_DARK[None, None, :] * (1 - lum_n[..., None])
        + SPOT_PURPLE[None, None, :] * lum_n[..., None]
    )
    s = spots[..., None] * 0.95 * valid[..., None]
    out = base * (1 - s) + spot_col * s
    if keep_leather:
        r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
        leather = ((r > g + 12) & (r > b + 5) & (lum > 28) & (lum < 170)).astype(np.float32)
        leather_col = np.array([78, 48, 42], dtype=np.float32)
        leather_shade = leather_col[None, None, :] * (0.45 + 0.7 * lum_n[..., None])
        out = out * (1 - leather[..., None] * 0.85) + leather_shade * (leather[..., None] * 0.85)
    out_img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")
    return ImageEnhance.Contrast(out_img).enhance(1.1)


def recolor_gun(img: Image.Image) -> Image.Image:
    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    lum_n = np.clip(luminance(arr) / 255.0, 0, 1)[..., None]
    dark = np.array([35, 40, 55], dtype=np.float32)
    mid = np.array([80, 110, 120], dtype=np.float32)
    light = np.array([150, 175, 185], dtype=np.float32)
    out = dark * (1 - lum_n) + mid * lum_n
    out = np.where(lum_n > 0.55, mid * (1 - (lum_n - 0.55) / 0.45) + light * ((lum_n - 0.55) / 0.45), out)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


def recolor_teeth(img: Image.Image) -> Image.Image:
    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    lum = luminance(arr) / 255.0
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    pinkish = ((r > g) & (r > b) & (lum > 0.12) & (lum < 0.72)).astype(np.float32)
    gum = np.array([155, 85, 115], dtype=np.float32)
    teeth = ((lum > 0.55) & (np.abs(r - g) < 30)).astype(np.float32)
    cream = np.array([245, 238, 220], dtype=np.float32)
    out = arr * (1 - pinkish[..., None] * 0.65) + gum * (pinkish[..., None] * 0.65)
    out = out * (1 - teeth[..., None] * 0.45) + cream * (teeth[..., None] * 0.45)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


def prepare_head_uv() -> None:
    # Prefer island-preserving UV (image 9); fallback to 6
    src = SESSION / "9.jpg"
    if not src.exists():
        src = SESSION / "6.jpg"
    im = Image.open(src).convert("RGB")
    im = im.resize((2048, 2048), Image.Resampling.LANCZOS)
    # Soft-clean pure mid-gray background to dark teal so unused texels don't flash gray
    arr = np.asarray(im, dtype=np.float32)
    # gray where R~G~B and mid
    diff = np.max(arr, axis=2) - np.min(arr, axis=2)
    mean = arr.mean(axis=2)
    gray = (diff < 18) & (mean > 90) & (mean < 170)
    fill = np.array([35, 120, 130], dtype=np.float32)
    arr[gray] = fill
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
    out = OUT / "abrams_head_color_png_ce8a55ec.png"
    im.save(out, format="PNG", compress_level=6)
    print(f"head UV -> {out}")


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
        top = max(0, (h - new_h) // 5)  # bias upward for face
        im = im.crop((0, top, w, min(h, top + new_h)))
    im = im.resize(size, Image.Resampling.LANCZOS)
    im = remove_near_black_bg(im)
    out = OUT / out_name
    im.save(out, format="PNG", compress_level=6)
    print(f"portrait {out_name} {im.size}")


def main() -> None:
    prepare_head_uv()

    jobs = [
        ("abrams_upper_body_color_png_798ad4a3.png", lambda im: recolor_to_fur(im, 22, True)),
        ("abrams_lower_body_color_png_8d3aa73d.png", lambda im: recolor_to_fur(im, 33, True)),
        ("abrams_coat_color_png_a3733b80.png", lambda im: recolor_to_fur(im, 11, True)),
        ("abrams_gun_color_png_3169bff9.png", recolor_gun),
        ("abrams_teeth_color_png_51646ccb.png", recolor_teeth),
    ]
    for name, fn in jobs:
        path = VANILLA / name
        out_im = fn(Image.open(path))
        out_im.save(OUT / name, format="PNG", compress_level=6)
        print(f"body {name}")

    # Portraits from reference-driven Imagine outputs (black bg, Sully likeness)
    card = SESSION / "5.jpg"
    if not card.exists():
        card = Path(r"C:\TestCode\Abrams\refs\sulley_profile.jpg")
    gloat = SESSION / "8.jpg" if (SESSION / "8.jpg").exists() else card
    crit = SESSION / "7.jpg" if (SESSION / "7.jpg").exists() else card
    fit_card(card, (280, 380), "bull_card_psd.png")
    fit_card(gloat, (280, 380), "bull_card_gloat_psd.png")
    fit_card(crit, (280, 380), "bull_card_critical_psd.png")
    fit_card(card, (128, 128), "bull_sm_psd.png")
    fit_card(card, (120, 200), "bull_vertical_psd.png")
    print("DONE")


if __name__ == "__main__":
    main()
