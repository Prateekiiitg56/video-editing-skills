"""Final encode to a platform preset, then print a verification summary.

usage: python export.py IN OUT --preset instagram|tiktok|shorts|youtube|master|preview
                        [--size 1080x1920] [--fps 30] [--loudnorm]

--loudnorm runs two-pass EBU R128 normalisation to the preset's loudness target.
"""
import argparse
import json
import re
import subprocess

PRESETS = {
    # name: (default size, video args, audio args, LUFS target)
    "instagram": ("1080x1920", ["-c:v", "libx264", "-profile:v", "high", "-crf", "17", "-preset", "slow",
                                "-maxrate", "25M", "-bufsize", "50M"], ["-c:a", "aac", "-b:a", "320k", "-ar", "48000"], -14),
    "tiktok": ("1080x1920", ["-c:v", "libx264", "-profile:v", "high", "-crf", "17", "-preset", "slow",
                             "-maxrate", "20M", "-bufsize", "40M"], ["-c:a", "aac", "-b:a", "256k", "-ar", "48000"], -14),
    "shorts": ("1080x1920", ["-c:v", "libx264", "-profile:v", "high", "-crf", "16", "-preset", "slow"],
               ["-c:a", "aac", "-b:a", "320k", "-ar", "48000"], -14),
    "youtube": ("3840x2160", ["-c:v", "libx264", "-profile:v", "high", "-crf", "16", "-preset", "slow"],
                ["-c:a", "aac", "-b:a", "320k", "-ar", "48000"], -14),
    "master": (None, ["-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le"],
               ["-c:a", "pcm_s24le", "-ar", "48000"], -14),
    "preview": ("720x1280", ["-c:v", "libx264", "-crf", "28", "-preset", "veryfast"],
                ["-c:a", "aac", "-b:a", "128k"], None),
}
TAGS = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]


def loudnorm_filter(src, target):
    first = f"loudnorm=I={target}:TP=-1.0:LRA=11:print_format=json"
    err = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-i", src, "-af", first, "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = json.loads(re.findall(r"\{[^{}]*\}", err)[-1])
    return (f"loudnorm=I={target}:TP=-1.0:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
            f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--preset", required=True, choices=PRESETS)
    ap.add_argument("--size")
    ap.add_argument("--fps", type=float)
    ap.add_argument("--loudnorm", action="store_true")
    a = ap.parse_args()

    size, vargs, aargs, lufs = PRESETS[a.preset]
    size = a.size or size
    vf = []
    if size:
        w, h = size.split("x")
        vf.append(f"scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos,"
                  f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2")
    if a.fps:
        vf.append(f"fps={a.fps}")
    if a.preset != "master":
        vf.append("format=yuv420p")
    cmd = ["ffmpeg", "-nostdin", "-y", "-v", "error", "-stats", "-i", a.src]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    cmd += vargs + TAGS
    has_audio = bool(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                                     "stream=index", "-of", "csv=p=0", a.src], capture_output=True, text=True).stdout.strip())
    if a.loudnorm and lufs is not None and not has_audio:
        print("no audio stream: skipping loudnorm")
    if a.loudnorm and lufs is not None and has_audio:
        cmd += ["-af", loudnorm_filter(a.src, lufs)]
    cmd += aargs + ["-movflags", "+faststart", a.out]
    subprocess.run(cmd, check=True)

    info = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                           "stream=codec_name,width,height,r_frame_rate,pix_fmt:format=duration",
                           "-of", "compact", a.out], capture_output=True, text=True).stdout
    print(info.strip())
    ebu = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-i", a.out, "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    summary = ebu[ebu.rfind("Summary:"):]
    print(summary.strip() or "no audio")
    m = re.search(r"I:\s+(-?[\d.]+) LUFS", summary)
    if a.loudnorm and lufs is not None and m and abs(float(m.group(1)) - lufs) > 1.0:
        print(f"WARNING: integrated loudness {m.group(1)} LUFS misses the {lufs} LUFS target. The -1 dBTP peak "
              "limit stopped linear gain (very peaky audio). Compress or limit the mix first, then export again.")


if __name__ == "__main__":
    main()
