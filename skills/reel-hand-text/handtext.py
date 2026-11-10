"""Hand-lettered "quote stack" overlay for vertical reels.

Renders a block of hand-drawn capitals the way trending IG reels do it:
stacked centred lines, mixed word sizes, each line bent along its own curve
(slope + arc), every glyph rotated to the curve tangent with small random
size / tilt / baseline jitter so it reads as hand-written, in a soft cream
colour that sits in the footage instead of on top of it.

Usage:
    python handtext.py layout.json out.png [--preview frame.png preview.png]

layout.json keys (all optional except "lines"):
    width, height          canvas px (default 2160x3840, 4K vertical)
    top                    y of first line's cap top, fraction of height (0.16)
    font                   TTF path (default Caveat Bold, de-slanted)
    deslant                shear to stand an italic font upright (0.34 for Caveat)
    color                  hex text colour (#FFF2A8 soft cream)
    opacity                0..1 text opacity (0.96)
    shadow                 0..1 soft shadow strength (0.35); 0 disables
    line_gap               px between lines (50)
    tracking               letter spacing, fraction of size (0.03)
    word_gap               word spacing, fraction of size (0.30)
    jitter                 [size frac, tilt deg, baseline px] ([0.06, 3, 8])
    seed                   random seed, keeps renders identical (7)
    lines: [{ "words": [["WORD", size_px], ...],
              "slope": deg (+ = right end lower),
              "arc": px (+ = ends higher than middle, "smile"),
              "dy": px extra offset for this line }]
"""
import json
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

DEFAULTS = dict(
    width=2160, height=3840, top=0.16,
    font=None, deslant=0.34,
    color="#FFF2A8", opacity=0.96, shadow=0.35,
    line_gap=50, tracking=0.03, word_gap=0.30,
    jitter=[0.06, 3.0, 8.0], seed=7,
)


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def glyph(ch, size, cfg, fonts):
    """One glyph on a transparent tile, baseline-centre at tile centre."""
    f = fonts.setdefault(size, ImageFont.truetype(cfg["font"], size))
    stroke = max(2, size // 45)
    s = size * 2
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((s / 2, s / 2), ch, font=f, anchor="ms",
                            fill=(255, 255, 255, 255), stroke_width=stroke,
                            stroke_fill=(255, 255, 255, 255))
    k = cfg["deslant"]
    # shear around the baseline row so the glyph stays anchored
    return im.transform(im.size, Image.AFFINE, (1, -k, k * s / 2, 0, 1, 0), Image.BICUBIC)


def layout_line(line, cfg, fonts):
    """Glyph list [(char, size, x_centre)] and total width for one line."""
    items, x = [], 0.0
    for wi, (word, size) in enumerate(line["words"]):
        f = fonts.setdefault(size, ImageFont.truetype(cfg["font"], size))
        for ch in word:
            adv = f.getlength(ch) * (1 - cfg["deslant"] * 0.15) + size * cfg["tracking"]
            items.append((ch, size, x + adv / 2))
            x += adv
        if wi < len(line["words"]) - 1:
            x += size * cfg["word_gap"]
    return items, x


FONT_CANDIDATES = [
    "fonts/Caveat-Bold.ttf", "Caveat-Bold.ttf", "Caveat[wght].ttf",
    "C:/Windows/Fonts/Caveat-Bold.ttf",
    os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/Caveat-Bold.ttf"),
    os.path.expanduser("~/Library/Fonts/Caveat-Bold.ttf"), "/Library/Fonts/Caveat-Bold.ttf",
    os.path.expanduser("~/.local/share/fonts/Caveat-Bold.ttf"), "/usr/share/fonts/truetype/caveat/Caveat-Bold.ttf",
]


def find_font(path):
    """Explicit path wins; otherwise look for Caveat Bold next to the layout, in the skill folder, or system fonts."""
    here = os.path.dirname(os.path.abspath(__file__))
    for c in ([path] if path else []) + FONT_CANDIDATES + [os.path.join(here, "fonts", "Caveat-Bold.ttf")]:
        if c and os.path.exists(c):
            return c
    sys.exit("Font not found. Download Caveat (OFL) from https://fonts.google.com/specimen/Caveat, "
             "put Caveat-Bold.ttf in ./fonts/ or set \"font\" in the layout JSON.")


def render(cfg):
    cfg = {**DEFAULTS, **cfg}
    cfg["font"] = find_font(cfg.get("font"))
    W, H = cfg["width"], cfg["height"]
    rnd = random.Random(cfg["seed"])
    fonts = {}
    mask = Image.new("L", (W, H), 0)
    y = cfg["top"] * H
    js, jt, jb = cfg["jitter"]
    for line in cfg["lines"]:
        items, width = layout_line(line, cfg, fonts)
        big = max(s for _, s in line["words"])
        cap = big * 0.62
        base = y + cap + line.get("dy", 0)
        x0 = (W - width) / 2
        half = width / 2
        slope = math.tan(math.radians(line.get("slope", 0)))
        arc = line.get("arc", 0)
        for ch, size, xc in items:
            if ch == " ":
                continue
            u = (xc - half) / half                      # -1 .. 1 across the line
            off = slope * (xc - half) - arc * u * u     # curve offset (px, + = down)
            deriv = slope - 2 * arc * u / half          # d(off)/dx
            ang = -math.degrees(math.atan(deriv)) + rnd.uniform(-jt, jt)
            sz = max(8, int(size * (1 + rnd.uniform(-js, js))))
            g = glyph(ch, sz, cfg, fonts).rotate(ang, Image.BICUBIC)
            gx = int(x0 + xc - g.width / 2)
            gy = int(base + off + rnd.uniform(-jb, jb) - g.height / 2)
            mask.paste(Image.new("L", g.size, 255), (gx, gy), g.split()[3])
        y += cap + cfg["line_gap"] + big * 0.12
    mask = mask.filter(ImageFilter.GaussianBlur(0.8))   # soften the digital edge
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if cfg["shadow"] > 0:
        sh = mask.filter(ImageFilter.GaussianBlur(W / 180)).point(lambda a: int(a * cfg["shadow"]))
        out.paste(Image.new("RGBA", (W, H), (0, 0, 0, 255)), (int(W / 400), int(W / 300)), sh)
    text = Image.new("RGBA", (W, H), (*hex_rgb(cfg["color"]), 255))
    text.putalpha(mask.point(lambda a: int(a * cfg["opacity"])))
    out.alpha_composite(text)
    return out


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    img = render(cfg)
    img.save(sys.argv[2])
    if "--preview" in sys.argv:
        i = sys.argv.index("--preview")
        bg = Image.open(sys.argv[i + 1]).convert("RGBA").resize(img.size)
        bg.alpha_composite(img)
        bg.convert("RGB").resize((img.width // 4, img.height // 4)).save(sys.argv[i + 2])
