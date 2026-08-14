"""Recolor Abrams hero textures into a Sulley-inspired blue fur + purple spots look."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

SRC = Path(r"C:\TestCode\Abrams\vanilla_clean\models\heroes_wip\abrams\materials")
OUT = Path(r"C:\TestCode\Abrams\sully_textures")
OUT.mkdir(parents=True, exist_ok=True)

# Sulley-inspired palette (cyan-blue fur, violet spots)
SULLY_BLUE = np.array([62, 168, 214], dtype=np.float32)
SULLY_BLUE_DARK = np.array([28, 88, 132], dtype=np.float32)
SULLY_BLUE_LIGHT = np.array([140, 210, 235], dtype=np.float32)
SPOT_PURPLE = np.array([120, 72, 175], dtype=np.float32)
SPOT_PURPLE_DARK = np.array([62, 34, 105], dtype=np.float32)
EYE_GREEN = np.array([80, 210, 75], dtype=np.float32)
EYE_PUPIL = np.array([20, 30, 25], dtype=np.float32)


def luminance(rgb: np.ndarray) -> np.ndarray:
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def make_spot_mask(
    h: int,
    w: int,
    seed: int,
    density: float = 0.11,
    min_r: float = 28,
    max_r: float = 140,
) -> np.ndarray:
    """Irregular purple-spot mask with hardish edges like cartoon spots."""
    rng = np.random.default_rng(seed)
    mask = np.zeros((h, w), dtype=np.float32)
    avg_r = (min_r + max_r) / 2.0
    n = int(density * (h * w) / (np.pi * avg_r**2))
    n = max(n, 40)
    ys = rng.integers(0, h, size=n)
    xs = rng.integers(0, w, size=n)
    rs = rng.uniform(min_r, max_r, size=n)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    for y, x, r in zip(ys, xs, rs):
        sx = float(r * rng.uniform(0.65, 1.35))
        sy = float(r * rng.uniform(0.65, 1.35))
        # slight rotation via shear noise
        shear = float(rng.uniform(-0.25, 0.25))
        xd = (xx - x) + shear * (yy - y)
        yd = (yy - y)
        d = (xd / sx) ** 2 + (yd / sy) ** 2
        # hard-ish edge with soft rim
        blob = np.clip(1.15 - d, 0, 1)
        blob = np.where(blob > 0.35, np.clip((blob - 0.15) / 0.85, 0, 1), blob * 0.4)
        blob = np.power(np.clip(blob, 0, 1), 0.85)
        mask = np.maximum(mask, blob.astype(np.float32))
    return np.clip(mask, 0, 1)


def fur_from_luminance(lum_n: np.ndarray) -> np.ndarray:
    """Map normalized luminance to Sulley blue fur, keeping shading."""
    dark = SULLY_BLUE_DARK
    mid = SULLY_BLUE
    light = SULLY_BLUE_LIGHT
    # piecewise blend
    t = lum_n[..., None]
    # boost mid contrast a bit
    t = np.clip((t - 0.15) / 0.7, 0, 1)
    t = t**0.85
    low = dark[None, None, :] * (1 - t * 2) + mid[None, None, :] * (t * 2)
    high = mid[None, None, :] * (1 - (t - 0.5) * 2) + light[None, None, :] * ((t - 0.5) * 2)
    base = np.where(t < 0.5, low, high)
    return base


def apply_spots(base: np.ndarray, spots: np.ndarray, lum_n: np.ndarray, strength: float = 0.95) -> np.ndarray:
    spot_col = (
        SPOT_PURPLE_DARK[None, None, :] * (1 - lum_n[..., None])
        + SPOT_PURPLE[None, None, :] * lum_n[..., None]
    )
    s = spots[..., None] * strength
    return base * (1 - s) + spot_col * s


def recolor_to_fur(
    img: Image.Image,
    seed: int,
    strong_spots: bool = True,
    keep_leather: bool = False,
) -> Image.Image:
    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    h, w = arr.shape[:2]
    lum = luminance(arr)
    # Preserve original micro-detail as residual
    detail = arr - lum[..., None]
    detail = detail * 0.35

    lum_n = np.clip((lum / 255.0 - 0.04) / 0.88, 0, 1)
    base = fur_from_luminance(lum_n)
    base = np.clip(base + detail * np.array([0.6, 0.9, 1.0]), 0, 255)

    spots = make_spot_mask(
        h,
        w,
        seed,
        density=0.12 if strong_spots else 0.07,
        min_r=24,
        max_r=150,
    )
    # Don't paint spots on pure black UV voids
    valid = np.clip((lum - 6.0) / 20.0, 0, 1)
    out = apply_spots(base, spots * valid, lum_n, strength=0.96)

    if keep_leather:
        r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
        leather = ((r > g + 12) & (r > b + 5) & (lum > 28) & (lum < 170)).astype(np.float32)
        leather_col = np.array([78, 48, 42], dtype=np.float32)
        # keep leather shading
        leather_shade = leather_col[None, None, :] * (0.45 + 0.7 * lum_n[..., None])
        out = out * (1 - leather[..., None] * 0.85) + leather_shade * (leather[..., None] * 0.85)

    # slight local contrast
    out_img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")
    out_img = ImageEnhance_Contrast(out_img, 1.12)
    return out_img


def ImageEnhance_Contrast(img: Image.Image, factor: float) -> Image.Image:
    from PIL import ImageEnhance

    return ImageEnhance.Contrast(img).enhance(factor)


def recolor_head(img: Image.Image) -> Image.Image:
    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    h, w = arr.shape[:2]
    lum = luminance(arr)
    detail = (arr - lum[..., None]) * 0.4
    lum_n = np.clip((lum / 255.0 - 0.03) / 0.85, 0, 1)
    base = fur_from_luminance(lum_n)
    base = np.clip(base + detail * np.array([0.5, 0.85, 1.0]), 0, 255)

    spots = make_spot_mask(h, w, seed=7, density=0.09, min_r=30, max_r=160)
    valid = np.clip((lum - 5.0) / 18.0, 0, 1)
    out = apply_spots(base, spots * valid, lum_n, strength=0.92)

    # Green eyes: original has orange/red emissive pupils + dark sockets
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    orange_eye = (
        (r > 70) & (r > g * 1.15) & (r > b * 1.05) & (g < 140) & (b < 120)
    ).astype(np.float32)
    dark_pupil = ((lum < 38) & (lum > 4)).astype(np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    face = (
        (xx > w * 0.04) & (xx < w * 0.72) & (yy > h * 0.22) & (yy < h * 0.78)
    ).astype(np.float32)
    iris = orange_eye * face
    pupil = dark_pupil * face * (1.0 - orange_eye)
    out = out * (1 - iris[..., None] * 0.95) + EYE_GREEN * (iris[..., None] * 0.95)
    out = out * (1 - pupil[..., None] * 0.85) + EYE_PUPIL * (pupil[..., None] * 0.85)

    # Dark hair/brows -> slightly deeper blue fur (already in base)

    out_img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")
    return ImageEnhance_Contrast(out_img, 1.15)


def recolor_gun(img: Image.Image) -> Image.Image:
    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    lum_n = np.clip(luminance(arr) / 255.0, 0, 1)
    # purple-metal gun
    dark = np.array([35, 30, 50], dtype=np.float32)
    mid = np.array([95, 85, 125], dtype=np.float32)
    light = np.array([170, 160, 195], dtype=np.float32)
    t = lum_n[..., None]
    out = dark * (1 - t) + mid * t
    out = np.where(t > 0.55, mid * (1 - (t - 0.55) / 0.45) + light * ((t - 0.55) / 0.45), out)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


def recolor_teeth(img: Image.Image) -> Image.Image:
    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    lum = luminance(arr) / 255.0
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    pinkish = ((r > g) & (r > b) & (lum > 0.12) & (lum < 0.72)).astype(np.float32)
    gum = np.array([155, 85, 115], dtype=np.float32)
    # teeth slightly cream
    teeth = ((lum > 0.55) & (np.abs(r - g) < 30)).astype(np.float32)
    cream = np.array([245, 238, 220], dtype=np.float32)
    out = arr.copy()
    out = out * (1 - pinkish[..., None] * 0.65) + gum * (pinkish[..., None] * 0.65)
    out = out * (1 - teeth[..., None] * 0.45) + cream * (teeth[..., None] * 0.45)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


JOBS = [
    ("abrams_head_color_png_ce8a55ec.png", recolor_head),
    (
        "abrams_upper_body_color_png_798ad4a3.png",
        lambda im: recolor_to_fur(im, 22, True, True),
    ),
    (
        "abrams_lower_body_color_png_8d3aa73d.png",
        lambda im: recolor_to_fur(im, 33, True, True),
    ),
    (
        "abrams_coat_color_png_a3733b80.png",
        lambda im: recolor_to_fur(im, 11, True, True),
    ),
    ("abrams_gun_color_png_3169bff9.png", recolor_gun),
    ("abrams_teeth_color_png_51646ccb.png", recolor_teeth),
]


def main() -> None:
    for name, fn in JOBS:
        path = SRC / name
        if not path.exists():
            raise SystemExit(f"Missing source texture: {path}")
        print(f"Processing {name}")
        out_im = fn(Image.open(path))
        # Ensure PNG RGB (no alpha) for DeadMod-style PNG_RGBA path we convert later
        if out_im.mode != "RGB":
            out_im = out_im.convert("RGB")
        out_path = OUT / name
        out_im.save(out_path, format="PNG", compress_level=6)
        print(f"  saved {out_path} {out_im.size}")
    print("DONE")


if __name__ == "__main__":
    main()
