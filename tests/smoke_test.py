"""End-to-end smoke test: runs every helper script on synthetic media and checks the outputs.

usage: python tests/smoke_test.py [--keep]
needs: ffmpeg/ffprobe on PATH, pip install -r requirements.txt
Creates a temp folder with a 6 s 1080x1920 test clip (moving pattern + hard cuts) and a
120 BPM click-track song, then exercises probe, export, frames, beats, timemap, grade,
captions (+ burn-in), sfx, mix, camera_motion, stabilize, track_point, analyze_reference
and handtext. Exits non-zero on the first failure.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SK = os.path.join(ROOT, "skills")
PY = sys.executable
CAVEAT = "https://github.com/google/fonts/raw/main/ofl/caveat/Caveat%5Bwght%5D.ttf"
results = []


def run(name, args, cwd):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print(f"FAIL {name}\n{p.stdout[-1500:]}\n{p.stderr[-1500:]}")
        sys.exit(1)
    return p.stdout + p.stderr


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(f"{'ok  ' if cond else 'FAIL'} {name} {detail}")
    if not cond:
        sys.exit(1)


def script(*parts):
    return os.path.join(SK, *parts)


def probe_json(path):
    return json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
                                     capture_output=True, text=True).stdout)


def main():
    keep = "--keep" in sys.argv
    t = tempfile.mkdtemp(prefix="ves_smoke_")
    print("work dir:", t)
    ff = ["ffmpeg", "-nostdin", "-v", "error", "-y"]

    # synthetic media: 3 shots of 2 s (hard cuts at 2 s and 4 s), panning pattern
    shots = []
    for i, src in enumerate(["testsrc2", "smptebars", "mandelbrot"]):
        f = os.path.join(t, f"s{i}.mp4")
        subprocess.run(ff + ["-f", "lavfi", "-i", f"{src}=size=640x1138:rate=30", "-t", "2",
                             "-vf", "crop=540:960:'50+40*sin(t*2)':'50+30*cos(t*2)'", "-pix_fmt", "yuv420p", f],
                       check=True)
        shots.append(f)
    lst = os.path.join(t, "list.txt")
    open(lst, "w").write("".join(f"file '{s}'\n".replace("\\", "/") for s in shots))
    clip = os.path.join(t, "clip.mp4")
    subprocess.run(ff + ["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", clip], check=True)
    # 120 BPM: kick on every beat (0.5 s), louder on every 4th
    song = os.path.join(t, "song.wav")
    expr = "(0.5*exp(-mod(t,2)*30)+0.3*exp(-mod(t,0.5)*40))*sin(2*PI*60*t)+0.25*sin(2*PI*220*t)"
    subprocess.run(ff + ["-f", "lavfi", "-i", f"aevalsrc='{expr}':s=44100:d=8", song], check=True)
    withsound = os.path.join(t, "clip_sound.mp4")
    subprocess.run(ff + ["-i", clip, "-i", song, "-map", "0:v", "-map", "1:a", "-shortest", "-c:v", "copy",
                         "-c:a", "aac", withsound], check=True)

    # ffmpeg-pipeline
    out = run("probe", [PY, script("ffmpeg-pipeline", "scripts", "probe.py"), withsound], t)
    check("probe", "540x960" in out and "aac" in out, out.strip()[-80:])
    out = run("frames --cuts", [PY, script("ffmpeg-pipeline", "scripts", "frames.py"), clip, "fr", "--cuts", "--sheet"], t)
    check("frames --cuts finds 2 cuts", "cuts at: [2.0, 4.0]" in out, out.splitlines()[0])
    check("frames contact sheet", os.path.exists(os.path.join(t, "fr", "contact_sheet.png")))

    # beat-sync
    run("beats", [PY, script("beat-sync", "scripts", "beats.py"), song, "--out", "beats.json"], t)
    b = json.load(open(os.path.join(t, "beats.json")))
    check("beats tempo ~120", 115 <= b["tempo"] <= 125 or 58 <= b["tempo"] <= 62 or 235 <= b["tempo"] <= 245,
          f"tempo={b['tempo']}")
    json.dump({"src_start": 0.2, "segments": [{"dur": 0.5, "speed": [1, 1]}, {"dur": 0.5, "speed": [1, 4], "ease": "in"},
                                               {"dur": 0.5, "speed": [4, 0.3], "ease": "out"}]},
              open(os.path.join(t, "ramps.json"), "w"))
    run("timemap", [PY, script("beat-sync", "scripts", "timemap.py"), clip, "ramp.mp4", "ramps.json",
                    "--size", "540x960", "--src-fps", "30"], t)
    d = float(probe_json(os.path.join(t, "ramp.mp4"))["format"]["duration"])
    check("timemap duration 1.5 s", abs(d - 1.5) < 0.05, f"{d:.3f}s")

    # color-grading
    run("grade look", [PY, script("color-grading", "scripts", "grade.py"), clip, "graded.mp4", "--look", "teal-orange",
                       "--strength", "0.7", "--grain", "3"], t)
    check("grade output", os.path.getsize(os.path.join(t, "graded.mp4")) > 10000)
    run("grade compare", [PY, script("color-grading", "scripts", "grade.py"), clip, "--compare", "grid.png"], t)
    check("grade compare grid", os.path.exists(os.path.join(t, "grid.png")))

    # captions
    words = [{"word": w, "start": 0.3 + i * 0.4, "end": 0.6 + i * 0.4} for i, w in enumerate("one more commit, then sleep.".split())]
    json.dump(words, open(os.path.join(t, "words.json"), "w"))
    for st in ("pop", "karaoke", "sentence", "minimal"):
        run(f"captions {st}", [PY, script("captions-typography", "scripts", "captions.py"), "words.json", f"{st}.ass",
                               "--style", st, "--font", "Arial"], t)
        check(f"captions {st}", "Dialogue:" in open(os.path.join(t, f"{st}.ass"), encoding="utf-8").read())
    run("burn captions", ff + ["-i", "graded.mp4", "-vf", "subtitles=pop.ass", "-t", "2", "capd.mp4"], t)
    check("captions burned", os.path.exists(os.path.join(t, "capd.mp4")))

    # sound-design
    out = run("sfx", [PY, script("sound-design", "scripts", "sfx.py"), "sfx"], t)
    check("sfx kit (10 files)", len(os.listdir(os.path.join(t, "sfx"))) == 10)
    json.dump({"duration": 6, "music": {"file": "song.wav", "fade_out": 0.5},
               "dialogue": [{"file": "sfx/riser.wav", "at": 1.0}],
               "sfx": [{"file": "sfx/whoosh_up.wav", "hit": 2.0, "attack": 0.52, "gain_db": -8, "pan": -0.3},
                       {"file": "sfx/hit.wav", "hit": 4.0}], "target_lufs": -14},
              open(os.path.join(t, "plan.json"), "w"))
    run("mix", [PY, script("sound-design", "scripts", "mix.py"), "plan.json", "mix.wav"], t)
    a = probe_json(os.path.join(t, "mix.wav"))["streams"][0]
    check("mix 48 kHz stereo", a["sample_rate"] == "48000" and a["channels"] == 2)

    # export with loudnorm
    out = run("export", [PY, script("ffmpeg-pipeline", "scripts", "export.py"), withsound, "ig.mp4", "--preset",
                         "instagram", "--loudnorm"], t)
    v = probe_json(os.path.join(t, "ig.mp4"))["streams"][0]
    check("export 1080x1920 yuv420p h264", (v["width"], v["height"], v["pix_fmt"], v["codec_name"]) ==
          (1080, 1920, "yuv420p", "h264"))
    lufs = float(out.split("I:")[1].split("LUFS")[0])
    check("export loudness -14 LUFS", abs(lufs + 14) <= 1.0, f"{lufs} LUFS")

    # motion-tracking
    run("camera_motion", [PY, script("motion-tracking", "scripts", "camera_motion.py"), clip, "cm.json"], t)
    check("camera_motion rows", len(json.load(open(os.path.join(t, "cm.json")))["rows"]) >= 170)
    run("stabilize", [PY, script("motion-tracking", "scripts", "stabilize.py"), shots[0], "stab.mp4"], t)
    check("stabilize output", os.path.exists(os.path.join(t, "stab.mp4")))
    run("track_point", [PY, script("motion-tracking", "scripts", "track_point.py"), shots[0], "tr.json",
                        "--x", "270", "--y", "480", "--t", "0.2", "--until", "1.8"], t)
    tr = json.load(open(os.path.join(t, "tr.json")))
    check("track_point frames", len(tr) >= 40, f"{len(tr)} frames, mean score "
          f"{sum(r['score'] for r in tr) / len(tr):.2f}")

    # reference-matching
    run("analyze_reference", [PY, script("reference-matching", "scripts", "analyze_reference.py"), withsound, "ref"], t)
    ref = json.load(open(os.path.join(t, "ref", "reference.json")))
    check("reference finds 3 shots", len(ref["shots"]) == 3, str([s["dur"] for s in ref["shots"]]))

    # reel-hand-text (downloads Caveat if not installed)
    fonts = os.path.join(t, "fonts")
    os.makedirs(fonts, exist_ok=True)
    try:
        urllib.request.urlretrieve(CAVEAT, os.path.join(fonts, "Caveat-Bold.ttf"))
        layout = json.load(open(script("reel-hand-text", "example_layout.json")))
        layout["font"] = os.path.join(fonts, "Caveat-Bold.ttf")
        json.dump(layout, open(os.path.join(t, "layout.json"), "w"))
        run("handtext", [PY, script("reel-hand-text", "handtext.py"), "layout.json", "ht.png"], t)
        from PIL import Image
        im = Image.open(os.path.join(t, "ht.png"))
        check("handtext 2160x3840 RGBA with text", im.size == (2160, 3840) and im.mode == "RGBA"
              and im.getchannel("A").getbbox() is not None)
    except OSError as e:
        print("skip handtext (font download failed):", e)

    print(f"\nALL {len(results)} CHECKS PASSED")
    if not keep:
        shutil.rmtree(t, ignore_errors=True)


if __name__ == "__main__":
    main()
