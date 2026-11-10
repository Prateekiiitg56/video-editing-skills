"""Smooth-path video stabilization (OpenCV), optional colour mask to ignore a moving subject.

usage: python stabilize.py IN OUT [--sigma 14] [--zoom 1.06] [--mask-hsv 0,22,110,70]
needs: pip install opencv-python numpy scipy

--mask-hsv h_lo,h_hi,s_min,v_min : pixels in this HSV range (OpenCV hue 0-180) are excluded
from feature tracking (e.g. a red can moving in frame), so only the background drives the fit.
Output: x264 CRF 12, same fps, audio copied from source.
"""
import argparse
import subprocess

import cv2
import numpy as np
from scipy.ndimage import gaussian_filter1d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--sigma", type=float, default=14)
    ap.add_argument("--zoom", type=float, default=1.06)
    ap.add_argument("--mask-hsv")
    a = ap.parse_args()

    cap = cv2.VideoCapture(a.src)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    if not frames:
        raise SystemExit("no frames read (check codec / rotation)")
    h, w = frames[0].shape[:2]
    sc = 540 / max(w, h)

    def prep(f):
        small = cv2.resize(f, None, fx=sc, fy=sc)
        g = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        m = np.full(g.shape, 255, np.uint8)
        if a.mask_hsv:
            h0, h1, s0, v0 = map(int, a.mask_hsv.split(","))
            hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
            subj = ((hsv[..., 0] >= h0) & (hsv[..., 0] <= h1) & (hsv[..., 1] >= s0) & (hsv[..., 2] >= v0))
            subj = cv2.dilate(subj.astype(np.uint8), np.ones((31, 31), np.uint8))
            m[subj > 0] = 0
        return g, m

    traj = [(0.0, 0.0, 0.0)]
    pg, pm = prep(frames[0])
    for f in frames[1:]:
        g, m = prep(f)
        dx = dy = da = 0.0
        p0 = cv2.goodFeaturesToTrack(pg, 600, 0.01, 10, mask=pm)
        if p0 is not None and len(p0) > 10:
            p1, st, _ = cv2.calcOpticalFlowPyrLK(pg, g, p0, None, winSize=(31, 31), maxLevel=4)
            ok = st.ravel() == 1
            A, _ = cv2.estimateAffinePartial2D(p0[ok], p1[ok], method=cv2.RANSAC, ransacReprojThreshold=2.0)
            if A is not None:
                da = float(np.arctan2(A[1, 0], A[0, 0]))
                cx, cy = g.shape[1] / 2, g.shape[0] / 2
                dx = (A[0, 0] * cx + A[0, 1] * cy + A[0, 2] - cx) / sc
                dy = (A[1, 0] * cx + A[1, 1] * cy + A[1, 2] - cy) / sc
        x, y, ang = traj[-1]
        traj.append((x + dx, y + dy, ang + da))
        pg, pm = g, m
    traj = np.array(traj)
    smooth = np.stack([gaussian_filter1d(traj[:, i], a.sigma, mode="nearest") for i in range(3)], 1)
    corr = smooth - traj
    print("max correction px:", np.abs(corr[:, :2]).max(0).round(1), "deg:", np.degrees(np.abs(corr[:, 2]).max()).round(2))

    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}",
                            "-r", str(fps), "-i", "-", "-i", a.src, "-map", "0:v", "-map", "1:a?",
                            "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", a.out],
                           stdin=subprocess.PIPE)
    for f, (dx, dy, da) in zip(frames, corr):
        M = cv2.getRotationMatrix2D((w / 2, h / 2), np.degrees(da), a.zoom)
        M[0, 2] += dx
        M[1, 2] += dy
        enc.stdin.write(cv2.warpAffine(f, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT).tobytes())
    enc.stdin.close()
    enc.wait()
    print("->", a.out)


if __name__ == "__main__":
    main()
