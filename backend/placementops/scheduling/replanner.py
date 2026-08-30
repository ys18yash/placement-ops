"""Minimal-change replanning for PlacementOps schedules."""

from __future__ import annotations

from placementops.dataset.constants import PLACEMENT_DAYS, TIME_SLOTS
from placementops.dataset.models import Dataset
from placementops.scheduling.constraints import can_assign
from placementops.scheduling.models import (
    Disruption,
    Schedule,
    ScheduleAssignment,
    ScheduleChange,
)


def replan_schedule(
    dataset: Dataset,
    schedule: Schedule,
    disruption: Disruption,
) -> tuple[Schedule, list[ScheduleChange]]:
    """Replan affected assignments with deterministic cascading moves."""

    students = {student.id: student for student in dataset.students}
    companies = {company.id: company for company in dataset.companies}
    panels = {panel.id: panel for panel in dataset.panels}
    rooms = {room.id: room for room in dataset.rooms}
    interviews = {interview.id: interview for interview in dataset.interviews}

    affected = []
    unaffected = []

    for assignment in schedule.assignments:
        if _is_affected(assignment, disruption):
            affected.append(assignment)
        else:
            unaffected.append(assignment)

    affected.sort(key=lambda assignment: assignment.interview_id)

    assignments = list(unaffected)
    changes: list[ScheduleChange] = []

    for old_assignment in affected:
        interview = interviews.get(old_assignment.interview_id)

        if interview is None:
            changes.append(
                ScheduleChange(
                    interview_id=old_assignment.interview_id,
                    change_type="UNSCHEDULED",
                    old_assignment=old_assignment,
                    new_assignment=None,
                    reason="Interview no longer exists in the dataset.",
                )
            )
            continue

        student = students.get(interview.student_id)
        company = companies.get(interview.company_id)

        replacement = _find_replacement(
            interview=interview,
            student=student,
            company=company,
            panels=list(panels.values()),
            rooms=list(rooms.values()),
            existing_assignments=assignments,
            disruption=disruption,
        )

        if replacement is None:
            changes.append(
                ScheduleChange(
                    interview_id=old_assignment.interview_id,
                    change_type="UNSCHEDULED",
                    old_assignment=old_assignment,
                    new_assignment=None,
                    reason=_unscheduled_reason(disruption),
                )
            )
            continue

        assignments.append(replacement)

        changes.append(
            ScheduleChange(
                interview_id=old_assignment.interview_id,
                change_type=(
                    "UNCHANGED"
                    if replacement == old_assignment
                    else "RESCHEDULED"
                ),
                old_assignment=old_assignment,
                new_assignment=replacement,
                reason=(
                    "Original assignment remains feasible."
                    if replacement == old_assignment
                    else _change_reason(disruption)
                ),
            )
        )

    scheduled_ids = {a.interview_id for a in assignments}

    unscheduled_ids = [
        interview_id
        for interview_id in schedule.unscheduled_interview_ids
        if interview_id not in scheduled_ids
    ]

    for old_assignment in affected:
        if (
            old_assignment.interview_id not in scheduled_ids
            and old_assignment.interview_id not in unscheduled_ids
        ):
            unscheduled_ids.append(old_assignment.interview_id)

    return (
        Schedule(
            assignments=assignments,
            unscheduled_interview_ids=unscheduled_ids,
        ),
        changes,
    )


def _is_affected(
    assignment: ScheduleAssignment,
    disruption: Disruption,
) -> bool:
    """Determine whether an existing assignment is invalidated."""

    if disruption.type == "PANEL_DROPOUT":
        return (
            disruption.resource_id is not None
            and assignment.panel_id == disruption.resource_id
            and assignment.day == disruption.day
        )

    if disruption.type == "ROOM_UNAVAILABLE":
        return (
            disruption.resource_id is not None
            and assignment.room_id == disruption.resource_id
            and assignment.day == disruption.day
        )

    if disruption.type == "STUDENT_WITHDRAWAL":
        return (
            disruption.resource_id is not None
            and assignment.student_id == disruption.resource_id
            and assignment.day == disruption.day
        )

    if disruption.type == "COMPANY_DELAY":
        if assignment.company_id != disruption.resource_id:
            return False

        if assignment.day != disruption.day:
            return False

        if disruption.effective_time is None:
            return True

        return assignment.start_time >= disruption.effective_time

    return False


def _find_replacement(
    *,
    interview,
    student,
    company,
    panels,
    rooms,
    existing_assignments,
    disruption,
):
    """Find the first deterministic feasible replacement."""

    if student is None or company is None:
        return None

    available_panels = [
        panel
        for panel in panels
        if panel.company_id == company.id
        and panel.status == "AVAILABLE"
    ]

    available_rooms = [
        room
        for room in rooms
        if room.status == "AVAILABLE"
    ]

    candidates = []

    for day in PLACEMENT_DAYS:
        if day not in company.placement_days:
            continue

        for start_time in TIME_SLOTS:
            end_time = _add_minutes(
                start_time,
                interview.duration_minutes,
            )

            if end_time is None or end_time > "18:00":
                continue

            if (
                disruption.type == "COMPANY_DELAY"
                and disruption.day == day
                and disruption.effective_time is not None
                and start_time < disruption.effective_time
            ):
                continue

            for panel in available_panels:
                if (
                    disruption.type == "PANEL_DROPOUT"
                    and panel.id == disruption.resource_id
                    and day == disruption.day
                ):
                    continue

                for room in available_rooms:
                    if (
                        disruption.type == "ROOM_UNAVAILABLE"
                        and room.id == disruption.resource_id
                        and day == disruption.day
                    ):
                        continue

                    assignment = ScheduleAssignment(
                        interview_id=interview.id,
                        student_id=interview.student_id,
                        company_id=interview.company_id,
                        panel_id=panel.id,
                        room_id=room.id,
                        day=day,
                        start_time=start_time,
                        end_time=end_time,
                    )

                    result = can_assign(
                        assignment,
                        student=student,
                        company=company,
                        panel=panel,
                        room=room,
                        existing_assignments=existing_assignments,
                    )

                    if result.valid:
                        candidates.append(assignment)

    if not candidates:
        return None

    candidates.sort(
        key=lambda assignment: (
            assignment.day,
            assignment.start_time,
            assignment.panel_id,
            assignment.room_id,
        )
    )

    return candidates[0]


def _add_minutes(
    start_time: str,
    duration_minutes: int,
) -> str | None:
    """Add minutes to an HH:MM time."""

    hour, minute = map(int, start_time.split(":"))
    total_minutes = hour * 60 + minute + duration_minutes

    if total_minutes > 24 * 60 - 1:
        return None

    end_hour = total_minutes // 60
    end_minute = total_minutes % 60

    return f"{end_hour:02d}:{end_minute:02d}"


def _change_reason(disruption: Disruption) -> str:
    """Return a human-readable reason for a rescheduling change."""

    reasons = {
        "PANEL_DROPOUT": "Original panel was affected by a panel dropout.",
        "ROOM_UNAVAILABLE": "Original room became unavailable.",
        "STUDENT_WITHDRAWAL": "Student withdrawal affected the original assignment.",
        "COMPANY_DELAY": "Company delay affected the original assignment.",
    }

    return reasons.get(
        disruption.type,
        "Assignment was affected by a disruption.",
    )


def _unscheduled_reason(disruption: Disruption) -> str:
    """Return a human-readable reason when no replacement exists."""

    return (
        f"No feasible replacement was found after disruption "
        f"{disruption.type}."
    )