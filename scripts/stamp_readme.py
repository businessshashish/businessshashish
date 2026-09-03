"""Stamps README.md image links with a hash of the file they point at.

GitHub proxies README images through its own cache, keyed on the URL. Since
these SVGs are regenerated at the same paths every night, an unchanged URL can
keep serving yesterday's drawing for a long time. Appending a content hash
gives changed art a new URL, so the profile updates the moment it is pushed.
"""

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

README = ROOT / "README.md"
IMAGES = ("profile.svg", "stats.svg")

text = README.read_text(encoding="utf-8")

for name in IMAGES:

    digest = hashlib.sha256(
        (ROOT / name).read_bytes()
    ).hexdigest()[:10]

    text = re.sub(
        rf"(\./{re.escape(name)})(\?v=[0-9a-f]+)?",
        rf"\g<1>?v={digest}",
        text,
    )

README.write_text(text, encoding="utf-8")

print("Stamped README.md")
