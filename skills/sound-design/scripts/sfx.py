"""Synthesize a starter kit of royalty-free SFX (48 kHz, 24-bit stereo WAV).

usage: python sfx.py OUTDIR [--seed 7]
needs: pip install numpy scipy soundfile

Writes: whoosh_up.wav whoosh_down.wav hit.wav thud.wav riser.wav tick.wav pop.wav
        sub_boom.wav glitch.wav shutter.wav, and prints each file's attack offset
        (seconds from file start to its peak) so you can start it early to hit a frame.
"""
import argparse
import os

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

SR = 48000


def env(n, a, d, curve=3.0):
    """Attack/decay envelope, a and d as fractions of n."""
    t = np.linspace(0, 1, n)
    up = np.clip(t / max(a, 1e-6), 0, 1) ** 2
    down = np.clip((1 - t) / max(d, 1e-6), 0, 1) ** curve
    return np.minimum(up, down)


def bandsweep(noise, f0, f1, q=2.0, blocks=64):
    out = np.zeros_like(noise)
    edges = np.linspace(0, len(noise), blocks + 1).astype(int)
    for i in range(blocks):
        f = f0 * (f1 / f0) ** (i / (blocks - 1))
        lo, hi = max(f / q, 30), min(f * q, SR / 2 - 100)
        sos = butter(2, [lo, hi], btype="band", fs=SR, output="sos")
        seg = slice(max(edges[i] - 512, 0), edges[i + 1])
        out[edges[i]:edges[i + 1]] = sosfilt(sos, noise[seg])[-(edges[i + 1] - edges[i]):]
    return out


def stereo(x, width=0.0, rng=None):
    if width and rng is not None:
        d = int(SR * 0.0004)
        r = np.concatenate([np.zeros(d), x[:-d]])
        return np.stack([x, (1 - width) * x + width * r], 1)
    return np.stack([x, x], 1)


def norm(x, peak_db=-1.0):
    return x / (np.abs(x).max() + 1e-9) * 10 ** (peak_db / 20)


def make(rng):
    n = lambda s: int(SR * s)
    noise = lambda s: rng.standard_normal(n(s))
    t = lambda s: np.arange(n(s)) / SR
    kit = {}
    kit["whoosh_up"] = bandsweep(noise(0.7), 300, 6000) * env(n(0.7), 0.75, 0.25)
    kit["whoosh_down"] = bandsweep(noise(0.7), 6000, 250) * env(n(0.7), 0.3, 0.7)
    body = np.sin(2 * np.pi * (60 + 120 * np.exp(-t(0.6) * 25)) * t(0.6)) * np.exp(-t(0.6) * 7)
    snap = sosfilt(butter(2, 1500, "high", fs=SR, output="sos"), noise(0.6)) * np.exp(-t(0.6) * 60)
    kit["hit"] = body + 0.5 * snap
    kit["thud"] = np.sin(2 * np.pi * (45 + 70 * np.exp(-t(0.45) * 30)) * t(0.45)) * np.exp(-t(0.45) * 10)
    sweep = np.sin(2 * np.pi * np.cumsum(200 * (8 ** (t(2.0) / 2.0))) / SR)
    kit["riser"] = (0.6 * sweep + 0.6 * bandsweep(noise(2.0), 400, 9000)) * env(n(2.0), 0.97, 0.03, 1)
    kit["tick"] = sosfilt(butter(2, [2000, 9000], "band", fs=SR, output="sos"), noise(0.04)) * np.exp(-t(0.04) * 180)
    kit["pop"] = np.sin(2 * np.pi * (900 - 500 * t(0.08) / 0.08) * t(0.08)) * env(n(0.08), 0.05, 0.95, 4)
    kit["sub_boom"] = np.sin(2 * np.pi * (38 + 40 * np.exp(-t(2.5) * 6)) * t(2.5)) * np.exp(-t(2.5) * 1.6)
    g = np.zeros(n(0.35))
    for k in range(9):
        s = int(rng.integers(0, len(g) - n(0.03)))
        f = rng.choice([800, 1600, 3200, 120])
        g[s:s + n(0.03)] += np.sign(np.sin(2 * np.pi * f * t(0.03))) * 0.5
    kit["glitch"] = g + 0.2 * noise(0.35) * env(n(0.35), 0.01, 0.99, 1)
    c = sosfilt(butter(2, [1500, 8000], "band", fs=SR, output="sos"), noise(0.18))
    kit["shutter"] = c * (np.exp(-t(0.18) * 80) + 0.8 * np.exp(-np.maximum(t(0.18) - 0.09, 0) * 90) * (t(0.18) > 0.09))
    return kit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    for name, sig in make(rng).items():
        st = stereo(norm(sig, -3 if name not in ("tick", "pop") else -6), 0.3, rng)
        path = os.path.join(a.outdir, f"{name}.wav")
        sf.write(path, st, SR, subtype="PCM_24")
        print(f"{name:12s} {len(sig) / SR:5.2f}s  attack(peak) at {np.abs(sig).argmax() / SR:.3f}s -> {path}")


if __name__ == "__main__":
    main()
