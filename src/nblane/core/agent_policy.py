"""Write policy for agent accounts (OpenClaw and other personal agents).

One table shared by the HTTP API and MCP decides how an agent write is
handled:

- ``T0`` read-only, nothing recorded (reads, divination).
- ``T1`` applied directly, journaled, undoable (daily ops: check-in, add or
  edit a task, tick a todo, habit plans).
- ``T2`` needs a second confirmation in the chat before it runs, then is
  journaled and undoable (deletes, batches above ``BATCH_THRESHOLD``,
  identity-level edits).
- ``T3`` web UI only; agents are refused.

Confirmation is a two-step handshake: the first request answers ``428``
with a ``confirm_id`` and a human-readable summary; the agent relays the
summary, and once the user agrees it repeats the *identical* request with
``X-Nblane-Confirm: <confirm_id>``. Tokens are single-use, bound to the
caller, and fingerprinted on method + path + body, so a confirmation for
"delete card A" can never authorize "delete card B". The server cannot prove
that a human typed the confirmation — that is the agent's contract (see
docs/zh/guides/assistant.md).

Pending confirmations of the HTTP API live in process memory
(single-process uvicorn); a restart simply means the agent asks again. MCP
stdio servers are spawned per agent session, so the token may be redeemed
by a sibling process: MCP uses ``FileConfirmStore`` under ``state_dir()``.

Which HTTP route maps to which action lives in ``web_api/agent_guard.py``.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import secrets
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

T0 = "T0"
T1 = "T1"
T2 = "T2"
T3 = "T3"

BATCH_THRESHOLD = 3
CONFIRM_TTL_SECONDS = 600.0
CONFIRM_HEADER = "X-Nblane-Confirm"
LEGACY_AGENT_ID = "openclaw"

# Unlisted write actions default to T2: a new endpoint must opt into direct
# writes explicitly instead of silently becoming agent-writable.
ACTION_TIERS: dict[str, str] = {
    # T0 — reads, stateless casts, AI drafts that write nothing, and the
    # undo endpoint itself.
    "divination.cast": T0,
    "ai.draft": T0,
    "journal.undo": T0,
    # T1 — daily ops.
    "checkin.add": T1,
    "kanban.card.add": T1,
    "kanban.card.patch": T1,
    "kanban.card.schedule": T1,
    "kanban.card.move": T1,
    "kanban.card.done": T1,
    "habit_plan.add": T1,
    "habit_plan.update": T1,
    "habit.archive": T1,
    "project_case.add": T1,
    "project_case.save": T1,
    "project_case.archive": T1,
    "goal.add": T1,
    "research_source.add": T1,
    "research_source.patch": T1,
    "research.paper_analysis": T1,
    # T2 — destructive or identity-level.
    "checkin.delete": T2,
    "kanban.card.delete": T2,
    "habit.delete": T2,
    "habit_plan.delete": T2,
    "project_case.delete": T2,
    "project_milestone.delete": T2,
    "research.import": T2,
    "plan_template.instantiate": T2,
    "skill_node.patch": T2,
    "north_star.patch": T2,
    "goal.patch": T2,
    "evidence.edit": T2,
    "evidence.review": T2,
    "evidence.skill_links": T2,
    "evidence.bulk": T2,
    "evidence.deprecate": T2,
    "crystallize.apply": T2,
    "skill_evidence.add": T2,
    # T3 — web only.
    "public.publish": T3,
    "settings.system": T3,
    "auth.permissions": T3,
    # Dismissing AI exceptions is the human's job.
    "review.decide": T3,
    "workshop.terminal": T3,
    # MCP-only writes. Append-only logs (interaction log) change no
    # profile facts and are not journaled.
    "growth_log.append": T1,
    "method_draft.write": T1,
    "interaction.log": T1,
    "agent_task.report": T1,
    # Reader / Paper Library. Raw route, event and Reader-action mappings are
    # below; unknown Reader writes use reader.unsupported and fail closed.
    "reader.auth": T0,
    "reader.search": T0,
    "reader.ai.ask": T0,
    "reader.ai.explain": T0,
    "reader.navigate": T0,
    "reader.token": T0,
    "reader.job.control": T0,
    "reader.cache_warm": T0,
    "reader.progress": T1,
    "reader.annotation.create": T1,
    "reader.annotation.update": T1,
    "reader.chunk.create": T1,
    "reader.citation.create": T1,
    "reader.citation.export": T1,
    "reader.translation": T1,
    "reader.analysis": T1,
    "reader.artifacts.prepare": T1,
    "reader.collection.edit": T1,
    "reader.source.edit": T1,
    "reader.pdf.save": T1,
    "reader.annotation.delete": T2,
    "reader.collection.trash": T2,
    "reader.collection.purge": T2,
    "reader.source.discard": T2,
    "reader.paper.delete": T2,
    "reader.paper.purge": T2,
    "reader.pdf.delete": T2,
    "reader.artifacts.delete": T2,
    "reader.unsupported": T3,
}

# Effective Reader action -> shared policy action. The execution layer uses
# this same registry to reject new, unclassified actions for every account.
READER_ACTIONS: dict[str, str] = {
    "save_progress": "reader.progress",
    "prepare_reader_artifacts": "reader.artifacts.prepare",
    "annotation_create": "reader.annotation.create",
    "create_annotation": "reader.annotation.create",
    "annotation_update": "reader.annotation.update",
    "annotation_delete": "reader.annotation.delete",
    "create_chunk_from_selection": "reader.chunk.create",
    "create_chunk": "reader.chunk.create",
    "create_citation": "reader.citation.create",
    "translate_full_paper": "reader.translation",
    "translate_visible_pages": "reader.translation",
    "retry_translation_scope": "reader.translation",
    "translate_selection": "reader.translation",
    "translate_segment": "reader.translation",
    "explain_selection": "reader.ai.explain",
    "ask_paper": "reader.ai.ask",
    "analyze_paper": "reader.analysis",
    "codex_deep_read": "reader.analysis",
    "generate_review_card": "reader.analysis",
    "request_page_previews": "reader.cache_warm",
    "selection_created": "reader.navigate",
    "page_changed": "reader.navigate",
    "viewport_changed": "reader.navigate",
    "reader_state_changed": "reader.navigate",
    "request_reader_context": "reader.navigate",
}

READER_TASK_ACTIONS: frozenset[str] = frozenset({
    "ask_paper",
    "explain_selection",
    "retry_translation_scope",
    "translate_full_paper",
    "translate_selection",
    "translate_visible_pages",
    "analyze_paper",
    "codex_deep_read",
    "generate_review_card",
    "prepare_reader_artifacts",
})

PAPER_LIBRARY_EVENT_ACTIONS: dict[str, str] = {
    "paper_library_select_view": "reader.navigate",
    "paper_library_select_collection": "reader.navigate",
    "paper_library_select_paper": "reader.navigate",
    "paper_library_sync_reader_tab": "reader.navigate",
    "paper_library_delete_paper_preview": "reader.navigate",
    "paper_library_create_collection": "reader.collection.edit",
    "paper_library_rename_collection": "reader.collection.edit",
    "paper_library_move_collection": "reader.collection.edit",
    "paper_library_reorder_collection": "reader.collection.edit",
    "paper_library_trash_collection": "reader.collection.trash",
    "paper_library_purge_collection": "reader.collection.purge",
    "paper_library_restore_collection": "reader.collection.edit",
    "paper_library_add_selected_papers_to_collection": "reader.source.edit",
    "paper_library_move_selected_papers_to_collection": "reader.source.edit",
    "paper_library_drop_papers_to_collection": "reader.source.edit",
    "paper_library_remove_papers_from_collection": "reader.source.edit",
    "paper_library_update_papers_status": "reader.source.edit",
    "paper_library_rename_paper": "reader.source.edit",
    "paper_library_download_pdf": "reader.pdf.save",
    "paper_library_run_extraction": "reader.artifacts.prepare",
    "paper_library_retry_translation": "reader.translation",
    "paper_library_auto_chunk": "reader.chunk.create",
    "paper_library_delete_paper_record": "reader.paper.delete",
    "paper_library_delete_paper_asset": "reader.pdf.delete",
    "paper_library_delete_paper_artifacts": "reader.artifacts.delete",
    "paper_library_purge_discarded_papers": "reader.paper.purge",
}


def paper_library_event_action(event: dict[str, Any]) -> str:
    """Resolve the effective policy action, including destructive status edits."""
    raw = str(event.get("action") or "").strip()
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    if raw == "paper_library_update_papers_status" and str(
        payload.get("status") or ""
    ).strip() == "discarded":
        return "reader.source.discard"
    return PAPER_LIBRARY_EVENT_ACTIONS.get(raw, "reader.unsupported")


# Chat-facing labels (confirmation summaries, journal rows).
ACTION_LABELS: dict[str, str] = {
    "kanban.card.add": "新建任务",
    "kanban.card.move": "移动任务",
    "kanban.card.done": "完成任务",
    "kanban.card.schedule": "任务排期",
    "kanban.card.patch": "修改任务",
    "kanban.card.delete": "删除任务",
    "checkin.add": "打卡",
    "checkin.delete": "删除打卡记录",
    "habit.archive": "归档/恢复习惯",
    "habit.delete": "删除习惯及其全部打卡",
    "habit_plan.add": "新建阶段计划",
    "habit_plan.update": "修改阶段计划",
    "habit_plan.delete": "删除阶段计划",
    "plan_template.instantiate": "套用计划模板",
    "goal.add": "新建目标",
    "goal.patch": "修改目标",
    "north_star.patch": "改写北极星",
    "skill_node.patch": "修改技能点状态",
    "evidence.edit": "编辑证据",
    "evidence.review": "评审证据",
    "evidence.skill_links": "修改证据关联的技能",
    "evidence.bulk": "批量修改证据",
    "evidence.deprecate": "批量弃用/恢复证据",
    "crystallize.apply": "结晶已完成任务为证据",
    "project_case.add": "新建项目",
    "project_case.save": "修改项目",
    "project_case.archive": "归档项目",
    "project_case.delete": "删除项目",
    "project_milestone.delete": "删除项目里程碑",
    "research_source.add": "添加资料",
    "research_source.patch": "修改资料",
    "research.paper_analysis": "生成论文分析",
    "research.import": "批量导入资料",
    "growth_log.append": "记一条成长日志",
    "method_draft.write": "写方法草稿",
    "interaction.log": "记录问答",
    "agent_task.report": "回报 agent 任务",
    "skill_evidence.add": "给技能点添加证据",
    "reader.auth": "Reader 会话控制",
    "reader.search": "搜索论文",
    "reader.ai.ask": "论文问答",
    "reader.ai.explain": "解释论文选区",
    "reader.navigate": "论文库导航",
    "reader.token": "创建 Reader 访问令牌",
    "reader.job.control": "控制 Reader 后台任务",
    "reader.cache_warm": "预热 Reader 缓存",
    "reader.progress": "保存阅读进度",
    "reader.annotation.create": "新建论文标注",
    "reader.annotation.update": "修改论文标注",
    "reader.annotation.delete": "删除论文标注",
    "reader.chunk.create": "保存论文引文片段",
    "reader.citation.create": "创建论文引用",
    "reader.citation.export": "导出论文引用",
    "reader.translation": "保存论文翻译",
    "reader.analysis": "生成论文分析",
    "reader.artifacts.prepare": "提取论文阅读产物",
    "reader.collection.edit": "编辑论文集合",
    "reader.collection.trash": "将论文集合移入回收站",
    "reader.collection.purge": "彻底删除论文集合",
    "reader.source.edit": "修改论文资料",
    "reader.source.discard": "弃用论文资料",
    "reader.paper.delete": "删除论文记录",
    "reader.paper.purge": "彻底清理已弃用论文",
    "reader.pdf.save": "上传或下载论文 PDF",
    "reader.pdf.delete": "物理删除论文 PDF",
    "reader.artifacts.delete": "删除 Reader 阅读产物",
    "reader.unsupported": "未登记的 Reader 写操作",
    "unknown": "执行未登记的写操作",
}

def is_agent(user: Any) -> bool:
    """Agent service account: ``agent: true`` in users.yaml (or legacy id)."""
    return bool(getattr(user, "agent", False)) or getattr(user, "id", "") == LEGACY_AGENT_ID


def tier_for(action: str, count: int = 1) -> str:
    """Tier for one agent action touching *count* entities."""
    tier = ACTION_TIERS.get(action, T2)
    if tier == T1 and count > BATCH_THRESHOLD:
        return T2
    return tier


def needs_confirmation(action: str, count: int = 1) -> bool:
    return tier_for(action, count) == T2


def fingerprint(method: str, path: str, body: Any = None) -> str:
    """Stable digest of one request: method + path + canonical JSON body."""
    canonical = json.dumps(body, sort_keys=True, ensure_ascii=False, default=str)
    raw = "\n".join([method.upper(), path, canonical])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PendingConfirmation:
    confirm_id: str
    actor: str
    profile: str
    action: str
    summary: str
    fingerprint: str
    expires_at: float

    def public(self) -> dict[str, Any]:
        return {
            "confirm_id": self.confirm_id,
            "action": self.action,
            "summary": self.summary,
            "expires_at": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.expires_at)
            ),
        }


class MemoryConfirmStore:
    """Pending confirmations in process memory (the HTTP API)."""

    def __init__(self) -> None:
        self._pending: dict[str, PendingConfirmation] = {}
        self._lock = threading.Lock()

    @contextmanager
    def edit(self) -> Iterator[dict[str, PendingConfirmation]]:
        with self._lock:
            yield self._pending


class FileConfirmStore:
    """Pending confirmations in one JSON file, shared across processes."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def _load(self) -> dict[str, PendingConfirmation]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        out: dict[str, PendingConfirmation] = {}
        for key, value in (raw if isinstance(raw, dict) else {}).items():
            try:
                out[key] = PendingConfirmation(**value)
            except TypeError:
                continue
        return out

    @contextmanager
    def edit(self) -> Iterator[dict[str, PendingConfirmation]]:
        from nblane.core.file_write import atomic_write_text

        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self.path.with_name(self.path.name + ".lock")
        with open(lock_path, "a", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                pending = self._load()
                before = dict(pending)
                yield pending
                if pending != before:
                    body = {key: asdict(value) for key, value in pending.items()}
                    atomic_write_text(self.path, json.dumps(body, ensure_ascii=False, indent=1))
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


ConfirmStore = MemoryConfirmStore | FileConfirmStore
_DEFAULT_STORE = MemoryConfirmStore()


def state_dir() -> Path:
    """Machine-local agent state (outside every git-backed data root)."""
    value = os.getenv("NBLANE_AGENT_STATE_DIR", "").strip()
    if value:
        return Path(value).expanduser()
    return Path.home() / ".local" / "share" / "nblane" / "agent"


def _prune(pending: dict[str, PendingConfirmation], now: float) -> None:
    for key in [k for k, v in pending.items() if v.expires_at <= now]:
        pending.pop(key, None)


def issue(
    *,
    actor: str,
    profile: str,
    action: str,
    summary: str,
    fingerprint: str,
    store: ConfirmStore | None = None,
) -> PendingConfirmation:
    """Register one pending confirmation and return it."""
    now = time.time()
    pending = PendingConfirmation(
        confirm_id="cf_" + secrets.token_hex(6),
        actor=actor,
        profile=profile,
        action=action,
        summary=summary,
        fingerprint=fingerprint,
        expires_at=now + CONFIRM_TTL_SECONDS,
    )
    with (store or _DEFAULT_STORE).edit() as table:
        _prune(table, now)
        table[pending.confirm_id] = pending
    return pending


def take(
    confirm_id: str,
    *,
    actor: str,
    fingerprint: str,
    store: ConfirmStore | None = None,
) -> PendingConfirmation | None:
    """Spend *confirm_id* when it matches caller + request; single use."""
    now = time.time()
    with (store or _DEFAULT_STORE).edit() as table:
        _prune(table, now)
        pending = table.get(confirm_id.strip())
        if (
            pending is None
            or pending.actor != actor
            or pending.fingerprint != fingerprint
        ):
            return None
        table.pop(pending.confirm_id, None)
    return pending


def consume(
    confirm_id: str,
    *,
    actor: str,
    fingerprint: str,
    store: ConfirmStore | None = None,
) -> bool:
    return take(confirm_id, actor=actor, fingerprint=fingerprint, store=store) is not None


def refund(pending: PendingConfirmation, store: ConfirmStore | None = None) -> None:
    """Return an unused token (the confirmed request changed nothing, e.g.
    a 412 that the client will retry); expiry is unchanged."""
    with (store or _DEFAULT_STORE).edit() as table:
        if pending.expires_at > time.time():
            table[pending.confirm_id] = pending


def reset(store: ConfirmStore | None = None) -> None:
    """Drop every pending confirmation (test helper)."""
    with (store or _DEFAULT_STORE).edit() as table:
        table.clear()
