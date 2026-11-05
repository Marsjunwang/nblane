#!/usr/bin/env bash
# Convert the recorded README videos into docs/assets/readme/*.gif.
# Usage: scripts/readme-gifs/to-gif.sh [videoDir] [outDir]
# Trim windows drop the blank loading frames at the start of each scene;
# re-check them (frame luminance) if a scene's timing changes.
set -euo pipefail

src="${1:-dist/readme-gifs}"
out="${2:-docs/assets/readme}"
mkdir -p "$out"

gif() {
  local in="$1" sel="$2" fps="$3" dest="$4"
  ffmpeg -loglevel error -y -i "$src/$in.webm" -filter_complex \
    "[0:v]select='$sel',setpts=N/FRAME_RATE/TB,fps=$fps,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];[b][p]paletteuse=dither=none:diff_mode=rectangle" \
    "$out/$dest.gif"
  printf '%-28s %s\n' "$dest.gif" "$(du -h "$out/$dest.gif" | cut -f1)"
}

gif home     'between(t,5.5,15.5)'                   8 starmap
gif loop     'gte(t,0.5)'                            6 project-evidence-skill
gif research 'between(t,0.5,6.5)+between(t,11.5,22)' 6 research
gif content  'gte(t,0.5)'                            6 content
