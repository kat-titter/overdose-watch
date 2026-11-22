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
CARD_W, CARD_H = 1200, 630  # the og:image size; card.html is laid out at this size
TOUCH_PX = 180  # the apple-touch-icon size
FONT_WAIT_MS = 8000  # virtual time for the card's Google Fonts to load before the screenshot


def head():
    """The icon, touch-icon and share-card tags for the page head."""
    svg = (ROOT / "share/icon.svg").read_text().strip().replace('"', "'")
    icon = "data:image/svg+xml," + urllib.parse.quote(svg, safe=" ='/:;,.-()")
    card = SITE + "share/card.png"
    return "\n".join([
        f'<link rel="icon" href="{icon}">',
        '<link rel="apple-touch-icon" href="share/apple-touch-icon.png">',
        f'<meta property="og:image" content="{card}">',
        f'<meta property="og:image:width" content="{CARD_W}"><meta property="og:image:height" content="{CARD_H}">',
        f'<meta property="og:image:alt" content="{ALT}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:image" content="{card}">',
    ])


def screenshot(page, png_path, width_px, height_px):
    """Draw one local HTML page to a PNG with headless Chrome; on failure, show Chrome's own error."""
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                        f"--virtual-time-budget={FONT_WAIT_MS}", f"--window-size={width_px},{height_px}",
                        f"--screenshot={png_path}", page.as_uri()], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"Chrome failed on {page.name}:\n{r.stderr}")


def render():
    """Redraw share/apple-touch-icon.png (180 px, opaque, iOS rounds the corners) and share/card.png."""
    tmp = ROOT / "share/.touch.html"
    tmp.write_text(f'<body style="margin:0;background:{TOUCH_BG}">{(ROOT / "share/icon.svg").read_text()}'
                   f'<style>svg{{display:block;width:{TOUCH_PX}px;height:{TOUCH_PX}px}}</style>')
    try:
        screenshot(tmp, ROOT / "share/apple-touch-icon.png", TOUCH_PX, TOUCH_PX)
    finally:
        tmp.unlink()
    screenshot(ROOT / "share/card.html", ROOT / "share/card.png", CARD_W, CARD_H)
    for p in ("apple-touch-icon.png", "card.png"):
        print(f"share/{p}: {(ROOT / 'share' / p).stat().st_size / 1024:.0f} KB")


def stamp(page="index.html"):
    """Put head() between the page's <!-- share --> markers."""
    p = ROOT / page
    block = "<!-- share: written by tools/share.py, edit share/ instead -->\n" + head() + "\n<!-- /share -->"
    s, n = re.subn(r"<!-- share[^>]*-->.*?<!-- /share -->", lambda m: block, p.read_text(), flags=re.S)
    assert n == 1, f"{page}: expected one <!-- share ... /share --> block"
    p.write_text(s)


if __name__ == "__main__":
    stamp()
    if "--stamp" not in sys.argv:
        render()
