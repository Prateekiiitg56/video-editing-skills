"""Mix music, dialogue and SFX from a JSON plan into one WAV, with ducking and loudness normalisation.

usage: python mix.py plan.json out.wav
needs: pip install numpy soundfile librosa

plan.json:
{
  "duration": 18.5,
  "target_lufs": -14,                       # optional; needs pyloudnorm, else peak-normalise to -1 dBFS
  "music": {"file": "song.mp3", "src_start": 41.8, "gain_db": 0, "fade_in": 0.02, "fade_out": 1.0},
  "dialogue": [{"file": "vo.wav", "at": 0.5, "gain_db": 0}],
  "duck_db": -14,                           # music level under dialogue
  "sfx": [{"file": "sfx/whoosh_up.wav", "hit": 3.0, "attack": 0.52, "gain_db": -8, "pan": -0.3}]
}
"hit" is the output time the effect should land on; "attack" is the effect's peak offset
(sfx.py prints it). The file starts at hit - attack.
"""
import json
import sys

import librosa
import numpy as np
import soundfile as sf

SR = 48000


def load(path, start=0.0, dur=None):
    y, _ = librosa.load(path, sr=SR, mono=False, offset=start, duration=dur)
    y = np.atleast_2d(y)
    if y.shape[0] == 1:
        y = np.vstack([y, y])
    return y.T  # N x 2


def place(buf, sig, at, gain_db=0.0, pan=0.0):
    i = int(round(at * SR))
    if i < 0:
        sig, i = sig[-i:], 0
    n = min(len(sig), len(buf) - i)
    if n <= 0:
        return
    g = 10 ** (gain_db / 20)
    lr = np.array([min(1, 1 - pan), min(1, 1 + pan)])
    buf[i:i + n] += sig[:n] * g * lr


def fade(sig, fin, fout):
    n = len(sig)
    a, b = int(fin * SR), int(fout * SR)
    if a:
        sig[:a] *= np.linspace(0, 1, a)[:, None]
    if b:
        sig[n - b:] *= np.linspace(1, 0, b)[:, None]
    return sig


def main():
    plan = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    N = int(plan["duration"] * SR)
    music = np.zeros((N, 2))
    voice = np.zeros((N, 2))
    fx = np.zeros((N, 2))

    if plan.get("music"):
        m = plan["music"]
        sig = load(m["file"], m.get("src_start", 0), plan["duration"] - m.get("at", 0))
        place(music, fade(sig, m.get("fade_in", 0.02), m.get("fade_out", 0.5)), m.get("at", 0), m.get("gain_db", 0))
    for d in plan.get("dialogue", []):
        sig = fade(load(d["file"], d.get("src_start", 0), d.get("dur")), 0.02, 0.03)
        place(voice, sig, d["at"], d.get("gain_db", 0))
    for s in plan.get("sfx", []):
        place(fx, load(s["file"]), s["hit"] - s.get("attack", 0), s.get("gain_db", -6), s.get("pan", 0))

    if np.abs(voice).max() > 0:  # duck music under dialogue with smoothed envelope
        e = np.abs(voice).max(1)
        win = int(0.15 * SR)
        e = np.convolve(e, np.ones(win) / win, mode="same")
        active = (e > e.max() * 0.05).astype(np.float64)
        # hold 0.4 s after speech (release), then smooth edges (~100 ms attack/release ramps)
        hold = int(0.4 * SR)
        active = np.lib.stride_tricks.sliding_window_view(np.pad(active, (hold, 0)), hold + 1).max(1)[:N]
        ramp = int(0.1 * SR)
        active = np.convolve(active, np.ones(ramp) / ramp, mode="same")
        gain = 1 - active * (1 - 10 ** (plan.get("duck_db", -14) / 20))
        music *= gain[:, None]

    mixbuf = music + voice + fx
    target = plan.get("target_lufs")
    try:
        import pyloudnorm as pyln
        if target is not None:
            loud = pyln.Meter(SR).integrated_loudness(mixbuf)
            mixbuf *= 10 ** ((target - loud) / 20)
            print(f"loudness {loud:.1f} -> {target} LUFS")
    except ImportError:
        print("pyloudnorm not installed: peak-normalising only; run export.py --loudnorm on the final file")
    peak = np.abs(mixbuf).max()
    if peak > 10 ** (-1 / 20):
        mixbuf *= 10 ** (-1 / 20) / peak
    sf.write(out, mixbuf, SR, subtype="PCM_24")
    print(f"mix {plan['duration']}s, peak {20 * np.log10(np.abs(mixbuf).max() + 1e-9):.1f} dBFS -> {out}")


if __name__ == "__main__":
    main()
