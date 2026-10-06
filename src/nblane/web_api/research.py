"""Research source intake endpoints for the SPA research desk.

Replaces the Streamlit Research page's "Inbox & Connectors" tab and its
"AI" popover so source intake no longer needs Streamlit:

- Source inbox: list / manual add / partial update of
  ``research/sources.yaml`` rows (plus "create linked kanban task").
- Connectors: read/upsert ``research/connectors.yaml`` (no secrets — keys
  that look like tokens, cookies or API keys are rejected), dry-run
  discovery and import of selected candidates. Saved-connector discovery
  hits the network, so preview/import run as async jobs
  (``research-connector-preview`` / ``research-connector-import``, see
  ``nblane.web_api.jobs``); pasted manual lists parse locally and answer
  synchronously.
- Research AI config: the research-scoped slice of
  ``web-preferences.yaml`` ``ai.actions`` (same storage the Settings page
  and the Streamlit popover write).

Claim / evidence flows are deliberately absent: sources are not evidence,
and promotion stays out of the SPA.

Concurrency: each source row carries a weak per-source ETag over its
user-editable fields (passive Reader progress metadata excluded, so a
paper being read in another tab does not invalidate an edit). ``PATCH``
honors ``If-Match`` against it (412 with the current source on mismatch);
every write passes its request-start file snapshot to
``save_research_sources`` so a concurrent write landing before the lock
also answers 412 (additive creates retry instead).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from fastapi import APIRouter, Depends, Header, Query, Response
from fastapi.responses import JSONResponse

from nblane.core import codex_adapter, file_state
from nblane.core import llm as llm_client
from nblane.core.research_connectors import (
    AUTO_PROVIDERS,
    CONNECTOR_PROVIDERS,
    SECRET_KEY_FRAGMENTS,
    discover_connector_items,
    find_duplicate_source,
    import_connector_items,
    import_manual_connector_items,
    load_connectors,
    preview_manual_connector_items,
    sync_connector,
    upsert_connector,
)
from nblane.core.research_sources import (
    READER_STATE_METADATA_KEYS,
    RESEARCH_DIRNAME,
    RESEARCH_SOURCES_FILENAME,
    SOURCE_KINDS,
    SOURCE_STATUSES,
    SOURCE_VISIBILITIES,
    ResearchSource,
    add_research_source,
    load_research_sources,
    save_research_sources,
    update_research_source,
)
from nblane.core.web_preferences import (
    AI_ACTION_DEFAULT_BACKENDS,
    load_web_preferences,
    update_web_preferences,
)
from nblane.web_api import jobs
from nblane.web_api.auth import CurrentUser
from nblane.web_api.routes_v1 import (
    ERROR_RESPONSES,
    PROFILE_DEPENDENCY,
    ApiError,
    _if_match_satisfied,
    _record_agent_writeback,
    _resolve_profile,
    require_profile_access,
)
from nblane.web_api.schemas import (
    JobCreateResponse,
    JobModel,
    ResearchAIActionModel,
    ResearchAIConfigResponse,
    ResearchAIConfigUpdateRequest,
    ResearchConnectorCandidateModel,
    ResearchConnectorImportRequest,
    ResearchConnectorImportResultModel,
    ResearchConnectorModel,
    ResearchConnectorPreviewModel,
    ResearchConnectorsResponse,
    ResearchConnectorUpsertRequest,
    ResearchLibraryNodeModel,
    ResearchManualImportRequest,
    ResearchManualPreviewRequest,
    ResearchSourceCreateRequest,
    ResearchSourceDetailModel,
    ResearchSourceErrorResponse,
    ResearchSourceMutationResponse,
    ResearchSourceOptionsModel,
    ResearchSourcePatchRequest,
    ResearchSourcesResponse,
    ResearchSourceTaskResponse,
)

router = APIRouter(prefix="/api/v1")

KIND_CONNECTOR_PREVIEW = "research-connector-preview"
KIND_CONNECTOR_IMPORT = "research-connector-import"

# Research actions owned by the research desk (same list as the Streamlit
# Research page "AI" popover, pages/7_Research.py ``_RESEARCH_AI_ACTIONS``).
RESEARCH_AI_ACTIONS: tuple[str, ...] = tuple(
    action for action in AI_ACTION_DEFAULT_BACKENDS if action.startswith("research.")
)
# Mirrors web_shared._ACTION_CODEX_MODEL_SUGGESTIONS (that module imports
# Streamlit, so it cannot be imported from the API process).
CODEX_MODEL_SUGGESTIONS: tuple[str, ...] = ("gpt-5.5", "gpt-5.1-codex", "gpt-5-codex")

SOURCE_MUTATION_RESPONSES = {
    **ERROR_RESPONSES,
    409: {"model": ResearchSourceErrorResponse, "description": "Duplicate source URL."},
    412: {"model": ResearchSourceErrorResponse, "description": "Source changed since it was loaded."},
}
CONNECTOR_JOB_RESPONSES = {
    **ERROR_RESPONSES,
    202: {"model": JobCreateResponse},
}


# --- helpers -----------------------------------------------------------------


def _sources_path(pdir):
    return pdir / RESEARCH_DIRNAME / RESEARCH_SOURCES_FILENAME


def _file_etag(pdir) -> str:
    snapshot = file_state.snapshot_file(_sources_path(pdir))
    return f'W/"{snapshot.sha256 or "empty"}"'


def _source_etag(source: ResearchSource) -> str:
    """Weak ETag over one source's user-editable state.

    Passive Reader progress keys (last page, panel layout, ...) are
    excluded so reading a paper never invalidates an edit of its row.
    """
    data = source.to_dict()
    metadata = dict(data.get("metadata") or {})
    for key in READER_STATE_METADATA_KEYS:
        metadata.pop(key, None)
    data["metadata"] = metadata
    digest = hashlib.sha256(
        json.dumps(data, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    return f'W/"{digest}"'


def _source_model(source: ResearchSource) -> ResearchSourceDetailModel:
    metadata = source.metadata if isinstance(source.metadata, dict) else {}
    return ResearchSourceDetailModel(
        id=source.id,
        title=source.title,
        kind=source.kind,
        status=source.status,
        url=source.url,
        captured_at=source.captured_at,
        authors=list(source.authors),
        published=source.published,
        tags=list(source.tags),
        summary=source.summary,
        notes=source.notes,
        visibility=source.visibility,
        origin=source.origin,
        library_node_refs=list(source.library_node_refs),
        provider=str(metadata.get("provider") or ""),
        pdf_available=bool(metadata.get("pdf_asset_ref")),
        etag=_source_etag(source),
    )


def _source_error(
    status_code: int,
    code: str,
    message: str,
    source: ResearchSource | None = None,
    *,
    duplicate_source_id: str = "",
) -> JSONResponse:
    body = ResearchSourceErrorResponse(
        code=code,
        message=message,
        source=_source_model(source) if source is not None else None,
        duplicate_source_id=duplicate_source_id,
    )
    headers = {"ETag": _source_etag(source)} if source is not None else {}
    return JSONResponse(status_code=status_code, content=body.model_dump(), headers=headers)


def _choice(value: str | None, options: tuple[str, ...], field: str) -> str:
    clean = str(value or "").strip()
    if clean not in options:
        raise ApiError(
            422,
            "invalid_research_source",
            f"{field} must be one of: {', '.join(options)}.",
        )
    return clean


def _split_filter(raw: str) -> set[str]:
    return {part.strip() for part in raw.split(",") if part.strip() and part.strip() != "all"}


def _secret_keys(value: object, prefix: str = "") -> list[str]:
    """Dotted paths of keys that look like credentials (rejected, never stored)."""
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}{key}"
            if any(fragment in str(key).lower() for fragment in SECRET_KEY_FRAGMENTS):
                found.append(path)
            found.extend(_secret_keys(item, f"{path}."))
    elif isinstance(value, list):
        for item in value:
            found.extend(_secret_keys(item, prefix))
    return found


def _connector_ids(pdir) -> set[str]:
    return {str(row.get("id") or "") for row in load_connectors(pdir).get("connectors") or []}


def _require_connector(pdir, connector_id: str) -> None:
    if connector_id not in _connector_ids(pdir):
        raise ApiError(404, "connector_not_found", f"Unknown research connector: {connector_id}")


def _require_provider(provider: str) -> str:
    clean = str(provider or "").strip()
    if clean not in CONNECTOR_PROVIDERS:
        raise ApiError(
            422,
            "invalid_connector_provider",
            f"provider must be one of: {', '.join(CONNECTOR_PROVIDERS)}.",
        )
    return clean


def _privacy(value: str) -> str:
    clean = str(value or "private").strip()
    if clean not in SOURCE_VISIBILITIES:
        raise ApiError(422, "invalid_connector_privacy", "privacy_default must be private or public.")
    return clean


def _library_nodes(pdir) -> list[ResearchLibraryNodeModel]:
    """Non-trashed Paper Library collections (connector import targets)."""
    try:
        from nblane.core.research_papers import load_paper_library_tree, paper_library_paths

        tree = load_paper_library_tree(pdir)
        paths = paper_library_paths(pdir)
    except Exception:  # noqa: BLE001 - a broken tree must not break intake
        return []
    rows = [
        ResearchLibraryNodeModel(id=node.id, path=paths.get(node.id, node.title))
        for node in tree.nodes
        if node.status != "trashed"
    ]
    return sorted(rows, key=lambda row: row.path.lower())


def _validate_target(pdir, target: dict[str, Any]) -> dict[str, str]:
    kind = str(target.get("kind") or "source_inbox")
    node_id = str(target.get("node_id") or "").strip()
    if kind == "collection":
        if not node_id or node_id not in {node.id for node in _library_nodes(pdir)}:
            raise ApiError(422, "invalid_import_target", f"Unknown Paper Library collection: {node_id}")
        return {"kind": kind, "node_id": node_id}
    return {"kind": kind, "node_id": ""}


def _connectors_response(pdir) -> ResearchConnectorsResponse:
    rows = load_connectors(pdir).get("connectors") or []
    return ResearchConnectorsResponse(
        profile=pdir.name,
        providers=list(CONNECTOR_PROVIDERS),
        auto_providers=sorted(AUTO_PROVIDERS),
        connectors=[
            ResearchConnectorModel(
                id=str(row.get("id") or ""),
                provider=str(row.get("provider") or ""),
                enabled=bool(row.get("enabled", True)),
                query=str(row.get("query") or ""),
                privacy_default=str(row.get("privacy_default") or "private"),
                status=str(row.get("status") or "idle"),
                last_run=str(row.get("last_run") or ""),
                options=dict(row.get("options") or {}),
                rate_limit=dict(row.get("rate_limit") or {}),
                last_result=dict(row.get("last_result") or {}),
            )
            for row in rows
        ],
        library_nodes=_library_nodes(pdir),
    )


def _preview_model(preview: dict[str, Any]) -> ResearchConnectorPreviewModel:
    return ResearchConnectorPreviewModel(
        connector_id=str(preview.get("connector_id") or ""),
        provider=str(preview.get("provider") or ""),
        query=str(preview.get("query") or ""),
        discovered=int(preview.get("discovered") or 0),
        importable=int(preview.get("importable") or 0),
        skipped=int(preview.get("skipped") or 0),
        candidates=[
            ResearchConnectorCandidateModel(
                fingerprint=str(candidate.get("fingerprint") or ""),
                canonical_url=str(candidate.get("canonical_url") or ""),
                selected=bool(candidate.get("selected")),
                duplicate=dict(candidate.get("duplicate") or {}),
                item=dict(candidate.get("item") or {}),
            )
            for candidate in preview.get("candidates") or []
            if isinstance(candidate, dict)
        ],
        warnings=[str(item) for item in preview.get("warnings") or []],
    )


def _import_model(result) -> ResearchConnectorImportResultModel:
    return ResearchConnectorImportResultModel(
        connector_id=result.connector_id,
        provider=result.provider,
        discovered=result.discovered,
        imported=result.imported,
        skipped=result.skipped,
        imported_source_ids=list(result.imported_source_ids),
        warnings=list(result.warnings),
        error=result.error,
    )


# --- source inbox --------------------------------------------------------------


@router.get(
    "/profiles/{name}/research/sources",
    response_model=ResearchSourcesResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def list_research_sources(
    name: str,
    response: Response,
    status: str = Query(default="", description="Comma-separated statuses; empty/all = every status."),
    kind: str = Query(default="", description="Comma-separated kinds; empty/all = every kind."),
    q: str = Query(default="", max_length=200, description="Case-insensitive title/url/summary/tag match."),
) -> ResearchSourcesResponse:
    """Research source inbox (all kinds), newest capture first."""
    pdir = _resolve_profile(name)
    inbox = load_research_sources(pdir)
    statuses = _split_filter(status)
    kinds = _split_filter(kind)
    needle = q.strip().lower()
    status_counts: dict[str, int] = {}
    kind_counts: dict[str, int] = {}
    rows: list[ResearchSource] = []
    for source in inbox.sources:
        if not source.id:
            continue
        status_counts[source.status] = status_counts.get(source.status, 0) + 1
        kind_counts[source.kind] = kind_counts.get(source.kind, 0) + 1
        if statuses and source.status not in statuses:
            continue
        if kinds and source.kind not in kinds:
            continue
        if needle:
            haystack = " ".join([source.title, source.url, source.summary, " ".join(source.tags)]).lower()
            if needle not in haystack:
                continue
        rows.append(source)
    rows.sort(key=lambda item: (item.captured_at, item.id), reverse=True)
    response.headers["ETag"] = _file_etag(pdir)
    return ResearchSourcesResponse(
        profile=pdir.name,
        total=sum(status_counts.values()),
        status_counts=status_counts,
        kind_counts=kind_counts,
        sources=[_source_model(item) for item in rows],
        options=ResearchSourceOptionsModel(
            kinds=list(SOURCE_KINDS),
            statuses=list(SOURCE_STATUSES),
            visibilities=list(SOURCE_VISIBILITIES),
        ),
    )


@router.post(
    "/profiles/{name}/research/sources",
    response_model=ResearchSourceMutationResponse,
    status_code=201,
    responses=SOURCE_MUTATION_RESPONSES,
)
def create_research_source(
    name: str,
    body: ResearchSourceCreateRequest,
    response: Response,
    user: CurrentUser = Depends(require_profile_access),
) -> ResearchSourceMutationResponse | JSONResponse:
    """Manually add one source (origin ``manual``); 409 on a duplicate URL."""
    pdir = _resolve_profile(name)
    kind = _choice(body.kind, SOURCE_KINDS, "kind")
    status = _choice(body.status, SOURCE_STATUSES, "status")
    visibility = _choice(body.visibility, SOURCE_VISIBILITIES, "visibility")
    path = _sources_path(pdir)
    # Additive write: a concurrent change (e.g. Reader progress) between the
    # load and the in-lock re-check just re-runs the load, never clobbers.
    for _attempt in range(3):
        snapshot = file_state.snapshot_file(path)
        inbox = load_research_sources(pdir)
        duplicate = find_duplicate_source(inbox, body.url)
        if duplicate is not None:
            existing = inbox.by_id().get(duplicate["source_id"])
            return _source_error(
                409,
                "duplicate_research_source",
                f"Source URL already in the inbox: {duplicate['source_id']}",
                existing,
                duplicate_source_id=duplicate["source_id"],
            )
        try:
            source = add_research_source(
                inbox,
                body.title,
                kind=kind,
                url=body.url,
                status=status,
                authors=body.authors,
                published=body.published,
                tags=body.tags,
                summary=body.summary,
                notes=body.notes,
                visibility=visibility,
                origin="manual",
            )
        except ValueError as exc:
            raise ApiError(422, "invalid_research_source", str(exc)) from exc
        try:
            save_research_sources(pdir, inbox, expected_snapshot=snapshot)
        except file_state.FileConflictError:
            continue
        break
    else:
        return _source_error(
            412, "etag_mismatch", "research/sources.yaml kept changing; reload and retry."
        )
    _record_agent_writeback(
        user,
        pdir.name,
        action="research_source_create",
        note=f"Added research source {source.id}",
        target_owner="research",
        refs={"research_sources": [source.id]},
        changed_paths=[path],
    )
    response.headers["ETag"] = _source_etag(source)
    return ResearchSourceMutationResponse(ok=True, source=_source_model(source))


@router.patch(
    "/profiles/{name}/research/sources/{source_id}",
    response_model=ResearchSourceMutationResponse,
    responses=SOURCE_MUTATION_RESPONSES,
)
def patch_research_source(
    name: str,
    source_id: str,
    body: ResearchSourcePatchRequest,
    response: Response,
    if_match: str | None = Header(default=None),
    user: CurrentUser = Depends(require_profile_access),
) -> ResearchSourceMutationResponse | JSONResponse:
    """Partial update (status / tags / title / visibility / summary / ...).

    ``If-Match`` carries the source's ``etag``; mismatch answers 412 with
    the current source. Changing ``url`` onto another source's URL is 409.
    """
    pdir = _resolve_profile(name)
    path = _sources_path(pdir)
    snapshot = file_state.snapshot_file(path)
    inbox = load_research_sources(pdir)
    source = inbox.by_id().get(source_id)
    if source is None:
        raise ApiError(404, "research_source_not_found", f"Unknown research source: {source_id}")
    if not _if_match_satisfied(if_match, _source_etag(source)):
        return _source_error(
            412, "etag_mismatch", "This source changed since it was loaded; reload before saving.", source
        )
    fields = body.model_dump(exclude_none=True)
    if "kind" in fields:
        fields["kind"] = _choice(fields["kind"], SOURCE_KINDS, "kind")
    if "status" in fields:
        fields["status"] = _choice(fields["status"], SOURCE_STATUSES, "status")
    if "visibility" in fields:
        fields["visibility"] = _choice(fields["visibility"], SOURCE_VISIBILITIES, "visibility")
    if "url" in fields and fields["url"].strip() and fields["url"].strip() != source.url:
        others = type(inbox)(sources=[item for item in inbox.sources if item.id != source.id])
        duplicate = find_duplicate_source(others, fields["url"])
        if duplicate is not None:
            return _source_error(
                409,
                "duplicate_research_source",
                f"Source URL already in the inbox: {duplicate['source_id']}",
                source,
                duplicate_source_id=duplicate["source_id"],
            )
    if not fields:
        response.headers["ETag"] = _source_etag(source)
        return ResearchSourceMutationResponse(ok=True, source=_source_model(source))
    try:
        update_research_source(inbox, source_id, **fields)
    except ValueError as exc:
        raise ApiError(422, "invalid_research_source", str(exc)) from exc
    try:
        save_research_sources(pdir, inbox, expected_snapshot=snapshot)
    except file_state.FileConflictError:
        current = load_research_sources(pdir).by_id().get(source_id)
        return _source_error(
            412, "etag_mismatch", "research/sources.yaml changed while saving; reload before retrying.", current
        )
    _record_agent_writeback(
        user,
        pdir.name,
        action="research_source_update",
        note=f"Updated research source {source_id}",
        target_owner="research",
        refs={"research_sources": [source_id]},
        changed_paths=[path],
    )
    saved = load_research_sources(pdir).by_id().get(source_id) or source
    response.headers["ETag"] = _source_etag(saved)
    return ResearchSourceMutationResponse(ok=True, source=_source_model(saved))


@router.post(
    "/profiles/{name}/research/sources/{source_id}/task",
    response_model=ResearchSourceTaskResponse,
    status_code=201,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def create_research_source_task(name: str, source_id: str) -> ResearchSourceTaskResponse:
    """Create a kanban Queue task linked to one source ("Read: <title>")."""
    from nblane.core.task_intake import create_learning_task

    pdir = _resolve_profile(name)
    source = load_research_sources(pdir).by_id().get(source_id)
    if source is None:
        raise ApiError(404, "research_source_not_found", f"Unknown research source: {source_id}")
    context = [part for part in (source.url, source.summary) if part]
    context.append(f"source: {source.id}")
    try:
        task = create_learning_task(
            pdir.name,
            title=f"阅读：{source.title or source.id}",
            context="\n".join(context),
            tags=["research", source.id],
        )
    except ValueError as exc:
        raise ApiError(422, "invalid_task", str(exc)) from exc
    return ResearchSourceTaskResponse(ok=True, task_id=task.id, title=task.title)


# --- connectors ----------------------------------------------------------------


@router.get(
    "/profiles/{name}/research/connectors",
    response_model=ResearchConnectorsResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_research_connectors(name: str) -> ResearchConnectorsResponse:
    """Saved connector configs, providers, and collection import targets."""
    return _connectors_response(_resolve_profile(name))


@router.put(
    "/profiles/{name}/research/connectors",
    response_model=ResearchConnectorsResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def upsert_research_connector(name: str, body: ResearchConnectorUpsertRequest) -> ResearchConnectorsResponse:
    """Create or update one connector config (secrets are rejected, 422)."""
    pdir = _resolve_profile(name)
    provider = _require_provider(body.provider)
    privacy = _privacy(body.privacy_default)
    connector_id = body.connector_id.strip()
    if connector_id == "manual" or "/" in connector_id:
        raise ApiError(422, "invalid_connector_id", "connector_id may not be 'manual' or contain '/'.")
    secrets = _secret_keys(body.options)
    if secrets:
        raise ApiError(
            422,
            "connector_secret_rejected",
            "连接器配置不保存 token、cookie 或 API key："
            + ", ".join(secrets)
            + "。请改用服务端环境变量。",
        )
    upsert_connector(
        pdir,
        provider=provider,
        connector_id=connector_id,
        query=body.query,
        enabled=body.enabled,
        privacy_default=privacy,
        options=body.options,
    )
    return _connectors_response(pdir)


@router.post(
    "/profiles/{name}/research/connectors/manual/preview",
    response_model=ResearchConnectorPreviewModel,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def preview_manual_connector(name: str, body: ResearchManualPreviewRequest) -> ResearchConnectorPreviewModel:
    """Parse pasted URLs / CSV / JSON locally and mark duplicates (no writes)."""
    pdir = _resolve_profile(name)
    provider = _require_provider(body.provider)
    try:
        preview = preview_manual_connector_items(pdir, provider, body.raw_items)
    except (ValueError, json.JSONDecodeError) as exc:
        raise ApiError(422, "invalid_manual_items", f"无法解析粘贴内容：{exc}") from exc
    return _preview_model(preview)


@router.post(
    "/profiles/{name}/research/connectors/manual/import",
    response_model=ResearchConnectorImportResultModel,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def import_manual_connector(name: str, body: ResearchManualImportRequest) -> ResearchConnectorImportResultModel:
    """Import selected fingerprints of a pasted list into the source inbox."""
    pdir = _resolve_profile(name)
    provider = _require_provider(body.provider)
    privacy = _privacy(body.privacy_default)
    target = _validate_target(pdir, body.target.model_dump())
    if not body.fingerprints:
        raise ApiError(422, "no_candidates_selected", "请至少选择一条候选。")
    try:
        result = import_manual_connector_items(
            pdir, provider, body.raw_items, body.fingerprints, target=target, privacy_default=privacy
        )
    except (ValueError, json.JSONDecodeError) as exc:
        raise ApiError(422, "invalid_manual_items", f"无法解析粘贴内容：{exc}") from exc
    return _import_model(result)


def _start_connector_job(pdir, kind: str, job_input: dict[str, Any]) -> JobCreateResponse:
    try:
        snapshot = jobs.create_job(pdir.name, kind, job_input, profile_scope=pdir)
    except jobs.JobInputError as exc:
        raise ApiError(422, exc.code, exc.message) from exc
    return JobCreateResponse(job_id=snapshot["job_id"], job=JobModel(**snapshot))


@router.post(
    "/profiles/{name}/research/connectors/{connector_id}/preview",
    response_model=JobCreateResponse,
    status_code=202,
    responses=CONNECTOR_JOB_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def preview_research_connector(name: str, connector_id: str) -> JobCreateResponse:
    """Start a dry-run discovery job; result is a ResearchConnectorPreviewModel."""
    pdir = _resolve_profile(name)
    _require_connector(pdir, connector_id)
    return _start_connector_job(pdir, KIND_CONNECTOR_PREVIEW, {"connector_id": connector_id})


@router.post(
    "/profiles/{name}/research/connectors/{connector_id}/import",
    response_model=JobCreateResponse,
    status_code=202,
    responses=CONNECTOR_JOB_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def import_research_connector(
    name: str, connector_id: str, body: ResearchConnectorImportRequest
) -> JobCreateResponse:
    """Start an import job; result is a ResearchConnectorImportResultModel.

    Selected fingerprints are re-discovered and imported (duplicates
    skipped); an empty selection runs the whole connector.
    """
    pdir = _resolve_profile(name)
    _require_connector(pdir, connector_id)
    target = _validate_target(pdir, body.target.model_dump())
    return _start_connector_job(
        pdir,
        KIND_CONNECTOR_IMPORT,
        {"connector_id": connector_id, "fingerprints": list(body.fingerprints), "target": target},
    )


# --- connector jobs --------------------------------------------------------------


def _validate_connector_job(job_input: dict[str, Any]) -> dict[str, Any]:
    connector_id = str(job_input.get("connector_id") or "").strip()
    if not connector_id:
        raise jobs.JobInputError("invalid_connector_job", "connector_id is required.")
    fingerprints = job_input.get("fingerprints") or []
    if not isinstance(fingerprints, list):
        raise jobs.JobInputError("invalid_connector_job", "fingerprints must be a list.")
    target = job_input.get("target") if isinstance(job_input.get("target"), dict) else {}
    return {
        "connector_id": connector_id,
        "fingerprints": [str(item) for item in fingerprints if str(item).strip()],
        "target": {
            "kind": str(target.get("kind") or "source_inbox"),
            "node_id": str(target.get("node_id") or ""),
        },
    }


def _connector_failure(exc: Exception) -> jobs.JobFailedError:
    if isinstance(exc, ValueError):
        return jobs.JobFailedError("connector_invalid", str(exc))
    return jobs.JobFailedError(
        "connector_unreachable",
        f"连接器请求失败（网络不可用或服务无响应）：{exc}",
    )


def _run_connector_preview(profile: str, job_input: dict[str, Any], report) -> Any:
    from nblane.core import profile_io

    report(phase="discovering", message="正在向外部来源查询候选。")
    try:
        preview = discover_connector_items(profile_io.profile_dir(profile), job_input["connector_id"])
    except Exception as exc:  # noqa: BLE001 - adapters raise network errors of any type
        raise _connector_failure(exc) from exc
    return _preview_model(preview).model_dump()


def _run_connector_import(profile: str, job_input: dict[str, Any], report) -> Any:
    from nblane.core import profile_io

    pdir = profile_io.profile_dir(profile)
    connector_id = job_input["connector_id"]
    report(phase="importing", message="正在导入选中的候选。")
    try:
        if job_input["fingerprints"]:
            result = import_connector_items(
                pdir, connector_id, job_input["fingerprints"], target=job_input["target"]
            )
        else:
            result = sync_connector(pdir, connector_id, dry_run=False)
    except Exception as exc:  # noqa: BLE001
        raise _connector_failure(exc) from exc
    if result.error:
        raise jobs.JobFailedError("connector_unreachable", f"连接器请求失败：{result.error}")
    return _import_model(result).model_dump()


jobs.register_kind(
    jobs.JobKind(
        name=KIND_CONNECTOR_PREVIEW,
        validate=_validate_connector_job,
        run=_run_connector_preview,
        queued_message="Queued connector preview.",
        timeout_seconds=150,
        timeout_message="连接器预览超时（150 秒），请稍后重试。",
    )
)
jobs.register_kind(
    jobs.JobKind(
        name=KIND_CONNECTOR_IMPORT,
        validate=_validate_connector_job,
        run=_run_connector_import,
        queued_message="Queued connector import.",
        timeout_seconds=180,
        timeout_message="连接器导入超时（3 分钟），请稍后重试。",
    )
)


# --- research AI config ------------------------------------------------------------


def _ai_config_response(pdir) -> ResearchAIConfigResponse:
    prefs = load_web_preferences(pdir)
    ai = prefs.get("ai") if isinstance(prefs.get("ai"), dict) else {}
    stored = ai.get("actions") if isinstance(ai.get("actions"), dict) else {}
    try:
        codex_default = str(codex_adapter.current_config(profile=pdir.name).model or "")
    except Exception:  # noqa: BLE001 - Codex readiness must not break the panel
        codex_default = ""
    actions = []
    for action in RESEARCH_AI_ACTIONS:
        row = stored.get(action) if isinstance(stored.get(action), dict) else {}
        actions.append(
            ResearchAIActionModel(
                action=action,
                default_backend=AI_ACTION_DEFAULT_BACKENDS.get(action, "llm"),
                backend=str(row.get("backend") or ""),
                llm_model=str(row.get("llm_model") or ""),
                codex_model=str(row.get("codex_model") or ""),
            )
        )
    return ResearchAIConfigResponse(
        profile=pdir.name,
        actions=actions,
        llm_default_model=str(llm_client.current_config(mask_key=True).get("model") or ""),
        codex_default_model=codex_default,
        codex_model_suggestions=list(CODEX_MODEL_SUGGESTIONS),
    )


@router.get(
    "/profiles/{name}/research/ai-config",
    response_model=ResearchAIConfigResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_research_ai_config(name: str) -> ResearchAIConfigResponse:
    """Per-action backend/model choice for research AI actions."""
    return _ai_config_response(_resolve_profile(name))


@router.put(
    "/profiles/{name}/research/ai-config",
    response_model=ResearchAIConfigResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def put_research_ai_config(name: str, body: ResearchAIConfigUpdateRequest) -> ResearchAIConfigResponse:
    """Write ``ai.actions.<research action>`` only; other actions are untouched."""
    pdir = _resolve_profile(name)
    unknown = sorted(set(body.actions) - set(RESEARCH_AI_ACTIONS))
    if unknown:
        raise ApiError(422, "unknown_research_action", f"Not a research AI action: {', '.join(unknown)}")
    patch = {
        action: {
            "backend": config.backend,
            "llm_model": config.llm_model.strip(),
            "codex_model": config.codex_model.strip(),
        }
        for action, config in body.actions.items()
    }
    if patch:
        update_web_preferences(pdir.name, {"ai": {"actions": patch}})
    return _ai_config_response(pdir)
