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


# -----------------------------
# Load profile configuration
# -----------------------------

with open(CONFIG, "r", encoding="utf-8") as f:
    config = json.load(f)

role = config["role"]
company = config["company"]
tagline = config["tagline"]
focus = config["focus"]


# -----------------------------
# Load portrait SVG
# -----------------------------

with open(PORTRAIT, "r", encoding="utf-8") as f:
    portrait_svg = f.read()

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


# -----------------------------
# Load Layerstop logo
# -----------------------------

with open(LOGO, "rb") as f:
    logo_data = base64.b64encode(f.read()).decode("ascii")

logo_href = f"data:image/png;base64,{logo_data}"


# -----------------------------
# GitHub data
# -----------------------------

USERNAME = "businessshashish"

github_url = f"https://api.github.com/users/{USERNAME}"

request = Request(
    github_url,
    headers={
        "User-Agent": "businessshashish-profile-generator"
    },
)

try:
    with urlopen(request, timeout=10) as response:
        github = json.load(response)

    repositories = github.get("public_repos", 0)
    followers = github.get("followers", 0)

except Exception:
    repositories = 0
    followers = 0


# -----------------------------
# Contributions from stats.svg
# -----------------------------

contributions = 0

stats_file = ROOT / "stats.svg"

if stats_file.exists():

    with open(stats_file, "r", encoding="utf-8") as f:
        stats_svg = f.read()

    match = re.search(
        r"CONTRIBUTIONS:\s*(\d+)",
        stats_svg
    )

    if match:
        contributions = int(match.group(1))


# -----------------------------
# Helpers
# -----------------------------

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
        f'<text x="{x}" y="{y}" '
        f'font-family="monospace" '
        f'font-size="{size}px" '
        f'font-weight="{weight}" '
        f'fill="{fill}" '
        f'text-anchor="{anchor}" '
        f'letter-spacing="{letter_spacing}px">'
        f'{esc(value)}</text>'
    )


def line(x1, y1, x2, y2, stroke=LINE):
    return (
        f'<line x1="{x1}" y1="{y1}" '
        f'x2="{x2}" y2="{y2}" '
        f'stroke="{stroke}" stroke-width="1"/>'
    )


# -----------------------------
# Build SVG
# -----------------------------

svg = []

svg.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'width="{WIDTH}" height="{HEIGHT}" '
    f'viewBox="0 0 {WIDTH} {HEIGHT}">'
)

svg.append(
    f'<rect width="100%" height="100%" fill="{BACKGROUND}"/>'
)

svg.append(
    f'<rect x="12" y="12" width="{WIDTH - 24}" '
    f'height="{HEIGHT - 24}" rx="8" '
    f'fill="none" stroke="{LINE}"/>'
)


# -----------------------------
# Portrait
# -----------------------------

PORTRAIT_X = 35
PORTRAIT_Y = 35
PORTRAIT_SCALE = 0.72

svg.append(
    f'<g transform="translate({PORTRAIT_X},{PORTRAIT_Y}) '
    f'scale({PORTRAIT_SCALE})">'
)

svg.append(portrait_content)

svg.append("</g>")


# -----------------------------
# Divider
# -----------------------------

svg.append(
    line(670, 45, 670, HEIGHT - 45)
)


# -----------------------------
# Right side
# -----------------------------

RIGHT = 720


# Layerstop logo

svg.append(
    f'<image href="{logo_href}" '
    f'x="{RIGHT}" y="55" '
    f'width="220" height="121" '
    f'preserveAspectRatio="xMidYMid meet"/>'
)


# Tagline

svg.append(
    text(
        tagline,
        RIGHT,
        205,
        size=17,
        fill=MUTED,
        weight="400",
        letter_spacing="2",
    )
)

svg.append(
    line(RIGHT, 225, 1145, 225)
)


# Identity

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


# -----------------------------
# Profile signals
# -----------------------------

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
        int((value / max_metric) * bar_width)
    )

    svg.append(
        f'<rect x="{x}" y="{metric_y + 40}" '
        f'width="{bar_width}" height="4" '
        f'fill="{SOFT}" rx="2"/>'
    )

    svg.append(
        f'<rect x="{x}" y="{metric_y + 40}" '
        f'width="{filled}" height="4" '
        f'fill="{TEXT}" rx="2"/>'
    )


# -----------------------------
# Current work
# -----------------------------

svg.append(
    line(RIGHT, 485, 1145, 485)
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


# -----------------------------
# Footer
# -----------------------------

svg.append(
    line(RIGHT, 675, 1145, 675)
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


svg.append("</svg>")


# -----------------------------
# Write output
# -----------------------------

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(svg))

print("Generated profile.svg")
print(f"Contributions: {contributions}")
print(f"Public repositories: {repositories}")
print(f"Followers: {followers}")
