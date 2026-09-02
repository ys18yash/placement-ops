"""Metrics for evaluating PlacementOps schedules."""

from __future__ import annotations

from collections import defaultdict

from placementops.dataset.models import Dataset
from placementops.scheduling.models import Schedule


def calculate_schedule_metrics(
    dataset: Dataset,
    schedule: Schedule,
) -> dict[str, object]:
    """Calculate deterministic quality metrics for a generated schedule."""

    total_interviews = len(dataset.interviews)
    scheduled = len(schedule.assignments)
    unscheduled = len(schedule.unscheduled_interview_ids)

    completion_rate = (
        scheduled / total_interviews
        if total_interviews
        else 0.0
    )

    room_utilization = _calculate_room_utilization(
        dataset,
        schedule,
    )

    panel_utilization = _calculate_panel_utilization(
        dataset,
        schedule,
    )

    schedule_span = _calculate_schedule_span(schedule)

    return {
        "total_interviews": total_interviews,
        "scheduled_interviews": scheduled,
        "unscheduled_interviews": unscheduled,
        "completion_rate": round(completion_rate, 4),
        "room_utilization": round(room_utilization, 4),
        "panel_utilization": round(panel_utilization, 4),
        "schedule_span": schedule_span,
    }


def _calculate_room_utilization(
    dataset: Dataset,
    schedule: Schedule,
) -> float:
    total_available_minutes = sum(
        _window_minutes(room.availability)
        for room in dataset.rooms
        if room.status == "AVAILABLE"
    )

    if total_available_minutes == 0:
        return 0.0

    scheduled_minutes = sum(
        _duration_minutes(
            assignment.start_time,
            assignment.end_time,
        )
        for assignment in schedule.assignments
    )

    return scheduled_minutes / total_available_minutes


def _calculate_panel_utilization(
    dataset: Dataset,
    schedule: Schedule,
) -> float:
    available_panels = {
        panel.id: panel
        for panel in dataset.panels
        if panel.status == "AVAILABLE"
    }

    total_available_minutes = sum(
        _window_minutes(panel.availability)
        for panel in available_panels.values()
    )

    if total_available_minutes == 0:
        return 0.0

    scheduled_minutes = sum(
        _duration_minutes(
            assignment.start_time,
            assignment.end_time,
        )
        for assignment in schedule.assignments
        if assignment.panel_id in available_panels
    )

    return scheduled_minutes / total_available_minutes


def _calculate_schedule_span(schedule: Schedule) -> dict[str, object]:
    by_day: dict[str, list[object]] = defaultdict(list)

    for assignment in schedule.assignments:
        by_day[assignment.day].append(assignment)

    day_spans: dict[str, int] = {}

    for day, assignments in by_day.items():
        start = min(
            assignment.start_time
            for assignment in assignments
        )
        end = max(
            assignment.end_time
            for assignment in assignments
        )

        day_spans[day] = _duration_minutes(start, end)

    return {
        "days_used": len(day_spans),
        "total_minutes": sum(day_spans.values()),
        "by_day": dict(sorted(day_spans.items())),
    }


def _window_minutes(windows: list[object]) -> int:
    total = 0

    for window in windows:
        total += _duration_minutes(
            window.start_time,
            window.end_time,
        )

    return total


def _duration_minutes(start_time: str, end_time: str) -> int:
    start_hour, start_minute = map(int, start_time.split(":"))
    end_hour, end_minute = map(int, end_time.split(":"))

    return (
        end_hour * 60
        + end_minute
        - start_hour * 60
        - start_minute
    )

def calculate_replanning_metrics(
    original_schedule: Schedule,
    replanned_schedule: Schedule,
    changes: list[object],
) -> dict[str, object]:
    """Measure how much an existing schedule changed after replanning."""

    original_scheduled = len(original_schedule.assignments)
    replanned_scheduled = len(replanned_schedule.assignments)
    original_unscheduled = len(original_schedule.unscheduled_interview_ids)
    replanned_unscheduled = len(replanned_schedule.unscheduled_interview_ids)

    unchanged_interviews = sum(
        1
        for change in changes
        if getattr(change, "change_type", None) == "UNCHANGED"
    )
    moved_interviews = sum(
        1
        for change in changes
        if getattr(change, "change_type", None) == "RESCHEDULED"
    )
    affected_interviews = len(changes)
    newly_unscheduled_interviews = len(
        set(replanned_schedule.unscheduled_interview_ids)
        - set(original_schedule.unscheduled_interview_ids)
    )
    schedule_change_count = (
        moved_interviews + newly_unscheduled_interviews
    )

    change_rate = (
        schedule_change_count / original_scheduled
        if original_scheduled
        else 0.0
    )

    completion_rate_before = _completion_rate(
        original_scheduled,
        original_scheduled + original_unscheduled,
    )

    completion_rate_after = _completion_rate(
        replanned_scheduled,
        replanned_scheduled + replanned_unscheduled,
    )

    return {
        "original_scheduled": original_scheduled,
        "replanned_scheduled": replanned_scheduled,
        "original_unscheduled": original_unscheduled,
        "replanned_unscheduled": replanned_unscheduled,
        "affected_interviews": affected_interviews,
        "unchanged_interviews": unchanged_interviews,
        "moved_interviews": moved_interviews,
        "newly_unscheduled_interviews": newly_unscheduled_interviews,
        "schedule_change_count": schedule_change_count,
        "change_rate": round(change_rate, 4),
        "completion_rate_before": round(completion_rate_before, 4),
        "completion_rate_after": round(completion_rate_after, 4),
    }


def _completion_rate(scheduled: int, total: int) -> float:
    if total == 0:
        return 0.0

    return scheduled / total
