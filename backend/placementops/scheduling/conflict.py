
"""Conflict detection for existing schedules."""

from __future__ import annotations

from .models import Conflict, Schedule, ScheduleAssignment


def _overlaps(
    first: ScheduleAssignment,
    second: ScheduleAssignment,
) -> bool:
    if first.day != second.day:
        return False

    return first.start_time < second.end_time and second.start_time < first.end_time


def detect_conflicts(schedule: Schedule) -> list[Conflict]:
    """Detect student, panel, and room overlaps in an existing schedule."""

    conflicts: list[Conflict] = []
    assignments = schedule.assignments

    for index, first in enumerate(assignments):
        for second in assignments[index + 1 :]:
            if not _overlaps(first, second):
                continue

            if first.student_id == second.student_id:
                conflicts.append(
                    Conflict(
                        conflict_type="STUDENT_OVERLAP",
                        interview_id=first.interview_id,
                        conflicting_interview_id=second.interview_id,
                        resource_id=first.student_id,
                        reason=(
                            f"Student {first.student_id} has overlapping interviews."
                        ),
                    )
                )

            if first.panel_id == second.panel_id:
                conflicts.append(
                    Conflict(
                        conflict_type="PANEL_OVERLAP",
                        interview_id=first.interview_id,
                        conflicting_interview_id=second.interview_id,
                        resource_id=first.panel_id,
                        reason=(
                            f"Panel {first.panel_id} has overlapping interviews."
                        ),
                    )
                )

            if first.room_id == second.room_id:
                conflicts.append(
                    Conflict(
                        conflict_type="ROOM_OVERLAP",
                        interview_id=first.interview_id,
                        conflicting_interview_id=second.interview_id,
                        resource_id=first.room_id,
                        reason=(
                            f"Room {first.room_id} has overlapping interviews."
                        ),
                    )
                )

    return conflicts


def has_conflicts(schedule: Schedule) -> bool:
    """Return True when the schedule contains at least one conflict."""

    return bool(detect_conflicts(schedule))
