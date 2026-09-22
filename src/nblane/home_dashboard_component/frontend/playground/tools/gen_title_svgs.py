#!/usr/bin/env python3
"""Generate the 成长天文图 title-seal SVG assets (path-based, self-contained).

Variants:
  a) horizontal plaque, light chisel erosion (feDisplacementMap, small scale)
  b) horizontal plaque, heavy wear (displacement + noise-mask chips)
  c) square vermilion seal layout (2 columns: 成长天 / 文图)
Glyph outlines are baked to paths with fontTools so the SVGs render
identically everywhere without a font dependency.
"""

from __future__ import annotations

import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent / "assets" / "fonts"
OUT = HERE.parent / "assets"

TITLE = "成长天文图"
INK = "#e8e2d2"


def load(path: Path):
    font = TTFont(str(path))
    return font, font.getGlyphSet(), font["head"].unitsPerEm, font.getBestCmap(), font["hmtx"]


def char_path(glyphset, cmap, hmtx, ch):
    g = cmap[ord(ch)]
    pen = SVGPathPen(glyphset)
    glyphset[g].draw(pen)
    return pen.getCommands(), hmtx[g][0]


def text_paths(font_ctx, text, font_size, letter_spacing, cx, baseline_y):
    """Return SVG path elements for `text` centered on cx (font units y-up)."""
    font, glyphset, upm, cmap, hmtx = font_ctx
    sc = font_size / upm
    widths = [hmtx[cmap[ord(ch)]][0] * sc for ch in text]
    total = sum(widths) + letter_spacing * (len(text) - 1)
    x = cx - total / 2
    parts = []
    for ch, w in zip(text, widths):
        d, _ = char_path(glyphset, cmap, hmtx, ch)
        parts.append(f'<path d="{d}" transform="translate({x:.2f},{baseline_y:.2f}) scale({sc:.5f},{-sc:.5f})"/>')
        x += w + letter_spacing
    return "\n    ".join(parts)


EROSION_LIGHT = """<filter id="erosion" x="-8%" y="-8%" width="116%" height="116%">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="11" result="n"/>
      <feDisplacementMap in="SourceGraphic" in2="n" scale="2.2" xChannelSelector="R" yChannelSelector="G"/>
    </filter>"""

EROSION_HEAVY = """<filter id="erosion" x="-10%" y="-10%" width="120%" height="120%">
      <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="2" seed="23" result="n1"/>
      <feDisplacementMap in="SourceGraphic" in2="n1" scale="4.5" xChannelSelector="R" yChannelSelector="G" result="disp"/>
      <feTurbulence type="fractalNoise" baseFrequency="0.09" numOctaves="3" seed="5" result="n2"/>
      <feColorMatrix in="n2" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  3.2 3.2 3.2 0 -3.85" result="mask"/>
      <feComposite in="disp" in2="mask" operator="in"/>
    </filter>"""

EROSION_SEAL = """<filter id="erosion" x="-8%" y="-8%" width="116%" height="116%">
      <feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="2" seed="31" result="n1"/>
      <feDisplacementMap in="SourceGraphic" in2="n1" scale="3.2" xChannelSelector="R" yChannelSelector="G" result="disp"/>
      <feTurbulence type="fractalNoise" baseFrequency="0.12" numOctaves="3" seed="9" result="n2"/>
      <feColorMatrix in="n2" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  2.2 2.2 2.2 0 -2.31" result="mask"/>
      <feComposite in="disp" in2="mask" operator="in"/>
    </filter>"""


def variant_a(font_ctx):
    paths = text_paths(font_ctx, TITLE, 76, 20, 320, 108)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="640" height="160" viewBox="0 0 640 160">
  <defs>
    {EROSION_LIGHT}
  </defs>
  <g filter="url(#erosion)">
    <rect x="8" y="8" width="624" height="144" fill="none" stroke="{INK}" stroke-width="2.6" opacity="0.9"/>
    <rect x="20" y="20" width="600" height="120" fill="none" stroke="{INK}" stroke-width="1.2" opacity="0.55"/>
    <g fill="{INK}">
    {paths}
    </g>
  </g>
</svg>
"""


def variant_b(font_ctx):
    paths = text_paths(font_ctx, TITLE, 76, 20, 320, 108)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="640" height="160" viewBox="0 0 640 160">
  <defs>
    {EROSION_HEAVY}
  </defs>
  <g filter="url(#erosion)">
    <rect x="8" y="8" width="624" height="144" fill="none" stroke="{INK}" stroke-width="2.6" opacity="0.9"/>
    <rect x="20" y="20" width="600" height="120" fill="none" stroke="{INK}" stroke-width="1.2" opacity="0.55"/>
    <g fill="{INK}">
    {paths}
    </g>
  </g>
</svg>
"""


def variant_c(font_ctx):
    # 2 columns, traditional right-to-left read: 成长天 | 文图
    col_r = text_paths(font_ctx, "成长天", 64, 0, 0, 0)  # placeholder, composed below
    del col_r
    font, glyphset, upm, cmap, hmtx = font_ctx
    sc = 64 / upm

    def col(chars, x, y0, gap):
        parts = []
        y = y0
        for ch in chars:
            d, adv = char_path(glyphset, cmap, hmtx, ch)
            w = adv * sc
            parts.append(
                f'<path d="{d}" transform="translate({x - w / 2:.2f},{y:.2f}) scale({sc:.5f},{-sc:.5f})"/>'
            )
            y += 64 + gap
        return "\n    ".join(parts)

    right = col("成长天", 192, 78, 14)   # right column read first
    left = col("文图", 74, 106, 26)      # left column, larger spacing
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="260" height="260" viewBox="0 0 260 260">
  <defs>
    {EROSION_SEAL}
  </defs>
  <g filter="url(#erosion)">
    <rect x="10" y="10" width="240" height="240" fill="#c0392b"/>
    <rect x="22" y="22" width="216" height="216" fill="none" stroke="#f4efe4" stroke-width="2" opacity="0.85"/>
    <g fill="#f4efe4">
    {right}
    {left}
    </g>
  </g>
</svg>
"""


# ---------- v2: 「成长图」 plaque after 石刻原匾 天文图.png ----------

import math
import random


def _flattened_char(font_ctx, ch, font_size, sx=1.12, sy=0.84):
    """文楷 glyph compressed toward 古隶 proportion (压扁+横展)."""
    font, glyphset, upm, cmap, hmtx = font_ctx
    sc = font_size / upm
    d, adv = char_path(glyphset, cmap, hmtx, ch)
    tx = f"translate(0,0) scale({sc * sx:.5f},{-sc * sy:.5f})"
    return f'<path d="{d}" transform="{tx}"/>', adv * sc * sx


def _tu_seal(font_ctx, x, baseline, side=86, font_size=80):
    """篆意「图」: 明体 glyph (囗+冬) flattened, wrapped in a hand-drawn outer 囗 ring."""
    font, glyphset, upm, cmap, hmtx = font_ctx
    sc = font_size / upm
    d, adv = char_path(glyphset, cmap, hmtx, "图")
    w = adv * sc * 1.08
    glyph = (f'<path d="{d}" transform="translate({x - w / 2:.2f},{baseline:.2f}) '
             f'scale({sc * 1.08:.5f},{-sc * 0.86:.5f})"/>')
    left = x - side / 2
    top = baseline - side + 2
    t = side * 0.075
    ring = (f"M{left},{top} H{left + side} V{top + side} H{left} Z "
            f"M{left + t},{top + t} V{top + side - t} H{left + side - t} V{top + t} Z")
    return f'<path fill-rule="evenodd" d="{ring}"/>' + glyph


def _chip(cx, cy, r, seed_n, n=12):
    """Irregular blotch path for the bold wear patches (大块斑蚀)."""
    rnd = random.Random(seed_n)
    pts = []
    for i in range(n):
        a = i / n * 2 * math.pi
        rr = r * (0.5 + rnd.random() * 0.65)
        pts.append(f"{cx + rr * math.cos(a):.1f},{cy + rr * math.sin(a):.1f}")
    return "M" + " L".join(pts) + " Z"


def _edge_filter(scale, seed):
    return (f'<filter id="edge" x="-8%" y="-8%" width="116%" height="116%">'
            f'<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="{seed}" result="n"/>'
            f'<feDisplacementMap in="SourceGraphic" in2="n" scale="{scale}" xChannelSelector="R" yChannelSelector="G"/>'
            f'</filter>')


def _wear_mask(chips):
    parts = ['<rect x="0" y="0" width="640" height="160" fill="#fff"/>']
    for d in chips:
        parts.append(f'<path d="{d}" fill="#000"/>')
    return ('<mask id="wear" maskUnits="userSpaceOnUse" x="0" y="0" width="640" height="160">'
            + "".join(parts) + "</mask>")


def _v2(wenkai_ctx, iming_ctx, *, edge_scale, edge_seed, border_w, chips, speckle_seed):
    cheng, w1 = _flattened_char(wenkai_ctx, "成", 88)
    zhang, w2 = _flattened_char(wenkai_ctx, "长", 88)
    baseline = 112
    x_cheng, x_zhang, x_tu = 470, 320, 165
    speckle_def = ""
    if speckle_seed is not None:
        speckle_def = (
            '<filter id="speckle" x="0" y="0" width="640" height="160" filterUnits="userSpaceOnUse">'
            f'<feTurbulence type="fractalNoise" baseFrequency="0.5" numOctaves="2" seed="{speckle_seed}" result="n"/>'
            '<feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  3.4 3.4 3.4 0 -4.6"/>'
            '</filter>')
    speckle_rect = ""
    if speckle_seed is not None:
        speckle_rect = '<rect x="0" y="0" width="640" height="160" fill="#000" filter="url(#speckle)"/>'
    mask = ""
    mask_attr = ""
    if chips or speckle_rect:
        mask = ('<mask id="wear" maskUnits="userSpaceOnUse" x="0" y="0" width="640" height="160">'
                '<rect x="0" y="0" width="640" height="160" fill="#fff"/>'
                + "".join(f'<path d="{d}" fill="#000"/>' for d in chips)
                + speckle_rect + "</mask>")
        mask_attr = ' mask="url(#wear)"'
    body = f"""
    <rect x="10" y="10" width="620" height="140" fill="none" stroke="{INK}" stroke-width="{border_w}" opacity="0.92"/>
    <rect x="{10 + border_w + 5}" y="{10 + border_w + 5}" width="{620 - 2 * (border_w + 5)}" height="{140 - 2 * (border_w + 5)}" fill="none" stroke="{INK}" stroke-width="1.1" opacity="0.55"/>
    <g fill="{INK}">
      <g transform="translate({x_cheng - w1 / 2:.1f},{baseline})">{cheng}</g>
      <g transform="translate({x_zhang - w2 / 2:.1f},{baseline})">{zhang}</g>
      {_tu_seal(iming_ctx, x_tu, baseline)}
    </g>"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="640" height="160" viewBox="0 0 640 160">
  <defs>
    {_edge_filter(edge_scale, edge_seed)}
    {speckle_def}
    {mask}
  </defs>
  <g filter="url(#edge)"{mask_attr}>{body}
  </g>
</svg>
"""


def v2_variants(wenkai_ctx, iming_ctx):
    return {
        "title-v2-a.svg": _v2(wenkai_ctx, iming_ctx, edge_scale=2.0, edge_seed=11, border_w=2.2,
                              chips=[], speckle_seed=7),
        "title-v2-b.svg": _v2(wenkai_ctx, iming_ctx, edge_scale=3.0, edge_seed=23, border_w=3.4,
                              chips=[_chip(282, 84, 46, 3)], speckle_seed=8),
        "title-v2-c.svg": _v2(wenkai_ctx, iming_ctx, edge_scale=2.5, edge_seed=17, border_w=2.8,
                              chips=[_chip(492, 116, 30, 5), _chip(150, 46, 26, 6)],
                              speckle_seed=None),
    }


def main() -> int:
    wenkai = load(FONTS / "LXGWWenKai-subset.ttf")
    iming = load(FONTS / "IMing-subset.ttf")
    (OUT / "title-seal-a.svg").write_text(variant_a(wenkai), encoding="utf-8")
    (OUT / "title-seal-b.svg").write_text(variant_b(wenkai), encoding="utf-8")
    (OUT / "title-seal-c.svg").write_text(variant_c(iming), encoding="utf-8")
    # v2: 「成长图」 three-char plaque, read right-to-left (成 right, 长 mid, 图 left)
    for name, svg in v2_variants(wenkai, iming).items():
        (OUT / name).write_text(svg, encoding="utf-8")
    for name in ["title-seal-a.svg", "title-seal-b.svg", "title-seal-c.svg",
                 "title-v2-a.svg", "title-v2-b.svg", "title-v2-c.svg"]:
        print("wrote", OUT / name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
