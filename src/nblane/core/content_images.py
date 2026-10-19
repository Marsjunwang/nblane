"""File-backed image editing sessions for the content workspace.

Generated files are candidates until explicitly accepted. Originals are never
mutated; each session snapshots its reference so iteration survives discards.
"""
from __future__ import annotations

import base64
import io
import json
import math
import time
import uuid
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from nblane.core import content_ai, content_workspace, public_site, visual_candidate_store, visual_generation
from nblane.core.file_lock import locked_profile_write
from nblane.core.file_write import atomic_write_text
from nblane.core.profile_io import profile_dir

PROCESS_ID = uuid.uuid4().hex
MAX_IMAGE_BYTES = 12 * 1024 * 1024


def _root(profile: str) -> Path:
    root = profile_dir(profile) / "blog" / ".image-edits"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(profile: str, run_id: str) -> Path:
    if not run_id.startswith("image-") or len(run_id) != 38 or any(c not in "0123456789abcdef" for c in run_id[6:]):
        raise ValueError("无效的图片任务。")
    return _root(profile) / f"{run_id}.json"


def _write(profile: str, row: dict[str, Any]) -> None:
    atomic_write_text(_path(profile, row["id"]), json.dumps(row, ensure_ascii=False))


def _read(profile: str, run_id: str) -> dict[str, Any]:
    return json.loads(_path(profile, run_id).read_text(encoding="utf-8"))


def image_info(data: bytes) -> tuple[str, tuple[int, int]]:
    """Validate decodable raster bytes, size and pixel count before any API call."""
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError("参考图须为 12 MB 以内的图片。")
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format not in {"PNG", "JPEG", "WEBP", "GIF"}:
                raise ValueError("请使用 PNG、JPEG、WebP 或 GIF 图片。")
            if image.width * image.height > 40_000_000:
                raise ValueError("参考图像素过大，请先缩小到 4000 万像素以内。")
            size = image.size
            mime = Image.MIME[image.format]
            image.verify()
            return mime, size
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("参考图损坏或格式不支持。") from exc


def upload_reference(profile: str, slug: str, data_url: str) -> str:
    post = public_site.load_blog_post(profile, slug)
    clean = content_ai.validate_reference_image(data_url)
    if not clean.startswith("data:"):
        raise ValueError("请上传图片文件。")
    data = base64.b64decode(clean.split(",", 1)[1], validate=True)
    mime, _ = image_info(data)
    ref = visual_candidate_store.write_candidate(
        profile, post.slug, f"reference-{uuid.uuid4().hex}", data=data,
        filename=f"reference.{mime.split('/')[1]}", kind="reference",
    )
    return ref.relative_path


def reference_bytes(profile: str, slug: str, source: str) -> bytes:
    """Accept only profile media or this article's candidates, never arbitrary URLs."""
    if source.startswith("blog/.candidates/"):
        rows = visual_candidate_store.list_candidates(profile)
        if not any(row["candidate_path"] == source and row["slug"] == slug for row in rows):
            raise ValueError("参考图不属于当前文章或已被移除。")
        path = visual_candidate_store.candidate_file_path(profile, source)
    else:
        path = content_workspace.media_file(profile, source)
        if path is None:
            raise ValueError("参考图不可用；请先将外部图片上传到媒体库。")
    if path.stat().st_size > MAX_IMAGE_BYTES:
        raise ValueError("参考图超过 12 MB，请先缩小。")
    data = path.read_bytes()
    image_info(data)
    return data


def output_size(profile: str, request: dict[str, Any]) -> dict[str, Any]:
    """Resolve output dimensions identically for previews and generation."""
    quality = request.get("quality", "standard")
    aspect = request.get("aspect", "original" if request.get("mode") == "edit" else "16:9")
    if quality not in {"standard", "high", "ultra"} or aspect not in {"original", "16:9", "1:1", "4:3", "3:4", "9:16"}:
        raise ValueError("请选择有效的清晰度和比例。")
    config = visual_generation.current_config()
    supports_4k = config["image_model"] == visual_generation.DEFAULT_IMAGE_MODEL and not request.get("reference")
    if quality == "ultra" and not supports_4k:
        raise ValueError("当前生成方式不支持超清 4K，请选择标准或高清。")
    if aspect == "original":
        if not request.get("reference"):
            raise ValueError("保持原图比例需要先选择参考图。")
        _, (rw, rh) = image_info(reference_bytes(profile, request["slug"], request["reference"]))
    else:
        rw, rh = map(int, aspect.split(":"))
    if max(rw, rh) / min(rw, rh) > 8:
        raise ValueError("原图比例超出支持范围，请选择其他输出比例（最长边不能超过最短边的 8 倍）。")
    budget = {"standard": 1024 ** 2, "high": 2048 ** 2, "ultra": 4096 ** 2}[quality]
    width = max(1, math.floor(math.sqrt(budget * rw / rh)))
    height = max(1, math.floor(math.sqrt(budget * rh / rw)))
    size = f"{width}*{height}"
    visual_generation._normalize_image_size(size, model=config["image_model"], has_reference_image=bool(request.get("reference")))
    return {"size": size, "width": width, "height": height, "supports_4k": supports_4k}


def generate(profile: str, request: dict[str, Any]) -> dict[str, Any]:
    post = public_site.load_blog_post(profile, request["slug"])
    row: dict[str, Any] = {
        "id": f"image-{uuid.uuid4().hex}", "slug": post.slug,
        "request": request.copy(), "status": "running", "created_at": time.time(),
        "process_id": PROCESS_ID, "candidates": [], "error": "", "reference": "",
    }
    _write(profile, row)
    try:
        if not content_ai.cover_available():
            raise ValueError("未配置图像服务。")
        source = request.get("reference", "")
        reference = ""
        dimensions = output_size(profile, request)
        row["output_size"] = dimensions["size"]
        size = dimensions["size"]
        if source:
            data = reference_bytes(profile, post.slug, source)
            mime, _ = image_info(data)
            snapshot = visual_candidate_store.write_candidate(
                profile, post.slug, row["id"] + "-ref", data=data,
                filename=f"reference.{mime.split('/')[1]}", kind="reference",
            )
            row["reference"] = snapshot.relative_path
            _write(profile, row)
            reference = f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
        if request["mode"] == "edit" and not reference:
            raise ValueError("请先选择要修改的图片。")
        assets = content_ai.generate_images(
            profile, "image_edit" if request["mode"] == "edit" else "cover", request["instruction"],
            reference_image=reference, size=size,
            title=request.get("title", ""), summary=request.get("summary", ""),
            tags=request.get("tags", []), body=request.get("body", ""),
        )
        for asset in assets:
            image_info(asset.data)
            candidate = visual_candidate_store.write_candidate(
                profile, post.slug, row["id"], data=asset.data,
                filename=visual_generation.generated_filename("edited" if request["mode"] == "edit" else "cover", asset.data, asset.extension),
                kind="image", provider=asset.provider, model=asset.model, prompt=asset.prompt.positive_prompt,
            )
            row["candidates"].append({"candidate_path": candidate.relative_path, "filename": candidate.filename, "applied_path": ""})
        if not row["candidates"]:
            raise ValueError("图像服务没有返回图片，请重试。")
        row["status"] = "done"
    except Exception as exc:
        row["status"] = "failed"
        row["error"] = str(exc)
    _write(profile, row)
    return row


def _interrupted(row: dict[str, Any]) -> bool:
    return row["status"] == "running" and (
        row.get("process_id") != PROCESS_ID or time.time() - row["created_at"] > 360
    )


def list_runs(profile: str, slug: str) -> list[dict[str, Any]]:
    post = public_site.load_blog_post(profile, slug)
    rows = []
    for path in _root(profile).glob("image-*.json"):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if row.get("slug") != post.slug or row.get("status") == "discarded":
            continue
        if _interrupted(row):
            row = {**row, "status": "failed", "error": "任务已中断或超时，可保留要求重新生成。"}
        rows.append(row)
    return sorted(rows, key=lambda row: row["created_at"], reverse=True)


def accept(profile: str, slug: str, run_id: str, candidate_path: str) -> str:
    """Copy a candidate into media, idempotently; keep its version for iteration."""
    public_site.load_blog_post(profile, slug)
    with locked_profile_write(_root(profile), run_id):
        row = _read(profile, run_id)
        if row["slug"] != slug or row["status"] != "done":
            raise ValueError("图片候选不属于当前文章或尚未完成。")
        candidate = next((c for c in row["candidates"] if c["candidate_path"] == candidate_path), None)
        if candidate is None:
            raise ValueError("图片候选不存在。")
        if candidate.get("applied_path") and content_workspace.media_file(profile, candidate["applied_path"]):
            return candidate["applied_path"]
        data = reference_bytes(profile, slug, candidate_path)
        result = public_site.add_blog_media_bytes(profile, slug, data=data, filename=candidate["filename"], kind="image", append=False)
        candidate["applied_path"] = result.relative_path
        _write(profile, row)
        return result.relative_path


def discard(profile: str, slug: str, run_id: str, candidate_path: str = "") -> None:
    with locked_profile_write(_root(profile), run_id):
        row = _read(profile, run_id)
        if row["slug"] != slug or (row["status"] == "running" and not _interrupted(row)):
            raise ValueError("无法移除该任务。")
        targets = [c for c in row["candidates"] if not candidate_path or c["candidate_path"] == candidate_path]
        for candidate in targets:
            visual_candidate_store.discard_candidate(profile, candidate["candidate_path"])
            row["candidates"].remove(candidate)
        if not row["candidates"]:
            row["status"] = "discarded"
            if row.get("reference"):
                visual_candidate_store.discard_candidate(profile, row["reference"])
        _write(profile, row)
