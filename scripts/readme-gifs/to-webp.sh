#!/usr/bin/env bash
# Convert the recorded README scenes into animated WebP in docs/assets/readme/.
# Usage: scripts/readme-gifs/to-webp.sh [recordDir] [outDir]
# WebP keeps full colour at 12-15 fps for a fraction of the GIF size and
# renders inline on GitHub. record.mjs writes <scene>.cuts.json with the
# loading gaps it waited through; those spans are cut so each clip jumps
# from a click straight to the rendered page.
set -euo pipefail

src="${1:-dist/readme-gifs}"
out="${2:-docs/assets/readme}"
width="${DEMO_WIDTH:-800}"
quality="${DEMO_QUALITY:-55}"
mkdir -p "$out"

webp_opts=(-c:v libwebp_anim -lossless 0 -quality "$quality" -compression_level 6 -loop 0)

report() { printf '%-30s %s\n' "$1.webp" "$(du -h "$out/$1.webp" | cut -f1)"; }

# ffmpeg select expression: keep everything except the recorded gaps.
keep_expr() {
  python3 - "$src/$1.cuts.json" <<'PY'
import json, sys
try:
    cuts = json.load(open(sys.argv[1]))
except FileNotFoundError:
    cuts = []
parts = [f"between(t,{a:.2f},{b:.2f})" for a, b in cuts if b > a]
print(f"not({'+'.join(parts)})" if parts else "1")
PY
}

# Video scene: drop the loading gaps, then resample to $fps.
video_clip() {
  local in="$1" fps="$2" dest="$3"
  local sel
  sel="$(keep_expr "$in")"
  ffmpeg -loglevel error -y -i "$src/$in.webm" \
    -vf "select='$sel',setpts=N/FRAME_RATE/TB,fps=$fps,scale=$width:-1:flags=lanczos" \
    "${webp_opts[@]}" "$out/$dest.webp"
  report "$dest"
}

# Frame scene: a PNG sequence captured on a frozen clock at $fps.
frames_clip() {
  local in="$1" fps="$2" dest="$3"
  ffmpeg -loglevel error -y -framerate "$fps" -i "$src/frames-$in/f%04d.png" \
    -vf "scale=$width:-1:flags=lanczos" \
    "${webp_opts[@]}" "$out/$dest.webp"
  report "$dest"
}

frames_clip home 15 starmap
video_clip loop     12 project-evidence-skill
video_clip research 12 research
video_clip content  12 content
