"""Compact learning/exercise check-ins for the Kanban page."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

import streamlit as st

from nblane.core.activity_log import (
    ACTIVITY_LOG_FILENAME,
    ActivityLog,
    ActivityLogParseError,
    Checkin,
    HabitTarget,
    add_activity_checkin,
    add_habit,
    delete_checkin,
    load as load_activity_log,
)
from nblane.web_shared import (
    assert_files_current,
    refresh_file_snapshots,
    stash_git_backup_results,
)

LEARNING_HABIT_ID = "learning"
EXERCISE_HABIT_ID = "exercise"
LEGACY_EXERCISE_HABIT_IDS = ("锻炼",)
WORKSPACE_HABIT_IDS = (LEARNING_HABIT_ID, EXERCISE_HABIT_ID)

EXERCISE_TYPES = (
    "running",
    "strength",
    "squat",
    "rowing",
    "mobility",
    "other",
)
EXERCISE_INTENSITIES = ("easy", "moderate", "hard")


def recent_day_window(
    *,
    today: date | None = None,
    days: int = 14,
) -> list[date]:
    """Return the recent day window ending at today."""
    if days <= 0:
        return []
    end = today or date.today()
    start = end - timedelta(days=days - 1)
    return [start + timedelta(days=offset) for offset in range(days)]


def month_day_window(year: int, month: int) -> list[date | None]:
    """Return a Monday-first 6x7 month grid with empty padding cells."""
    first = date(year, month, 1)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    month_days = [
        first + timedelta(days=offset)
        for offset in range((next_month - first).days)
    ]
    cells: list[date | None] = [None] * first.weekday()
    cells.extend(month_days)
    while len(cells) < 42:
        cells.append(None)
    return cells[:42]


def workspace_habit_refs(checkin: Checkin) -> set[str]:
    """Return workspace habit refs represented by one check-in."""
    raw_refs = {checkin.habit_id, *checkin.habits}
    refs = {str(ref).strip() for ref in raw_refs if str(ref).strip()}
    out: set[str] = set()
    if LEARNING_HABIT_ID in refs:
        out.add(LEARNING_HABIT_ID)
    if EXERCISE_HABIT_ID in refs or any(
        legacy in refs for legacy in LEGACY_EXERCISE_HABIT_IDS
    ):
        out.add(EXERCISE_HABIT_ID)
    return out


def workspace_habit_id(checkin: Checkin) -> str:
    """Return the primary workspace habit id for display."""
    refs = workspace_habit_refs(checkin)
    if LEARNING_HABIT_ID in refs:
        return LEARNING_HABIT_ID
    if EXERCISE_HABIT_ID in refs:
        return EXERCISE_HABIT_ID
    return ""


def daily_workspace_counts(
    activity: ActivityLog,
    days: list[date],
) -> dict[str, dict[str, int]]:
    """Return learning/exercise counts for selected days."""
    out = {
        day.isoformat(): {
            LEARNING_HABIT_ID: 0,
            EXERCISE_HABIT_ID: 0,
        }
        for day in days
    }
    selected = set(out)
    for checkin in activity.checkins:
        when = checkin_date(checkin)
        if when is None or when.isoformat() not in selected:
            continue
        bucket = out[when.isoformat()]
        for habit_id in workspace_habit_refs(checkin):
            bucket[habit_id] += 1
    return out


def checkin_date(checkin: Checkin) -> date | None:
    """Parse check-in date text."""
    try:
        return date.fromisoformat(str(checkin.date)[:10])
    except ValueError:
        return None


def checkins_for_day(activity: ActivityLog, day: date) -> list[Checkin]:
    """Return workspace check-ins for one day."""
    rows: list[Checkin] = []
    for checkin in activity.checkins:
        if checkin_date(checkin) != day:
            continue
        if workspace_habit_refs(checkin):
            rows.append(checkin)
    return sorted(rows, key=lambda item: item.id, reverse=True)


def _activity_log_path(profile_path: Path) -> Path:
    """Return the activity-log path for one profile."""
    return profile_path / ACTIVITY_LOG_FILENAME


def _refresh_activity(path: Path) -> None:
    """Refresh file snapshots and preserve Git backup notices."""
    refresh_file_snapshots([path])
    stash_git_backup_results()


def _show_activity_log_parse_error(
    exc: ActivityLogParseError,
    ui: dict[str, str] | None = None,
) -> None:
    """Show a stable UI error for a malformed activity log."""
    labels = ui or {}
    message = labels.get(
        "kb_activity_log_parse_error",
        "activity-log.yaml could not be parsed. Fix it before adding "
        "or deleting check-ins.",
    )
    error = getattr(st, "error", None)
    if callable(error):
        error(message)
    caption = getattr(st, "caption", None)
    if callable(caption):
        caption(str(exc.path))


def _mark_activity_unwritable(
    payload: dict[str, Any],
    exc: ActivityLogParseError,
) -> dict[str, Any]:
    """Annotate a calendar payload when activity-log writes are blocked."""
    payload["activity_log_writable"] = False
    payload["activity_log_error"] = str(exc)
    return payload


def _load_activity(profile: str, profile_path: Path) -> ActivityLog:
    """Load the profile activity log with a stable profile name."""
    log = load_activity_log(profile_path)
    if not log.profile:
        log.profile = profile
    return log


def _ensure_learning_habit(profile_path: Path) -> None:
    """Ensure the built-in learning habit exists."""
    add_habit(
        profile_path,
        "Learning",
        kind="learning",
        cadence="daily",
        target=HabitTarget(count=1.0, unit="session"),
        tags=["flow/habit", "habit/learning", "learning"],
        notes="Daily learning anchor.",
    )


def _ensure_exercise_habit(profile_path: Path) -> None:
    """Ensure the built-in exercise habit exists."""
    add_habit(
        profile_path,
        "Exercise",
        kind="health",
        cadence="daily",
        target=HabitTarget(count=1.0, unit="session"),
        tags=["flow/habit", "habit/exercise", "health"],
        notes="Daily movement anchor.",
    )


def _clean_lines(value: object) -> list[str]:
    """Return non-empty unique lines from text or a sequence."""
    out: list[str] = []
    seen: set[str] = set()
    if isinstance(value, (list, tuple, set)):
        raw_lines: list[str] = []
        for item in value:
            raw_lines.extend(str(item or "").splitlines())
    else:
        raw_lines = str(value or "").splitlines()
    for line in raw_lines:
        clean = line.strip()
        if not clean:
            continue
        key = clean.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(clean)
    return out


def _learning_summary(note: str, links: list[str]) -> str:
    """Build a compact learning check-in summary."""
    for line in _clean_lines(note):
        return line[:120]
    return links[0] if links else ""


def _exercise_type_label(value: str, ui: dict[str, str]) -> str:
    """Return display text for an exercise type."""
    return ui.get(
        f"kb_exercise_type_{value}",
        value.replace("_", " ").title(),
    )


def _exercise_intensity_label(value: str, ui: dict[str, str]) -> str:
    """Return display text for an exercise intensity."""
    return ui.get(f"kb_exercise_intensity_{value}", value.title())


def _count_text(day_counts: dict[str, int], ui: dict[str, str]) -> str:
    """Return compact count text for one date cell."""
    bits: list[str] = []
    learning = day_counts.get(LEARNING_HABIT_ID, 0)
    exercise = day_counts.get(EXERCISE_HABIT_ID, 0)
    if learning:
        bits.append(
            ui.get("kb_calendar_learning_short", "Learn {count}").format(
                count=learning
            )
        )
    if exercise:
        bits.append(
            ui.get("kb_calendar_exercise_short", "Exercise {count}").format(
                count=exercise
            )
        )
    return " · ".join(bits)


def _strip_count_text(day_counts: dict[str, int], ui: dict[str, str]) -> str:
    """Return very short count text for the horizontal strip."""
    bits: list[str] = []
    learning = day_counts.get(LEARNING_HABIT_ID, 0)
    exercise = day_counts.get(EXERCISE_HABIT_ID, 0)
    if learning:
        bits.append(
            ui.get("kb_checkin_strip_learning_short", "L{count}").format(
                count=learning
            )
        )
    if exercise:
        bits.append(
            ui.get("kb_checkin_strip_exercise_short", "E{count}").format(
                count=exercise
            )
        )
    return " ".join(bits)


def _day_popover_label(day: date, today: date, ui: dict[str, str]) -> str:
    """Return a short popover button label for a day."""
    if day == today:
        return ui.get("kb_checkin_today_short", "Today")
    return f"{day.day}"


def _weekday_labels(ui: dict[str, str]) -> list[str]:
    """Return seven weekday labels, Monday first."""
    labels = [
        item.strip()
        for item in ui.get(
            "kb_calendar_weekdays",
            "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
        ).split(",")
    ]
    if len(labels) != 7:
        return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return labels


def checkin_record_payload(
    checkin: Checkin,
    ui: dict[str, str],
) -> dict[str, Any]:
    """Serialize one workspace check-in for the custom board component."""
    kind = workspace_habit_id(checkin)
    return {
        "id": checkin.id,
        "date": checkin.date,
        "kind": kind,
        "label": _checkin_kind_label(checkin, ui),
        "detail": _checkin_detail(checkin, ui),
        "can_delete": bool(checkin.id),
    }


def checkin_calendar_payload_from_activity(
    activity: ActivityLog,
    ui: dict[str, str],
    *,
    today: date | None = None,
    days: int = 14,
) -> dict[str, Any]:
    """Return a compact 14-day calendar payload for the React shell."""
    current = today or date.today()
    window = recent_day_window(today=current, days=days)
    counts = daily_workspace_counts(activity, window)
    weekday_labels = _weekday_labels(ui)

    return {
        "title": ui.get("kb_checkin_strip_title", "Recent 14 days"),
        "today": current.isoformat(),
        "weekdays": weekday_labels,
        "days": [
            {
                "date": day.isoformat(),
                "day": day.day,
                "weekday": weekday_labels[day.weekday()],
                "is_today": day == current,
                "counts": counts[day.isoformat()],
                "marker_text": _strip_count_text(counts[day.isoformat()], ui),
                "summary": _count_text(counts[day.isoformat()], ui),
                "records": [
                    checkin_record_payload(checkin, ui)
                    for checkin in checkins_for_day(activity, day)
                ],
            }
            for day in window
        ],
        "exercise_types": [
            {"value": value, "label": _exercise_type_label(value, ui)}
            for value in EXERCISE_TYPES
        ],
        "exercise_intensities": [
            {"value": value, "label": _exercise_intensity_label(value, ui)}
            for value in EXERCISE_INTENSITIES
        ],
    }


def checkin_calendar_payload(
    profile: str,
    profile_path: Path,
    ui: dict[str, str],
    *,
    today: date | None = None,
    days: int = 14,
) -> dict[str, Any]:
    """Load activity-log.yaml and return the compact calendar payload."""
    try:
        activity = _load_activity(profile, profile_path)
    except ActivityLogParseError as exc:
        _show_activity_log_parse_error(exc, ui)
        return _mark_activity_unwritable(
            checkin_calendar_payload_from_activity(
                ActivityLog(profile=profile),
                ui,
                today=today,
                days=days,
            ),
            exc,
        )
    return checkin_calendar_payload_from_activity(
        activity,
        ui,
        today=today,
        days=days,
    )


def checkin_month_payload_from_activity(
    activity: ActivityLog,
    ui: dict[str, str],
    *,
    year: int,
    month: int,
    today: date | None = None,
) -> dict[str, Any]:
    """Return a compact month-grid payload for the toolbar calendar."""
    current = today or date.today()
    cells = month_day_window(year, month)
    month_days = [day for day in cells if day is not None]
    counts = daily_workspace_counts(activity, month_days)
    weekday_labels = _weekday_labels(ui)

    days: list[dict[str, Any] | None] = []
    for day in cells:
        if day is None:
            days.append(None)
            continue
        day_counts = counts[day.isoformat()]
        days.append(
            {
                "date": day.isoformat(),
                "day": day.day,
                "weekday": weekday_labels[day.weekday()],
                "is_today": day == current,
                "counts": day_counts,
                "marker_text": _strip_count_text(day_counts, ui),
                "summary": _count_text(day_counts, ui),
                "records": [
                    checkin_record_payload(checkin, ui)
                    for checkin in checkins_for_day(activity, day)
                ],
            }
        )

    return {
        "title": ui.get("kb_checkin_month_title", "Check-ins"),
        "month_label": f"{year:04d}-{month:02d}",
        "year": year,
        "month": month,
        "today": current.isoformat(),
        "weekdays": weekday_labels,
        "days": days,
        "weeks": [days[index : index + 7] for index in range(0, 42, 7)],
    }


def checkin_month_payload(
    profile: str,
    profile_path: Path,
    ui: dict[str, str],
    *,
    year: int,
    month: int,
    today: date | None = None,
) -> dict[str, Any]:
    """Load activity-log.yaml and return the toolbar month payload."""
    try:
        activity = _load_activity(profile, profile_path)
    except ActivityLogParseError as exc:
        _show_activity_log_parse_error(exc, ui)
        return _mark_activity_unwritable(
            checkin_month_payload_from_activity(
                ActivityLog(profile=profile),
                ui,
                year=year,
                month=month,
                today=today,
            ),
            exc,
        )
    return checkin_month_payload_from_activity(
        activity,
        ui,
        year=year,
        month=month,
        today=today,
    )


def _record_learning(
    profile_path: Path,
    *,
    when: date,
    note: str,
    links: list[str],
) -> None:
    """Persist one learning check-in."""
    _ensure_learning_habit(profile_path)
    add_activity_checkin(
        profile_path,
        LEARNING_HABIT_ID,
        when=when,
        count=1.0,
        unit="session",
        summary=_learning_summary(note, links),
        note=note,
        links=links,
        tags=["flow/habit", "habit/learning", "learning"],
    )


def _record_exercise(
    profile_path: Path,
    *,
    when: date,
    workout_type: str,
    duration_min: float,
    intensity: str,
    note: str,
) -> None:
    """Persist one exercise check-in."""
    _ensure_exercise_habit(profile_path)
    add_activity_checkin(
        profile_path,
        EXERCISE_HABIT_ID,
        when=when,
        count=1.0,
        unit="session",
        note=note,
        tags=[
            "flow/habit",
            "habit/exercise",
            "health",
            f"exercise/{workout_type}",
        ],
        workout_type=workout_type,
        duration_min=duration_min,
        intensity=intensity,
    )


def record_learning_checkin(
    profile_path: Path,
    *,
    when: date,
    note: str,
    links: list[str] | str,
) -> None:
    """Persist one learning check-in and refresh file state."""
    path = _activity_log_path(profile_path)
    try:
        assert_files_current([path])
        _record_learning(
            profile_path,
            when=when,
            note=str(note or "").strip(),
            links=_clean_lines(links),
        )
        _refresh_activity(path)
    except ActivityLogParseError as exc:
        _show_activity_log_parse_error(exc)


def record_exercise_checkin(
    profile_path: Path,
    *,
    when: date,
    workout_type: str,
    duration_min: float,
    intensity: str,
    note: str,
) -> None:
    """Persist one exercise check-in and refresh file state."""
    path = _activity_log_path(profile_path)
    try:
        assert_files_current([path])
        _record_exercise(
            profile_path,
            when=when,
            workout_type=str(workout_type or "").strip() or "other",
            duration_min=float(duration_min or 0.0),
            intensity=str(intensity or "").strip() or "moderate",
            note=str(note or "").strip(),
        )
        _refresh_activity(path)
    except ActivityLogParseError as exc:
        _show_activity_log_parse_error(exc)


def delete_workspace_checkin(
    profile_path: Path,
    checkin_id: str,
) -> bool:
    """Delete one workspace check-in by id and refresh file state."""
    path = _activity_log_path(profile_path)
    try:
        assert_files_current([path])
        deleted = delete_checkin(path, checkin_id)
        _refresh_activity(path)
        return deleted
    except ActivityLogParseError as exc:
        _show_activity_log_parse_error(exc)
        return False


def _checkin_kind_label(checkin: Checkin, ui: dict[str, str]) -> str:
    """Return display label for check-in habit."""
    habit_id = workspace_habit_id(checkin)
    if habit_id == LEARNING_HABIT_ID:
        return ui.get("kb_checkin_type_learning", "Learning")
    if habit_id == EXERCISE_HABIT_ID:
        return ui.get("kb_checkin_type_exercise", "Exercise")
    return habit_id or "-"


def _checkin_detail(checkin: Checkin, ui: dict[str, str]) -> str:
    """Return compact check-in detail text."""
    habit_id = workspace_habit_id(checkin)
    if habit_id == LEARNING_HABIT_ID:
        if checkin.summary:
            return checkin.summary
        if checkin.notes:
            return checkin.notes.splitlines()[0][:120]
        if checkin.links:
            return ui.get("kb_checkin_links_count", "{count} links").format(
                count=len(checkin.links)
            )
    if habit_id == EXERCISE_HABIT_ID:
        bits: list[str] = []
        if checkin.workout_type:
            bits.append(_exercise_type_label(checkin.workout_type, ui))
        if checkin.duration_min:
            bits.append(
                ui.get("kb_checkin_minutes", "{minutes:g} min").format(
                    minutes=checkin.duration_min
                )
            )
        if checkin.intensity:
            bits.append(_exercise_intensity_label(checkin.intensity, ui))
        if checkin.notes:
            bits.append(checkin.notes.splitlines()[0][:80])
        if bits:
            return " · ".join(bits)
    return ui.get("kb_checkin_detail_empty", "No details")


def _render_day_records(
    profile: str,
    profile_path: Path,
    records: list[Checkin],
    ui: dict[str, str],
) -> None:
    """Render deletable records inside one day popover."""
    st.caption(ui.get("kb_checkin_day_records", "Day records"))
    if not records:
        st.caption(
            ui.get(
                "kb_checkin_day_records_empty",
                "No learning/exercise records on this day.",
            )
        )
        return

    for index, checkin in enumerate(records):
        cols = st.columns([1.0, 3.0, 0.9])
        cols[0].caption(_checkin_kind_label(checkin, ui))
        cols[1].caption(_checkin_detail(checkin, ui))
        disabled = not bool(checkin.id)
        if cols[2].button(
            ui.get("kb_checkin_delete", "Delete"),
            key=f"kb_delete_checkin_{profile}_{checkin.id or index}",
            help=ui.get(
                "kb_checkin_delete_help",
                "Remove this check-in from activity-log.yaml.",
            ),
            disabled=disabled,
        ):
            path = _activity_log_path(profile_path)
            try:
                assert_files_current([path])
                deleted = delete_checkin(path, checkin.id)
                _refresh_activity(path)
            except ActivityLogParseError as exc:
                _show_activity_log_parse_error(exc, ui)
                return
            if deleted:
                st.success(ui.get("kb_checkin_deleted", "Check-in deleted."))
            else:
                st.warning(
                    ui.get(
                        "kb_checkin_delete_missing",
                        "That check-in was already gone.",
                    )
                )
            st.rerun()


def _render_learning_form(
    profile: str,
    profile_path: Path,
    day: date,
    ui: dict[str, str],
) -> None:
    """Render a compact learning form for one day."""
    with st.form(f"kb_learning_checkin_{profile}_{day.isoformat()}"):
        note = st.text_area(
            ui.get("kb_learning_checkin_note", "Learning note"),
            key=f"kb_learning_note_{profile}_{day.isoformat()}",
            height=80,
            placeholder=ui.get(
                "kb_learning_checkin_note_placeholder",
                "What did you study, and what is worth remembering?",
            ),
        )
        links_text = st.text_area(
            ui.get("kb_learning_checkin_links", "Links"),
            key=f"kb_learning_links_{profile}_{day.isoformat()}",
            height=58,
            placeholder=ui.get(
                "kb_learning_checkin_links_placeholder",
                "One link per line.",
            ),
        )
        submitted = st.form_submit_button(
            ui.get("kb_checkin_add_learning", "Add learning"),
            type="primary",
        )
    if not submitted:
        return

    links = _clean_lines(links_text)
    if not note.strip() and not links:
        st.warning(
            ui.get(
                "kb_learning_checkin_required",
                "Add a note or at least one link.",
            )
        )
        return
    path = _activity_log_path(profile_path)
    try:
        assert_files_current([path])
        _record_learning(
            profile_path,
            when=day,
            note=note.strip(),
            links=links,
        )
        _refresh_activity(path)
    except ActivityLogParseError as exc:
        _show_activity_log_parse_error(exc, ui)
        return
    st.success(ui.get("kb_checkin_saved", "Check-in saved."))


def _render_exercise_form(
    profile: str,
    profile_path: Path,
    day: date,
    ui: dict[str, str],
) -> None:
    """Render a compact exercise form for one day."""
    with st.form(f"kb_exercise_checkin_{profile}_{day.isoformat()}"):
        workout_type = st.selectbox(
            ui.get("kb_exercise_type", "Type"),
            list(EXERCISE_TYPES),
            format_func=lambda value: _exercise_type_label(value, ui),
            key=f"kb_exercise_type_{profile}_{day.isoformat()}",
        )
        duration_min = st.number_input(
            ui.get("kb_exercise_duration", "Duration (min)"),
            min_value=0.0,
            step=5.0,
            value=0.0,
            key=f"kb_exercise_duration_{profile}_{day.isoformat()}",
        )
        intensity = st.selectbox(
            ui.get("kb_exercise_intensity", "Intensity"),
            list(EXERCISE_INTENSITIES),
            format_func=lambda value: _exercise_intensity_label(value, ui),
            key=f"kb_exercise_intensity_{profile}_{day.isoformat()}",
        )
        note = st.text_area(
            ui.get("kb_capture_note", "Note"),
            key=f"kb_exercise_note_{profile}_{day.isoformat()}",
            height=58,
        )
        submitted = st.form_submit_button(
            ui.get("kb_checkin_add_exercise", "Add exercise"),
            type="primary",
        )
    if not submitted:
        return

    path = _activity_log_path(profile_path)
    try:
        assert_files_current([path])
        _record_exercise(
            profile_path,
            when=day,
            workout_type=workout_type,
            duration_min=float(duration_min),
            intensity=intensity,
            note=note.strip(),
        )
        _refresh_activity(path)
    except ActivityLogParseError as exc:
        _show_activity_log_parse_error(exc, ui)
        return
    st.success(ui.get("kb_checkin_saved", "Check-in saved."))


def _render_day_popover(
    profile: str,
    profile_path: Path,
    activity: ActivityLog,
    day: date,
    day_counts: dict[str, int],
    ui: dict[str, str],
) -> None:
    """Render records and add forms for one selected day."""
    count_text = _count_text(day_counts, ui)
    st.markdown(f"**{day.isoformat()}**")
    st.caption(count_text or ui.get("kb_checkin_no_marks", "No marks"))
    _render_day_records(
        profile,
        profile_path,
        checkins_for_day(activity, day),
        ui,
    )
    with st.expander(
        ui.get("kb_checkin_add_learning", "Add learning"),
        expanded=False,
    ):
        _render_learning_form(profile, profile_path, day, ui)
    with st.expander(
        ui.get("kb_checkin_add_exercise", "Add exercise"),
        expanded=False,
    ):
        _render_exercise_form(profile, profile_path, day, ui)


def render_checkin_strip(
    profile: str,
    profile_path: Path,
    ui: dict[str, str],
) -> None:
    """Render a compact 14-day check-in strip."""
    try:
        activity = _load_activity(profile, profile_path)
    except ActivityLogParseError as exc:
        _show_activity_log_parse_error(exc, ui)
        return
    today = date.today()
    days = recent_day_window(today=today, days=14)
    counts = daily_workspace_counts(activity, days)

    st.caption(ui.get("kb_checkin_strip_title", "Recent 14 days"))
    columns = st.columns(len(days), gap="small")
    for column, day in zip(columns, days):
        day_counts = counts[day.isoformat()]
        with column:
            label = _day_popover_label(day, today, ui)
            with st.popover(
                label,
                help=ui.get(
                    "kb_checkin_day_help",
                    "Open this day to add or delete check-ins.",
                ),
            ):
                _render_day_popover(
                    profile,
                    profile_path,
                    activity,
                    day,
                    day_counts,
                    ui,
                )
            text = _strip_count_text(day_counts, ui)
            st.caption(text if text else " ")


# Backward-compatible import for any older page code during development.
render_personal_workspace = render_checkin_strip
