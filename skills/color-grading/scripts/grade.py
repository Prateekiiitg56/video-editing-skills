"""Apply a named look (ffmpeg filter chain) or a LUT to a video or image.

usage:
  python grade.py --list
  python grade.py IN OUT --look teal-orange [--strength 0.8] [--grain 5]
  python grade.py IN OUT --lut my.cube [--strength 0.6]
  python grade.py IN --compare grid.png [--at 3.0] [--looks teal-orange,warm-golden,film-kodak]

--strength blends the graded image with the original (0..1).
--compare renders one frame through several looks into a labelled grid for choosing by eye.
Outputs are x264 CRF 12 intermediates (re-encode once later with the export step).
"""
import argparse
import os
import subprocess
import tempfile

LOOKS = {
    "neutral-punch": "eq=contrast=1.08:saturation=1.08,curves=preset=medium_contrast",
    "teal-orange": ("colorbalance=rs=-0.08:gs=0.02:bs=0.10:rm=0.03:bm=-0.03:rh=0.08:gh=0.02:bh=-0.08,"
                    "eq=contrast=1.06:saturation=1.12"),
    "warm-golden": ("colortemperature=temperature=5000:mix=0.6,"
                    "colorbalance=rs=0.04:bs=-0.03:rh=0.05:bh=-0.05,eq=contrast=0.98:saturation=1.05"),
    "cool-moody": ("colortemperature=temperature=8000:mix=0.5,eq=contrast=1.1:saturation=0.8:gamma=0.95,"
                   "curves=all='0/0.03 0.5/0.45 1/0.95'"),
    "film-kodak": ("curves=r='0/0.02 0.5/0.52 1/0.96':g='0/0.03 0.5/0.5 1/0.95':b='0/0.06 0.5/0.47 1/0.9',"
                   "colorbalance=gs=0.02:bs=0.03:rm=0.03:bm=-0.02,eq=saturation=0.95,noise=alls=5:allf=t"),
    "bleach-bypass": "eq=contrast=1.3:saturation=0.6:gamma=0.95,curves=preset=strong_contrast",
    "pastel-matte": ("curves=all='0/0.08 0.5/0.52 1/0.95',eq=contrast=0.92:saturation=0.85,"
                     "colorbalance=rh=0.05:bh=0.02:rs=0.02:bs=0.03"),
    "day-for-night": ("eq=brightness=-0.12:gamma=0.75:saturation=0.4,"
                      "colorbalance=rs=-0.1:gs=-0.02:bs=0.15:rm=-0.08:bm=0.1:rh=-0.05:bh=0.08,"
                      "curves=all='0/0 0.6/0.38 1/0.75'"),
    "vintage-faded": ("curves=all='0/0.1 0.5/0.5 1/0.9',colorbalance=rh=0.04:gh=0.04:bh=-0.06:bs=0.05,"
                      "eq=saturation=0.8,noise=c0s=8:c1s=10:c2s=10:allf=t"),
    "bw-contrast": "colorchannelmixer=.4:.4:.2:0:.4:.4:.2:0:.4:.4:.2,curves=preset=strong_contrast,noise=alls=7:allf=t",
    "cyberpunk-neon": ("colorbalance=rs=0.05:bs=0.15:rh=0.12:gh=-0.06:bh=0.1,"
                       "eq=contrast=1.15:saturation=1.35:gamma=0.95"),
}


def chain(look=None, lut=None, strength=1.0, grain=0):
    g = LOOKS[look] if look else f"lut3d='{lut}':interp=tetrahedral"
    if strength < 0.999:
        f = f"split[a][b];[b]{g}[g];[a][g]blend=all_expr='A*{1 - strength:.3f}+B*{strength:.3f}'"
    else:
        f = g
    if grain:
        f += f",noise=alls={grain}:allf=t"
    return f + ",format=yuv420p"


def is_image(p):
    return os.path.splitext(p)[1].lower() in (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp")


def run(src, out, vf):
    cmd = ["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", src, "-filter_complex", vf]
    if is_image(out):
        cmd += ["-frames:v", "1", out]
    else:
        cmd += ["-c:v", "libx264", "-crf", "12", "-preset", "medium", "-c:a", "copy", out]
    subprocess.run(cmd, check=True)


def compare(src, out, at, looks):
    from PIL import Image, ImageDraw
    tmp = tempfile.mkdtemp()
    base = os.path.join(tmp, "orig.png")
    seek = [] if is_image(src) else ["-ss", str(at)]
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", *seek, "-i", src, "-frames:v", "1", "-vf", "scale=480:-2", base],
                   check=True)
    tiles = [("original", base)]
    for lk in looks:
        p = os.path.join(tmp, f"{lk}.png")
        run(base, p, LOOKS[lk])
        tiles.append((lk, p))
    ims = [(n, Image.open(p).convert("RGB")) for n, p in tiles]
    w, h = ims[0][1].size
    cols = min(4, len(ims))
    sheet = Image.new("RGB", (cols * w, ((len(ims) + cols - 1) // cols) * (h + 28)), "black")
    d = ImageDraw.Draw(sheet)
    for i, (n, im) in enumerate(ims):
        x, y = (i % cols) * w, (i // cols) * (h + 28)
        sheet.paste(im, (x, y + 28))
        d.text((x + 8, y + 8), n, fill="white")
    sheet.save(out)
    print("compare grid ->", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--look", choices=LOOKS)
    ap.add_argument("--lut")
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--grain", type=int, default=0)
    ap.add_argument("--compare")
    ap.add_argument("--at", type=float, default=1.0)
    ap.add_argument("--looks", default=",".join(LOOKS))
    a = ap.parse_args()
    if a.list:
        for k, v in LOOKS.items():
            print(f"{k:15s} {v}")
        return
    if a.compare:
        compare(a.src, a.compare, a.at, [x for x in a.looks.split(",") if x])
        return
    if not (a.src and a.out and (a.look or a.lut)):
        ap.error("need IN OUT and --look or --lut")
    run(a.src, a.out, chain(a.look, a.lut, a.strength, a.grain))
    print("graded ->", a.out)


if __name__ == "__main__":
    main()
