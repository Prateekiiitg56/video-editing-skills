"""Analyse a reference video: cuts, shot lengths, beat alignment, colour stats, loudness, thumbnail strip.

usage: python analyze_reference.py REF.mp4 OUTDIR [--threshold 0.3]
needs: ffmpeg, numpy, pillow; librosa optional (beat alignment)
"""
import argparse
import json
import os
import re
import subprocess

import numpy as np
from PIL import Image


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ref")
    ap.add_argument("outdir")
    ap.add_argument("--threshold", type=float, default=0.3)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    meta = json.loads(run(["ffprobe", "-v", "error", "-show_entries",
                           "stream=codec_type,width,height,avg_frame_rate:format=duration", "-of", "json", a.ref]).stdout)
    v = next(s for s in meta["streams"] if s["codec_type"] == "video")
    n, d = v["avg_frame_rate"].split("/")
    fps = float(n) / float(d)
    dur = float(meta["format"]["duration"])

    err = run(["ffmpeg", "-nostdin", "-hide_banner", "-i", a.ref, "-vf", f"select='gt(scene,{a.threshold})',showinfo",
               "-f", "null", "-"]).stderr
    cuts = [round(float(t), 3) for t in re.findall(r"pts_time:([\d.]+)", err)]
    bounds = [0.0] + cuts + [dur]
    shots = [{"start": bounds[i], "end": bounds[i + 1], "dur": round(bounds[i + 1] - bounds[i], 3)}
             for i in range(len(bounds) - 1)]

    beats_info = None
    try:
        import librosa
        wav = os.path.join(a.outdir, "ref_audio.wav")
        run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", a.ref, "-vn", "-ac", "1", "-ar", "22050", wav])
        y, sr = librosa.load(wav, sr=22050)
        tempo, bf = librosa.beat.beat_track(y=y, sr=sr)
        beats = librosa.frames_to_time(bf, sr=sr)
        tempo = float(np.atleast_1d(tempo)[0])
        off = [round(float(c - beats[np.argmin(np.abs(beats - c))]), 3) for c in cuts] if len(beats) else []
        beats_info = {"tempo": round(tempo, 1), "beats": [round(float(b), 3) for b in beats],
                      "cut_offset_from_nearest_beat_s": off,
                      "cuts_within_2_frames_of_beat": sum(abs(o) <= 2 / fps for o in off)}
    except Exception as e:  # librosa missing or no audio
        beats_info = {"error": str(e)}

    thumbs, stats = [], []
    for i, s in enumerate(shots):
        t = s["start"] + s["dur"] / 2
        p = os.path.join(a.outdir, f"shot_{i:02d}.png")
        run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", a.ref, "-frames:v", "1", "-vf", "scale=240:-2", p])
        if os.path.exists(p):
            im = Image.open(p).convert("RGB")
            arr = np.asarray(im, np.float32) / 255
            luma = arr @ np.array([0.2126, 0.7152, 0.0722])
            sat = arr.max(2) - arr.min(2)
            stats.append({"shot": i, "mean_rgb": arr.reshape(-1, 3).mean(0).round(3).tolist(),
                          "luma_mean": round(float(luma.mean()), 3), "luma_p2_p98":
                          [round(float(np.percentile(luma, 2)), 3), round(float(np.percentile(luma, 98)), 3)],
                          "sat_mean": round(float(sat.mean()), 3)})
            thumbs.append(im)
    if thumbs:
        w, h = thumbs[0].size
        cols = min(8, len(thumbs))
        strip = Image.new("RGB", (cols * w, ((len(thumbs) + cols - 1) // cols) * h))
        for i, im in enumerate(thumbs):
            strip.paste(im.resize((w, h)), ((i % cols) * w, (i // cols) * h))
        strip.save(os.path.join(a.outdir, "strip.png"))

    ebu = run(["ffmpeg", "-nostdin", "-hide_banner", "-i", a.ref, "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    m = re.search(r"I:\s+(-?[\d.]+) LUFS", ebu[ebu.rfind("Summary"):] if "Summary" in ebu else "")
    durs = [s["dur"] for s in shots]
    out = {"file": a.ref, "width": v["width"], "height": v["height"], "fps": round(fps, 3), "duration": dur,
           "cuts": cuts, "shots": shots, "shot_len": {"mean": round(float(np.mean(durs)), 3),
                                                       "min": min(durs), "max": max(durs)},
           "beats": beats_info, "colour": stats, "loudness_lufs": float(m.group(1)) if m else None}
    json.dump(out, open(os.path.join(a.outdir, "reference.json"), "w"), indent=1)
    print(f"{v['width']}x{v['height']} {fps:.2f}fps {dur:.2f}s | {len(shots)} shots, mean {out['shot_len']['mean']}s")
    if isinstance(beats_info, dict) and "tempo" in beats_info:
        print(f"tempo {beats_info['tempo']} | cuts on beat (+/-2 frames): {beats_info['cuts_within_2_frames_of_beat']}/{len(cuts)}")
    print("->", os.path.join(a.outdir, "reference.json"), "+ strip.png")


if __name__ == "__main__":
    main()
