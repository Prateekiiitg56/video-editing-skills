"""Track a patch through a clip by template matching (forward from time T).

usage: python track_point.py IN out.json --x X --y Y --t T [--size 120] [--until T2] [--update 0.0]

X, Y in full-resolution display pixels at time T. Writes [{t, x, y, score}] per frame,
smoothed over 5 frames. --update blends the template toward the latest match (0..1) to
follow slow appearance changes; keep it small (0.05) or the track drifts.
Score below ~0.5 means the match is unreliable (occlusion / blur): keyframe by hand there.
"""
import argparse
import json
import subprocess

import cv2
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--x", type=float, required=True)
    ap.add_argument("--y", type=float, required=True)
    ap.add_argument("--t", type=float, default=0.0)
    ap.add_argument("--until", type=float)
    ap.add_argument("--size", type=int, default=120)
    ap.add_argument("--search", type=int, default=160, help="search radius px")
    ap.add_argument("--update", type=float, default=0.0)
    a = ap.parse_args()

    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                      "stream=width,height,avg_frame_rate:stream_side_data=rotation", "-of", "json", a.src],
                                     capture_output=True, text=True).stdout)["streams"][0]
    w, h = info["width"], info["height"]
    if any(abs(int(sd.get("rotation", 0))) in (90, 270) for sd in info.get("side_data_list", [])):
        w, h = h, w
    n, d = info["avg_frame_rate"].split("/")
    fps = float(n) / float(d)
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(a.t), "-i", a.src]
    if a.until:
        cmd += ["-t", str(a.until - a.t)]
    cmd += ["-f", "rawvideo", "-pix_fmt", "gray", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    half = a.size // 2
    tpl, x, y, rows, i = None, a.x, a.y, [], 0
    while True:
        buf = proc.stdout.read(w * h)
        if len(buf) < w * h:
            break
        g = np.frombuffer(buf, np.uint8).reshape(h, w)
        if tpl is None:
            tpl = g[int(y) - half:int(y) + half, int(x) - half:int(x) + half].astype(np.float32)
            score = 1.0
        else:
            x0, y0 = int(max(x - a.search, 0)), int(max(y - a.search, 0))
            x1, y1 = int(min(x + a.search, w)), int(min(y + a.search, h))
            region = g[y0:y1, x0:x1].astype(np.float32)
            r = cv2.matchTemplate(region, tpl, cv2.TM_CCOEFF_NORMED)
            _, score, _, loc = cv2.minMaxLoc(r)
            x, y = x0 + loc[0] + half, y0 + loc[1] + half
            if a.update > 0 and score > 0.7:
                new = g[int(y) - half:int(y) + half, int(x) - half:int(x) + half].astype(np.float32)
                if new.shape == tpl.shape:
                    tpl = (1 - a.update) * tpl + a.update * new
        rows.append([round(a.t + i / fps, 4), float(x), float(y), round(float(score), 3)])
        i += 1
    arr = np.array(rows)
    if len(arr) >= 5:
        k = np.ones(5) / 5
        for c in (1, 2):
            arr[:, c] = np.convolve(np.pad(arr[:, c], 2, mode="edge"), k, "valid")
    out = [dict(t=r[0], x=round(r[1], 1), y=round(r[2], 1), score=r[3]) for r in arr.tolist()]
    json.dump(out, open(a.out, "w"), indent=0)
    weak = [o["t"] for o in out if o["score"] < 0.5]
    print(f"{len(out)} frames tracked; weak matches at {weak[:10]}{'...' if len(weak) > 10 else ''} -> {a.out}")


if __name__ == "__main__":
    main()
