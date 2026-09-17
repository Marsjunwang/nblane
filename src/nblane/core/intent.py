"""Heuristic natural-language intent parser (offline, no LLM required).

Shared by the Home command bar and the Kanban quick-add box. Produces a
structured :class:`IntentAction` that callers confirm before writing;
LLM-based disambiguation can refine ``unknown`` results upstream.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta

_KIND_KANBAN_ADD = "kanban.add"
_KIND_EVIDENCE_CAPTURE = "evidence.capture"
_KIND_REVIEW_WEEKLY = "review.weekly_summary"
_KIND_NAVIGATE = "navigate"
_KIND_UNKNOWN = "unknown"

KANBAN_COLUMNS = ("Doing", "Queue", "Someday")

# Sidebar page map (keyword -> Streamlit page path).
_PAGE_MAP: tuple[tuple[str, ...], str] = (
    (("看板", "kanban"), "pages/3_Kanban.py"),
    (("证据", "evidence"), "pages/2_Evidence_Review.py"),
    (("技能树", "skill"), "pages/1_Skill_Tree.py"),
    (("gap", "差距", "缺口"), "pages/2_Gap_Analysis.py"),
    (("健康", "health"), "pages/5_Profile_Health.py"),
    (("研究", "research", "论文", "paper"), "pages/7_Research.py"),
    (("复盘", "review"), "pages/8_Review.py"),
    (("agent", "代理活动"), "pages/9_Agent_Activity.py"),
    (("项目", "project"), "pages/11_Project_Board.py"),
    (("设置", "settings"), "pages/12_Settings.py"),
    (("首页", "home", "dashboard"), "app.py"),
)

_WEEKDAYS = {
    "一": 0,
    "二": 1,
    "三": 2,
    "四": 3,
    "五": 4,
    "六": 5,
    "日": 6,
    "天": 6,
}

_EN_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


@dataclass
class IntentAction:
    """One parsed intent. ``kind`` is one of the module ``_KIND_*`` values."""

    kind: str
    raw: str
    title: str = ""
    column: str = "Doing"
    due: str = ""
    tags: list[str] = field(default_factory=list)
    page: str = ""
    confidence: float = 0.0


def _extract_tags(text: str) -> tuple[str, list[str]]:
    tags = re.findall(r"#([\w\-一-鿿]+)", text)
    cleaned = re.sub(r"\s*#[\w\-一-鿿]+", "", text)
    return cleaned.strip(), tags


def _weekday_date(today: date, target: int, *, next_week: bool) -> date:
    if next_week:
        # "下周X"/"next X": X of the week starting next Monday.
        return today + timedelta(days=(6 - today.weekday()) + 1 + target)
    delta = (target - today.weekday()) % 7 or 7
    return today + timedelta(days=delta)


def _extract_due(text: str, today: date) -> tuple[str, str]:
    """Pull one due date out of *text*; return ``(remaining, iso_due)``."""
    patterns: list[tuple[str, object]] = [
        (r"大后天(?:前|之前)?", lambda m: today + timedelta(days=3)),
        (r"后天(?:前|之前)?", lambda m: today + timedelta(days=2)),
        (r"明天(?:前|之前)?|tomorrow", lambda m: today + timedelta(days=1)),
        (r"今天(?:前|之前)?|today", lambda m: today),
        (
            r"(\d+)\s*天后|in\s+(\d+)\s+days?",
            lambda m: today
            + timedelta(days=int(m.group(1) or m.group(2))),
        ),
        (
            r"下(?:周|星期)([一二三四五六日天])",
            lambda m: _weekday_date(today, _WEEKDAYS[m.group(1)], next_week=True),
        ),
        (
            r"(?:周|星期)([一二三四五六日天])(?:前|之前|截止|交货|ddl)?",
            lambda m: today
            + timedelta(
                days=((_WEEKDAYS[m.group(1)] - today.weekday()) % 7) or 7
            ),
        ),
        (
            r"\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
            lambda m: _weekday_date(
                today, _EN_WEEKDAYS[m.group(1).lower()], next_week=True
            ),
        ),
        (
            r"\b(?:(?:by|this|on)\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
            lambda m: today
            + timedelta(
                days=(
                    (_EN_WEEKDAYS[m.group(1).lower()] - today.weekday()) % 7
                )
                or 7
            ),
        ),
        (
            r"(20\d{2})[-/年](\d{1,2})[-/月](\d{1,2})日?",
            lambda m: date(
                int(m.group(1)), int(m.group(2)), int(m.group(3))
            ),
        ),
        (
            r"(\d{1,2})月(\d{1,2})[日号](?:前|之前|截止)?",
            lambda m: date(today.year, int(m.group(1)), int(m.group(2))),
        ),
        (
            r"\b(\d{1,2})[-/](\d{1,2})\b",
            lambda m: date(today.year, int(m.group(1)), int(m.group(2))),
        ),
    ]
    for pattern, resolver in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        try:
            due = resolver(match)
        except (ValueError, OverflowError):
            continue
        remaining = (text[: match.start()] + text[match.end() :]).strip()
        return remaining, due.isoformat()
    return text, ""


def _extract_column(text: str) -> tuple[str, str]:
    lowered = text.lower()
    for keyword, column in (
        (" to someday", "Someday"),
        (" to queue", "Queue"),
        (" to doing", "Doing"),
        ("someday", "Someday"),
        ("maybe", "Someday"),
        ("以后再说", "Someday"),
        ("也许", "Someday"),
        ("queue", "Queue"),
        ("排队", "Queue"),
        ("待办池", "Queue"),
        ("doing", "Doing"),
        ("进行中", "Doing"),
        ("在做", "Doing"),
    ):
        if keyword in lowered or keyword in text:
            return re.sub(re.escape(keyword), "", text, flags=re.IGNORECASE).strip(), column
    return text, "Doing"


def _match_page(text: str) -> str:
    lowered = text.lower()
    for keywords, page in _PAGE_MAP:
        for keyword in keywords:
            if keyword in lowered or keyword in text:
                return page
    return ""


def parse_intent(text: str, *, today: date | None = None) -> IntentAction:
    """Parse *text* into an :class:`IntentAction` (never raises)."""
    day = today or date.today()
    raw = (text or "").strip()
    if not raw:
        return IntentAction(kind=_KIND_UNKNOWN, raw="", confidence=0.0)

    if re.search(r"(这周|本周|这一周|上周).*(做|完成|进展|总结|干了|复盘)|^(?:看|总结一下?)?周报$|weekly\s+(summary|review)", raw, re.IGNORECASE):
        return IntentAction(kind=_KIND_REVIEW_WEEKLY, raw=raw, confidence=0.9)

    nav = re.match(r"^(打开|跳转?到?|去|go\s+to|open)\s*(.+)$", raw, re.IGNORECASE)
    if nav:
        page = _match_page(nav.group(2))
        if page:
            return IntentAction(
                kind=_KIND_NAVIGATE, raw=raw, page=page, confidence=0.9
            )

    ev = re.match(r"^(记(?:一条|一下|个)?证据|记录证据|log\s+evidence)\s*[:：]?\s*(.+)$", raw, re.IGNORECASE | re.DOTALL)
    if ev and ev.group(2).strip():
        return IntentAction(
            kind=_KIND_EVIDENCE_CAPTURE,
            raw=raw,
            title=ev.group(2).strip(),
            confidence=0.85,
        )

    add = re.match(
        r"^(?:把(.+?)加到|把(.+?)加入|加到|加入|新增(?:任务)?|添加(?:任务)?|建(?:个|一个)?任务|提醒我|add(?:\s+to)?|new\s+task)\s*(.+)$",
        raw,
        re.IGNORECASE | re.DOTALL,
    )
    if add:
        parts = [g for g in (add.group(1), add.group(2)) if g]
        parts.append(add.group(3))
        body = " ".join(p.strip() for p in parts if p and p.strip())
        body, tags = _extract_tags(body)
        body, due = _extract_due(body, day)
        body, column = _extract_column(body)
        body = re.sub(
            r"(?:\s*(?:到|至))?\s*(?:看板|kanban(?:\s+board)?)$",
            "",
            body,
            flags=re.IGNORECASE,
        )
        body = body.strip(" ,,。.::：")
        if body:
            return IntentAction(
                kind=_KIND_KANBAN_ADD,
                raw=raw,
                title=body,
                column=column,
                due=due,
                tags=tags,
                confidence=0.9 if add.group(1) or add.group(2) else 0.7,
            )

    return IntentAction(kind=_KIND_UNKNOWN, raw=raw, confidence=0.0)


__all__ = [
    "IntentAction",
    "KANBAN_COLUMNS",
    "parse_intent",
]
