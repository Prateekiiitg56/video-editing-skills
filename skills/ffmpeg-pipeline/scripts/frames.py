"""Grab check frames from a video, plus an optional contact sheet.

usage: python frames.py IN OUTDIR (--times 0.5,3,7.2 | --every 1.0 | --cuts) [--width 540] [--sheet]

--cuts  finds scene changes (ffmpeg scene score > 0.3) and grabs the frame before and after each.
"""
import argparse
import os
import re
import subprocess


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", path], capture_output=True, text=True).stdout)


def scene_cuts(path, thr=0.3):
    err = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-i", path, "-vf",
                          f"select='gt(scene,{thr})',showinfo", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return [float(t) for t in re.findall(r"pts_time:([\d.]+)", err)]


def grab(path, t, out, width):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{max(t, 0):.3f}", "-i", path, "-frames:v", "1",
                    "-vf", f"scale={width}:-2", out], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("outdir")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--times")
    g.add_argument("--every", type=float)
    g.add_argument("--cuts", action="store_true")
    ap.add_argument("--width", type=int, default=540)
    ap.add_argument("--sheet", action="store_true", help="also write contact_sheet.png")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    if a.times:
        times = [float(x) for x in a.times.split(",")]
    elif a.every:
        d = duration(a.src)
        times = [round(i * a.every, 3) for i in range(int(d / a.every) + 1)]
    else:
        cuts = scene_cuts(a.src)
        print("cuts at:", [round(c, 3) for c in cuts])
        times = sorted({x for c in cuts for x in (c - 0.07, c + 0.04)})
    files = []
    for t in times:
        f = os.path.join(a.outdir, f"t{t:08.3f}.png")
        grab(a.src, t, f, a.width)
        files.append(f)
    print(f"{len(files)} frames -> {a.outdir}")
    if a.sheet and files:
        from PIL import Image  # contact sheet via PIL (ffmpeg glob input is unavailable on Windows)
        ims = [Image.open(f).convert("RGB") for f in files]
        cols = min(6, len(ims))
        w, h = ims[0].size
        sheet = Image.new("RGB", (cols * w, ((len(ims) + cols - 1) // cols) * h))
        for i, im in enumerate(ims):
            sheet.paste(im.resize((w, h)), ((i % cols) * w, (i // cols) * h))
        sheet.save(os.path.join(a.outdir, "contact_sheet.png"))


if __name__ == "__main__":
    main()
