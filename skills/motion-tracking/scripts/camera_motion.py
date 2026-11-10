"""Per-frame global camera motion: rotation (deg) and translation (px at analysis width).

usage: python camera_motion.py IN out.json [--width 270] [--fps 30]

Tracks corners with LK optical flow and fits a similarity transform with RANSAC, so the
background (majority) drives the estimate and on-screen scrolling or moving people are outliers.
Prints a 0.5 s summary: summed |rotation| and translation per window. Big numbers = camera move.
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
    ap.add_argument("--width", type=int, default=270)
    ap.add_argument("--fps", type=float, default=30)
    a = ap.parse_args()
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height:stream_side_data=rotation", "-of", "json", a.src],
                           capture_output=True, text=True).stdout
    st = json.loads(probe)["streams"][0]
    w, h = st["width"], st["height"]
    rot = next((abs(int(sd.get("rotation", 0))) for sd in st.get("side_data_list", []) if "rotation" in sd), 0)
    if rot in (90, 270):
        w, h = h, w
    W = a.width
    H = int(round(h * W / w / 2) * 2)
    proc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-i", a.src, "-vf", f"fps={a.fps},scale={W}:{H},format=gray",
                             "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    prev, rows, i = None, [], 0
    while True:
        buf = proc.stdout.read(W * H)
        if len(buf) < W * H:
            break
        g = np.frombuffer(buf, np.uint8).reshape(H, W)
        r = s = 0.0
        if prev is not None:
            p0 = cv2.goodFeaturesToTrack(prev, 300, 0.01, 6)
            if p0 is not None and len(p0) > 10:
                p1, ok, _ = cv2.calcOpticalFlowPyrLK(prev, g, p0, None)
                ok = ok.ravel() == 1
                if ok.sum() > 6:
                    M, _ = cv2.estimateAffinePartial2D(p0[ok], p1[ok], method=cv2.RANSAC, ransacReprojThreshold=1.5)
                    if M is not None:
                        r = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
                        s = float(np.hypot(M[0, 2], M[1, 2]))
        rows.append((round(i / a.fps, 3), round(r, 3), round(s, 2)))
        prev, i = g, i + 1
    json.dump({"width": W, "fps": a.fps, "rows": rows}, open(a.out, "w"))
    step = int(a.fps / 2)
    for k in range(0, len(rows), step):
        win = rows[k:k + step]
        rs, ms = sum(abs(x[1]) for x in win), sum(x[2] for x in win)
        flag = "  MOVE" if rs > 1.0 or ms > W * 0.05 else ""
        print(f"{win[0][0]:6.1f}s  rot {rs:5.2f}  move {ms:6.1f}{flag}")
    print("->", a.out)


if __name__ == "__main__":
    main()
