"""Render a variable-speed (speed ramp) clip from a time-map, frame-exact.

usage: python timemap.py SRC OUT ramps.json [--fps 30] [--size 1080x1920] [--blend 3]

ramps.json:
{
  "src_start": 2.0,                     # source time at output t=0
  "segments": [                         # consecutive output segments
    {"dur": 0.8, "speed": [1.0, 1.0]},
    {"dur": 0.6, "speed": [1.0, 4.0], "ease": "in"},     # ramp up
    {"dur": 0.4, "speed": [4.0, 0.3], "ease": "out"},    # slam down onto the hit
    {"dur": 1.0, "speed": [0.3, 1.0], "ease": "inout"}
  ]
}
Speed is interpolated across each segment with the given easing. Source time is the
integral of speed. --blend N averages N sub-frames when speed > 1.5 (motion blur).
Video only; build the audio separately (music bed). Source is decoded once into RAM
at the output size, so keep clips short (a few seconds of 1080p is fine).
"""
import argparse
import json
import subprocess

import numpy as np

EASE = {
    "linear": lambda u: u,
    "in": lambda u: u ** 3,
    "out": lambda u: 1 - (1 - u) ** 3,
    "inout": lambda u: 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2,
}


def build_map(spec, fps):
    """Return source time for every output frame (and the speed there)."""
    t_src, out = spec.get("src_start", 0.0), []
    sub = 8  # integration sub-steps per frame
    for seg in spec["segments"]:
        n = int(round(seg["dur"] * fps))
        s0, s1 = seg["speed"]
        ease = EASE[seg.get("ease", "inout")]
        for i in range(n):
            out.append((t_src, s0 + (s1 - s0) * ease(i / max(n, 1))))
            for k in range(sub):
                u = (i + (k + 0.5) / sub) / max(n, 1)
                t_src += (s0 + (s1 - s0) * ease(min(u, 1))) / fps / sub
    return out


def read_frames(src, w, h, fps_src):
    p = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", src, "-vf",
                        f"fps={fps_src},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(p, np.uint8).reshape(-1, h, w, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("ramps")
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--src-fps", type=float, default=60, help="decode rate; use the source's real fps")
    ap.add_argument("--size", default="1080x1920")
    ap.add_argument("--blend", type=int, default=3)
    a = ap.parse_args()
    w, h = map(int, a.size.split("x"))
    spec = json.load(open(a.ramps))
    tmap = build_map(spec, a.fps)
    frames = read_frames(a.src, w, h, a.src_fps)
    last = len(frames) - 1

    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                            "-r", str(a.fps), "-i", "-", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p",
                            a.out], stdin=subprocess.PIPE)
    for t, speed in tmap:
        idx = t * a.src_fps
        if speed > 1.5 and a.blend > 1:  # motion blur: average frames spanned by this output frame
            span = speed * a.src_fps / a.fps
            ids = np.clip(np.round(idx + np.linspace(-span / 2, span / 2, a.blend)).astype(int), 0, last)
            img = frames[ids].astype(np.float32).mean(0).astype(np.uint8)
        else:
            img = frames[min(int(round(idx)), last)]
        enc.stdin.write(img.tobytes())
    enc.stdin.close()
    enc.wait()
    print(f"{len(tmap)} frames ({len(tmap) / a.fps:.2f}s), source used {tmap[0][0]:.2f}-{tmap[-1][0]:.2f}s -> {a.out}")


if __name__ == "__main__":
    main()
