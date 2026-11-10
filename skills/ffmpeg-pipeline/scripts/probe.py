"""One-line technical summary per media file (needs ffprobe on PATH).

usage: python probe.py FILE [FILE ...]
Prints: name  WxH (display, after rotation)  fps (VFR flag)  duration  codec/pix_fmt  HDR  audio
"""
import json
import subprocess
import sys


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
        capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def rotation(stream):
    rot = int(stream.get("tags", {}).get("rotate", 0) or 0)
    for sd in stream.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(sd["rotation"])
    return rot % 360


def fps(rate):
    n, d = (rate or "0/1").split("/")
    return float(n) / float(d) if float(d) else 0.0


def summary(path):
    info = probe(path)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    dur = float(info["format"].get("duration", 0))
    if v is None:
        return f"{path}  audio-only  {dur:.2f}s  {a['codec_name']} {a.get('sample_rate')}Hz ch={a.get('channels')}"
    w, h = v["width"], v["height"]
    rot = rotation(v)
    if rot in (90, 270):
        w, h = h, w
    r, avg = fps(v.get("r_frame_rate")), fps(v.get("avg_frame_rate"))
    vfr = " VFR" if avg and abs(r - avg) > 0.01 else ""
    trc = v.get("color_transfer", "")
    hdr = {"arib-std-b67": "HDR-HLG", "smpte2084": "HDR-PQ"}.get(trc, "SDR")
    if any("dovi" in str(sd).lower() for sd in v.get("side_data_list", []) or []):
        hdr += "+DolbyVision"
    aud = f"{a['codec_name']} {a.get('sample_rate')}Hz ch={a.get('channels')}" if a else "no-audio"
    return (f"{path}  {w}x{h} rot={rot}  {avg or r:.3f}fps{vfr}  {dur:.2f}s  "
            f"{v['codec_name']}/{v.get('pix_fmt')}  {hdr}  {aud}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for p in sys.argv[1:]:
        try:
            print(summary(p))
        except Exception as e:  # keep going on bad files
            print(f"{p}  ERROR {e}")
