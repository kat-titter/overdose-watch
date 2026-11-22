#!/usr/bin/env python3
"""Tab icon and share card. `python3 tools/share.py` stamps head() into index.html and redraws the two PNGs.

share/icon.svg is the one home of the icon: the tab icon is inlined from it and the 180 px touch icon drawn from it.
share/card.html is the 1200 x 630 share card's source. The PNGs need Google Chrome; `--stamp` alone updates the page.
"""
import re, subprocess, sys, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://kat-titter.github.io/overdose-watch/"
ALT = "Overdose Watch: overdose deaths and new drugs in the Bay Area, California and Nevada."
TOUCH_BG = "#ffffff"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def head():
    """The icon, touch-icon and share-card tags for the page head."""
    svg = (ROOT / "share/icon.svg").read_text().strip().replace('"', "'")
    icon = "data:image/svg+xml," + urllib.parse.quote(svg, safe=" ='/:;,.-()")
    card = SITE + "share/card.png"
    return "\n".join([
        f'<link rel="icon" href="{icon}">',
        '<link rel="apple-touch-icon" href="share/apple-touch-icon.png">',
        f'<meta property="og:image" content="{card}">',
        '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{ALT}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:image" content="{card}">',
    ])


def shot(page, png, w, h):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                    "--virtual-time-budget=8000", f"--window-size={w},{h}", f"--screenshot={png}", page.as_uri()],
                   check=True, capture_output=True)


def render():
    """Redraw share/apple-touch-icon.png (180 px, opaque, iOS rounds the corners) and share/card.png."""
    tmp = ROOT / "share/.touch.html"
    tmp.write_text(f'<body style="margin:0;background:{TOUCH_BG}">{(ROOT / "share/icon.svg").read_text()}'
                   '<style>svg{display:block;width:180px;height:180px}</style>')
    try:
        shot(tmp, ROOT / "share/apple-touch-icon.png", 180, 180)
    finally:
        tmp.unlink()
    shot(ROOT / "share/card.html", ROOT / "share/card.png", 1200, 630)
    for p in ("apple-touch-icon.png", "card.png"):
        print(f"share/{p}: {(ROOT / 'share' / p).stat().st_size / 1024:.0f} KB")


def stamp(page="index.html"):
    """Put head() between the page's <!-- share --> markers."""
    p = ROOT / page
    s, n = re.subn(r"<!-- share -->.*?<!-- /share -->", lambda m: "<!-- share -->\n" + head() + "\n<!-- /share -->",
                   p.read_text(), flags=re.S)
    assert n == 1, f"{page}: expected one <!-- share --> block"
    p.write_text(s)


if __name__ == "__main__":
    stamp()
    if "--stamp" not in sys.argv:
        render()
