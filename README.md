<div align="center">

# 🎬 video-editing-skills

**Teach your coding agent to edit video like a professional editor.**

17 named editing styles · production-correct ffmpeg pipeline · beat sync · color grading · captions · sound design · tracking

[![test](https://github.com/Prateekiiitg56/video-editing-skills/actions/workflows/test.yml/badge.svg)](https://github.com/Prateekiiitg56/video-editing-skills/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Skills](https://img.shields.io/badge/skills-29-8A2BE2)
![Agents](https://img.shields.io/badge/agents-Claude%20Code%20%7C%20Codex%20%7C%20Gemini%20%7C%20OpenCode%20%7C%20Cursor-black)

[Quick start](#-quick-start) · [Editing styles](#-editing-styles) · [Packs](#-packs) · [How it works](#-how-it-works) · [Helper scripts](#-helper-scripts) · [FAQ](#-faq)

</div>

---

## What is this?

`video-editing-skills` is a library of [Agent Skills](https://agentskills.io): folders with a `SKILL.md` file that coding agents load when a task needs them. Install it, put your footage in a folder, and ask in plain language:

- *"Cut these clips into a 15-second Instagram reel synced to this song, with bold captions."*
- *"Make a velocity edit of my car footage."*
- *"Grade this travel footage cinematic and add a title."*
- *"Turn this podcast into three shorts with captions."*

The agent picks the right **editing style** and loads only the skills that style needs. It follows hard correctness rules (no cuts inside words, no audio pops, safe zones, single final encode, measured loudness) and checks its own render before showing you.

The pack comes from real production work, including:
- beat-synced Instagram reels
- restaurant and product promos
- a trailer cut from a git log
- 3D hologram composites
- photo carousels

Film-editing craft and current platform specs are added on top.

## ✨ Features

- **17 named editing styles**: Instagram Reels, Velocity, Cinematic, Motion Graphics, Kinetic Typography, Talking Head, Documentary, Music Video, Vlog/Travel, Commercial, Explainer, Trailer, VFX, Aesthetic, Meme, Event, Carousel. A hand-lettered quote overlay is included as an 18th style skill.
- **Smart router**: one entry skill inspects your footage and request, then loads the minimum set of skills.
- **Install only what you need**: install everything, a pack such as `reels` or `cinematic`, or single skills.
- **Works with many agents**: Claude Code, Codex, Gemini CLI, OpenCode, Cursor, and any agent that reads `SKILL.md`.
- **14 tested helper scripts** for beats, speed ramps, grading, captions, SFX, mixing, tracking, stabilization, reference analysis and export.
- **CI-verified**: every push runs an end-to-end smoke test and both installers on Ubuntu and Windows.

---

## 🚀 Quick start

### 1. Install

**macOS · Linux · Git Bash**
```bash
curl -fsSL https://raw.githubusercontent.com/Prateekiiitg56/video-editing-skills/main/install.sh | bash
```

**Windows PowerShell**
```powershell
irm https://raw.githubusercontent.com/Prateekiiitg56/video-editing-skills/main/install.ps1 | iex
```

<details>
<summary><b>Other install methods</b> (Claude Code plugin, skills CLI, manual)</summary>

**Claude Code plugin marketplace**
```
/plugin install video-editing-all --marketplace Prateekiiitg56/video-editing-skills
```
Claude Code older than 2.1.275:
```
/plugin marketplace add Prateekiiitg56/video-editing-skills
/plugin install video-editing-all@video-editing-skills
```

**skills CLI** (Vercel `skills`, supports 40+ agents)
```bash
npx skills add Prateekiiitg56/video-editing-skills
```
When you choose single skills with `--skill`, add `--skill video-editing` too. That skill is the router that picks the style.

**Manual**
```bash
git clone https://github.com/Prateekiiitg56/video-editing-skills
cp -R video-editing-skills/skills/* ~/.claude/skills/
```
</details>

### 2. Install the tools the skills use

| Tool | Needed for | Install |
|---|---|---|
| `ffmpeg` + `ffprobe` | all rendering | `brew install ffmpeg` · `sudo apt install ffmpeg` · `winget install Gyan.FFmpeg` |
| Python 3.9+ | helper scripts | [python.org](https://www.python.org/downloads/) |
| Python packages | helper scripts | `pip install -r requirements.txt`, or add `--deps` to the installer |

Optional:
- DaVinci Resolve
- Node.js 22+ for HyperFrames or Remotion
- a speech-to-text service with word timestamps (for example ElevenLabs Scribe, Deepgram or WhisperX)

### 3. Restart your agent and ask

```
Edit the clips in ./footage into a 20 s Instagram reel on ./song.mp3, cinematic grade, captions.
```

The agent replies with the style it chose and a short plan. Once you confirm, it builds a preview, checks it, and renders the final file.

---

## 🎨 Editing styles

| Style | Skill | Use it for | Signature techniques |
|---|---|---|---|
| **Instagram Reels / TikTok / Shorts** | `style-instagram-reels` | vertical short-form | 1 s hook, beat cuts, safe-zone text, loop endings, trending-audio workflow |
| **Velocity edit** | `style-velocity-edit` | "edit audio" trend: cars, gym, anime, sports | speed ramps on hits, zoom punches, shakes, flashes, RGB split |
| **Cinematic** | `style-cinematic` | brand films, travel films, short films | 24 fps, J/L cuts, match cuts, filmic grade, 2.39:1 letterbox, grain |
| **Motion graphics** | `style-motion-graphics` | logo stings, titles, lower thirds, UI, charts | design system, easing, stagger, alpha overlays |
| **Kinetic typography** | `style-kinetic-typography` | lyric videos, quote reels, word-by-word text | words timed to syllables, size hierarchy, tracked text |
| **Talking head** | `style-talking-head` | YouTube, podcasts, courses | silence/filler removal, punch-ins, B-roll, bold captions, multi-cam |
| **Documentary** | `style-documentary` | interviews, mini-docs, testimonials | paper edit, radio cut, nat-sound, lower thirds |
| **Music video** | `style-music-video` | artist videos, performance, visualizers | bar-structure cutting, lip-sync alignment, drops |
| **Vlog / Travel** | `style-vlog-travel` | trips, day-in-life | journey arc, whip/match transitions, route maps |
| **Commercial / Promo** | `style-commercial-promo` | products, restaurants, real estate, ads | hook → benefits → CTA, hero push-ins, end cards |
| **Explainer / Tutorial** | `style-explainer` | demos, screencasts, SaaS launches | cursor zooms, callouts, voiceover sync |
| **Trailer / Teaser** | `style-trailer` | trailers, launch hype, story-as-trailer | three acts, title cards, risers, silence drops |
| **VFX compositing** | `style-vfx-compositing` | tracked text, green screen, holograms, glows | tracking, keying, light/grain matching, 3D pose |
| **Aesthetic / Minimal** | `style-aesthetic-minimal` | calm lifestyle, desk, cafe, cozy | long holds, matte grade, lowercase serif, foley |
| **Meme / Comedy** | `style-meme-comedy` | skits, reactions, POV memes | comedic timing, crash zooms, freeze frames, SFX |
| **Event highlight** | `style-event-highlight` | weddings, concerts, sports, conferences | emotional arc, speech L-cuts, slow-mo peaks |
| **Instagram carousel** | `style-instagram-carousel` | photo dumps, swipe posts | 4:5 batch grading, cover hook, blurred-fill |
| **Hand-lettered quote** | `reel-hand-text` | trending quote overlay on reels | curved stacked hand-drawn capitals, 4K PNG |

## 🧱 Foundation skills

Style skills build on these shared skills:

| Skill | Responsible for |
|---|---|
| `video-editing` | **Router**: inspects the project, picks the style, loads skills, enforces hard rules and quality gates |
| `editing-foundations` | cut types (J/L, match, smash, jump), transitions, pacing, shot grammar, story structures, hooks |
| `ffmpeg-pipeline` | probing, rotation/VFR/HDR fixes, per-segment rendering, concat, xfade, overlays, export presets |
| `beat-sync` | beat/downbeat/hit detection, beat grids, cutting on hits, speed-ramp time-maps |
| `color-grading` | CDL model, LUTs, 11 named looks, log/HDR transforms, skin tones, shot matching |
| `captions-typography` | caption styles, word timing, font sizes for phones, safe zones, ASS rendering |
| `sound-design` | SFX vocabulary, hit alignment, ducking, dialogue cleanup, loudness mastering |
| `motion-tracking` | camera-motion analysis, stabilization, point/planar tracking, chroma keying |
| `reference-matching` | measure a reference video (cuts, beats, text, grade) and rebuild it |
| `shoot-planning` | shot lists, storyboards, camera settings (shutter, flicker, log, codecs) |
| `davinci-resolve` | Resolve pages, node grading, render presets, scripting API and MCP automation |

---

## 📦 Packs

Install only the editing type you need. The router is included in every pack.

| Pack | Skills | Includes |
|---|---:|---|
| `all` *(default)* | 29 | everything |
| `core` | 7 | router, foundations, ffmpeg, beat sync, color, captions, sound |
| `reels` | 15 | core + Reels, Velocity, Meme, Kinetic type, Aesthetic, Carousel, Hand-lettered quote, Reference matching |
| `cinematic` | 14 | core + Cinematic, Trailer, Music video, Documentary, Event, Shoot planning, Tracking |
| `motion` | 12 | core + Motion graphics, Kinetic type, Explainer, VFX, Tracking |
| `youtube` | 11 | core + Talking head, Documentary, Vlog/Travel, Explainer |
| `commercial` | 11 | core + Commercial, Event, Reference matching, Shoot planning |
| `vfx` | 9 | core + VFX compositing, Tracking |
| `resolve` | 3 | router, DaVinci Resolve, Color grading |

### Installer options

| Option (bash) | Option (PowerShell) | Effect |
|---|---|---|
| `--pack NAME` | `-Pack NAME` | install one pack |
| `--skills a,b` | `-Skills a,b` | install single skills (router is added automatically) |
| `--agent NAME` | `-Agent NAME` | `claude` (default), `codex`, `gemini`, `opencode`, `cursor`, `agents`, `all` |
| `--project` | `-Project` | install into the current folder (`./.claude/skills`) instead of your home folder |
| `--list` | `-List` | show packs and skills |
| `--uninstall` | `-Uninstall` | remove the selected pack/skills |
| `--deps` | `-Deps` | also `pip install` the Python helpers |

**Examples**
```bash
# Instagram reel editing only
curl -fsSL https://raw.githubusercontent.com/Prateekiiitg56/video-editing-skills/main/install.sh | bash -s -- --pack reels

# one style + color, for Codex
curl -fsSL https://raw.githubusercontent.com/Prateekiiitg56/video-editing-skills/main/install.sh | bash -s -- --skills style-cinematic,color-grading --agent codex

# YouTube pack into this project only
curl -fsSL https://raw.githubusercontent.com/Prateekiiitg56/video-editing-skills/main/install.sh | bash -s -- --pack youtube --project
```
```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/Prateekiiitg56/video-editing-skills/main/install.ps1))) -Pack reels
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/Prateekiiitg56/video-editing-skills/main/install.ps1))) -Skills style-cinematic,color-grading -Agent codex
```

**Claude Code plugins** (one per pack)
```
/plugin install video-editing-reels --marketplace Prateekiiitg56/video-editing-skills
/plugin install video-editing-cinematic --marketplace Prateekiiitg56/video-editing-skills
/plugin install video-editing-motion --marketplace Prateekiiitg56/video-editing-skills
/plugin install video-editing-youtube --marketplace Prateekiiitg56/video-editing-skills
/plugin install video-editing-commercial --marketplace Prateekiiitg56/video-editing-skills
/plugin install video-editing-vfx --marketplace Prateekiiitg56/video-editing-skills
/plugin install video-editing-resolve --marketplace Prateekiiitg56/video-editing-skills
/plugin install video-editing-core --marketplace Prateekiiitg56/video-editing-skills
```

### Where skills are installed

| Agent | Global (default) | With `--project` |
|---|---|---|
| Claude Code | `~/.claude/skills` | `./.claude/skills` |
| Codex | `~/.codex/skills` | `./.codex/skills` |
| Gemini CLI | `~/.gemini/skills` | `./.gemini/skills` |
| OpenCode | `~/.config/opencode/skills` | `./.opencode/skills` |
| Cursor | `~/.cursor/skills` | `./.cursor/skills` |
| Generic | `~/.agents/skills` | `./.agents/skills` |

---

## ⚙️ How it works

```mermaid
flowchart LR
    A[Your request + footage] --> B[video-editing router]
    B -->|inspects ffprobe, aspect, music, project files| C{Pick style}
    C --> D[style-* skill]
    D --> E[Foundation skills it needs<br/>ffmpeg · beat-sync · color · captions · sound · tracking]
    E --> F[Plan in plain English]
    F -->|you confirm| G[Build script + data files<br/>edl.json, timing.json]
    G --> H[Preview render]
    H --> I[Self-check<br/>frames at cuts, safe zones, LUFS, duration]
    I -->|fix up to 3 passes| G
    I --> J[Final export to platform spec]
```

**Workflow every style follows**
1. **Inspect**: probe sources (rotation, VFR, HDR, fps), detect beats, transcribe speech word by word.
2. **Ask only what the footage can't answer**: platform, length, music, brand, must-keep moments, reference video.
3. **Plan**: a 4–8 sentence strategy. Nothing is rendered until you confirm.
4. **Build**: a reproducible script plus data files. Feedback means editing data and running the script again.
5. **Self-check**: frames at every cut, text safe zones, `ffprobe` specs, measured loudness.
6. **Deliver**: final encode to the platform preset, plus a short project log.

**Hard rules the agent always follows**

| | |
|---|---|
| ✂️ Never cut inside a spoken word | 🔇 10–30 ms audio fades at every cut |
| 🔄 Fix rotation / HDR before editing | 🎞️ Encode lossy only once |
| 📝 Captions composited last | 📱 All text inside platform safe zones |
| 🔤 Fonts loaded from explicit files | 📈 Never linear easing |
| 🥁 Beat cuts land on the exact frame | 🚫 Never invent facts in on-screen text |
| 📏 Measure, don't claim (LUFS, fps, duration) | |

---

## 🛠 Helper scripts

Every script runs standalone. Usage is in the docstring at the top of each file. Every script is covered by the smoke test.

| Script | What it does |
|---|---|
| `ffmpeg-pipeline/scripts/probe.py` | one-line summary per file: size after rotation, fps/VFR, HDR, codec, audio |
| `ffmpeg-pipeline/scripts/export.py` | final encode: `instagram`, `tiktok`, `shorts`, `youtube`, `master`, `preview`; two-pass loudnorm; verification |
| `ffmpeg-pipeline/scripts/frames.py` | check frames at times, at intervals, or around every detected cut; contact sheet |
| `beat-sync/scripts/beats.py` | tempo, beats, downbeats, strong hits, energy curve, frame numbers |
| `beat-sync/scripts/timemap.py` | frame-exact speed ramps with easing and motion blur |
| `color-grading/scripts/grade.py` | 11 looks or any `.cube` LUT at chosen strength; side-by-side comparison grid |
| `captions-typography/scripts/captions.py` | word timestamps → styled ASS (`pop`, `karaoke`, `sentence`, `minimal`) |
| `sound-design/scripts/sfx.py` | synthesizes 10 royalty-free SFX (whoosh, hit, riser, boom, glitch…) with attack offsets |
| `sound-design/scripts/mix.py` | places music, dialogue and SFX on a timeline, with ducking and loudness |
| `motion-tracking/scripts/camera_motion.py` | finds camera moves and static parts (optical flow + RANSAC) |
| `motion-tracking/scripts/stabilize.py` | smooth-path stabilization; colour mask that ignores a moving subject |
| `motion-tracking/scripts/track_point.py` | template tracking with confidence scores |
| `reference-matching/scripts/analyze_reference.py` | cuts, shot lengths, beat alignment, colour, loudness and a thumbnail strip of a reference video |
| `reel-hand-text/handtext.py` | 4K transparent hand-lettered quote stack |

**Example: beat-synced cut points from a song**
```bash
python ~/.claude/skills/beat-sync/scripts/beats.py song.mp3 --out beats.json --start 41.8 --end 60.5
```

**Example: compare looks before grading**
```bash
python ~/.claude/skills/color-grading/scripts/grade.py clip.mp4 --compare looks.png --at 3
```

---

## ✅ Testing

```bash
pip install -r requirements.txt
python tests/smoke_test.py
```

The smoke test generates its own test media (3 shots with hard cuts and a 120 BPM track) and runs every script. It checks the results, for example:
- cuts found at exactly 2.0 s and 4.0 s
- tempo detection
- speed-ramp duration
- caption files
- a 1080x1920 H.264 export at **-14.0 LUFS**
- tracking confidence
- reference shot detection
- hand-lettered text rendering

CI ([`.github/workflows/test.yml`](.github/workflows/test.yml)) runs on Ubuntu and Windows for every push. It runs the smoke test plus:
- skill and manifest validation
- bash and PowerShell installer tests

---

## ❓ FAQ

<details>
<summary><b>Does it edit in a GUI editor?</b></summary>

Usually not. By default the agent writes a reproducible Python + ffmpeg build script. If your project is in DaVinci Resolve, the `davinci-resolve` skill works there instead, through the Resolve scripting API or a DaVinci Resolve MCP server.
</details>

<details>
<summary><b>Can I use trending Instagram/TikTok audio?</b></summary>

Trending sounds are licensed only inside the app. The reels skill exports a silent (or guide-audio) version for upload and tells you the exact song start point, so you can add the sound in-app.
</details>

<details>
<summary><b>Which transcription service do I need?</b></summary>

Any service that returns word-level timestamps: ElevenLabs Scribe, Deepgram, AssemblyAI, or local WhisperX/faster-whisper. `captions.py` accepts `[{word, start, end}]` JSON or `{"words": [...]}`.
</details>

<details>
<summary><b>Fonts look wrong / fall back to Arial</b></summary>

Fonts must be available as files. Download the free fonts (Montserrat, Inter, Caveat…) from Google Fonts. Put them in `./fonts` and pass `fontsdir=fonts` to ffmpeg's `subtitles` filter, or set `"font"` in the hand-text layout.
</details>

<details>
<summary><b>Export says loudness missed -14 LUFS</b></summary>

The audio is too peaky for linear gain under the -1 dBTP limit. Compress or limit the mix (`sound-design`), then export again.
</details>

<details>
<summary><b>Uninstalling one pack removed skills another pack needs</b></summary>

Packs share core skills. After `--uninstall`, reinstall any pack you still use.
</details>

<details>
<summary><b>Does it work with Remotion / HyperFrames / video-use?</b></summary>

Yes. When these are installed, the router uses them:
- Remotion: `npx skills add remotion-dev/skills`
- HyperFrames: `npx skills add heygen-com/hyperframes`
- video-use: [browser-use/video-use](https://github.com/browser-use/video-use)

They are separate projects and are not bundled here.
</details>

---

## 🗂 Repository layout

```
video-editing-skills/
├── skills/
│   ├── video-editing/            # router (entry point)
│   ├── editing-foundations/      # foundation skills …
│   ├── ffmpeg-pipeline/scripts/  # helper scripts live next to their skill
│   └── style-*/                  # one folder per editing style
├── packs/*.txt                   # skill lists used by the installers
├── .claude-plugin/marketplace.json  # Claude Code marketplace (one plugin per pack)
├── install.sh · install.ps1      # one-command installers
├── tests/smoke_test.py           # end-to-end test of every script
└── .github/workflows/test.yml    # CI on Ubuntu + Windows
```

## 🤝 Contributing

Contributions are welcome: new styles, better techniques, more scripts.

1. Fork the repo, then add or edit `skills/<name>/SKILL.md`. The frontmatter `name` must match the folder name, and the `description` must say **when** to use the skill (1024 characters max).
2. Add the skill to the right `packs/*.txt` files and to `.claude-plugin/marketplace.json`.
3. Scripts go in `skills/<name>/scripts/`. Pass `-nostdin` to every ffmpeg call, and add a check to `tests/smoke_test.py`.
4. Run `python tests/smoke_test.py`, then open a pull request.

A good skill teaches techniques that are both **correct** (they render right) and **tasteful** (they look professional). Use concrete numbers (durations, sizes, levels) rather than vague advice.

## 📄 License

[MIT](LICENSE) © Prateekiiitg56

Fonts mentioned (Caveat, Montserrat, Inter, Playfair Display, etc.) are Google Fonts under the SIL Open Font License; they are not bundled. Music and sound effects you use are your responsibility to license.
