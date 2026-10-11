"""Share cards: one blog post rendered as 3:4 images for Xiaohongshu / X.

The post body is laid out as 1080×1440 cards (cover, body pages, optional
closing card) by a small paginator that runs inside headless Chromium, then
printed to PDF and rasterised with PyMuPDF. Nothing is uploaded anywhere:
the owner downloads or shares the PNGs and posts them by hand.

Per-post share settings (theme, cover text, signature, closing card, post
copy) live in ``profiles/<name>/social-cards.yaml`` keyed by blog route, so
they never touch the post files an open editor is saving. Rendered PNGs are
a cache under ``~/.cache/nblane/social-cards`` keyed by the page hash.
"""

from __future__ import annotations

import base64
import hashlib
import html
import io
import mimetypes
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any

import yaml

from nblane.core import git_backup, public_site, resume_doc
from nblane.core.file_lock import locked_profile_write
from nblane.core.file_write import atomic_write_text
from nblane.core.profile_io import profile_dir
from nblane.core.yaml_io import _load_yaml_dict

SETTINGS_FILENAME = "social-cards.yaml"
THEMES = ("paper", "warm", "night")
SIGNATURES = ("site", "custom", "none")
END_CARDS = ("thanks_url", "thanks", "none")
CARD_WIDTH = 1080
CARD_HEIGHT = 1440
# Xiaohongshu accepts at most 18 images per note.
XHS_MAX_IMAGES = 18
_CACHE_KEEP = 20
_KEY_RE = re.compile(r"^[0-9a-f]{24}$")

DEFAULT_SETTINGS: dict[str, Any] = {
    "theme": "paper",
    "kicker": "",
    "cover_title": "",
    "cover_subtitle": "",
    "cover_image": False,
    "signature": "site",
    "signature_text": "",
    "end_card": "thanks",
    "site_url": "",
    "xhs_title": "",
    "xhs_body": "",
    "x_text": "",
}

_TEXT_LIMITS = {
    "kicker": 40,
    "cover_title": 80,
    "cover_subtitle": 200,
    "signature_text": 60,
    "site_url": 200,
    "xhs_title": 40,
    "xhs_body": 2000,
    "x_text": 1000,
}


class SocialCardError(RuntimeError):
    """Structured failure with a stable ``code`` for API error mapping."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


# --- settings -------------------------------------------------------------------


def _settings_path(profile: str) -> Path:
    return profile_dir(profile) / SETTINGS_FILENAME


def normalize_settings(raw: object) -> dict[str, Any]:
    """Coerce a stored/edited mapping into the canonical settings shape."""
    source = raw if isinstance(raw, dict) else {}
    out = dict(DEFAULT_SETTINGS)
    for key, limit in _TEXT_LIMITS.items():
        if key in source and source[key] is not None:
            out[key] = str(source[key]).strip()[:limit]
    if source.get("theme") in THEMES:
        out["theme"] = source["theme"]
    if source.get("signature") in SIGNATURES:
        out["signature"] = source["signature"]
    if source.get("end_card") in END_CARDS:
        out["end_card"] = source["end_card"]
    out["cover_image"] = bool(source.get("cover_image", False))
    out["site_url"] = _display_url(out["site_url"])
    return out


def _display_url(value: str) -> str:
    """``https://a.b/`` → ``a.b``: cards show the bare host and path."""
    clean = re.sub(r"^https?://", "", str(value or "").strip(), flags=re.I)
    return clean.rstrip("/")


def default_site_url(profile: str) -> str:
    """Site host from ``public-profile.yaml: site.base_url`` (may be empty)."""
    try:
        site = (public_site.load_public_profile(profile).get("site") or {})
    except (FileNotFoundError, OSError, yaml.YAMLError):
        return ""
    return _display_url(str(site.get("base_url") or "")) if isinstance(site, dict) else ""


def load_settings(profile: str, route: str) -> dict[str, Any]:
    """Saved settings for one post, defaults filled; never ``None``."""
    raw = _load_yaml_dict(_settings_path(profile)) or {}
    posts = raw.get("posts") if isinstance(raw.get("posts"), dict) else {}
    settings = normalize_settings(posts.get(route))
    if not settings["site_url"]:
        settings["site_url"] = _display_url(str(raw.get("site_url") or "")) or default_site_url(profile)
    return settings


def save_settings(profile: str, route: str, settings: dict[str, Any]) -> dict[str, Any]:
    """Persist settings for one post; the site URL is remembered profile-wide."""
    clean = normalize_settings(settings)
    path = _settings_path(profile)
    with locked_profile_write(path.parent, SETTINGS_FILENAME):
        raw = _load_yaml_dict(path) or {}
        posts = raw.get("posts") if isinstance(raw.get("posts"), dict) else {}
        if posts.get(route) == clean and raw.get("site_url", "") == clean["site_url"]:
            return clean
        posts[route] = clean
        raw["posts"] = posts
        if clean["site_url"]:
            raw["site_url"] = clean["site_url"]
        body = yaml.safe_dump(raw, allow_unicode=True, sort_keys=False)
        atomic_write_text(path, "# Share-card settings per blog post (Xiaohongshu / X export).\n" + body)
    git_backup.record_change([path], action=f"update {path.parent.name}/{SETTINGS_FILENAME}")
    return clean


# --- page HTML --------------------------------------------------------------------

_LONG_HEADING_RE = re.compile(r"<h([1-6])>(?P<text>(?:(?!</h\1>).){40,}?)</h\1>", re.S)
_MERMAID_RE = re.compile(r'<pre class="mermaid">.*?</pre>(?:<noscript>(?P<svg>.*?)</noscript>)?', re.S)
_VIDEO_RE = re.compile(
    r'<figure class="media-block"><video[^>]*></video>(?:<figcaption class="media-caption">(?P<cap>.*?)</figcaption>)?</figure>',
    re.S,
)
_IMG_SRC_RE = re.compile(r'(<img\b[^>]*?\bsrc=")(?P<src>[^"]+)(")')


def _inline_media(profile: str, body_html: str) -> str:
    """Embed profile ``media/`` images as data URIs (cards render offline)."""
    root = profile_dir(profile)

    def repl(match: re.Match[str]) -> str:
        src = html.unescape(match.group("src"))
        if src.startswith("data:"):
            return match.group(0)
        target = public_site._local_media_target(root, src)
        if target is None or not target.is_file():
            # Remote or missing images would stall or break the print.
            return match.group(1) + "" + match.group(3)
        mime = mimetypes.guess_type(target.name)[0] or "image/png"
        data = base64.b64encode(target.read_bytes()).decode("ascii")
        return f"{match.group(1)}data:{mime};base64,{data}{match.group(3)}"

    return _IMG_SRC_RE.sub(repl, body_html)


def _card_body_html(profile: str, post: public_site.BlogPost) -> str:
    body = public_site._markdown_to_html(post.body or "")
    # Posts often use ### for whole paragraphs; on a card that is body text.
    body = _LONG_HEADING_RE.sub(lambda m: f"<p>{m.group('text')}</p>", body)
    # mermaid.js is not loaded on cards: use the static SVG fallback.
    body = _MERMAID_RE.sub(lambda m: f'<div class="diagram">{m.group("svg") or ""}</div>', body)
    body = _VIDEO_RE.sub(
        lambda m: f'<p class="media-note">▶ 视频：{m.group("cap") or "见原文"}</p>', body
    )
    body = re.sub(r"<hr\s*/?>", "", body)
    return _inline_media(profile, body)


def _cover_image_uri(profile: str, post: public_site.BlogPost) -> str:
    cover = str(post.meta.get("cover") or "").strip()
    if not cover:
        return ""
    target = public_site._local_media_target(profile_dir(profile), cover)
    if target is None or not target.is_file():
        return ""
    mime = mimetypes.guess_type(target.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(target.read_bytes()).decode('ascii')}"


def _signature(settings: dict[str, Any]) -> str:
    if settings["signature"] == "none":
        return ""
    if settings["signature"] == "custom":
        return settings["signature_text"]
    return settings["site_url"]


THEME_VARS = {
    "paper": (
        "--card:#f6f2ea;--ink:#222;--muted:#8a8274;--accent:#b4532a;--rule:#e3dccd;--code:#ede6d8;"
        "--cover:#f6f2ea;--title-font:'Noto Serif CJK SC',serif;--body-font:'Noto Serif CJK SC',serif;"
    ),
    "warm": (
        "--card:#fff8ec;--ink:#3b2a1a;--muted:#a0815f;--accent:#e8590c;--rule:#f2dcb9;--code:#fdebd0;"
        "--cover:#ffd8a8;--title-font:'Noto Sans CJK SC',sans-serif;--body-font:'Noto Sans CJK SC',sans-serif;"
    ),
    "night": (
        "--card:#0f1529;--ink:#e3e7f1;--muted:#8a93ab;--accent:#ffd166;--rule:#232b45;--code:#18213d;"
        "--cover:#0b1020;--title-font:'Noto Serif CJK SC',serif;--body-font:'Noto Sans CJK SC',sans-serif;"
    ),
}

_CSS = """
@page{size:1080px 1440px;margin:0}
*{box-sizing:border-box;margin:0}
html,body{background:var(--card);-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{font-family:var(--body-font);color:var(--ink)}
#src{position:absolute;left:-99999px;top:0;width:904px}
.card{width:1080px;height:1440px;background:var(--card);position:relative;overflow:hidden;
  display:flex;flex-direction:column;padding:120px 88px 0;break-after:page;page-break-after:always}
.content{flex:1;overflow:hidden;font-size:40px;line-height:1.9;text-align:justify;word-break:break-word}
.content>*{margin:0 0 40px}
.content p{text-indent:2em}
.content p.cont,.content li p,.content blockquote p,.content p.media-note{text-indent:0}
.content h1,.content h2{font-family:var(--title-font);font-size:54px;line-height:1.4;font-weight:800;margin:4px 0 32px}
.content h3,.content h4,.content h5,.content h6{font-size:44px;line-height:1.45;font-weight:700;margin:4px 0 24px}
.content strong{color:var(--accent);font-weight:700}
.content ol,.content ul{padding-left:1.4em}
.content li{margin:0 0 14px}
.content blockquote{border-left:8px solid var(--accent);padding:4px 0 4px 32px;color:var(--muted)}
.content pre{background:var(--code);border-radius:20px;padding:28px 32px;font-size:26px;line-height:1.55;
  white-space:pre-wrap;word-break:break-all;font-family:'DejaVu Sans Mono','Noto Sans Mono CJK SC',monospace;text-align:left}
.content code{font-family:'DejaVu Sans Mono','Noto Sans Mono CJK SC',monospace;font-size:.85em;background:var(--code);
  padding:2px 10px;border-radius:8px}
.content pre code{background:none;padding:0;font-size:inherit}
.content table{border-collapse:collapse;font-size:28px;line-height:1.5;width:100%;text-align:left}
.content th,.content td{border-bottom:2px solid var(--rule);padding:12px 10px;vertical-align:top;word-break:break-all}
.content th{color:var(--muted)}
.content img{max-width:100%;max-height:1000px;display:block;margin:0 auto;border-radius:16px}
.content p:has(>img:only-child){text-indent:0}
.content .diagram{background:var(--code);border-radius:20px;padding:24px;text-align:center}
.content .diagram svg{max-width:100%;height:auto;max-height:1000px}
.content .math-display{font-family:'DejaVu Sans Mono',monospace;font-size:30px;background:var(--code);
  border-radius:16px;padding:20px 28px;white-space:pre-wrap;text-align:left}
.content .media-note{color:var(--muted);font-size:32px}
.mermaid-static-node rect{fill:var(--card);stroke:var(--muted);stroke-width:2}
.mermaid-static-node text{fill:var(--ink);font-size:18px}
.mermaid-static-edge{fill:none;stroke:var(--muted);stroke-width:2}
.mermaid-static marker path{fill:var(--muted)}
.foot{height:110px;flex:none;display:flex;align-items:center;justify-content:space-between;
  color:var(--muted);font-size:24px;border-top:2px solid var(--rule)}
.foot.bare{border-top-color:transparent}
.cover{background:var(--cover);padding:0}
.cover .art{height:560px;margin:80px 88px 0;border-radius:28px;background:center/cover no-repeat}
.cover .txt{flex:1;padding:150px 96px 0;display:flex;flex-direction:column}
.cover.with-art .txt{padding-top:64px}
.cover .kicker{font-size:30px;color:var(--accent);letter-spacing:.12em;margin-bottom:48px}
.cover h1{font-family:var(--title-font);font-size:104px;line-height:1.28;font-weight:900;white-space:pre-line}
.cover.with-art h1{font-size:84px}
.cover .quote{margin-top:auto;margin-bottom:88px;font-size:36px;line-height:1.7;color:var(--muted);
  border-left:8px solid var(--accent);padding-left:32px;white-space:pre-line}
.cover .foot,.end .foot{margin:0 88px}
.end{justify-content:center;text-align:center}
.end .grow{flex:1}
.end .big{font-family:var(--title-font);font-size:60px;font-weight:900;line-height:1.5}
.end .sub{font-size:32px;color:var(--muted);margin:36px 0 64px}
.end .url{display:inline-block;font-size:40px;font-weight:700;color:var(--accent);
  border:4px solid var(--accent);border-radius:999px;padding:18px 48px}
.t-paper .card:not(.cover):not(.end)::before{content:"";position:absolute;left:88px;top:64px;width:72px;height:6px;background:var(--accent)}
.t-warm .cover h1{color:#3b2a1a}
.t-warm .cover .quote{background:#fff8ec;border:none;border-radius:28px;padding:36px 40px;color:#6b4e31}
.t-warm .cover .art{border:8px solid #fff;border-radius:40px}
.t-warm .content h2{background:var(--cover);display:inline-block;padding:4px 22px;border-radius:14px}
.t-night .cover h1{color:#fff}
.t-night .cover::after{content:"";position:absolute;right:-180px;top:-180px;width:620px;height:620px;border-radius:50%;
  background:radial-gradient(circle,rgba(255,209,102,.28),transparent 65%)}
.t-night .cover .quote{color:#c5cbe0}
.t-night .content strong{color:#ffd166}
"""

# Paginator: moves #src children into fixed-size cards. Blocks that do not
# fit are split (paragraph at sentence ends, list by item, code by line,
# table by row with the header repeated); an unsplittable block that is too
# tall alone is scaled down. A heading never ends a card. Sets
# body[data-ready] so the print waits for it (virtual time budget).
_JS = r"""
(function(){
const FOOT = __FOOT__;
function foot(){const f=document.createElement('div');f.className='foot'+(FOOT?'':' bare');
  f.innerHTML='<span class="sig"></span><span class="pg"></span>';f.querySelector('.sig').textContent=FOOT;return f}
const cardsEl=document.getElementById('cards');
function newCard(){const c=document.createElement('section');c.className='card';const box=document.createElement('div');
  box.className='content';c.appendChild(box);c.appendChild(foot());cardsEl.appendChild(c);return box}
const over=box=>box.scrollHeight>box.clientHeight+1;
const isHeading=el=>/^H[1-6]$/.test(el.tagName);
const BREAK=/[。！？；!?;]|[，,](?=\S)/g;
function textCuts(el){const cuts=[];const w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);let n;
  while((n=w.nextNode())){BREAK.lastIndex=0;let m;while((m=BREAK.exec(n.data))){cuts.push([n,m.index+1])}}
  return cuts}
function splitByRange(el,node,offset){const r1=document.createRange();r1.setStart(el,0);r1.setEnd(node,offset);
  const r2=document.createRange();r2.setStart(node,offset);r2.setEnd(el,el.childNodes.length);
  const head=el.cloneNode(false);head.appendChild(r1.cloneContents());
  const tail=el.cloneNode(false);tail.appendChild(r2.cloneContents());tail.classList.add('cont');
  return [head,tail]}
function splitter(el){const t=el.tagName;
  if(t==='P'||t==='BLOCKQUOTE'){const cuts=textCuts(el).filter(([n,o])=>!(n===cutsLast(el)&&o>=n.data.length));
    if(!cuts.length)return null;return{count:cuts.length,make:i=>splitByRange(el,cuts[i-1][0],cuts[i-1][1])}}
  if(t==='OL'||t==='UL'){const items=[...el.children];if(items.length<2)return null;
    const start=parseInt(el.getAttribute('start')||'1',10);
    return{count:items.length-1,make:i=>{const h=el.cloneNode(false),tl=el.cloneNode(false);
      items.slice(0,i).forEach(x=>h.appendChild(x.cloneNode(true)));items.slice(i).forEach(x=>tl.appendChild(x.cloneNode(true)));
      if(t==='OL')tl.setAttribute('start',String(start+i));return[h,tl]}}}
  if(t==='PRE'){const lines=el.textContent.replace(/\n$/,'').split('\n');if(lines.length<2)return null;
    return{count:lines.length-1,make:i=>{const h=el.cloneNode(false),tl=el.cloneNode(false);
      h.textContent=lines.slice(0,i).join('\n');tl.textContent=lines.slice(i).join('\n');return[h,tl]}}}
  if(t==='TABLE'){const head=el.querySelector('thead');const rows=[...el.querySelectorAll('tbody tr')];if(rows.length<2)return null;
    const build=rs=>{const n=el.cloneNode(false);if(head)n.appendChild(head.cloneNode(true));const b=document.createElement('tbody');
      rs.forEach(r=>b.appendChild(r.cloneNode(true)));n.appendChild(b);return n};
    return{count:rows.length-1,make:i=>[build(rows.slice(0,i)),build(rows.slice(i))]}}
  return null}
function cutsLast(el){const w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);let n,last=null;while((n=w.nextNode()))last=n;return last}
function fitHead(el,box){const s=splitter(el);if(!s)return null;let best=null;
  for(let i=1;i<=s.count;i++){const [h,t]=s.make(i);box.appendChild(h);const bad=over(box);box.removeChild(h);
    if(bad)break;best=[h,t]}
  return best}
function shrink(el,box){let z=1;while(over(box)&&z>0.3){z-=0.05;el.style.zoom=String(z)}}
function flow(nodes){let box=newCard();const queue=[...nodes];let guard=0;
  while(queue.length&&guard++<20000){const el=queue.shift();box.appendChild(el);if(!over(box))continue;box.removeChild(el);
    const fit=fitHead(el,box);
    if(fit){box.appendChild(fit[0]);box=newCard();queue.unshift(fit[1]);continue}
    const kids=[...box.children];
    if(!kids.length||kids.every(isHeading)){box.appendChild(el);
      const fresh=fitHead(el,box);
      if(fresh){box.removeChild(el);box.appendChild(fresh[0]);box=newCard();queue.unshift(fresh[1]);continue}
      shrink(el,box);box=newCard();continue}
    const carry=[];while(box.lastElementChild&&isHeading(box.lastElementChild)&&box.children.length>1){carry.unshift(box.lastElementChild);box.removeChild(box.lastElementChild)}
    box=newCard();carry.forEach(c=>box.appendChild(c));queue.unshift(el)}}
// A short last card (a line or two) reads like a mistake: pull blocks from
// the card before it until both are roughly balanced.
function balanceTail(){const cards=[...cardsEl.querySelectorAll('.card')];if(cards.length<2)return;
  const last=cards[cards.length-1].querySelector('.content'),prev=cards[cards.length-2].querySelector('.content');
  const used=b=>[...b.children].reduce((h,c)=>Math.max(h,c.offsetTop+c.offsetHeight),0)-b.offsetTop;
  let guard=0;
  while(guard++<50&&prev.children.length>1&&used(last)<last.clientHeight*0.35){
    const moved=prev.lastElementChild;last.insertBefore(moved,last.firstChild);
    if(over(last)||used(prev)<used(last)){prev.appendChild(moved);break}}}
function run(){const src=document.getElementById('src');flow([...src.children]);src.remove();
  cardsEl.querySelectorAll('.card').forEach(c=>{if(!c.querySelector('.content').children.length)c.remove()});
  balanceTail();
  const all=[...document.querySelectorAll('section.card')];
  all.forEach((c,i)=>{const pg=c.querySelector('.pg');if(pg)pg.textContent=`${i+1} / ${all.length}`});
  document.body.dataset.cards=String(all.length);document.body.dataset.ready='1'}
(document.fonts&&document.fonts.ready?document.fonts.ready:Promise.resolve()).then(run);
})();
"""


def build_card_html(profile: str, post: public_site.BlogPost, settings: dict[str, Any]) -> str:
    """Self-contained HTML that lays the post out as cards when loaded."""
    s = normalize_settings(settings)
    title = s["cover_title"] or post.title
    sig = _signature(s)
    art = _cover_image_uri(profile, post) if s["cover_image"] else ""
    cover_cls = "card cover with-art" if art else "card cover"
    art_html = f'<div class="art" style="background-image:url(\'{art}\')"></div>' if art else ""
    kicker = f'<div class="kicker">{html.escape(s["kicker"])}</div>' if s["kicker"] else ""
    quote = f'<div class="quote">{html.escape(s["cover_subtitle"])}</div>' if s["cover_subtitle"] else ""
    foot = (
        f'<div class="foot{"" if sig else " bare"}"><span class="sig">{html.escape(sig)}</span>'
        '<span class="pg"></span></div>'
    )
    end = ""
    if s["end_card"] != "none":
        url = s["site_url"] if s["end_card"] == "thanks_url" else ""
        url_html = (
            f'<div class="sub">更多文字在我的网站</div><div><span class="url">{html.escape(url)}</span></div>'
            if url
            else ""
        )
        end = (
            '<section class="card end"><div class="grow"></div><div class="big">谢谢你读到这里</div>'
            f"{url_html}<div class=\"grow\"></div>{foot}</section>"
        )
    import json

    script = _JS.replace("__FOOT__", json.dumps(sig, ensure_ascii=False))
    return (
        '<!doctype html><html lang="zh"><head><meta charset="utf-8">'
        f"<style>:root{{{THEME_VARS[s['theme']]}}}{_CSS}</style></head>"
        f'<body class="t-{s["theme"]}">'
        f'<div id="src" class="content">{_card_body_html(profile, post)}</div>'
        f'<section class="{cover_cls}">{art_html}<div class="txt">{kicker}'
        f"<h1>{html.escape(title)}</h1>{quote}</div>{foot}</section>"
        f'<div id="cards"></div>{end}<script>{script}</script></body></html>'
    )


# --- rendering --------------------------------------------------------------------


def _cache_root(profile: str) -> Path:
    tag = hashlib.sha256(profile.encode("utf-8")).hexdigest()[:12]
    return Path.home() / ".cache" / "nblane" / "social-cards" / tag


def cache_dir(profile: str, key: str) -> Path | None:
    """Directory of one rendered set, or ``None`` for a bad/missing key."""
    if not _KEY_RE.match(key or ""):
        return None
    path = _cache_root(profile) / key
    return path if path.is_dir() else None


def card_files(profile: str, key: str) -> list[Path]:
    path = cache_dir(profile, key)
    return sorted(path.glob("card-*.png")) if path else []


def _prune(profile: str, keep: str) -> None:
    root = _cache_root(profile)
    sets = sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True)
    for stale in sets[_CACHE_KEEP:]:
        if stale.name != keep:
            shutil.rmtree(stale, ignore_errors=True)


def render_cards(profile: str, post: public_site.BlogPost, settings: dict[str, Any]) -> dict[str, Any]:
    """Render (or reuse) the PNG set for *post*; return ``{key, count, warnings}``."""
    page = build_card_html(profile, post, settings)
    key = hashlib.sha256(page.encode("utf-8")).hexdigest()[:24]
    existing = card_files(profile, key)
    if not existing:
        try:
            pdf = resume_doc.print_html_to_pdf(
                page,
                scratch_name="social-cards",
                extra_args=("--virtual-time-budget=15000", "--run-all-compositor-stages-before-draw"),
                timeout=90.0,
            )
        except resume_doc.ResumePdfUnavailable as exc:
            raise SocialCardError("social_render_unavailable", str(exc).replace("PDF", "卡片")) from exc
        existing = _rasterize(profile, key, pdf)
    warnings: list[str] = []
    if len(existing) > XHS_MAX_IMAGES:
        warnings.append(
            f"共 {len(existing)} 张，超过小红书单条笔记 {XHS_MAX_IMAGES} 张的上限；可以删减正文，或分成两条发。"
        )
    return {"key": key, "count": len(existing), "warnings": warnings}


def _rasterize(profile: str, key: str, pdf: bytes) -> list[Path]:
    import fitz  # PyMuPDF

    target = _cache_root(profile) / key
    scratch = target.with_name(key + ".tmp")
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True)
    doc = fitz.open(stream=pdf, filetype="pdf")
    try:
        if doc.page_count == 0:
            raise SocialCardError("social_render_failed", "没有生成任何卡片。")
        for index, page in enumerate(doc):
            zoom = CARD_WIDTH / page.rect.width
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            pix.save(str(scratch / f"card-{index + 1:02d}.png"))
    finally:
        doc.close()
    shutil.rmtree(target, ignore_errors=True)
    scratch.rename(target)
    _prune(profile, key)
    return sorted(target.glob("card-*.png"))


def build_pack(profile: str, key: str, settings: dict[str, Any], *, post_url: str = "") -> bytes:
    """Zip of the card PNGs plus ready-to-paste post copy."""
    files = card_files(profile, key)
    if not files:
        raise SocialCardError("social_cards_not_found", "卡片已过期，请重新生成。")
    s = normalize_settings(settings)
    x_text = s["x_text"]
    if post_url and s["end_card"] == "thanks_url" and post_url not in x_text:
        x_text = f"{x_text}\n{post_url}".strip()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            zf.write(path, arcname=path.name)
        zf.writestr("xiaohongshu.txt", f"{s['xhs_title']}\n\n{s['xhs_body']}".strip() + "\n")
        zf.writestr("x.txt", x_text + "\n")
    return buffer.getvalue()


def post_url(settings: dict[str, Any], post: public_site.BlogPost) -> str:
    """Public article URL when a site URL is known (``host/blog/<route>/``)."""
    site = normalize_settings(settings)["site_url"]
    return f"https://{site}/{post.url_path}" if site else ""


__all__ = [
    "DEFAULT_SETTINGS",
    "END_CARDS",
    "SIGNATURES",
    "SocialCardError",
    "THEMES",
    "XHS_MAX_IMAGES",
    "build_card_html",
    "build_pack",
    "card_files",
    "load_settings",
    "normalize_settings",
    "post_url",
    "render_cards",
    "save_settings",
]
