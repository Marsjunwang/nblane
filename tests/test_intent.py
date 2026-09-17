"""Tests for nblane.core.intent (offline heuristic parser)."""

from __future__ import annotations

from datetime import date

from nblane.core.intent import parse_intent

# 2026-09-16 is a Wednesday.
NOW = date(2026, 9, 16)


def test_add_to_doing_keeps_title_and_column() -> None:
    intent = parse_intent("把复现GR00T的VLA训练加到Doing", today=NOW)
    assert intent.kind == "kanban.add"
    assert intent.title == "复现GR00T的VLA训练"
    assert intent.column == "Doing"


def test_add_to_queue_strips_column_keyword() -> None:
    intent = parse_intent("加到Queue:整理论文笔记", today=NOW)
    assert intent.kind == "kanban.add"
    assert intent.column == "Queue"
    assert intent.title == "整理论文笔记"


def test_add_with_weekday_due_and_tag() -> None:
    intent = parse_intent("新增任务 周五前复现 GR00T 训练 #vla", today=NOW)
    assert intent.kind == "kanban.add"
    assert intent.due == "2026-09-18"  # upcoming Friday
    assert intent.tags == ["vla"]
    assert intent.title == "复现 GR00T 训练"


def test_add_with_next_week_due() -> None:
    intent = parse_intent("加到 下周三前交论文初稿", today=NOW)
    assert intent.kind == "kanban.add"
    assert intent.due == "2026-09-23"  # next week's Wednesday


def test_add_with_tomorrow_due() -> None:
    intent = parse_intent("提醒我 明天前写完周报", today=NOW)
    assert intent.kind == "kanban.add"
    assert intent.due == "2026-09-17"
    assert "写完周报" in intent.title


def test_add_with_month_day_due() -> None:
    intent = parse_intent("加到 10月1日前交稿", today=NOW)
    assert intent.kind == "kanban.add"
    assert intent.due == "2026-10-01"


def test_add_with_iso_due_and_someday() -> None:
    intent = parse_intent("add learn rust 2026-12-01 someday", today=NOW)
    assert intent.kind == "kanban.add"
    assert intent.due == "2026-12-01"
    assert intent.column == "Someday"
    assert "learn rust" in intent.title


def test_evidence_capture() -> None:
    intent = parse_intent("记一条证据:完成了 GR00T 论文复现", today=NOW)
    assert intent.kind == "evidence.capture"
    assert intent.title == "完成了 GR00T 论文复现"


def test_weekly_summary() -> None:
    intent = parse_intent("我这周做了什么", today=NOW)
    assert intent.kind == "review.weekly_summary"


def test_navigate_chinese() -> None:
    intent = parse_intent("打开看板", today=NOW)
    assert intent.kind == "navigate"
    assert intent.page == "pages/3_Kanban.py"


def test_navigate_english() -> None:
    intent = parse_intent("go to evidence", today=NOW)
    assert intent.kind == "navigate"
    assert intent.page == "pages/2_Evidence_Review.py"


def test_unknown_without_trigger() -> None:
    intent = parse_intent("随便一句话", today=NOW)
    assert intent.kind == "unknown"


def test_empty_is_unknown() -> None:
    intent = parse_intent("   ", today=NOW)
    assert intent.kind == "unknown"


def test_english_add_to_doing_strips_to_and_by_friday() -> None:
    intent = parse_intent("add calibrate dataset to Doing by Friday", today=NOW)
    assert intent.kind == "kanban.add"
    assert intent.column == "Doing"
    assert intent.due == "2026-09-18"  # upcoming Friday
    assert intent.title == "calibrate dataset"


def test_english_next_weekday_due() -> None:
    intent = parse_intent("add write design doc next Monday", today=NOW)
    assert intent.kind == "kanban.add"
    assert intent.due == "2026-09-21"
    assert intent.title == "write design doc"


def test_board_noun_stripped_when_target() -> None:
    intent = parse_intent("把整理实验记录加到看板", today=NOW)
    assert intent.kind == "kanban.add"
    assert intent.title == "整理实验记录"
    assert intent.column == "Doing"


def test_board_noun_kept_inside_title() -> None:
    intent = parse_intent("把修看板拖拽bug加到Doing", today=NOW)
    assert intent.kind == "kanban.add"
    assert intent.title == "修看板拖拽bug"


def test_last_week_and_zhoubao_trigger_weekly() -> None:
    assert parse_intent("上周总结", today=NOW).kind == "review.weekly_summary"
    assert parse_intent("周报", today=NOW).kind == "review.weekly_summary"


def test_write_zhoubao_is_task_not_weekly() -> None:
    intent = parse_intent("提醒我明天写周报", today=NOW)
    assert intent.kind == "kanban.add"
    assert intent.due == "2026-09-17"


def test_parse_never_raises_on_garbage() -> None:
    for text in ("###", "加到", "把", "add", "周九", "13月99日"):
        intent = parse_intent(text, today=NOW)
        assert intent.kind in {
            "kanban.add",
            "evidence.capture",
            "navigate",
            "review.weekly_summary",
            "unknown",
        }
