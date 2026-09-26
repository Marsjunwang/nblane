"""占卜 (divination): hexagram casts anchored in the real starmap data.

Design: ``docs/zh/dev/home-starmap-enhancements-design.md`` §5.

Both modes derive the hexagram deterministically from a hash of the
profile's real starmap state salted with the date, so the same state
yields the same 卦 within a day:

- 戏占 (``play``, default): playful reading (大富大贵彩头 allowed), but
  every number quoted comes from the real snapshot anchors.
- 正占 (``serious``): the user's question is run through the REAL rule
  gap analysis (``core/gap.py``); the 卦辞 language is the wrapper and
  the gap result (missing skills etc.) is the content.

The reading text is either LLM-polished via the AI gateway action
``divination.cast`` (``source == "llm"``) or composed by the
deterministic rule path (``source == "rule"``) when the gateway is
unconfigured, errors, or times out. The result is single-consumption:
nothing is persisted by this module.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import date
from pathlib import Path
from typing import Any, Callable

from nblane.core import gap as gap_core
from nblane.core import projects_board
from nblane.core import starmap_snapshot as starmap_snapshot_core

MODE_PLAY = "play"
MODE_SERIOUS = "serious"
MODES = (MODE_PLAY, MODE_SERIOUS)

DIVINATION_ACTION = "divination.cast"
# Thinking stays ON (王军 ruling 2026-09-26): a qwen3.8-flash cast thinks
# ~45s, so 60s timed out at the borderline and the SDK's silent retries
# tripled the wait (mobile clients dropped → "failed to fetch"). 90s gives
# headroom; llm_max_retries=0 below makes a slow cast fail fast to the rule
# reading instead of multiplying the wait.
LLM_TIMEOUT_SECONDS = 90.0
LLM_MODEL_DEFAULT = "qwen3.8-flash"
QUESTION_MAX_LENGTH = 500

# Curated hexagram table (King Wen number, name, classical 卦辞, modern
# one-line gloss). ``lines`` are the six yao bottom-to-top (初爻→上爻),
# 1 = yang (⚊), 0 = yin (⚋). The deterministic pick indexes into this
# table, so every cast lands on a real classical hexagram.
HEXAGRAMS: tuple[dict[str, Any], ...] = (
    {"king_wen": 1, "name": "乾为天", "lines": (1, 1, 1, 1, 1, 1),
     "judgment": "乾：元亨利贞。",
     "gloss": "六龙御天，进德修业，正当其时也。"},
    {"king_wen": 2, "name": "坤为地", "lines": (0, 0, 0, 0, 0, 0),
     "judgment": "坤：元亨，利牝马之贞。君子有攸往，先迷后得主，利。",
     "gloss": "厚德载物，稳字当头，厚积薄发。"},
    {"king_wen": 3, "name": "水雷屯", "lines": (1, 0, 0, 0, 1, 0),
     "judgment": "屯：元亨利贞。勿用有攸往，利建侯。",
     "gloss": "万事开头难，宜立桩建基，不宜远图。"},
    {"king_wen": 10, "name": "天泽履", "lines": (1, 1, 0, 1, 1, 1),
     "judgment": "履虎尾，不咥人，亨。",
     "gloss": "如履虎尾而虎不咬——险处行得稳，便是通途。"},
    {"king_wen": 11, "name": "地天泰", "lines": (1, 1, 1, 0, 0, 0),
     "judgment": "泰：小往大来，吉亨。",
     "gloss": "天地交而万物通，小付出换大回报。"},
    {"king_wen": 12, "name": "天地否", "lines": (0, 0, 0, 1, 1, 1),
     "judgment": "否之匪人，不利君子贞，大往小来。",
     "gloss": "天地不交，宜守不宜进，蓄力待时。"},
    {"king_wen": 13, "name": "天火同人", "lines": (1, 0, 1, 1, 1, 1),
     "judgment": "同人于野，亨。利涉大川，利君子贞。",
     "gloss": "聚众于野，与人同道，可成大事。"},
    {"king_wen": 14, "name": "火天大有", "lines": (1, 1, 1, 1, 0, 1),
     "judgment": "大有：元亨。",
     "gloss": "火在天上，照见四方——大丰大有所象也。"},
    {"king_wen": 15, "name": "地山谦", "lines": (0, 0, 1, 0, 0, 0),
     "judgment": "谦：亨，君子有终。",
     "gloss": "山藏地中，谦而有光，善始者善终。"},
    {"king_wen": 16, "name": "雷地豫", "lines": (0, 0, 0, 1, 0, 0),
     "judgment": "豫：利建侯行师。",
     "gloss": "雷出地奋，宜谋定而动、张弛有度。"},
    {"king_wen": 17, "name": "泽雷随", "lines": (1, 0, 0, 1, 1, 0),
     "judgment": "随：元亨利贞，无咎。",
     "gloss": "随顺时势，因势利导，随时之义大矣哉。"},
    {"king_wen": 19, "name": "地泽临", "lines": (1, 1, 0, 0, 0, 0),
     "judgment": "临：元亨利贞。至于八月有凶。",
     "gloss": "阳气方长，趁热打铁，勿待时过。"},
    {"king_wen": 20, "name": "风地观", "lines": (0, 0, 0, 0, 1, 1),
     "judgment": "观：盥而不荐，有孚颙若。",
     "gloss": "观其所行，省己之身，先看清楚再出手。"},
    {"king_wen": 24, "name": "地雷复", "lines": (1, 0, 0, 0, 0, 0),
     "judgment": "复：亨。出入无疾，朋来无咎。",
     "gloss": "一阳来复，旧的功夫回来了，从头越。"},
    {"king_wen": 26, "name": "山天大畜", "lines": (1, 1, 1, 0, 0, 1),
     "judgment": "大畜：利贞。不家食吉，利涉大川。",
     "gloss": "大山蓄天光——厚积之时，所蓄者大。"},
    {"king_wen": 29, "name": "坎为水", "lines": (0, 1, 0, 0, 1, 0),
     "judgment": "习坎：有孚，维心亨，行有尚。",
     "gloss": "水流不息，险中习坎，心诚则行有成。"},
    {"king_wen": 30, "name": "离为火", "lines": (1, 0, 1, 1, 0, 1),
     "judgment": "离：利贞，亨。畜牝牛，吉。",
     "gloss": "火附于物而明，有所依傍则光华自生。"},
    {"king_wen": 31, "name": "泽山咸", "lines": (0, 0, 1, 1, 1, 0),
     "judgment": "咸：亨，利贞，取女吉。",
     "gloss": "山上有泽，两感相通，感应而事成。"},
    {"king_wen": 32, "name": "雷风恒", "lines": (0, 1, 1, 1, 0, 0),
     "judgment": "恒：亨，无咎，利贞，利有攸往。",
     "gloss": "雷风相与，恒久之道——日课不辍之谓也。"},
    {"king_wen": 35, "name": "火地晋", "lines": (0, 0, 0, 1, 0, 1),
     "judgment": "晋：康侯用锡马蕃庶，昼日三接。",
     "gloss": "日出地上，节节晋升，一日三见。"},
    {"king_wen": 40, "name": "雷水解", "lines": (0, 1, 0, 1, 0, 0),
     "judgment": "解：利西南。无所往，其来复吉。",
     "gloss": "雷雨作而百果草木皆甲坼——郁结得解。"},
    {"king_wen": 42, "name": "风雷益", "lines": (1, 0, 0, 0, 1, 1),
     "judgment": "益：利有攸往，利涉大川。",
     "gloss": "风雷相益，见善则迁，有过则改。"},
    {"king_wen": 46, "name": "地风升", "lines": (0, 1, 1, 0, 0, 0),
     "judgment": "升：元亨，用见大人，勿恤。南征吉。",
     "gloss": "木生地中，日长一寸——稳步高升之象。"},
    {"king_wen": 48, "name": "水风井", "lines": (0, 1, 1, 0, 1, 0),
     "judgment": "井：改邑不改井，无丧无得，往来井井。",
     "gloss": "井养而不穷，守好根本，自有活水。"},
    {"king_wen": 49, "name": "泽火革", "lines": (1, 0, 1, 1, 1, 0),
     "judgment": "革：巳日乃孚，元亨利贞，悔亡。",
     "gloss": "泽中有火，变革之时——破旧立新，当断则断。"},
    {"king_wen": 50, "name": "火风鼎", "lines": (0, 1, 1, 1, 0, 1),
     "judgment": "鼎：元吉，亨。",
     "gloss": "鼎新之器，稳重而烹新——基业可立。"},
    {"king_wen": 51, "name": "震为雷", "lines": (1, 0, 0, 1, 0, 0),
     "judgment": "震：亨。震来虩虩，笑言哑哑。",
     "gloss": "惊雷百里而匕鬯不惊——定力见功夫。"},
    {"king_wen": 52, "name": "艮为山", "lines": (0, 0, 1, 0, 0, 1),
     "judgment": "艮其背，不获其身；行其庭，不见其人，无咎。",
     "gloss": "山止于此，当止则止，静而后能定。"},
    {"king_wen": 53, "name": "风山渐", "lines": (0, 0, 1, 0, 1, 1),
     "judgment": "渐：女归吉，利贞。",
     "gloss": "木在山上，循序渐进——慢功夫成正果。"},
    {"king_wen": 55, "name": "雷火丰", "lines": (1, 0, 1, 1, 0, 0),
     "judgment": "丰：亨，王假之，勿忧，宜日中。",
     "gloss": "雷电皆至，丰大之时，宜照四方。"},
    {"king_wen": 60, "name": "水泽节", "lines": (1, 1, 0, 0, 1, 0),
     "judgment": "节：亨。苦节不可贞。",
     "gloss": "泽上有水，节以制度——有度则通，苦节则穷。"},
    {"king_wen": 61, "name": "风泽中孚", "lines": (1, 1, 0, 0, 1, 1),
     "judgment": "中孚：豚鱼吉，利涉大川，利贞。",
     "gloss": "诚在中孚，信及豚鱼——实心最有力量。"},
    {"king_wen": 63, "name": "水火既济", "lines": (1, 0, 1, 0, 1, 0),
     "judgment": "既济：亨小，利贞。初吉终乱。",
     "gloss": "水在火上，事已成矣——守成尤须防乱。"},
    {"king_wen": 64, "name": "火水未济", "lines": (0, 1, 0, 1, 0, 1),
     "judgment": "未济：亨。小狐汔济，濡其尾，无攸利。",
     "gloss": "事未竟而前景明——差一点火候，再烧一把。"},
)

_STATUS_ZH = {
    "locked": "未启",
    "learning": "在学",
    "solid": "已固",
    "expert": "精湛",
}

Runner = Callable[[str, dict[str, Any]], Any]


def build_anchors(snapshot: dict, board: Any) -> dict[str, Any]:
    """Distill the starmap snapshot + habits board into reading anchors.

    Every value here is a real, verifiable data point — the reading
    (rule or LLM) may only quote from this dict.
    """
    counts = dict(snapshot.get("counts") or {})
    skills = snapshot.get("skills") or []
    projects = snapshot.get("projects") or []
    goals = snapshot.get("goals") or []
    habit_streaks = [
        {"title": habit.title or habit.id, "streak": int(habit.streak)}
        for habit in getattr(board, "habits", [])
    ]
    return {
        "skills_lit": int(counts.get("skills_lit", 0)),
        "skills_learning": sum(1 for s in skills if s.get("status") == "learning"),
        "skills_total": len(skills),
        "evidence": int(counts.get("evidence", 0)),
        "evidence_flying": int(counts.get("evidence_flying", 0)),
        "evidence_needs_review": int(counts.get("evidence_needs_review", 0)),
        "projects_active": int(counts.get("projects_active", 0)),
        "project_titles": [
            str(p.get("title") or p.get("id"))
            for p in projects
            if p.get("status") == "active"
        ][:9],
        "goals_active": len(goals),
        "goal_titles": [str(g.get("title") or g.get("id")) for g in goals][:7],
        "habit_streaks": habit_streaks,
        "best_streak": max((h["streak"] for h in habit_streaks), default=0),
        "north_star": str(snapshot.get("north_star") or ""),
    }


def hexagram_material(
    profile: str,
    mode: str,
    question: str,
    anchors: dict[str, Any],
    today: date,
) -> str:
    """Canonical string hashed for the deterministic hexagram pick.

    Same profile state + same day (+ same question in serious mode)
    yields the same 卦; any real state change re-rolls.
    """
    material = {
        "profile": profile,
        "date": today.isoformat(),
        "mode": mode,
        "question": question if mode == MODE_SERIOUS else "",
        "skills_lit": anchors.get("skills_lit", 0),
        "skills_total": anchors.get("skills_total", 0),
        "evidence": anchors.get("evidence", 0),
        "evidence_flying": anchors.get("evidence_flying", 0),
        "evidence_needs_review": anchors.get("evidence_needs_review", 0),
        "projects_active": anchors.get("projects_active", 0),
        "goals_active": anchors.get("goals_active", 0),
        "streaks": [
            (h.get("title", ""), h.get("streak", 0))
            for h in anchors.get("habit_streaks") or []
        ],
    }
    return json.dumps(material, ensure_ascii=False, sort_keys=True)


def pick_hexagram(material: str) -> dict[str, Any]:
    """Deterministically pick one curated hexagram from the material hash."""
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    index = int(digest[:16], 16) % len(HEXAGRAMS)
    return dict(HEXAGRAMS[index])


def summarize_gap(result: Any, *, max_nodes: int = 12) -> dict[str, Any]:
    """Project a ``GapResult`` into the plain dict used by prompt + anchors."""
    if result is None:
        return {}
    if getattr(result, "error", None):
        return {"error": str(result.error)}
    closure = list(getattr(result, "closure", []) or [])
    gap_nodes = [n for n in closure if n.get("is_gap")]
    strong_nodes = [n for n in closure if not n.get("is_gap")]
    return {
        "can_solve": bool(getattr(result, "can_solve", False)),
        "gap_labels": [str(n.get("label") or n.get("id")) for n in gap_nodes],
        "strong_labels": [str(n.get("label") or n.get("id")) for n in strong_nodes][:5],
        "closure": [
            {
                "id": str(n.get("id") or ""),
                "label": str(n.get("label") or n.get("id") or ""),
                "status": str(n.get("status") or "locked"),
                "is_gap": bool(n.get("is_gap")),
            }
            for n in closure[:max_nodes]
        ],
    }


def run_gap_analysis(profile_name: str, question: str) -> dict[str, Any]:
    """Run the REAL rule gap analysis for serious mode (never raises)."""
    try:
        result = gap_core.analyze(profile_name, question)
    except Exception as exc:  # pragma: no cover - defensive
        return {"error": f"gap_analysis_failed: {exc}"}
    return summarize_gap(result)


def _hexagram_payload(hexagram: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": str(hexagram["name"]),
        "symbol_lines": [int(yao) for yao in hexagram["lines"]],
        "judgment": "",
    }


def _rule_judgment(hexagram: dict[str, Any]) -> str:
    return f"{hexagram['judgment']}（{hexagram['gloss']}）"


def _rule_reading_play(hexagram: dict[str, Any], anchors: dict[str, Any]) -> str:
    lines = [
        f"星盘微光一滞，星尘聚成「{hexagram['name']}」。卦曰：{hexagram['judgment']}",
        (
            f"今日星图实况：{anchors['skills_lit']} 星官已点亮（共 "
            f"{anchors['skills_total']} 位），{anchors['skills_learning']} 位在学；"
            f"{anchors['projects_active']} 行星在轨"
        ),
    ]
    titles = anchors.get("project_titles") or []
    if titles:
        lines[-1] += f"（{'、'.join(titles[:3])}{'……' if len(titles) > 3 else ''}）"
    lines[-1] += (
        f"；{anchors['evidence_flying']} 客星正掠过长河，"
        f"{anchors['evidence_needs_review']} 件证据候印。"
    )
    best = anchors.get("best_streak", 0)
    if best > 0:
        top = max(
            anchors.get("habit_streaks") or [{"title": "", "streak": 0}],
            key=lambda h: h.get("streak", 0),
        )
        lines.append(f"日课「{top['title']}」已连续钤印 {best} 日。")
    if anchors["skills_lit"] >= 10 and best >= 7:
        lines.append(
            "紫微垣星光大盛——卦师掐指一算：三年之内，大富大贵"
            "（戏言彩头，星尘还须一日一日攒）。"
        )
    elif anchors["skills_lit"] >= 5 or anchors["evidence_flying"] >= 4:
        lines.append(
            "星尘渐厚，小有财气；至于大富大贵，卦上说：且再攒攒（戏言）。"
        )
    else:
        lines.append(
            "星光尚微。大富大贵之卦，从点亮下一颗星官开始（戏言，勿尽信）。"
        )
    return "\n".join(lines)


def _rule_reading_serious(
    hexagram: dict[str, Any],
    question: str,
    gap_summary: dict[str, Any],
) -> str:
    lines = [f"所问「{question}」，卦得「{hexagram['name']}」。卦曰：{hexagram['judgment']}"]
    if not gap_summary or gap_summary.get("error"):
        lines.append(
            "然就星图实勘，此问与现有技能脉络尚无对应——卦象渺茫。"
            "或先把所问拆成小目标、积攒证据，再来问卦。"
        )
        return "\n".join(lines)
    if gap_summary.get("can_solve"):
        strong = "、".join(gap_summary.get("strong_labels") or []) or "诸般根基"
        lines.append(f"卦象曰可：星图所恃已足（{strong}），放胆去做，勿疑。")
        return "\n".join(lines)
    gap_labels = gap_summary.get("gap_labels") or []
    strong_labels = gap_summary.get("strong_labels") or []
    lines.append(
        f"卦象所示，所缺 {len(gap_labels)} 处：{'、'.join(gap_labels)}。"
        f"所恃者：{'、'.join(strong_labels) if strong_labels else '尚无——皆是新域'}。"
    )
    steps = []
    for node in gap_summary.get("closure") or []:
        if not node.get("is_gap"):
            continue
        status_zh = _STATUS_ZH.get(node.get("status", ""), node.get("status", ""))
        steps.append(f"先补「{node['label']}」（今{status_zh}）")
        if len(steps) >= 3:
            break
    if steps:
        lines.append(f"进路：{'；'.join(steps)}。卦辞为引，功夫在人。")
    return "\n".join(lines)


def _llm_payload(
    mode: str,
    question: str,
    hexagram: dict[str, Any],
    anchors: dict[str, Any],
    gap_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "mode": mode,
        "question": question,
        "reply_language": "zh",
        "hexagram": {
            "name": hexagram["name"],
            "king_wen": hexagram["king_wen"],
            "symbol_lines": [int(yao) for yao in hexagram["lines"]],
            "judgment_classical": hexagram["judgment"],
            "gloss": hexagram["gloss"],
        },
        "anchors": anchors,
        "gap": gap_summary,
        "llm_timeout_seconds": LLM_TIMEOUT_SECONDS,
        # Flash-tier model (王军 ruling: thinking stays on); the global
        # qwen3.6-plus thinks past the timeout on this action. No SDK
        # retries: a slow cast fails fast to the rule reading.
        "llm_model": os.getenv("NBLANE_DIVINATION_MODEL", "").strip()
        or LLM_MODEL_DEFAULT,
        "llm_max_retries": 0,
    }


def _default_runner(profile: str, payload: dict[str, Any]) -> Any:
    """Run the divination action through the AI gateway."""
    from nblane.core.ai.gateway import run_json

    return run_json(
        DIVINATION_ACTION,
        payload,
        profile=profile,
        require_review=False,
    )


def _llm_texts(result: Any) -> tuple[str, str] | None:
    """Extract (judgment, reading) from a gateway result, or None."""
    if not getattr(result, "ok", False):
        return None
    structured = getattr(result, "structured", None)
    if not isinstance(structured, dict):
        return None
    judgment = str(structured.get("judgment") or "").strip()
    reading = str(structured.get("reading") or "").strip()
    if not judgment or not reading:
        return None
    return judgment, reading


def cast_divination(
    pdir: Path,
    mode: str = MODE_PLAY,
    question: str = "",
    *,
    today: date | None = None,
    runner: Runner | None = None,
) -> dict[str, Any]:
    """Cast one 卦 for *pdir* and return the API-shaped payload.

    The hexagram is deterministic for (profile state, day, mode,
    question). Texts come from the LLM gateway when it succeeds
    (``source == "llm"``); otherwise the deterministic, data-anchored
    rule path answers (``source == "rule"``).
    """
    if mode not in MODES:
        raise ValueError(f"unknown divination mode: {mode!r}")
    today = today or date.today()
    question = (question or "").strip()[:QUESTION_MAX_LENGTH]

    snapshot = starmap_snapshot_core.build_starmap_snapshot(pdir, today=today)
    board = projects_board.build_projects_board(pdir)
    anchors = build_anchors(snapshot, board)
    hexagram = pick_hexagram(
        hexagram_material(pdir.name, mode, question, anchors, today)
    )

    gap_summary: dict[str, Any] = {}
    if mode == MODE_SERIOUS:
        gap_summary = run_gap_analysis(pdir.name, question)
        anchors["gap"] = gap_summary

    rule_judgment = _rule_judgment(hexagram)
    if mode == MODE_SERIOUS:
        rule_reading = _rule_reading_serious(hexagram, question, gap_summary)
    else:
        rule_reading = _rule_reading_play(hexagram, anchors)

    judgment, reading, source = rule_judgment, rule_reading, "rule"
    run = runner if runner is not None else _default_runner
    try:
        result = run(pdir.name, _llm_payload(mode, question, hexagram, anchors, gap_summary))
    except Exception:
        result = None
    texts = _llm_texts(result)
    if texts is not None:
        judgment, reading, source = texts[0], texts[1], "llm"

    hexagram_payload = _hexagram_payload(hexagram)
    hexagram_payload["judgment"] = judgment
    return {
        "profile": pdir.name,
        "mode": mode,
        "question": question,
        "hexagram": hexagram_payload,
        "reading": reading,
        "anchors": anchors,
        "source": source,
        "generated_on": today.isoformat(),
    }


__all__ = [
    "DIVINATION_ACTION",
    "HEXAGRAMS",
    "LLM_TIMEOUT_SECONDS",
    "MODES",
    "MODE_PLAY",
    "MODE_SERIOUS",
    "QUESTION_MAX_LENGTH",
    "build_anchors",
    "cast_divination",
    "hexagram_material",
    "pick_hexagram",
    "run_gap_analysis",
    "summarize_gap",
]
