import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone

TOKEN = os.environ["GITHUB_TOKEN"]
LOGIN = os.environ["GH_LOGIN"]

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

query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
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

calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

total = calendar["totalContributions"]

days = []

for week in calendar["weeks"]:
    days.extend(week["contributionDays"])


# --------------------------------------------------
# Generate simple contribution SVG
# --------------------------------------------------

cell_size = 12
gap = 3
columns = len(calendar["weeks"])
rows = 7

width = columns * (cell_size + gap)
height = rows * (cell_size + gap) + 45

levels = [0, 1, 3, 6, 10]

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


svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'width="{width}" height="{height}" '
    f'viewBox="0 0 {width} {height}">',
    
    '<rect width="100%" height="100%" fill="white"/>',

    f'<text x="0" y="20" '
    f'font-family="monospace" font-size="16" '
    f'fill="black">CONTRIBUTIONS: {total}</text>'
]


for i, week in enumerate(calendar["weeks"]):

    for day in week["contributionDays"]:

        date = datetime.fromisoformat(
            day["date"]
        ).date()

        count = day["contributionCount"]

        # weekday(): Monday = 0, Sunday = 6
        row = date.weekday()

        x = i * (cell_size + gap)
        y = 30 + row * (cell_size + gap)

        # Different opacity levels represent activity.
        opacity = [
            0.08,
            0.25,
            0.45,
            0.70,
            1.0
        ][level(count)]

        svg.append(
            f'<rect x="{x}" y="{y}" '
            f'width="{cell_size}" height="{cell_size}" '
            f'fill="black" opacity="{opacity}">'
            f'<title>{date}: {count} contributions</title>'
            f'</rect>'
        )


svg.append("</svg>")

with open("stats.svg", "w", encoding="utf-8") as file:
    file.write("\n".join(svg))


print(f"Generated stats.svg")
print(f"Total contributions: {total}")
print(f"Days returned: {len(days)}")
