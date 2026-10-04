from __future__ import annotations

from pathlib import Path

import yaml

from nblane.core.ai.exceptions import collect_profile_exceptions


def _dump(path: Path, value: dict) -> None:
    path.write_text(yaml.safe_dump(value, allow_unicode=True), encoding="utf-8")


def test_collects_failures_across_ai_sources_and_deduplicates_activity(tmp_path: Path) -> None:
    profile = tmp_path / "alice"
    profile.mkdir()
    _dump(
        profile / "agent-activity.yaml",
        {
            "items": [
                {
                    "id": "act:failed",
                    "status": "failed",
                    "title": "写回看板失败",
                    "error": "看板文件发生冲突",
                    "candidate_type": "kanban_move",
                    "updated": "2026-10-04T10:00:00+00:00",
                },
                {
                    "id": "act:success",
                    "status": "applied",
                    "title": "已应用",
                },
            ]
        },
    )
    _dump(
        profile / "ai-runs.yaml",
        {
            "runs": [
                {
                    "id": "run-1",
                    "action": "research.paper_qa",
                    "ok": False,
                    "error": "模型不可用",
                    "created": "2026-10-04T11:00:00+00:00",
                },
                {
                    "id": "run-2",
                    "action": "kanban.task_alignment",
                    "ok": False,
                    "error": "duplicate activity",
                    "activity_item_id": "act:failed",
                    "created": "2026-10-04T12:00:00+00:00",
                },
            ]
        },
    )
    _dump(
        profile / "agent-tasks.yaml",
        {
            "tasks": [
                {
                    "id": "task-1",
                    "title": "外部 Agent 任务",
                    "status": "failed",
                    "error": "Agent 超时",
                    "updated": "2026-10-04T09:00:00+00:00",
                }
            ]
        },
    )

    items = collect_profile_exceptions(
        profile,
        jobs=[
            {
                "job_id": "job-1",
                "kind": "studio-jd-match",
                "status": "failed",
                "message": "LLM 未配置",
                "created_at": 1_790_000_000.0,
            }
        ],
    )

    assert {item["id"] for item in items} == {
        "activity:act:failed",
        "run:run-1",
        "agent-task:task-1",
        "job:job-1",
    }
    run_item = next(item for item in items if item["id"] == "run:run-1")
    assert run_item["source"] == "AI 调用"
    assert run_item["href"] == "/p/alice/research"
    assert all(item["retryable"] for item in items)
