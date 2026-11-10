"""Beat / downbeat / hit analysis for music-driven edits.

usage: python beats.py MUSIC [--out beats.json] [--start S] [--end E] [--fps 30]
needs: pip install librosa numpy soundfile

Writes JSON: tempo, beats, downbeats, hits (strong onsets), energy (RMS per 0.5 s),
all times in seconds relative to --start (default 0), plus frame numbers at --fps.
"""
import argparse
import json

import librosa
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("music")
    ap.add_argument("--out", default="beats.json")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float)
    ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--hit-threshold", type=float, default=0.8,
                    help="onset strength quantile 0..1 counted as a hit (higher = fewer hits)")
    a = ap.parse_args()

    dur = None if a.end is None else a.end - a.start
    y, sr = librosa.load(a.music, sr=22050, mono=True, offset=a.start, duration=dur)
    hop = 512
    oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    tempo, beat_frames = librosa.beat.beat_track(onset_envelope=oenv, sr=sr, hop_length=hop)
    tempo = float(np.atleast_1d(tempo)[0])
    beats = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop)

    # downbeat guess: the beat phase (0..3) with the highest summed onset strength
    strength = oenv[beat_frames] if len(beat_frames) else np.array([])
    phase = int(np.argmax([strength[p::4].sum() for p in range(4)])) if len(beats) >= 8 else 0
    downbeats = beats[phase::4]

    # hits: onset peaks above a strength quantile, at least 1/8 beat apart
    peaks = librosa.util.peak_pick(oenv, pre_max=3, post_max=3, pre_avg=10, post_avg=10,
                                   delta=0.1, wait=max(1, int(0.125 * 60 / max(tempo, 1) * sr / hop)))
    thr = np.quantile(oenv, a.hit_threshold) if len(oenv) else 0
    hits = librosa.frames_to_time([p for p in peaks if oenv[p] >= thr], sr=sr, hop_length=hop)

    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    rt = librosa.times_like(rms, sr=sr, hop_length=hop)
    energy = [round(float(rms[(rt >= s) & (rt < s + 0.5)].mean()), 4)
              for s in np.arange(0, rt[-1] if len(rt) else 0, 0.5)]

    fr = lambda ts: [int(round(t * a.fps)) for t in ts]
    out = {
        "source": a.music, "window_start": a.start, "fps": a.fps,
        "tempo": round(tempo, 2), "beat_period": round(60 / tempo, 4) if tempo else None,
        "beats": [round(float(t), 3) for t in beats], "beat_frames": fr(beats),
        "downbeats": [round(float(t), 3) for t in downbeats], "downbeat_frames": fr(downbeats),
        "hits": [round(float(t), 3) for t in hits], "hit_frames": fr(hits),
        "energy_per_0_5s": energy,
    }
    json.dump(out, open(a.out, "w"), indent=1)
    print(f"tempo {out['tempo']} BPM  beats {len(beats)}  downbeat phase {phase}  hits {len(hits)}")
    print("first downbeats:", out["downbeats"][:8])
    if energy:
        jump = int(np.argmax(np.diff(energy))) if len(energy) > 1 else 0
        print(f"biggest energy jump (drop?) near {jump * 0.5 + 0.5:.1f}s")
    print("->", a.out)


if __name__ == "__main__":
    main()
