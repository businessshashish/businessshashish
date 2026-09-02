"""System metrics -> stats.svg

GitHub already draws a contribution calendar directly below the README, so
this row shows what that calendar cannot: what the systems actually produced.

Numbers live in metrics.json. Each tile's block meter is one block per unit,
capped at the grid, so a zero is empty space rather than an implied value.
Also refreshes data.json (contribution total) for the hero's profile signals.
"""

import json
import os
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CONFIG = ROOT / "metrics.json"
DATA = ROOT / "data.json"
OUTPUT = ROOT / "stats.svg"

WIDTH = 1200
HEIGHT = 270

BACKGROUND = "#0d1117"
TEXT = "#f0f0f0"
MUTED = "#8b949e"
LINE = "#30363d"

# GitHub contribution greens
EMPTY = "#161b22"
FILL_A = "#26a641"
FILL_B = "#39d353"

MARGIN = 40

GRID_COLS = 8
GRID_ROWS = 6
CELL = 11
GAP = 4

GRID_W = GRID_COLS * (CELL + GAP) - GAP
PITCH = (WIDTH - MARGIN * 2 - GRID_W) // 4

ICON_Y = 44
LABEL_Y = 92
VALUE_Y = 132
GRID_Y = 154


# ==================================================
# CONTRIBUTION TOTAL
# ==================================================

def fetch_contributions():
    """Whole UTC days, public data only, so two runs the same day agree."""

    token = os.environ.get("GITHUB_TOKEN")
    login = os.environ.get("GH_LOGIN")

    if not token or not login:
        return None

    today = datetime.now(timezone.utc).date()

    start = datetime.combine(
        today - timedelta(days=364), datetime.min.time(), timezone.utc
    )
    end = datetime.combine(today, datetime.max.time(), timezone.utc)

    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar { totalContributions }
        }
      }
    }
    """

    payload = json.dumps({
        "query": query,
        "variables": {
            "login": login,
            "from": start.isoformat(),
            "to": end.isoformat(),
        },
    }).encode()

    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "businessshashish-profile",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = json.load(response)
    except Exception:
        return None

    if "errors" in body:
        return None

    return (
        body["data"]["user"]["contributionsCollection"]
        ["contributionCalendar"]["totalContributions"]
    )


data = {}

if DATA.exists():
    data = json.loads(DATA.read_text(encoding="utf-8"))

total = fetch_contributions()

if total is not None:
    data["contributions"] = total

DATA.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


# ==================================================
# METRICS
# ==================================================

metrics = json.loads(CONFIG.read_text(encoding="utf-8"))["metrics"]

CAPACITY = GRID_COLS * GRID_ROWS


def blocks(metric):
    """One block per unit, capped at the grid."""

    if "blocks" in metric:
        return max(0, min(CAPACITY, int(metric["blocks"])))

    match = re.match(r"([\d.]+)\s*([KMkm]?)", str(metric["value"]))

    if not match:
        return 0

    amount = float(match.group(1))

    if match.group(2).upper() == "K":
        amount *= 1000
    elif match.group(2).upper() == "M":
        amount *= 1_000_000

    return max(0, min(CAPACITY, int(round(amount))))


# ==================================================
# ICONS  (20 x 20, stroked)
# ==================================================

ICONS = {
    "layers": '<path d="M10 2 18 6 10 10 2 6Z"/>'
              '<path d="M2 10 10 14 18 10"/>'
              '<path d="M2 14 10 18 18 14"/>',

    "users":  '<circle cx="8" cy="6.5" r="3.2"/>'
              '<path d="M2 17.5c0-3.4 2.7-5.2 6-5.2s6 1.8 6 5.2"/>'
              '<path d="M14.2 4.2a3.2 3.2 0 0 1 0 6"/>'
              '<path d="M15 12.6c2.1.5 3.4 2.1 3.4 4.9"/>',

    "nodes":  '<circle cx="10" cy="4" r="2.2"/>'
              '<circle cx="4" cy="16" r="2.2"/>'
              '<circle cx="16" cy="16" r="2.2"/>'
              '<path d="M8.7 5.9 5.2 13.9M11.3 5.9l3.5 8M6.2 16h7.6"/>',

    "code":   '<path d="M7 5 2 10l5 5"/>'
              '<path d="M13 5l5 5-5 5"/>',

    "trend":  '<path d="M2 15 7.5 9.5 11 13 18 5"/>'
              '<path d="M13 5h5v5"/>',
}


# ==================================================
# BUILD
# ==================================================

def esc(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
    f'height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',

    f'<rect width="100%" height="100%" fill="{BACKGROUND}"/>',

    f'<rect x="12" y="12" width="{WIDTH - 24}" height="{HEIGHT - 24}" '
    f'rx="8" fill="none" stroke="{LINE}"/>',
]


for index, metric in enumerate(metrics):

    x = MARGIN + index * PITCH

    svg.append(
        f'<g transform="translate({x},{ICON_Y})" fill="none" '
        f'stroke="{FILL_B}" stroke-width="1.5" stroke-linecap="round" '
        f'stroke-linejoin="round">{ICONS.get(metric.get("icon"), "")}</g>'
    )

    svg.append(
        f'<text x="{x}" y="{LABEL_Y}" font-family="monospace" '
        f'font-size="13px" fill="{MUTED}" letter-spacing="2px">'
        f'{esc(metric["label"])}</text>'
    )

    svg.append(
        f'<text x="{x}" y="{VALUE_Y}" font-family="monospace" '
        f'font-size="34px" font-weight="700" fill="{TEXT}">'
        f'{esc(metric["value"])}</text>'
    )

    filled = blocks(metric)

    for cell in range(CAPACITY):

        column = cell % GRID_COLS
        row = cell // GRID_COLS

        cx = x + column * (CELL + GAP)
        cy = GRID_Y + row * (CELL + GAP)

        if cell >= filled:
            svg.append(
                f'<rect x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" '
                f'rx="2" fill="{EMPTY}"/>'
            )
            continue

        fill = FILL_B if (column + row) % 2 == 0 else FILL_A
        begin = round(index * 0.22 + cell * 0.012, 3)

        svg.append(
            f'<rect x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" '
            f'rx="2" fill="{fill}" opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" '
            f'dur="0.25s" begin="{begin}s" fill="freeze"/>'
            f'</rect>'
        )


svg.append("</svg>")

OUTPUT.write_text("\n".join(svg), encoding="utf-8")

print(f"Generated {OUTPUT.name}")
print(f"Contributions: {data.get('contributions')}")
