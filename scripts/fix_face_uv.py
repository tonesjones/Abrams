"""Surgical Sully face composite onto Abrams head UV + softened normals."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

mat = Path(r"C:\TestCode\Abrams\vanilla_clean\models\heroes_wip\abrams\materials")
session = Path(
    r"C:\Users\Owner\.grok\sessions\C%3A%5CTestCode%5CAbrams\019fe34f-a791-76b1-a53a-c9039a574e66\images"
)
out = Path(r"C:\TestCode\Abrams\sully_textures")
fix = Path(r"C:\TestCode\Abrams\face_fix")
out.mkdir(exist_ok=True)
fix.mkdir(exist_ok=True)

vanilla = Image.open(mat / "abrams_head_color_png_ce8a55ec.png").convert("RGB")
van = np.asarray(vanilla, dtype=np.float32)

sully_uv = Image.open(session / "11.jpg").convert("RGB").resize(
    (2048, 2048), Image.Resampling.LANCZOS
)
sully = np.asarray(sully_uv, dtype=np.float32)

y1, y2, x1, x2 = 720, 1520, 120, 1120
lum = 0.2126 * van[..., 0] + 0.7152 * van[..., 1] + 0.0722 * van[..., 2]
valid = (lum > 12).astype(np.float32)

yy, xx = np.mgrid[0:2048, 0:2048].astype(np.float32)
cx, cy = (x1 + x2) / 2, (y1 + y2) / 2 + 40
rx, ry = (x2 - x1) / 2 * 0.92, (y2 - y1) / 2 * 0.95
ell = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
face_mask = np.clip(1.15 - ell, 0, 1).astype(np.float32)
face_mask = np.power(face_mask, 1.3) * valid

# Prefer prior Sully UV paint across painted head texels
result = van * (1 - valid[..., None] * 0.92) + sully * (valid[..., None] * 0.92)
result = result * (1 - face_mask[..., None]) + sully * face_mask[..., None]

# Hard green eyes at UV eye landmarks
for ex, ey in [(420, 950), (720, 950)]:
    d = np.sqrt((xx - ex) ** 2 + (yy - ey) ** 2)
    iris = np.clip(1 - d / 42, 0, 1)
    pupil = np.clip(1 - d / 16, 0, 1)
    green = np.array([70, 200, 70], dtype=np.float32)
    black = np.array([15, 25, 15], dtype=np.float32)
    result = result * (1 - iris[..., None] * 0.95) + green * (iris[..., None] * 0.95)
    result = result * (1 - pupil[..., None] * 0.95) + black * (pupil[..., None] * 0.95)

# Snout over nose
nx, ny = 570, 1050
d = np.sqrt((xx - nx) ** 2 + (yy - ny) ** 2)
snout = np.clip(1 - d / 70, 0, 1) ** 1.2
snout_col = np.array([40, 55, 90], dtype=np.float32)
result = result * (1 - snout[..., None] * 0.55) + snout_col * (snout[..., None] * 0.55)

# Cover goatee with fur
gx, gy = 570, 1320
d = np.sqrt((xx - gx) ** 2 + ((yy - gy) / 0.7) ** 2)
goat = np.clip(1 - d / 90, 0, 1)
fur = np.array([50, 175, 185], dtype=np.float32)
result = result * (1 - goat[..., None] * 0.85) + fur * (goat[..., None] * 0.85)

# Extra purple spots on face
rng = np.random.default_rng(42)
for _ in range(12):
    sx = int(rng.integers(x1 + 80, x2 - 80))
    sy = int(rng.integers(y1 + 80, y2 - 80))
    r = float(rng.uniform(35, 90))
    sx_s = r * float(rng.uniform(0.7, 1.3))
    sy_s = r * float(rng.uniform(0.7, 1.3))
    d = np.sqrt(((xx - sx) / sx_s) ** 2 + ((yy - sy) / sy_s) ** 2)
    blob = np.clip(1.1 - d, 0, 1) ** 1.5 * face_mask
    purp = np.array([110, 60, 160], dtype=np.float32)
    result = result * (1 - blob[..., None] * 0.75) + purp * (blob[..., None] * 0.75)

out_im = Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))
out_im = ImageEnhance.Contrast(out_im).enhance(1.08)
out_im = ImageEnhance.Color(out_im).enhance(1.1)
out_im.save(out / "abrams_head_color_png_ce8a55ec.png")
out_im.save(out / "abrams_head_basecolor_png_f84c4214.png")
out_im.save(fix / "final_head_color.png")
print("color saved")

# Soften normals on face only (keep Z/blue channel-ish)
normal = Image.open(mat / "abrams_head_normal.png").convert("RGB")
n = np.asarray(normal, dtype=np.float32)
strength = face_mask * 0.88
n[..., 0] = n[..., 0] * (1 - strength) + 128.0 * strength
n[..., 1] = n[..., 1] * (1 - strength) + 128.0 * strength
n[..., 2] = n[..., 2] * (1 - strength * 0.5) + 255.0 * (strength * 0.5)
n_img = Image.fromarray(np.clip(n, 0, 255).astype(np.uint8))
blur = n_img.filter(ImageFilter.GaussianBlur(2))
nb = np.asarray(blur, dtype=np.float32)
n = n * (1 - face_mask[..., None] * 0.45) + nb * (face_mask[..., None] * 0.45)
Image.fromarray(np.clip(n, 0, 255).astype(np.uint8)).save(
    out / "abrams_head_normal_png_20d421b4.png"
)
print("normal softened")

Image.fromarray(np.zeros((2048, 2048), dtype=np.uint8), "L").save(
    out / "abrams_head_emmisive_mask_png_1f8bb825.png"
)
print("emissive off")
print("DONE")
