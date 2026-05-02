"""AI editor reviewer helpers for public blog drafts."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from schemas.ai_patch import AIPatch, AIPatchTarget, AIProvenance, patch_to_dict


Finding = dict[str, Any]

_IMAGE_RE = re.compile(r"!\[(?P<alt>[^\]\r\n]*)\]\((?P<src>[^)\r\n]+)\)")
_VISUAL_COMMENT_RE = re.compile(
    r"<!--\s*nblane:visual_block(?:\s+(?P<payload>\{[^\r\n]*\}))?\s*-->",
    re.IGNORECASE,
)
_MATH_COMMENT_RE = re.compile(
    r"<!--\s*nblane:math_block(?:\s+(?P<payload>\{[^\r\n]*\}))?\s*-->",
    re.IGNORECASE,
)
_PRIVACY_RE = re.compile(
    r"(?i)(profiles/|evidence-pool\.yaml|agent-profile\.yaml|skill-tree\.yaml|"
    r"kanban\.md|auth/users\.ya?ml|resume-source\.yaml|/home/|[A-Z]:\\|"
    r"\.env|\.ssh|token|secret|api[_-]?key)"
)
_DATE_OR_NUMBER_CLAIM_RE = re.compile(
    r"(?i)\b(?:19|20)\d{2}\b|\b\d+(?:\.\d+)?\s*(?:%|ms|s|x|倍|万|亿|million|billion)\b"
)


def _clean_text(value: object) -> str:
    return "" if value is None else str(value)


def _finding_id(category: str, seed: str) -> str:
    digest = hashlib.sha1(f"{category}:{seed}".encode("utf-8")).hexdigest()[:10]
    return f"{category}-{digest}"


def _finding(
    category: str,
    *,
    severity: str,
    title: str,
    detail: str,
    excerpt: str = "",
    location: dict[str, Any] | None = None,
    repairable: bool = False,
    repair_intent: str = "",
    source: str = "deterministic",
) -> Finding:
    return {
        "id": _finding_id(category, "|".join([title, detail, excerpt])),
        "category": category,
        "severity": severity,
        "title": title,
        "detail": detail,
        "source": source,
        "excerpt": excerpt,
        "location": location or {},
        "repairable": repairable,
        "repair_action": "request_reviewer_repair" if repairable else "",
        "repair_intent": repair_intent,
    }


def _markdown_images(body: str) -> list[dict[str, str]]:
    return [
        {
            "alt": _clean_text(match.group("alt")).strip(),
            "src": _clean_text(match.group("src")).strip(),
            "raw": match.group(0),
        }
        for match in _IMAGE_RE.finditer(body or "")
    ]


def _visual_payloads(body: str) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for match in _VISUAL_COMMENT_RE.finditer(body or ""):
        raw = _clean_text(match.group("payload")).strip()
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
        except Exception:
            continue
        if isinstance(parsed, dict):
            parsed["_raw"] = match.group(0)
            payloads.append(parsed)
    return payloads


def _has_formula_syntax_issue(body: str) -> bool:
    for match in _MATH_COMMENT_RE.finditer(body or ""):
        raw = _clean_text(match.group("payload")).strip()
        if not raw:
            return True
        try:
            parsed = json.loads(raw)
        except Exception:
            return True
        latex = _clean_text(parsed.get("latex") if isinstance(parsed, dict) else "").strip()
        if not latex or latex.count("{") != latex.count("}"):
            return True
    if (body or "").count("$$") % 2:
        return True
    return False


def review_blog(
    *,
    slug: str,
    meta: dict,
    body: str,
    media_rows: list[dict],
    orphan_candidates: list[dict] | None = None,
) -> list[Finding]:
    """Return structured editor-review findings for one draft."""

    findings: list[Finding] = []
    title = _clean_text((meta or {}).get("title")).strip()
    summary = _clean_text((meta or {}).get("summary")).strip()
    evidence = (meta or {}).get("related_evidence")
    evidence_refs = [str(item).strip() for item in evidence if str(item).strip()] if isinstance(evidence, list) else []

    if not title or len(title) < 6 or title.lower() in {"draft", "untitled", "test", "tttt"}:
        findings.append(
            _finding(
                "weak_title",
                severity="warning",
                title="Title is weak or too generic",
                detail="A public post needs a specific title before publishing.",
                excerpt=title,
                location={"kind": "meta", "field": "title"},
                repairable=True,
                repair_intent="Suggest a clearer title from the draft body.",
            )
        )
    if not summary:
        findings.append(
            _finding(
                "missing_summary",
                severity="info",
                title="Summary is missing",
                detail="Add a short public summary for blog cards and previews.",
                location={"kind": "meta", "field": "summary"},
                repairable=True,
                repair_intent="Draft a concise summary from the body.",
            )
        )
    tags = (meta or {}).get("tags")
    tag_values = [str(item).strip() for item in tags if str(item).strip()] if isinstance(tags, list) else []
    if not tag_values:
        findings.append(
            _finding(
                "missing_tags",
                severity="info",
                title="Tags are missing",
                detail="Add one or two tags so the post can be grouped and discovered.",
                location={"kind": "meta", "field": "tags"},
                repairable=True,
                repair_intent="Suggest conservative tags from the title and body.",
            )
        )
    if not _clean_text((meta or {}).get("cover")).strip():
        image = next(
            (
                row
                for row in media_rows
                if isinstance(row, dict) and _clean_text(row.get("kind")).lower() == "image"
            ),
            None,
        )
        findings.append(
            _finding(
                "missing_cover",
                severity="info",
                title="Cover image is missing",
                detail="A cover improves the public blog card and detail page.",
                location={"kind": "meta", "field": "cover"},
                repairable=bool(image),
                repair_intent="Use the first local image as the cover." if image else "",
            )
        )
    if "<!-- nblane:insert -->" in (body or ""):
        findings.append(
            _finding(
                "leftover_insert_marker",
                severity="warning",
                title="Insert marker is still in the body",
                detail="Remove the editor insertion marker before publishing.",
                excerpt="<!-- nblane:insert -->",
                location={"kind": "body"},
                repairable=True,
                repair_intent="Remove the insertion marker from the body.",
            )
        )
    if not evidence_refs:
        findings.append(
            _finding(
                "missing_evidence",
                severity="info",
                title="No related evidence is attached",
                detail="Attach evidence IDs for claims that should be traceable.",
                location={"kind": "meta", "field": "related_evidence"},
                repairable=False,
            )
        )

    for match in _PRIVACY_RE.finditer(body or ""):
        excerpt = (body or "")[max(0, match.start() - 40) : match.end() + 40]
        findings.append(
            _finding(
                "privacy_path",
                severity="error",
                title="Possible private path or secret reference",
                detail="Remove local paths, private profile files, tokens, or secret names from public copy.",
                excerpt=excerpt,
                location={"kind": "body"},
                repairable=True,
                repair_intent="Redact private implementation details from the body.",
            )
        )
        break

    for image in _markdown_images(body):
        if image["src"].startswith("media/") and not image["alt"]:
            findings.append(
                _finding(
                    "missing_alt_text",
                    severity="warning",
                    title="Image alt text is missing",
                    detail=f"Add concise alt text for {image['src']}.",
                    excerpt=image["raw"],
                    location={"kind": "body", "src": image["src"]},
                    repairable=True,
                    repair_intent="Fill Markdown image alt text.",
                )
            )
    for payload in _visual_payloads(body):
        src = _clean_text(payload.get("src")).strip()
        if src and not _clean_text(payload.get("alt")).strip():
            findings.append(
                _finding(
                    "missing_alt_text",
                    severity="warning",
                    title="Visual block alt text is missing",
                    detail=f"Add concise alt text for {src}.",
                    excerpt=src,
                    location={"kind": "body", "src": src},
                    repairable=False,
                )
            )

    for row in media_rows:
        if not isinstance(row, dict) or row.get("referenced"):
            continue
        rel = _clean_text(row.get("relative_path")).strip()
        if not rel:
            continue
        findings.append(
            _finding(
                "unreferenced_media",
                severity="info",
                title="Media is not referenced",
                detail=f"{rel} exists in the media library but is not used by the draft.",
                excerpt=rel,
                location={"kind": "media", "relative_path": rel},
                repairable=True,
                repair_intent="Append this media item to the article body.",
            )
        )

    if _has_formula_syntax_issue(body):
        findings.append(
            _finding(
                "formula_render_failure",
                severity="warning",
                title="Formula syntax may not render",
                detail="A math block is empty, malformed, or has unbalanced delimiters.",
                location={"kind": "body"},
                repairable=False,
            )
        )

    if _DATE_OR_NUMBER_CLAIM_RE.search(body or "") and not evidence_refs and not summary:
        findings.append(
            _finding(
                "fact_risk",
                severity="info",
                title="Numeric or date claim has no evidence context",
                detail="Treat unsupported numeric/date claims as review risks until evidence is attached.",
                location={"kind": "body"},
                repairable=False,
            )
        )

    orphan_rows = [item for item in (orphan_candidates or []) if isinstance(item, dict)]
    if orphan_rows:
        total_bytes = sum(
            int(item.get("size_bytes", 0) or 0)
            for item in orphan_rows
            if isinstance(item.get("size_bytes", 0), int | float)
        )
        size_mb = total_bytes / (1024 * 1024)
        first_paths = [
            _clean_text(item.get("candidate_path")).strip()
            for item in orphan_rows[:3]
            if _clean_text(item.get("candidate_path")).strip()
        ]
        detail = (
            f"{len(orphan_rows)} staged visual candidate file(s)"
            f" ({size_mb:.1f} MB) are not referenced by the current draft or active AI patches."
        )
        if first_paths:
            detail = f"{detail} Examples: {', '.join(first_paths)}"
        findings.append(
            _finding(
                "orphan_visual_candidates",
                severity="info",
                title="Staged visual candidates are orphaned",
                detail=detail,
                excerpt=", ".join(first_paths),
                location={
                    "kind": "candidate_store",
                    "count": len(orphan_rows),
                    "size_bytes": total_bytes,
                    "paths": first_paths,
                },
                repairable=False,
            )
        )

    # Stable order keeps UI and tests predictable.
    order = {
        "privacy_path": 0,
        "formula_render_failure": 1,
        "missing_alt_text": 2,
        "weak_title": 3,
        "missing_cover": 4,
        "missing_summary": 5,
        "missing_tags": 6,
        "leftover_insert_marker": 7,
        "missing_evidence": 8,
        "unreferenced_media": 9,
        "fact_risk": 10,
        "orphan_visual_candidates": 11,
    }
    return sorted(findings, key=lambda item: (order.get(item["category"], 99), item["id"]))


def parse_ai_reviewer_response(raw: str) -> list[Finding]:
    """Parse optional LLM reviewer JSON into normalized findings."""

    text = _clean_text(raw).strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        payload = json.loads(text)
    except Exception:
        return []
    items = payload.get("findings") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return []
    findings: list[Finding] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        category = _clean_text(item.get("category")).strip()
        title = _clean_text(item.get("title") or item.get("reason")).strip()
        if not category or not title:
            continue
        findings.append(
            _finding(
                category,
                severity=_clean_text(item.get("severity") or "info").strip() or "info",
                title=title,
                detail=_clean_text(item.get("detail") or item.get("reason")).strip(),
                excerpt=_clean_text(item.get("excerpt")).strip(),
                location=item.get("location") if isinstance(item.get("location"), dict) else {},
                repairable=bool(item.get("repairable")),
                repair_intent=_clean_text(item.get("repair_intent")).strip(),
                source="ai",
            )
        )
    return findings


def repair_patch_for_finding(
    *,
    slug: str,
    meta: dict,
    body: str,
    media_rows: list[dict],
    finding: Finding,
    source_event_id: str = "",
    lang: str = "en",
) -> dict[str, Any]:
    """Return an AIPatch that repairs one reviewer finding without applying it."""

    category = _clean_text(finding.get("category")).strip()
    patch_id = f"check-{hashlib.sha1(json.dumps(finding, sort_keys=True, default=str).encode('utf-8')).hexdigest()[:12]}"
    meta_patch: dict[str, Any] = {}
    markdown_fallback = ""
    target = AIPatchTarget(selection_text="", range=None)
    warnings: list[str] = []

    if category == "weak_title":
        first_heading = re.search(r"(?m)^#{1,3}\s+(.+)$", body or "")
        candidate = first_heading.group(1).strip() if first_heading else ""
        if not candidate:
            words = re.sub(r"\s+", " ", re.sub(r"[#*_>`\[\]()]+" , " ", body or "")).strip()
            candidate = words[:48].strip(" ,.;:") or "Reviewed public note"
        meta_patch["title"] = candidate[:80]
    elif category == "missing_cover":
        image = next(
            (
                row
                for row in media_rows
                if isinstance(row, dict)
                and _clean_text(row.get("kind")).lower() == "image"
                and _clean_text(row.get("relative_path")).strip()
            ),
            None,
        )
        if image:
            meta_patch["cover"] = _clean_text(image.get("relative_path")).strip()
        else:
            warnings.append("No local image is available for a cover repair.")
    elif category == "missing_summary":
        text = re.sub(r"\s+", " ", re.sub(r"[#*_>`\[\]()]+" , " ", body or "")).strip()
        summary = text[:140].strip(" ,.;:")
        meta_patch["summary"] = summary or _clean_text((meta or {}).get("title")).strip()
    elif category == "missing_tags":
        source = f"{_clean_text((meta or {}).get('title'))} {body or ''}".lower()
        tags: list[str] = []
        candidates = [
            ("ai", (" ai ", "llm", "model", "智能")),
            ("robotics", ("robot", "机器人", "ros", "vla")),
            ("research", ("paper", "diffusion", "flow", "policy", "研究")),
            ("engineering", ("system", "工程", "架构", "pipeline")),
        ]
        for tag, needles in candidates:
            if any(needle in source for needle in needles):
                tags.append(tag)
        meta_patch["tags"] = tags[:3] or ["note"]
    elif category == "leftover_insert_marker":
        next_body = (body or "").replace("<!-- nblane:insert -->", "").strip()
        markdown_fallback = f"{next_body}\n" if next_body else ""
        target = AIPatchTarget(selection_text="<!-- nblane:insert -->", range={"full_document": True})
    elif category == "privacy_path":
        next_body = _PRIVACY_RE.sub("[redacted internal reference]", body or "")
        markdown_fallback = next_body
        target = AIPatchTarget(selection_text=body or "", range={"full_document": True})
    elif category == "missing_alt_text":
        src = _clean_text((finding.get("location") or {}).get("src")).strip()
        alt = _clean_text((meta or {}).get("title")).strip() or "Blog image"
        next_body = body or ""
        if src:
            next_body = re.sub(
                rf"!\[\]\({re.escape(src)}\)",
                f"![{alt}]({src})",
                next_body,
                count=1,
            )
        if next_body != (body or ""):
            markdown_fallback = next_body
            target = AIPatchTarget(selection_text=body or "", range={"full_document": True})
        else:
            warnings.append("Could not locate the Markdown image to repair.")
    elif category == "unreferenced_media":
        rel = _clean_text((finding.get("location") or {}).get("relative_path") or finding.get("excerpt")).strip()
        if rel:
            alt = _clean_text((meta or {}).get("title")).strip() or "Media"
            markdown_fallback = f"![{alt}]({rel})"
        else:
            warnings.append("Could not locate the media reference to insert.")
    else:
        warnings.append(f"No deterministic repair is available for {category}.")

    patch = AIPatch(
        patch_id=patch_id,
        ai_source_id=source_event_id or patch_id,
        operation="check",
        target=target,
        meta_patch=meta_patch,
        block_patches=[],
        markdown_fallback=markdown_fallback,
        warnings=warnings,
        citations=[],
        provenance=AIProvenance(
            model="deterministic-reviewer",
            prompt_id=f"check.repair.{category}",
            lang="zh" if lang == "zh" else "en",
            source_refs=[ref for ref in (slug, source_event_id, finding.get("id")) if _clean_text(ref).strip()],
        ),
    )
    return patch_to_dict(patch)
