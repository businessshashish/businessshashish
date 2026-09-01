import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone


TOKEN = os.environ["GITHUB_TOKEN"]
LOGIN = os.environ["GH_LOGIN"]


# ==================================================
# DATE RANGE
# ==================================================

today = datetime.now(timezone.utc).date()

start = datetime.combine(
    today - timedelta(days=364),
    datetime.min.time(),
    timezone.utc,
)

end = datetime.combine(
    today,
    datetime.max.time(),
    timezone.utc,
)


# ==================================================
# GITHUB GRAPHQL QUERY
# ==================================================

query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalContributions
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


payload = json.dumps({
    "query": query,
    "variables": {
        "login": LOGIN,
        "from": start.isoformat(),
        "to": end.isoformat(),
    },
}).encode()


# ==================================================
# GITHUB REQUEST
# ==================================================

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "github-profile-generator",
    },
)


with urllib.request.urlopen(request) as response:
    data = json.load(response)


if "errors" in data:
    raise RuntimeError(data["errors"])


# ==================================================
# EXTRACT CONTRIBUTION CALENDAR
# ==================================================

calendar = (
    data["data"]
    ["user"]
    ["contributionsCollection"]
    ["contributionCalendar"]
)


total = calendar["totalContributions"]


days = []

for week in calendar["weeks"]:
    days.extend(
        week["contributionDays"]
    )


# ==================================================
# SVG SETTINGS
# ==================================================

cell_size = 12
gap = 3

columns = len(calendar["weeks"])
rows = 7

width = columns * (cell_size + gap)
height = rows * (cell_size + gap) + 45


# ==================================================
# CONTRIBUTION LEVEL
# ==================================================

def level(count):

    if count == 0:
        return 0

    if count <= 2:
        return 1

    if count <= 5:
        return 2

    if count <= 9:
        return 3

    return 4


# ==================================================
# GITHUB DARK MODE COLORS
# ==================================================

BACKGROUND = "#0d1117"

EMPTY = "#161b22"

LEVELS = [
    "#161b22",
    "#0e4429",
    "#006d32",
    "#26a641",
    "#39d353",
]

TEXT = "#f0f0f0"


# ==================================================
# BUILD SVG
# ==================================================

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'width="{width}" '
    f'height="{height}" '
    f'viewBox="0 0 {width} {height}">',

    # Background
    f'<rect '
    f'width="100%" '
    f'height="100%" '
    f'fill="{BACKGROUND}"/>',

    # Contribution count
    f'<text '
    f'x="0" '
    f'y="20" '
    f'font-family="monospace" '
    f'font-size="16" '
    f'fill="{TEXT}">'
    f'CONTRIBUTIONS: {total}'
    f'</text>',
]


# ==================================================
# DRAW CONTRIBUTION CELLS
# ==================================================

for i, week in enumerate(
    calendar["weeks"]
):

    for day in week["contributionDays"]:

        date = datetime.fromisoformat(
            day["date"]
        ).date()

        count = day["contributionCount"]

        row = date.weekday()

        x = i * (cell_size + gap)

        y = 30 + row * (
            cell_size + gap
        )

        contribution_level = level(
            count
        )

        fill = LEVELS[
            contribution_level
        ]

        svg.append(
            f'<rect '
            f'x="{x}" '
            f'y="{y}" '
            f'width="{cell_size}" '
            f'height="{cell_size}" '
            f'rx="2" '
            f'fill="{fill}">'
            f'<title>'
            f'{date}: {count} contributions'
            f'</title>'
            f'</rect>'
        )


# ==================================================
# CLOSE SVG
# ==================================================

svg.append("</svg>")


# ==================================================
# WRITE FILE
# ==================================================

with open(
    "stats.svg",
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "\n".join(svg)
    )


print("Generated stats.svg")
print(
    f"Total contributions: {total}"
)
print(
    f"Days returned: {len(days)}"
)
