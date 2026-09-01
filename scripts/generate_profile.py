import base64
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent

PORTRAIT = ROOT / "portrait.svg"
LOGO = ROOT / "assets" / "layerstop.png"
CONFIG = ROOT / "profile.json"
OUTPUT = ROOT / "profile.svg"

WIDTH = 1200
HEIGHT = 760

BACKGROUND = "#0d1117"
TEXT = "#f0f0f0"
MUTED = "#8b949e"
LINE = "#30363d"
SOFT = "#21262d"


# ==================================================
# LOAD CONFIG
# ==================================================

with open(CONFIG, "r", encoding="utf-8") as f:
    config = json.load(f)

role = config["role"]
company = config["company"]
tagline = config["tagline"]
focus = config["focus"]


# ==================================================
# LOAD PORTRAIT
# ==================================================

with open(PORTRAIT, "r", encoding="utf-8") as f:
    portrait_svg = f.read()


# Remove outer SVG tag
portrait_content = re.sub(
    r"^\s*<svg[^>]*>",
    "",
    portrait_svg,
    count=1,
)

portrait_content = re.sub(
    r"</svg>\s*$",
    "",
    portrait_content,
    count=1,
)


# --------------------------------------------------
# Remove ONLY the portrait background.
# Keep all text, clip paths and animations.
# --------------------------------------------------

portrait_content = re.sub(
    r'<rect\s+width="100%"\s+height="100%"\s+fill="#0d1117"\s*/>',
    "",
    portrait_content,
    count=1,
)


# --------------------------------------------------
# Prevent duplicate IDs from causing conflicts.
# --------------------------------------------------

portrait_content = portrait_content.replace(
    'id="row',
    'id="portrait_row'
)

portrait_content = portrait_content.replace(
    'url(#row',
    'url(#portrait_row'
)


# ==================================================
# LOAD LOGO
# ==================================================

with open(LOGO, "rb") as f:
    logo_data = base64.b64encode(
        f.read()
    ).decode("ascii")

logo_href = f"data:image/png;base64,{logo_data}"


# ==================================================
# GITHUB DATA
# ==================================================

USERNAME = "businessshashish"

request = Request(
    f"https://api.github.com/users/{USERNAME}",
    headers={
        "User-Agent": "businessshashish-profile-generator"
    },
)

try:

    with urlopen(
        request,
        timeout=10
    ) as response:

        github = json.load(response)

    repositories = github.get(
        "public_repos",
        0
    )

    followers = github.get(
        "followers",
        0
    )

except Exception:

    repositories = 0
    followers = 0


# ==================================================
# CONTRIBUTIONS
# ==================================================

contributions = 0

stats_file = ROOT / "stats.svg"

if stats_file.exists():

    with open(
        stats_file,
        "r",
        encoding="utf-8"
    ) as f:

        stats_svg = f.read()

    match = re.search(
        r"CONTRIBUTIONS:\s*(\d+)",
        stats_svg
    )

    if match:
        contributions = int(
            match.group(1)
        )


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
        f'<text '
        f'x="{x}" '
        f'y="{y}" '
        f'font-family="monospace" '
        f'font-size="{size}px" '
        f'font-weight="{weight}" '
        f'fill="{fill}" '
        f'text-anchor="{anchor}" '
        f'letter-spacing="{letter_spacing}px">'
        f'{esc(value)}'
        f'</text>'
    )


def line(x1, y1, x2, y2, stroke=LINE):

    return (
        f'<line '
        f'x1="{x1}" '
        f'y1="{y1}" '
        f'x2="{x2}" '
        f'y2="{y2}" '
        f'stroke="{stroke}" '
        f'stroke-width="1"/>'
    )


# ==================================================
# BUILD SVG
# ==================================================

svg = []

svg.append(
    f'<svg '
    f'xmlns="http://www.w3.org/2000/svg" '
    f'width="{WIDTH}" '
    f'height="{HEIGHT}" '
    f'viewBox="0 0 {WIDTH} {HEIGHT}">'
)


# ==================================================
# MAIN BACKGROUND
# ==================================================

svg.append(
    f'<rect '
    f'width="100%" '
    f'height="100%" '
    f'fill="{BACKGROUND}"/>'
)


# Border

svg.append(
    f'<rect '
    f'x="12" '
    f'y="12" '
    f'width="{WIDTH - 24}" '
    f'height="{HEIGHT - 24}" '
    f'rx="8" '
    f'fill="none" '
    f'stroke="{LINE}"/>'
)


# ==================================================
# PORTRAIT
# ==================================================

PORTRAIT_X = 35
PORTRAIT_Y = 35
PORTRAIT_SCALE = 0.72

svg.append(
    f'<g '
    f'transform="translate({PORTRAIT_X},{PORTRAIT_Y}) '
    f'scale({PORTRAIT_SCALE})">'
)

svg.append(
    portrait_content
)

svg.append("</g>")


# ==================================================
# DIVIDER
# ==================================================

svg.append(
    line(
        670,
        45,
        670,
        HEIGHT - 45
    )
)


# ==================================================
# RIGHT SIDE
# ==================================================

RIGHT = 720


# ==================================================
# LOGO
# ==================================================

svg.append(
    f'<image '
    f'href="{logo_href}" '
    f'x="{RIGHT}" '
    f'y="55" '
    f'width="220" '
    f'height="121" '
    f'preserveAspectRatio="xMidYMid meet"/>'
)


# ==================================================
# TAGLINE
# ==================================================

svg.append(
    text(
        tagline,
        RIGHT,
        205,
        size=17,
        fill=MUTED,
        letter_spacing="2",
    )
)

svg.append(
    line(
        RIGHT,
        225,
        1145,
        225
    )
)


# ==================================================
# IDENTITY
# ==================================================

svg.append(
    text(
        role,
        RIGHT,
        270,
        size=28,
        weight="700",
        letter_spacing="1",
    )
)

svg.append(
    text(
        company,
        RIGHT,
        302,
        size=17,
        fill=MUTED,
        letter_spacing="1",
    )
)


# ==================================================
# PROFILE SIGNALS
# ==================================================

svg.append(
    text(
        "PROFILE SIGNALS",
        RIGHT,
        355,
        size=14,
        fill=MUTED,
        letter_spacing="2",
    )
)

metric_y = 405

metrics = [
    ("CONTRIBUTIONS", contributions),
    ("PUBLIC REPOS", repositories),
    ("FOLLOWERS", followers),
]

max_metric = max(
    [value for _, value in metrics] + [1]
)


for i, (label, value) in enumerate(metrics):

    x = RIGHT + i * 135

    svg.append(
        text(
            str(value),
            x,
            metric_y,
            size=28,
            weight="700",
        )
    )

    svg.append(
        text(
            label,
            x,
            metric_y + 25,
            size=10,
            fill=MUTED,
            letter_spacing="1",
        )
    )

    bar_width = 90

    filled = max(
        3,
        int(
            (value / max_metric)
            * bar_width
        )
    )

    svg.append(
        f'<rect '
        f'x="{x}" '
        f'y="{metric_y + 40}" '
        f'width="{bar_width}" '
        f'height="4" '
        f'fill="{SOFT}" '
        f'rx="2"/>'
    )

    svg.append(
        f'<rect '
        f'x="{x}" '
        f'y="{metric_y + 40}" '
        f'width="{filled}" '
        f'height="4" '
        f'fill="{TEXT}" '
        f'rx="2"/>'
    )


# ==================================================
# CURRENTLY BUILDING
# ==================================================

svg.append(
    line(
        RIGHT,
        485,
        1145,
        485
    )
)

svg.append(
    text(
        "CURRENTLY BUILDING",
        RIGHT,
        525,
        size=14,
        fill=MUTED,
        letter_spacing="2",
    )
)

focus_y = 565

for item in focus:

    svg.append(
        text(
            "→ " + item,
            RIGHT,
            focus_y,
            size=18,
            fill=TEXT,
        )
    )

    focus_y += 32


# ==================================================
# FOOTER
# ==================================================

svg.append(
    line(
        RIGHT,
        675,
        1145,
        675
    )
)

svg.append(
    text(
        "GENERATED PROFILE",
        RIGHT,
        710,
        size=11,
        fill=MUTED,
        letter_spacing="2",
    )
)

svg.append(
    text(
        "AUTO-REFRESH",
        1145,
        710,
        size=11,
        fill=MUTED,
        anchor="end",
        letter_spacing="2",
    )
)


# ==================================================
# CLOSE SVG
# ==================================================

svg.append("</svg>")


# ==================================================
# WRITE FILE
# ==================================================

with open(
    OUTPUT,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "\n".join(svg)
    )


print("Generated profile.svg")
print("Portrait animation embedded directly")
print(f"Contributions: {contributions}")
print(f"Public repositories: {repositories}")
print(f"Followers: {followers}")
