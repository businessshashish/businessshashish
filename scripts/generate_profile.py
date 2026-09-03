"""Hero card -> profile.svg

Top: the Cortex system map from systems.txt, typed in row by row. Each cell's
role comes from systems.map, so shadows, fills, rules and labels each carry
their own weight instead of the whole drawing sitting on one flat tone.

Bottom: an identity strip — logo, role, live GitHub signals, ASCII face.

Everything is inlined. The page makes zero third-party requests.
"""

import base64
import io
import json
import os
import re
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent

SYSTEMS = ROOT / "systems.txt"
SYSTEMS_MAP = ROOT / "systems.map"
PORTRAIT = ROOT / "portrait.svg"
LOGO = ROOT / "assets" / "layerstop.png"
CONFIG = ROOT / "profile.json"
DATA = ROOT / "data.json"
OUTPUT = ROOT / "profile.svg"

USERNAME = "businessshashish"

WIDTH = 1200
HEIGHT = 850

BACKGROUND = "#0d1117"
LINE = "#30363d"
SOFT = "#21262d"

# One weight per role in systems.map — this is what gives the map depth.
WEIGHTS = {
    "h": "#f0f6fc",   # heading
    "t": "#d1d9e0",   # label text
    "m": "#7d8590",   # muted text
    "l": "#414b56",   # structure
    "f": "#21262d",   # shaded fill
    "s": "#171d24",   # drop shadow
    "a": "#39d353",   # live
}

TEXT = WEIGHTS["h"]
BODY = WEIGHTS["t"]
MUTED = WEIGHTS["m"]

# --- map -------------------------------------------------------------------

ART_X = 52
ART_Y = 40
ART_CELL_W = 7.32
ART_CELL_H = 15.5
ART_FONT = 12.2

TYPE_STEP = 0.045
TYPE_DUR = 0.40

# --- identity strip --------------------------------------------------------

STRIP_RULE = 638

LOGO_X = 52
IDENT_X = 245
SIGNAL_X = 600
FACE_X = 992
FACE_Y = 652


def esc(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def text(value, x, y, size=20, fill=TEXT, weight="400", anchor="start",
         letter_spacing="0"):
    return (
        f'<text x="{x}" y="{y}" font-family="monospace" '
        f'font-size="{size}px" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}" letter-spacing="{letter_spacing}px">'
        f'{esc(value)}</text>'
    )


# ==================================================
# INPUTS
# ==================================================

config = json.loads(CONFIG.read_text(encoding="utf-8"))

art_lines = SYSTEMS.read_text(encoding="utf-8").rstrip("\n").split("\n")
map_lines = SYSTEMS_MAP.read_text(encoding="utf-8").rstrip("\n").split("\n")

portrait = PORTRAIT.read_text(encoding="utf-8")
portrait = re.sub(r"^\s*<svg[^>]*>", "", portrait, count=1)
portrait = re.sub(r"</svg>\s*$", "", portrait, count=1)
portrait = re.sub(r'<rect class="bg"[^>]*/>', "", portrait, count=1)

# The mark is near-black, which disappears on a dark card. Keep its alpha,
# repaint the pixels white.
source_logo = Image.open(LOGO).convert("RGBA")
white_logo = Image.new("RGBA", source_logo.size, (255, 255, 255, 0))
white_logo.putalpha(source_logo.getchannel("A"))

buffer = io.BytesIO()
white_logo.save(buffer, format="PNG", optimize=True)
logo_href = "data:image/png;base64," + base64.b64encode(
    buffer.getvalue()
).decode("ascii")


data = {}

if DATA.exists():
    data = json.loads(DATA.read_text(encoding="utf-8"))

# A failed call must not publish zeros: keep the last known values and
# only write back what actually came off the wire.
headers = {"User-Agent": "businessshashish-profile"}

# Unauthenticated REST is 60 calls an hour per IP, which a few local runs
# will exhaust. CI already has a token; use it when it is there.
if os.environ.get("GITHUB_TOKEN"):
    headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]

try:
    request = Request(
        f"https://api.github.com/users/{USERNAME}",
        headers=headers,
    )
    with urlopen(request, timeout=10) as response:
        github = json.load(response)

    data["repositories"] = github["public_repos"]
    data["followers"] = github["followers"]

    DATA.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

except Exception:
    pass

contributions = data.get("contributions", 0)
repositories = data.get("repositories", 0)
followers = data.get("followers", 0)


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
# SYSTEM MAP
# ==================================================

ART_WIDTH = round(max(len(l) for l in art_lines) * ART_CELL_W, 2)

# Masks are padded past the glyph run: per-glyph advances round differently
# across platforms, and an unpadded mask leaks the last character of a row.
COVER_X = ART_X - 3
COVER_W = round(ART_WIDTH + 16, 2)

for index, raw in enumerate(art_lines):

    roles = (map_lines[index] if index < len(map_lines) else "")
    roles = roles.ljust(len(raw), ".")

    baseline = round(ART_Y + index * ART_CELL_H + ART_FONT - 0.5, 2)

    start = 0

    while start < len(raw):

        role = roles[start]

        stop = start
        while stop < len(raw) and roles[stop] == role:
            stop += 1

        if role != ".":
            svg.append(
                f'<text x="{round(ART_X + start * ART_CELL_W, 2)}" '
                f'y="{baseline}" font-family="monospace" '
                f'font-size="{ART_FONT}px" fill="{WEIGHTS.get(role, BODY)}" '
                f'xml:space="preserve">{esc(raw[start:stop])}</text>'
            )

        start = stop


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
    f'<line x1="40" y1="{STRIP_RULE}" x2="{WIDTH - 40}" y2="{STRIP_RULE}" '
    f'stroke="{LINE}" stroke-width="1"/>'
)


# ==================================================
# IDENTITY STRIP
# ==================================================

svg.append(
    '<g opacity="0">'
    '<animate attributeName="opacity" from="0" to="1" dur="0.55s" '
    'begin="0.2s" fill="freeze"/>'
)

svg.append(
    f'<image href="{logo_href}" x="{LOGO_X}" y="672" width="150" '
    f'height="83" preserveAspectRatio="xMinYMid meet"/>'
)

svg.append(
    text(config["tagline"], IDENT_X, 682, size=12, fill=MUTED,
         letter_spacing="2")
)
svg.append(
    text(config["role"], IDENT_X, 720, size=27, weight="700",
         letter_spacing="1")
)
svg.append(text(config["company"], IDENT_X, 746, size=15, fill=MUTED))

svg.append(
    text("BUILDING  " + "  .  ".join(config["focus"]), IDENT_X, 782,
         size=12, fill=MUTED, letter_spacing="1")
)

signals = [
    ("CONTRIBUTIONS", contributions),
    ("PUBLIC REPOS", repositories),
    ("FOLLOWERS", followers),
]

largest = max([value for _, value in signals] + [1])

for index, (label, value) in enumerate(signals):

    x = SIGNAL_X + index * 122

    svg.append(text(value, x, 720, size=26, weight="700"))
    svg.append(text(label, x, 742, size=10, fill=MUTED, letter_spacing="1"))

    filled = max(3, int((value / largest) * 100))

    svg.append(
        f'<rect x="{x}" y="756" width="100" height="4" fill="{SOFT}" rx="2"/>'
    )
    svg.append(
        f'<rect x="{x}" y="756" width="{filled}" height="4" '
        f'fill="{BODY}" rx="2"/>'
    )

svg.append("</g>")


# ==================================================
# ASCII FACE
# ==================================================

svg.append(f'<g transform="translate({FACE_X},{FACE_Y})">')
svg.append(portrait)
svg.append("</g>")

svg.append("</svg>")

OUTPUT.write_text("\n".join(svg), encoding="utf-8")

print(f"Generated {OUTPUT.name}  map {len(art_lines)} rows")
print(f"Signals: {contributions} / {repositories} / {followers}")
