from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import numpy as np

from rembg import remove


INPUT = "assets/portrait.jpg"
OUTPUT = "portrait.svg"

COLS = 110

# Dark → light
RAMP = "@%#*+cs=:-.` "

BACKGROUND = "#0d1117"
TEXT_COLOR = "#f0f0f0"


# --------------------------------------------------
# 1. Read image
# --------------------------------------------------

image = Image.open(INPUT).convert("RGBA")


# --------------------------------------------------
# 2. Remove background
# --------------------------------------------------

image = remove(image)


# --------------------------------------------------
# 3. Crop tightly around the person
# --------------------------------------------------

alpha = image.getchannel("A")

bbox = alpha.getbbox()

if bbox:
    image = image.crop(bbox)
    alpha = image.getchannel("A")


# --------------------------------------------------
# 4. Prepare the person's brightness
# --------------------------------------------------

rgb = image.convert("RGB")

gray = ImageOps.grayscale(rgb)

gray = ImageEnhance.Contrast(gray).enhance(1.35)

gray = gray.filter(
    ImageFilter.GaussianBlur(radius=0.35)
)


# --------------------------------------------------
# 5. Convert to numpy
# --------------------------------------------------

brightness = np.array(gray).astype(np.float32)
alpha_array = np.array(alpha).astype(np.float32)


# --------------------------------------------------
# 6. Darken brightness for better ASCII depth
# --------------------------------------------------

brightness = brightness / 255.0

brightness = np.power(brightness, 1.7)

brightness = brightness * 255.0

brightness = np.clip(brightness, 0, 255)


# --------------------------------------------------
# 7. Calculate ASCII dimensions
# --------------------------------------------------

width, height = gray.size

cols = COLS

rows = max(
    1,
    int(cols * (height / width) * 0.48)
)


# --------------------------------------------------
# 8. Resize brightness + alpha mask
# --------------------------------------------------

small_brightness = gray.resize(
    (cols, rows),
    Image.Resampling.LANCZOS
)

small_brightness = np.array(
    small_brightness
).astype(np.float32)

small_alpha = alpha.resize(
    (cols, rows),
    Image.Resampling.LANCZOS
)

small_alpha = np.array(
    small_alpha
).astype(np.float32)


# --------------------------------------------------
# 9. Convert brightness → ASCII
# --------------------------------------------------

ramp_length = len(RAMP)

ascii_rows = []

for y in range(rows):

    line = ""

    for x in range(cols):

        a = small_alpha[y, x]

        b = small_brightness[y, x]

        # Completely transparent = no character
        if a < 35:
            line += " "
            continue

        # Fade characters near the edge of the subject
        effective_brightness = b * (a / 255.0)

        index = int(
            effective_brightness / 255
            * (ramp_length - 1)
        )

        index = max(
            0,
            min(ramp_length - 1, index)
        )

        line += RAMP[index]

    ascii_rows.append(line)


# --------------------------------------------------
# 10. Create SVG
# --------------------------------------------------

CELL_WIDTH = 8
CELL_HEIGHT = 14

SVG_WIDTH = cols * CELL_WIDTH
SVG_HEIGHT = rows * CELL_HEIGHT

svg = []

svg.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'width="{SVG_WIDTH}" '
    f'height="{SVG_HEIGHT}" '
    f'viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}">'
)


# --------------------------------------------------
# 11. Dark background
# --------------------------------------------------

svg.append(
    f'<rect width="100%" height="100%" fill="{BACKGROUND}"/>'
)


# --------------------------------------------------
# 12. Add ASCII rows
# --------------------------------------------------

for y, row in enumerate(ascii_rows):

    escaped = (
        row
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    y_position = (
        y * CELL_HEIGHT
        + CELL_HEIGHT
    )

    svg.append(
        f'<text '
        f'x="0" '
        f'y="{y_position}" '
        f'font-family="monospace" '
        f'font-size="13px" '
        f'font-weight="400" '
        f'fill="{TEXT_COLOR}" '
        f'xml:space="preserve">'
        f'{escaped}'
        f'</text>'
    )


# --------------------------------------------------
# 13. Animate the ASCII rows
# --------------------------------------------------

for y in range(rows):

    delay = y * 0.09

    svg.append(
        f'<rect '
        f'x="0" '
        f'y="{y * CELL_HEIGHT}" '
        f'width="{SVG_WIDTH}" '
        f'height="{CELL_HEIGHT}" '
        f'fill="{BACKGROUND}" '
        f'opacity="1">'
        f'<animate '
        f'attributeName="opacity" '
        f'from="1" '
        f'to="0" '
        f'dur="0.35s" '
        f'begin="{delay:.2f}s" '
        f'fill="freeze"/>'
        f'</rect>'
    )


# --------------------------------------------------
# 14. Close SVG
# --------------------------------------------------

svg.append("</svg>")


# --------------------------------------------------
# 15. Write file
# --------------------------------------------------

with open(
    OUTPUT,
    "w",
    encoding="utf-8"
) as f:

    f.write("\n".join(svg))


print("Generated portrait.svg")
print(f"Size: {cols} × {rows}")
