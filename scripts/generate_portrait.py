"""ASCII portrait -> portrait.svg

Small on purpose: the GitHub avatar already carries the photograph, so this
is a texture in the identity strip, not the hero itself.

Reads assets/portrait_cutout.png (background already removed, committed to the
repo) so CI needs nothing heavier than pillow + numpy. If the cutout is missing
it falls back to rembg on assets/portrait.jpg and writes the cutout for reuse.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent

CUTOUT = ROOT / "assets" / "portrait_cutout.png"
SOURCE = ROOT / "assets" / "portrait.jpg"
OUTPUT = ROOT / "portrait.svg"

COLS = 37

CELL_W = 4.05
CELL_H = 6.9
FONT_SIZE = 6.7

# Dark -> light
RAMP = "@%#*+cs=:-.` "

BACKGROUND = "#0d1117"
TEXT_COLOR = "#c9d1d9"

# The systems map types itself in first; the face follows it.
BASE_DELAY = 1.05
ROW_STEP = 0.035
ROW_DUR = 0.30


# --------------------------------------------------
# Source image
# --------------------------------------------------

if CUTOUT.exists():
    image = Image.open(CUTOUT).convert("RGBA")
else:
    from rembg import remove

    image = remove(Image.open(SOURCE).convert("RGBA"))

    bbox = image.getchannel("A").getbbox()
    if bbox:
        image = image.crop(bbox)

    image.thumbnail((600, 600), Image.Resampling.LANCZOS)
    image.save(CUTOUT, optimize=True)


alpha = image.getchannel("A")

gray = ImageOps.grayscale(image.convert("RGB"))
gray = ImageEnhance.Contrast(gray).enhance(1.35)
gray = gray.filter(ImageFilter.GaussianBlur(radius=0.35))


# --------------------------------------------------
# Grid
# --------------------------------------------------

width, height = gray.size

cols = COLS
rows = max(1, int(cols * (height / width) * 0.48))

brightness = np.array(
    gray.resize((cols, rows), Image.Resampling.LANCZOS)
).astype(np.float32)

# Darkening curve: without it a side-lit face flattens into one tone.
brightness = np.clip(np.power(brightness / 255.0, 1.7) * 255.0, 0, 255)

mask = np.array(
    alpha.resize((cols, rows), Image.Resampling.LANCZOS)
).astype(np.float32)


# --------------------------------------------------
# Brightness -> characters
# --------------------------------------------------

ramp_length = len(RAMP)

ascii_rows = []

for y in range(rows):

    line = ""

    for x in range(cols):

        if mask[y, x] < 35:
            line += " "
            continue

        value = brightness[y, x] * (mask[y, x] / 255.0)

        index = int(value / 255 * (ramp_length - 1))
        index = max(0, min(ramp_length - 1, index))

        line += RAMP[index]

    ascii_rows.append(line)


# --------------------------------------------------
# SVG
# --------------------------------------------------

SVG_WIDTH = round(cols * CELL_W, 2)
SVG_HEIGHT = round(rows * CELL_H, 2)

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'width="{SVG_WIDTH}" height="{SVG_HEIGHT}" '
    f'viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}">',
    f'<rect class="bg" width="100%" height="100%" fill="{BACKGROUND}"/>',
]


for y, row in enumerate(ascii_rows):

    escaped = (
        row.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )

    baseline = round(y * CELL_H + CELL_H - 1.4, 2)

    svg.append(
        f'<text x="0" y="{baseline}" '
        f'font-family="monospace" font-size="{FONT_SIZE}px" '
        f'fill="{TEXT_COLOR}" xml:space="preserve">{escaped}</text>'
    )


# Left-to-right reveal, one row at a time. The mask runs past the glyph
# run so a rounded advance can't leak the last character of a row.
COVER_W = round(SVG_WIDTH + 6, 2)
# Left-to-right reveal, one row at a time.
for y in range(rows):

    begin = round(BASE_DELAY + y * ROW_STEP, 2)
    top = round(y * CELL_H, 2)

    svg.append(
        f'<rect x="-2" y="{round(top - 0.5, 2)}" width="{COVER_W}" '
        f'height="{round(CELL_H + 1, 2)}" fill="{BACKGROUND}">'
        f'<animate attributeName="x" from="-2" to="{COVER_W - 2}" '
        f'dur="{ROW_DUR}s" begin="{begin}s" fill="freeze"/>'
        f'<animate attributeName="width" from="{COVER_W}" to="0" '
        f'dur="{ROW_DUR}s" begin="{begin}s" fill="freeze"/>'
        f'</rect>'
    )


svg.append("</svg>")

OUTPUT.write_text("\n".join(svg), encoding="utf-8")

print(f"Generated {OUTPUT.name}  {cols} x {rows}")
