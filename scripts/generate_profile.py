"""Hero card -> profile.svg

Left: the systems map from systems.txt, typed in row by row.
Right: identity, live GitHub signals, and a small ASCII face.

Everything is inlined. The page makes zero third-party requests.
"""

import base64
import io
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent

SYSTEMS = ROOT / "systems.txt"
PORTRAIT = ROOT / "portrait.svg"
LOGO = ROOT / "assets" / "layerstop.png"
CONFIG = ROOT / "profile.json"
DATA = ROOT / "data.json"
OUTPUT = ROOT / "profile.svg"

USERNAME = "businessshashish"

WIDTH = 1200
HEIGHT = 660

BACKGROUND = "#0d1117"
TEXT = "#f0f0f0"
BODY = "#c9d1d9"
MUTED = "#8b949e"
LINE = "#30363d"
SOFT = "#21262d"
ACCENT = "#39d353"

# --- systems map -----------------------------------------------------------

ART_X = 30
ART_Y = 83
ART_CELL_W = 7.8
ART_CELL_H = 17
ART_FONT = 13

TYPE_STEP = 0.05
TYPE_DUR = 0.42

DIVIDER_X = 670

# --- right column ----------------------------------------------------------

RIGHT = 720
RIGHT_EDGE = 1145

FACE_X = 968
FACE_Y = 450


# ==================================================
# HELPERS
# ==================================================

def esc(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def text(
    value,
    x,
    y,
    size=20,
    fill=TEXT,
    weight="400",
    anchor="start",
    letter_spacing="0",
):
    return (
        f'<text x="{x}" y="{y}" font-family="monospace" '
        f'font-size="{size}px" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}" letter-spacing="{letter_spacing}px">'
        f'{esc(value)}</text>'
    )


def rule(y, x1=RIGHT, x2=RIGHT_EDGE, stroke=LINE):
    return (
        f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" '
        f'stroke="{stroke}" stroke-width="1"/>'
    )


# ==================================================
# INPUTS
# ==================================================

config = json.loads(CONFIG.read_text(encoding="utf-8"))

role = config["role"]
company = config["company"]
tagline = config["tagline"]
focus = config["focus"]

art_lines = SYSTEMS.read_text(encoding="utf-8").rstrip("\n").split("\n")


# Portrait: drop the wrapper and its standalone background, keep the animation.
portrait = PORTRAIT.read_text(encoding="utf-8")
portrait = re.sub(r"^\s*<svg[^>]*>", "", portrait, count=1)
portrait = re.sub(r"</svg>\s*$", "", portrait, count=1)
portrait = re.sub(r'<rect class="bg"[^>]*/>', "", portrait, count=1)


# Logo: the source art is near-black, which disappears on a dark card.
# Keep its alpha, repaint the pixels white.
source_logo = Image.open(LOGO).convert("RGBA")

white_logo = Image.new("RGBA", source_logo.size, (255, 255, 255, 0))
white_logo.putalpha(source_logo.getchannel("A"))

buffer = io.BytesIO()
white_logo.save(buffer, format="PNG", optimize=True)

logo_href = (
    "data:image/png;base64,"
    + base64.b64encode(buffer.getvalue()).decode("ascii")
)


# ==================================================
# GITHUB SIGNALS
# ==================================================

repositories = 0
followers = 0

try:
    request = Request(
        f"https://api.github.com/users/{USERNAME}",
        headers={"User-Agent": "businessshashish-profile"},
    )

    with urlopen(request, timeout=10) as response:
        github = json.load(response)

    repositories = github.get("public_repos", 0)
    followers = github.get("followers", 0)

except Exception:
    pass


contributions = 0

if DATA.exists():
    contributions = json.loads(
        DATA.read_text(encoding="utf-8")
    ).get("contributions", 0)


# ==================================================
# CANVAS
# ==================================================

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
    f'height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',

    f'<rect width="100%" height="100%" fill="{BACKGROUND}"/>',

    f'<rect x="12" y="12" width="{WIDTH - 24}" height="{HEIGHT - 24}" '
    f'rx="8" fill="none" stroke="{LINE}"/>',
]


# ==================================================
# SYSTEMS MAP
# ==================================================

ART_WIDTH = round(len(max(art_lines, key=len)) * ART_CELL_W, 2)

# Masks are padded past the glyph run: per-glyph advances round
# differently across platforms, and an unpadded mask leaks the last
# character of every row.
COVER_X = ART_X - 3
COVER_W = round(ART_WIDTH + 16, 2)

# Row colours: the frame reads quieter than the diagram it holds.
ROW_COLOURS = {0: TEXT, 1: LINE, 3: MUTED}

for index, raw in enumerate(art_lines):

    baseline = round(ART_Y + index * ART_CELL_H + ART_FONT - 0.5, 2)

    fill = ROW_COLOURS.get(index, BODY)

    if raw.strip().startswith("RUNTIME") or (
        index == len(art_lines) - 1
    ):
        fill = MUTED

    # Status markers are drawn separately so they can carry the accent.
    markers = [m.span() for m in re.finditer(r"\[on\]", raw)]

    body = raw

    for start, stop in markers:
        body = body[:start] + " " * (stop - start) + body[stop:]

    svg.append(
        f'<text x="{ART_X}" y="{baseline}" font-family="monospace" '
        f'font-size="{ART_FONT}px" fill="{fill}" xml:space="preserve">'
        f'{esc(body)}</text>'
    )

    for start, stop in markers:
        svg.append(
            f'<text x="{round(ART_X + start * ART_CELL_W, 2)}" '
            f'y="{baseline}" font-family="monospace" '
            f'font-size="{ART_FONT}px" fill="{ACCENT}" '
            f'xml:space="preserve">{esc(raw[start:stop])}</text>'
        )


# Type it in: a cover slides right, a block rides the edge.
for index in range(len(art_lines)):

    begin = round(index * TYPE_STEP, 2)
    done = round(begin + TYPE_DUR, 2)
    top = round(ART_Y + index * ART_CELL_H, 2)

    svg.append(
        f'<rect x="{COVER_X}" y="{top - 0.5}" width="{COVER_W}" '
        f'height="{ART_CELL_H + 1}" fill="{BACKGROUND}">'
        f'<animate attributeName="x" from="{COVER_X}" '
        f'to="{round(COVER_X + COVER_W, 2)}" dur="{TYPE_DUR}s" '
        f'begin="{begin}s" fill="freeze"/>'
        f'<animate attributeName="width" from="{COVER_W}" to="0" '
        f'dur="{TYPE_DUR}s" begin="{begin}s" fill="freeze"/>'
        f'</rect>'
    )

    svg.append(
        f'<rect x="{ART_X}" y="{top + 2}" width="{ART_CELL_W}" '
        f'height="{ART_CELL_H - 4}" fill="{TEXT}" opacity="0">'
        f'<animate attributeName="x" from="{ART_X}" '
        f'to="{round(ART_X + ART_WIDTH, 2)}" dur="{TYPE_DUR}s" '
        f'begin="{begin}s" fill="freeze"/>'
        f'<set attributeName="opacity" to="0.85" begin="{begin}s"/>'
        f'<set attributeName="opacity" to="0" begin="{done}s"/>'
        f'</rect>'
    )


svg.append(
    f'<line x1="{DIVIDER_X}" y1="45" x2="{DIVIDER_X}" y2="{HEIGHT - 45}" '
    f'stroke="{LINE}" stroke-width="1"/>'
)


# ==================================================
# RIGHT COLUMN
# ==================================================

svg.append(
    '<g opacity="0">'
    '<animate attributeName="opacity" from="0" to="1" dur="0.55s" '
    'begin="0.15s" fill="freeze"/>'
)

svg.append(
    f'<image href="{logo_href}" x="{RIGHT}" y="38" width="210" '
    f'height="110" preserveAspectRatio="xMinYMid meet"/>'
)

svg.append(text(tagline, RIGHT, 182, size=17, fill=MUTED, letter_spacing="2"))
svg.append(rule(200))

svg.append(text(role, RIGHT, 243, size=28, weight="700", letter_spacing="1"))
svg.append(text(company, RIGHT, 273, size=17, fill=MUTED, letter_spacing="1"))

svg.append(
    text("PROFILE SIGNALS", RIGHT, 320, size=14, fill=MUTED, letter_spacing="2")
)

signals = [
    ("CONTRIBUTIONS", contributions),
    ("PUBLIC REPOS", repositories),
    ("FOLLOWERS", followers),
]

largest = max([value for _, value in signals] + [1])

for index, (label, value) in enumerate(signals):

    x = RIGHT + index * 135

    svg.append(text(value, x, 366, size=28, weight="700"))
    svg.append(text(label, x, 391, size=10, fill=MUTED, letter_spacing="1"))

    filled = max(3, int((value / largest) * 90))

    svg.append(
        f'<rect x="{x}" y="406" width="90" height="4" fill="{SOFT}" rx="2"/>'
    )
    svg.append(
        f'<rect x="{x}" y="406" width="{filled}" height="4" '
        f'fill="{TEXT}" rx="2"/>'
    )


svg.append(rule(440))

svg.append(
    text(
        "CURRENTLY BUILDING",
        RIGHT,
        476,
        size=14,
        fill=MUTED,
        letter_spacing="2",
    )
)

focus_y = 512

for item in focus:
    svg.append(text("→ " + item, RIGHT, focus_y, size=18))
    focus_y += 32

svg.append("</g>")


# ==================================================
# ASCII FACE
# ==================================================

svg.append(f'<g transform="translate({FACE_X},{FACE_Y})">')
svg.append(portrait)
svg.append("</g>")

svg.append("</svg>")

OUTPUT.write_text("\n".join(svg), encoding="utf-8")

print(f"Generated {OUTPUT.name}")
print(f"Systems map: {len(art_lines)} rows")
print(f"Signals: {contributions} contributions, "
      f"{repositories} repos, {followers} followers")
