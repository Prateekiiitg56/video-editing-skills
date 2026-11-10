# video-editing-skills

Skills that teach coding agents (Claude Code, Codex, Gemini CLI, OpenCode, Cursor, and any agent that reads `SKILL.md` folders) to **edit video like a professional editor**. The pack covers 17 named editing styles, built on production-correct foundations: cutting, ffmpeg, beat sync, color grading, captions, sound design, tracking, and DaVinci Resolve.

The pack comes from real projects: beat-synced Instagram reels, restaurant promos, a trailer cut from a git log, 3D hologram composites, and carousels. Craft knowledge from film editing and current platform specs is added on top.

## Install (one command)

**macOS / Linux / Git Bash**
```bash
curl -fsSL https://raw.githubusercontent.com/Prateekiiitg56/video-editing-skills/main/install.sh | bash
```

**Windows PowerShell**
```powershell
irm https://raw.githubusercontent.com/Prateekiiitg56/video-editing-skills/main/install.ps1 | iex
```

**Claude Code plugin marketplace**
```
/plugin install video-editing-all --marketplace Prateekiiitg56/video-editing-skills
```
On Claude Code older than 2.1.275, use two steps:
```
/plugin marketplace add Prateekiiitg56/video-editing-skills
/plugin install video-editing-all@video-editing-skills
```

**skills CLI (works with 40+ agents)**
```bash
npx skills add Prateekiiitg56/video-editing-skills
```
When you pick single skills with `--skill`, also add `--skill video-editing` (the router that picks the style).

Restart your agent, then just ask: *"Edit these clips into a cinematic travel reel"*, *"Make a velocity edit to this song"*, *"Cut this podcast into shorts with bold captions"*.

## Install only what you need

Each editing type is a **pack**:

| Pack | What you get |
|---|---|
| `all` (default) | everything |
| `core` | router + foundations (cuts, ffmpeg, beat sync, color, captions, sound) |
| `reels` | Instagram Reels / TikTok / Shorts, velocity edit, meme, kinetic type, aesthetic, carousel, hand-lettered quotes, reference matching |
| `cinematic` | cinematic, trailer, music video, documentary, event films, shoot planning |
| `motion` | motion graphics, kinetic typography, explainers, VFX |
| `youtube` | talking head, documentary, vlog/travel, explainers |
| `commercial` | product, restaurant, real-estate and brand promos, event highlights |
| `vfx` | compositing, tracking, stabilization, keying |
| `resolve` | DaVinci Resolve workflows and automation |

```bash
# Instagram reel editing only
curl -fsSL https://raw.githubusercontent.com/Prateekiiitg56/video-editing-skills/main/install.sh | bash -s -- --pack reels

# pick single skills (the router is always added)
curl -fsSL .../install.sh | bash -s -- --skills style-cinematic,color-grading

# other agents, or into the current project instead of your home folder
curl -fsSL .../install.sh | bash -s -- --agent codex          # claude | codex | gemini | opencode | cursor | agents | all
curl -fsSL .../install.sh | bash -s -- --pack youtube --project

# list, uninstall, and install the Python helpers
curl -fsSL .../install.sh | bash -s -- --list
curl -fsSL .../install.sh | bash -s -- --pack reels --uninstall
curl -fsSL .../install.sh | bash -s -- --deps
```

PowerShell takes the same options as parameters:
```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/Prateekiiitg56/video-editing-skills/main/install.ps1))) -Pack reels
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/Prateekiiitg56/video-editing-skills/main/install.ps1))) -Skills style-cinematic,color-grading -Agent codex
```

Claude Code marketplace plugins follow the same packs:
```
/plugin install video-editing-core --marketplace Prateekiiitg56/video-editing-skills
/plugin install video-editing-reels --marketplace Prateekiiitg56/video-editing-skills
/plugin install video-editing-cinematic --marketplace Prateekiiitg56/video-editing-skills
/plugin install video-editing-motion --marketplace Prateekiiitg56/video-editing-skills
/plugin install video-editing-youtube --marketplace Prateekiiitg56/video-editing-skills
/plugin install video-editing-commercial --marketplace Prateekiiitg56/video-editing-skills
/plugin install video-editing-vfx --marketplace Prateekiiitg56/video-editing-skills
/plugin install video-editing-resolve --marketplace Prateekiiitg56/video-editing-skills
```

Uninstalling a pack removes every skill in it, including core skills that other installed packs also use. Reinstall the other pack afterwards if you still need it.

## Editing styles

| Style | Skill | For |
|---|---|---|
| Instagram Reels / TikTok / Shorts | `style-instagram-reels` | 9:16 short-form, hook in 1 s, beat cuts, safe-zone captions |
| Velocity edit | `style-velocity-edit` | "edit audio" trend: speed ramps on hits, flashes, shakes |
| Cinematic | `style-cinematic` | film look, 24 fps, J/L cuts, filmic grade, letterbox |
| Motion graphics | `style-motion-graphics` | logo stings, titles, lower thirds, UI and data animation |
| Kinetic typography | `style-kinetic-typography` | lyric videos, word-by-word text, quote reels |
| Talking head | `style-talking-head` | YouTube, podcasts, jump cuts, punch-ins, bold captions |
| Documentary | `style-documentary` | interviews, paper edit, B-roll, lower thirds |
| Music video | `style-music-video` | song structure, performance sync, drops |
| Vlog / travel | `style-vlog-travel` | journey arc, whip/match transitions, maps |
| Commercial / promo | `style-commercial-promo` | products, restaurants, real estate, ads, CTA |
| Explainer / tutorial | `style-explainer` | screen recordings, zooms, callouts, demos |
| Trailer / teaser | `style-trailer` | three acts, title cards, risers, silence drops |
| VFX compositing | `style-vfx-compositing` | tracked text, green screen, holograms, glows, 3D |
| Aesthetic / minimal | `style-aesthetic-minimal` | calm lifestyle, lowercase serif, grain |
| Meme / comedy | `style-meme-comedy` | timing, crash zooms, freeze frames, SFX |
| Event highlight | `style-event-highlight` | weddings, concerts, sports, conferences |
| Instagram carousel | `style-instagram-carousel` | 4:5 photo dumps, batch grading |
| Hand-lettered quote | `reel-hand-text` | trending curved hand-drawn quote stack |

## Foundation skills

| Skill | Owns | Scripts |
|---|---|---|
| `video-editing` | router: picks style + skills, workflow, hard rules, quality gates | — |
| `editing-foundations` | cut types, transitions, pacing, shot grammar, story structures | — |
| `ffmpeg-pipeline` | probing, HDR/rotation/VFR, segments, concat, xfade, overlays, export presets | `probe.py`, `export.py`, `frames.py` |
| `beat-sync` | beats/downbeats/hits, grids, cuts on beats, speed-ramp time-maps | `beats.py`, `timemap.py` |
| `color-grading` | CDL, LUTs, 11 named looks, log/HDR, skin, shot matching | `grade.py` |
| `captions-typography` | caption styles, timing, fonts, sizes, safe zones | `captions.py` (word JSON → styled ASS) |
| `sound-design` | SFX vocabulary, hit alignment, ducking, loudness | `sfx.py` (synth SFX kit), `mix.py` |
| `motion-tracking` | camera motion, stabilization, point/planar tracking, keying | `camera_motion.py`, `stabilize.py`, `track_point.py` |
| `reference-matching` | measure and reproduce a reference video | `analyze_reference.py` |
| `shoot-planning` | shot lists, storyboards, camera settings (shutter, flicker, log) | — |
| `davinci-resolve` | Resolve pages, grading nodes, render presets, scripting API / MCP | — |

## Requirements

- `ffmpeg` and `ffprobe` on PATH.
- Python 3.9+ for the helper scripts: `pip install -r requirements.txt` (or run the installer with `--deps`).
- Optional: DaVinci Resolve, Node.js 22+ (HyperFrames/Remotion), and an ASR provider for word-level transcripts.

## Works well with (optional, separate projects)

- Remotion skills: `npx skills add remotion-dev/skills`
- HyperFrames (HTML → video): `npx skills add heygen-com/hyperframes`
- video-use (transcript-driven editing): https://github.com/browser-use/video-use

The router skill uses these when they are installed. This pack does not bundle them.

## Testing

`python tests/smoke_test.py` builds synthetic test media and runs every helper script, checking real outputs: cut detection, tempo, speed-ramp duration, caption files, a -14 LUFS export, tracking, and hand-lettered text. CI runs the smoke test and both installers on Ubuntu and Windows for every push.

## Repository layout

```
skills/<skill-name>/SKILL.md     one folder per skill (+ scripts/)
packs/<pack>.txt                 skill lists used by the installers
.claude-plugin/marketplace.json  Claude Code plugin marketplace (one plugin per pack)
install.sh / install.ps1         one-command installers
```

## License

MIT. Fonts referenced (Caveat, Montserrat, Inter, etc.) are Google Fonts under the SIL Open Font License and are not bundled. Download them separately.
