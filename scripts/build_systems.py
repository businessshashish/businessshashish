"""Generates systems.txt and systems.map — the ASCII system map in the hero.

systems.txt is the art. systems.map is a parallel grid of one letter per cell
naming what that character is, so the renderer can give the drawing depth:

    h heading   t label text   m muted text
    l structure (box rules and connectors)
    f shaded fill   s drop shadow   a accent (live status)

Edit the data blocks below and re-run. Both files are committed.
"""

from pathlib import Path

WIDTH = 148
HEIGHT = 38

TITLE = "LAYERSTOP CORTEX"
STATUS = "8 PILLARS  .  5 AGENTS  .  NIGHTLY"

# (label, note under the bar, rows filled out of BAR_H - 2)
PILLARS = [
    ("CRAFT", "27 BUILT", 5),
    ("DELIVERY", "14 DAYS", 4),
    ("DEMAND", "20 / DAY", 2),
    ("EVIDENCE", "3 PROOFS", 2),
    ("LEVERAGE", "5 AGENTS", 4),
    ("POV", "DRAFTING", 1),
    ("REPUTATION", "BUILDING", 3),
    ("CONVERSION", "3 FIRED", 2),
]

SIGNAL = [
    ("FIRECRAWL", "web . social"),
    ("IG / X / YT", "reels . posts"),
    ("GITHUB API", "commits . repos"),
]

SURFACE = [
    ("CORTEX CONTROL", "127.0.0.1:7777"),
    ("DAILY DIGESTS", "one run a day"),
    ("OUTBOUND / N8N", "20 mails a day"),
]

AGENTS = [
    ("01", "MARKET INTEL"),
    ("02", "PAIN SUPERVISOR"),
    ("03", "ALIGNMENT GUARD"),
    ("04", "MCP BRIDGE"),
    ("05", "VAULT LIBRARIAN"),
]

CLOSER = "ZERO THIRD-PARTY REQUESTS"
RUNTIME = "claude code . mcp . n8n . python . next.js . obsidian . figma"


# ==================================================
# CANVAS
# ==================================================

art = [[" "] * WIDTH for _ in range(HEIGHT)]
layer = [["."] * WIDTH for _ in range(HEIGHT)]


def put(row, col, text, cls="t"):
    for i, ch in enumerate(text):
        c = col + i
        if 0 <= c < WIDTH and 0 <= row < HEIGHT:
            art[row][c] = ch
            layer[row][c] = cls if ch != " " else "."


def centre(row, left, width, text, cls="t"):
    put(row, left + (width - len(text)) // 2, text, cls)


def box(top, left, width, height, fill=None, shadow=True):
    """Outline, optional shaded interior, and a dotted drop shadow."""

    rule = "+" + "-" * (width - 2) + "+"
    put(top, left, rule, "l")
    put(top + height - 1, left, rule, "l")

    for r in range(top + 1, top + height - 1):
        put(r, left, "|", "l")
        put(r, left + width - 1, "|", "l")
        if fill:
            put(r, left + 1, fill * (width - 2), "f")

    if shadow:
        put(top + height, left + 1, ":" * (width - 1), "s")
        for r in range(top + 1, top + height + 1):
            put(r, left + width, ":", "s")


# ==================================================
# HEADER
# ==================================================

put(0, 4, TITLE, "h")
put(0, WIDTH - 4 - len(STATUS), STATUS, "m")
put(1, 4, "=" * (WIDTH - 8), "l")


# ==================================================
# PILLAR STRIP
# ==================================================

BAR_W, BAR_GAP, BAR_X = 10, 8, 5
BAR_TOP, BAR_H = 4, 8

put(3, BAR_X, "PILLARS", "m")
put(3, WIDTH - 4 - len("PILLAR STATE"), "PILLAR STATE", "m")

for i, (name, note, filled) in enumerate(PILLARS):

    x = BAR_X + i * (BAR_W + BAR_GAP)

    put(BAR_TOP, x, "." + "-" * (BAR_W - 2) + ".", "l")
    put(BAR_TOP + BAR_H - 1, x, "'" + "-" * (BAR_W - 2) + "'", "l")

    inner = BAR_H - 2

    for r in range(inner):
        row = BAR_TOP + 1 + r
        live = r >= inner - filled
        put(row, x, "|", "l")
        put(row, x + BAR_W - 1, "|", "l")
        put(row, x + 1, "#" * (BAR_W - 2), "a" if live else "f")

    centre(BAR_TOP + BAR_H, x, BAR_W, name, "t")
    centre(BAR_TOP + BAR_H + 1, x, BAR_W, note, "m")


# ==================================================
# RULE
# ==================================================

put(15, 4, ". " * ((WIDTH - 8) // 2), "l")


# ==================================================
# FLOW
# ==================================================

SIG_X, SIG_W = 4, 21
BUS_L = 30
VAULT_X, VAULT_W = 37, 26
BUS_R = 69
SUR_X, SUR_W = 76, 25

FLOW_TOP = 19

put(17, SIG_X + 2, "SIGNAL", "m")
put(17, VAULT_X + 6, "CORE", "m")
put(17, SUR_X + 2, "SURFACE", "m")
put(17, 108, "AGENTS", "m")

for i, (name, sub) in enumerate(SIGNAL):
    top = FLOW_TOP + i * 5
    box(top, SIG_X, SIG_W, 4)
    put(top + 1, SIG_X + 2, name, "t")
    put(top + 2, SIG_X + 2, sub, "m")

for i, (name, sub) in enumerate(SURFACE):
    top = FLOW_TOP + i * 5
    box(top, SUR_X, SUR_W, 4)
    put(top + 1, SUR_X + 2, name, "t")
    put(top + 2, SUR_X + 2, sub, "m")

# Vault: shaded slab with a knocked-out label plate.
VAULT_TOP = FLOW_TOP + 4
box(VAULT_TOP, VAULT_X, VAULT_W, 6, fill="#")

for offset, label, cls in ((2, "OBSIDIAN VAULT", "t"), (3, "one linked corpus", "m")):
    put(VAULT_TOP + offset, VAULT_X + 1, " " * (VAULT_W - 2))
    centre(VAULT_TOP + offset, VAULT_X, VAULT_W, label, cls)

MID = FLOW_TOP + 6

for r in range(FLOW_TOP + 1, FLOW_TOP + 12):
    put(r, BUS_L, "|", "l")
    put(r, BUS_R, "|", "l")

for i in range(3):
    row = FLOW_TOP + 1 + i * 5
    corner = "." if i == 0 else ("'" if i == 2 else "+")

    put(row, SIG_X + SIG_W - 1, "+", "l")
    put(row, SIG_X + SIG_W, "-" * (BUS_L - SIG_X - SIG_W), "l")
    put(row, BUS_L, corner, "l")

    put(row, BUS_R, corner, "l")
    put(row, BUS_R + 1, "-" * (SUR_X - BUS_R - 1), "l")
    put(row, SUR_X, "+", "l")

put(MID, BUS_L, "+", "l")
put(MID, BUS_L + 1, "-" * (VAULT_X - BUS_L - 1), "l")
put(MID, VAULT_X, "+", "l")
put(MID, VAULT_X + VAULT_W - 1, "+", "l")
put(MID, VAULT_X + VAULT_W, "-" * (BUS_R - VAULT_X - VAULT_W), "l")
put(MID, BUS_R, "+", "l")


# ==================================================
# AGENT RACK
# ==================================================

RACK_X, RACK_W, RACK_TOP = 106, 38, 19

box(RACK_TOP, RACK_X, RACK_W, len(AGENTS) + 2)

for i, (number, name) in enumerate(AGENTS):
    row = RACK_TOP + 1 + i
    put(row, RACK_X + 2, number, "m")
    put(row, RACK_X + 6, name, "t")
    put(row, RACK_X + RACK_W - 7, "[on]", "a")

put(RACK_TOP + len(AGENTS) + 3, RACK_X + 1, "nightly, over the vault", "m")


# ==================================================
# RUNTIME
# ==================================================

put(34, 4, ". " * ((WIDTH - 8) // 2), "l")
put(35, 4, "RUNTIME", "m")
put(35, WIDTH - 4 - len(CLOSER), CLOSER, "m")
put(36, 4, RUNTIME, "t")


# ==================================================
# WRITE
# ==================================================

root = Path(__file__).resolve().parent.parent

rows = ["".join(r).rstrip() for r in art]

while rows and not rows[-1]:
    rows.pop()

(root / "systems.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")

(root / "systems.map").write_text(
    "\n".join("".join(layer[i])[: len(rows[i])] for i in range(len(rows))) + "\n",
    encoding="utf-8",
)

print(f"Wrote systems.txt + systems.map  {WIDTH} x {len(rows)}")
