"""Constraint checks for PlacementOps scheduling."""

from __future__ import annotations

from dataclasses import dataclass

from placementops.dataset.models import (
    Company,
    Panel,
    Room,
    Student,
)
from placementops.scheduling.models import ScheduleAssignment


@dataclass(slots=True, frozen=True)
class ConstraintResult:
    """Result of evaluating a scheduling constraint."""

    valid: bool
    reason: str | None = None


def can_assign(
    assignment: ScheduleAssignment,
    *,
    student: Student,
    company: Company,
    panel: Panel,
    room: Room,
    existing_assignments: list[ScheduleAssignment] | None = None,
) -> ConstraintResult:
    """Check whether an interview assignment satisfies scheduling constraints."""

    res = _check_day_and_time(assignment)
    if not res.valid:
        return res

    res = _check_student_availability(assignment, student)
    if not res.valid:
        return res

    res = _check_company_availability(assignment, company)
    if not res.valid:
        return res

    res = _check_panel_availability(assignment, panel)
    if not res.valid:
        return res

    res = _check_room_availability(assignment, room)
    if not res.valid:
        return res

    res = _check_panel_status(panel)
    if not res.valid:
        return res

    res = _check_room_status(room)
    if not res.valid:
        return res

    res = _check_existing_conflicts(
        assignment,
        existing_assignments or [],
    )
    if not res.valid:
        return res

    return ConstraintResult(valid=True)


def _check_day_and_time(
    assignment: ScheduleAssignment,
) -> ConstraintResult:
    if assignment.day not in {"DAY_1", "DAY_2", "DAY_3", "DAY_4"}:
        return ConstraintResult(
            False,
            f"Invalid placement day: {assignment.day}.",
        )

    if not _is_valid_time(assignment.start_time):
        return ConstraintResult(
            False,
            f"Invalid start time: {assignment.start_time}.",
        )

    if not _is_valid_time(assignment.end_time):
        return ConstraintResult(
            False,
            f"Invalid end time: {assignment.end_time}.",
        )

    if assignment.start_time >= assignment.end_time:
        return ConstraintResult(
            False,
            "Assignment start time must be before end time.",
        )

    if assignment.start_time < "09:00" or assignment.end_time > "18:00":
        return ConstraintResult(
            False,
            "Assignment must be within operating hours 09:00-18:00.",
        )

    return ConstraintResult(True)


def _check_student_availability(
    assignment: ScheduleAssignment,
    student: Student,
) -> ConstraintResult:
    if not _fits_any_window(
        assignment.day,
        assignment.start_time,
        assignment.end_time,
        student.availability,
    ):
        return ConstraintResult(
            False,
            f"Student {student.id} is unavailable for the proposed slot.",
        )

    return ConstraintResult(True)


def _check_company_availability(
    assignment: ScheduleAssignment,
    company: Company,
) -> ConstraintResult:
    if assignment.day not in company.placement_days:
        return ConstraintResult(
            False,
            f"Company {company.id} is not available on {assignment.day}.",
        )

    if not _fits_any_window(
        assignment.day,
        assignment.start_time,
        assignment.end_time,
        company.availability,
    ):
        return ConstraintResult(
            False,
            f"Company {company.id} is unavailable for the proposed slot.",
        )

    return ConstraintResult(True)


def _check_panel_availability(
    assignment: ScheduleAssignment,
    panel: Panel,
) -> ConstraintResult:
    if not _fits_any_window(
        assignment.day,
        assignment.start_time,
        assignment.end_time,
        panel.availability,
    ):
        return ConstraintResult(
            False,
            f"Panel {panel.id} is unavailable for the proposed slot.",
        )

    return ConstraintResult(True)


def _check_room_availability(
    assignment: ScheduleAssignment,
    room: Room,
) -> ConstraintResult:
    if not _fits_any_window(
        assignment.day,
        assignment.start_time,
        assignment.end_time,
        room.availability,
    ):
        return ConstraintResult(
            False,
            f"Room {room.id} is unavailable for the proposed slot.",
        )

    return ConstraintResult(True)


def _check_panel_status(
    panel: Panel,
) -> ConstraintResult:
    if panel.status != "AVAILABLE":
        return ConstraintResult(
            False,
            f"Panel {panel.id} is not available.",
        )

    return ConstraintResult(True)


def _check_room_status(
    room: Room,
) -> ConstraintResult:
    if room.status != "AVAILABLE":
        return ConstraintResult(
            False,
            f"Room {room.id} is not available.",
        )

    return ConstraintResult(True)


def _check_existing_conflicts(
    assignment: ScheduleAssignment,
    existing_assignments: list[ScheduleAssignment],
) -> ConstraintResult:
    for existing in existing_assignments:
        if existing.day != assignment.day:
            continue

        if not _times_overlap(
            assignment.start_time,
            assignment.end_time,
            existing.start_time,
            existing.end_time,
        ):
            continue

        if existing.student_id == assignment.student_id:
            return ConstraintResult(
                False,
                f"Student {assignment.student_id} has an overlapping interview.",
            )

        if existing.panel_id == assignment.panel_id:
            return ConstraintResult(
                False,
                f"Panel {assignment.panel_id} has an overlapping interview.",
            )

        if existing.room_id == assignment.room_id:
            return ConstraintResult(
                False,
                f"Room {assignment.room_id} has an overlapping interview.",
            )

    return ConstraintResult(True)


def _fits_any_window(
    day: str,
    start_time: str,
    end_time: str,
    windows: list[object],
) -> bool:
    for window in windows:
        if (
            window.day == day
            and window.start_time <= start_time
            and end_time <= window.end_time
        ):
            return True

    return False


def _times_overlap(
    start_a: str,
    end_a: str,
    start_b: str,
    end_b: str,
) -> bool:
    return start_a < end_b and start_b < end_a


def _is_valid_time(value: str) -> bool:
    if not isinstance(value, str) or len(value) != 5 or value[2] != ":":
        return False

    hour, minute = value.split(":")

    return (
        hour.isdigit()
        and minute.isdigit()
        and 0 <= int(hour) <= 23
        and minute in {"00", "15", "30", "45"}
    )
