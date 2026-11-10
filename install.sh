#!/usr/bin/env bash
# video-editing-skills installer (macOS / Linux / Git Bash on Windows)
#
# One command:
#   curl -fsSL https://raw.githubusercontent.com/Prateekiiitg56/video-editing-skills/main/install.sh | bash
# Choose a pack or single skills:
#   curl -fsSL .../install.sh | bash -s -- --pack reels
#   curl -fsSL .../install.sh | bash -s -- --skills style-cinematic,color-grading
# Other agents / project-local:
#   ... | bash -s -- --agent codex          (claude | codex | gemini | opencode | cursor | agents | all)
#   ... | bash -s -- --project              (install into ./.claude/skills of the current folder)
#   ... | bash -s -- --list | --uninstall | --deps
set -euo pipefail

REPO="${VES_REPO:-Prateekiiitg56/video-editing-skills}"
BRANCH="${VES_BRANCH:-main}"
PACK="all"; SKILLS=""; AGENT="claude"; PROJECT=0; ACTION="install"; DEPS=0; SRC="${VES_SRC:-}"

usage() { sed -n '2,13p' "$0" 2>/dev/null || true; echo "packs: all core reels cinematic motion youtube commercial vfx resolve"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --pack) PACK="$2"; shift 2 ;;
    --skills) SKILLS="$2"; shift 2 ;;
    --agent) AGENT="$2"; shift 2 ;;
    --project) PROJECT=1; shift ;;
    --list) ACTION="list"; shift ;;
    --uninstall) ACTION="uninstall"; shift ;;
    --deps) DEPS=1; shift ;;
    --source) SRC="$2"; shift 2 ;;   # use a local checkout instead of downloading
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

# 1. get the repository (local checkout, or download a tarball)
if [ -z "$SRC" ]; then
  if [ -f "$(dirname "$0")/packs/all.txt" ] 2>/dev/null; then
    SRC="$(cd "$(dirname "$0")" && pwd)"
  else
    TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
    echo "Downloading $REPO@$BRANCH ..."
    curl -fsSL "https://codeload.github.com/$REPO/tar.gz/refs/heads/$BRANCH" | tar -xz -C "$TMP"
    SRC="$(find "$TMP" -mindepth 1 -maxdepth 1 -type d | head -1)"
  fi
fi
[ -d "$SRC/skills" ] || { echo "skills/ not found in $SRC" >&2; exit 1; }

if [ "$ACTION" = "list" ]; then
  echo "Packs:"; for p in "$SRC"/packs/*.txt; do printf "  %-11s %s\n" "$(basename "$p" .txt)" "$(tr '\n' ' ' < "$p")"; done
  echo; echo "Skills:"
  for d in "$SRC"/skills/*/; do
    n="$(basename "$d")"
    desc="$(sed -n 's/^description: //p' "$d/SKILL.md" | cut -c1-90)"
    printf "  %-26s %s...\n" "$n" "$desc"
  done
  exit 0
fi

# 2. resolve the skill list
if [ -n "$SKILLS" ]; then
  LIST="$(echo "$SKILLS" | tr ',' '\n')"
  # always include the router so the agent can pick styles
  echo "$LIST" | grep -qx "video-editing" || LIST="video-editing
$LIST"
else
  [ -f "$SRC/packs/$PACK.txt" ] || { echo "unknown pack: $PACK" >&2; usage; exit 1; }
  LIST="$(cat "$SRC/packs/$PACK.txt")"
fi

# 3. resolve target folders
targets() {
  local base="$HOME"
  [ "$PROJECT" = 1 ] && base="$(pwd)"
  case "$1" in
    claude)   echo "$base/.claude/skills" ;;
    codex)    echo "$base/.codex/skills" ;;
    gemini)   echo "$base/.gemini/skills" ;;
    opencode) [ "$PROJECT" = 1 ] && echo "$base/.opencode/skills" || echo "$HOME/.config/opencode/skills" ;;
    cursor)   echo "$base/.cursor/skills" ;;
    agents)   echo "$base/.agents/skills" ;;
    all)      for a in claude codex gemini opencode cursor agents; do targets "$a"; done ;;
    *) echo "unknown agent: $1" >&2; exit 1 ;;
  esac
}

count=0
for T in $(targets "$AGENT"); do
  mkdir -p "$T"
  for s in $LIST; do
    s="$(echo "$s" | tr -d '\r ')"; [ -z "$s" ] && continue
    if [ ! -d "$SRC/skills/$s" ]; then echo "  ! unknown skill: $s" >&2; continue; fi
    if [ "$ACTION" = "uninstall" ]; then
      rm -rf "${T:?}/$s" && echo "  - $T/$s"
    else
      rm -rf "${T:?}/$s"; cp -R "$SRC/skills/$s" "$T/$s"; count=$((count+1))
    fi
  done
  [ "$ACTION" = "install" ] && echo "Installed into $T"
done

if [ "$ACTION" = "install" ]; then
  echo "Done: $count skill copies. Restart your agent, then ask e.g. \"edit this into an Instagram reel\"."
  if [ "$DEPS" = 1 ]; then
    echo "Installing Python helpers (numpy scipy opencv-python librosa soundfile pillow)..."
    python3 -m pip install --user numpy scipy opencv-python librosa soundfile pillow pyloudnorm || \
      python -m pip install --user numpy scipy opencv-python librosa soundfile pillow pyloudnorm
  fi
  command -v ffmpeg >/dev/null 2>&1 || echo "Note: ffmpeg not found on PATH. Install it (brew install ffmpeg / apt install ffmpeg / winget install Gyan.FFmpeg)."
fi
