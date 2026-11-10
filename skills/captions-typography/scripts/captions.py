"""Word-level timestamps -> styled ASS captions (burn in with ffmpeg subtitles filter).

usage: python captions.py words.json out.ass --style pop|karaoke|sentence|minimal
                          [--size 1080x1920] [--font "Montserrat ExtraBold"] [--y 0.68]
                          [--accent FFD400] [--offset 0.0]

words.json: [{"word": "Hello", "start": 0.12, "end": 0.40}, ...]  (seconds, output timeline)
            also accepts {"words": [...]} (ElevenLabs/whisperx style) with "text" instead of "word".
Burn:  ffmpeg -i in.mp4 -vf "subtitles=out.ass:fontsdir=fonts" -c:a copy out.mp4
"""
import argparse
import json

STYLES = {
    #          words/chunk, upper, font size @1080w, outline, shadow, bold
    "pop": dict(max_words=3, upper=True, size=88, outline=6, shadow=2, bold=1, font="Montserrat ExtraBold"),
    "karaoke": dict(max_words=6, upper=False, size=64, outline=4, shadow=1, bold=1, font="Montserrat SemiBold"),
    "sentence": dict(max_words=9, upper=False, size=52, outline=2, shadow=2, bold=0, font="Inter"),
    "minimal": dict(max_words=7, upper=False, size=50, outline=0, shadow=3, bold=0, font="Cormorant Garamond"),
}
MIN_DUR = 0.35
GAP_BREAK = 0.30


def load(path):
    data = json.load(open(path, encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("words", [])
    out = []
    for w in data:
        text = (w.get("word") or w.get("text") or "").strip()
        if text and w.get("type", "word") == "word":
            out.append({"word": text, "start": float(w["start"]), "end": float(w["end"])})
    return out


def chunk(words, max_words):
    chunks, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        punct = w["word"][-1] in ".,!?;:"
        gap = nxt and nxt["start"] - w["end"] >= GAP_BREAK
        if len(cur) >= max_words or punct or gap or nxt is None:
            chunks.append(cur)
            cur = []
    # merge chunks that would flash too briefly
    merged = []
    for c in chunks:
        if merged and c[-1]["end"] - c[0]["start"] < MIN_DUR and len(merged[-1]) < 4:
            merged[-1] = merged[-1] + c
        else:
            merged.append(c)
    return merged


def ts(t):
    t = max(t, 0)
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def bgr(hex_rgb):
    r, g, b = hex_rgb[0:2], hex_rgb[2:4], hex_rgb[4:6]
    return f"&H00{b}{g}{r}&".upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("words")
    ap.add_argument("out")
    ap.add_argument("--style", default="pop", choices=STYLES)
    ap.add_argument("--size", default="1080x1920")
    ap.add_argument("--font")
    ap.add_argument("--y", type=float, default=0.68, help="caption centre as fraction of height")
    ap.add_argument("--accent", default="FFD400", help="active word colour RRGGBB")
    ap.add_argument("--offset", type=float, default=0.0, help="seconds added to every timestamp")
    a = ap.parse_args()
    st = STYLES[a.style]
    W, H = map(int, a.size.split("x"))
    k = W / 1080
    font = a.font or st["font"]
    words = [dict(w, start=w["start"] + a.offset, end=w["end"] + a.offset) for w in load(a.words)]
    x, y = W // 2, int(H * a.y)

    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{font},{int(st['size'] * k)},&H00FFFFFF,{bgr(a.accent)},&H00000000,&H80000000,{st['bold']},0,0,0,100,100,0,0,1,{st['outline'] * k:.1f},{st['shadow'] * k:.1f},5,{int(60 * k)},{int(140 * k)},0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    chunks = chunk(words, st["max_words"])
    for ci, c in enumerate(chunks):
        start = c[0]["start"]
        nxt_start = chunks[ci + 1][0]["start"] if ci + 1 < len(chunks) else None
        end = c[-1]["end"] + 0.15
        if nxt_start is not None:
            end = min(end, nxt_start)
        end = max(end, start + MIN_DUR)
        txt = lambda w: w["word"].upper() if st["upper"] else w["word"]
        pos = f"\\pos({x},{y})"
        if a.style == "pop":
            # one event per word: whole chunk visible, active word accented + scaled, pop-in on chunk start
            for wi, w in enumerate(c):
                ws = w["start"] if wi else start
                we = c[wi + 1]["start"] if wi + 1 < len(c) else end
                parts = []
                for j, o in enumerate(c):
                    if j == wi:
                        parts.append(f"{{\\c{bgr(a.accent)}\\fscx110\\fscy110}}{txt(o)}{{\\c&H00FFFFFF&\\fscx100\\fscy100}}")
                    else:
                        parts.append(txt(o))
                anim = "\\fscx80\\fscy80\\t(0,90,\\fscx100\\fscy100)" if wi == 0 else ""
                lines.append(f"Dialogue: 0,{ts(ws)},{ts(we)},Cap,,0,0,0,,{{{pos}{anim}}}{' '.join(parts)}")
        elif a.style == "karaoke":
            body = "".join(f"{{\\k{max(1, round((w['end'] - w['start']) * 100))}}}{txt(w)} " for w in c)
            lines.append(f"Dialogue: 0,{ts(start)},{ts(end)},Cap,,0,0,0,,{{{pos}\\fad(80,60)}}{body.strip()}")
        else:
            lines.append(f"Dialogue: 0,{ts(start)},{ts(end)},Cap,,0,0,0,,{{{pos}\\fad(120,100)}}"
                         + " ".join(txt(w) for w in c))
    open(a.out, "w", encoding="utf-8").write(head + "\n".join(lines) + "\n")
    print(f"{len(chunks)} caption chunks, style {a.style}, font '{font}' -> {a.out}")
    print("reminder: pass fontsdir= with the font file, or libass falls back silently")


if __name__ == "__main__":
    main()
