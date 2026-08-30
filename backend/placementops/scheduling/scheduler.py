"""Deterministic scarcity-aware greedy scheduler for PlacementOps."""

from __future__ import annotations

from collections import Counter

from placementops.dataset.constants import PLACEMENT_DAYS, TIME_SLOTS
from placementops.dataset.models import Dataset, Interview
from placementops.scheduling.constraints import can_assign
from placementops.scheduling.models import Schedule, ScheduleAssignment


def generate_schedule(dataset: Dataset) -> Schedule:
    """Generate a deterministic schedule using best-candidate allocation."""

    students = {student.id: student for student in dataset.students}
    companies = {company.id: company for company in dataset.companies}

    available_panels = [
        panel
        for panel in dataset.panels
        if panel.status == "AVAILABLE"
    ]

    available_rooms = [
        room
        for room in dataset.rooms
        if room.status == "AVAILABLE"
    ]

    interviews = _order_interviews(
        dataset.interviews,
        students,
        companies,
        available_panels,
        available_rooms,
    )

    assignments: list[ScheduleAssignment] = []
    unscheduled: list[str] = []

    for interview in interviews:
        student = students.get(interview.student_id)
        company = companies.get(interview.company_id)

        if student is None or company is None:
            unscheduled.append(interview.id)
            continue

        candidates = _candidate_assignments(
            interview=interview,
            student=student,
            company=company,
            available_panels=available_panels,
            available_rooms=available_rooms,
            existing_assignments=assignments,
        )

        if not candidates:
            unscheduled.append(interview.id)
            continue

        candidates.sort(
            key=lambda candidate: _candidate_score(
                candidate,
                interview,
                assignments,
            )
        )

        assignments.append(candidates[0])

    return Schedule(
        assignments=assignments,
        unscheduled_interview_ids=unscheduled,
    )


def _order_interviews(
    interviews: list[Interview],
    students: dict[str, object],
    companies: dict[str, object],
    panels: list[object],
    rooms: list[object],
) -> list[Interview]:
    """Put the most constrained interviews first."""

    panel_counts = Counter(
        panel.company_id
        for panel in panels
    )

    room_count = len(rooms)

    priority_rank = {
        "P1": 1,
        "P2": 2,
        "P3": 3,
        "P4": 4,
    }

    def sort_key(interview: Interview) -> tuple:
        company = companies.get(interview.company_id)
        student = students.get(interview.student_id)

        if company is None or student is None:
            return (
                999999,
                999999,
                999999,
                999999,
                interview.id,
            )

        placement_days = len(company.placement_days)
        company_windows = len(company.availability)
        student_windows = len(student.availability)
        panel_count = panel_counts.get(company.id, 0)

        # Lower values mean fewer scheduling alternatives.
        scarcity_score = (
            placement_days
            * max(company_windows, 1)
            * max(student_windows, 1)
            * max(panel_count, 1)
            * max(room_count, 1)
        )

        return (
            scarcity_score,
            placement_days,
            company_windows,
            student_windows,
            panel_count,
            priority_rank.get(company.priority_tier, 99),
            -company.popularity_score,
            interview.id,
        )

    return sorted(interviews, key=sort_key)


def _candidate_assignments(
    *,
    interview: Interview,
    student: object,
    company: object,
    available_panels: list[object],
    available_rooms: list[object],
    existing_assignments: list[ScheduleAssignment],
) -> list[ScheduleAssignment]:
    """Generate all currently feasible assignments."""

    company_panels = [
        panel
        for panel in available_panels
        if panel.company_id == company.id
    ]

    candidates: list[ScheduleAssignment] = []

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

            for panel in company_panels:
                for room in available_rooms:
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

    return candidates


def _candidate_score(
    candidate: ScheduleAssignment,
    interview: Interview,
    existing_assignments: list[ScheduleAssignment],
) -> tuple:
    """Score a feasible candidate while preserving resource flexibility."""

    same_company_day = sum(
        1
        for assignment in existing_assignments
        if (
            assignment.company_id == candidate.company_id
            and assignment.day == candidate.day
        )
    )

    same_panel_day = sum(
        1
        for assignment in existing_assignments
        if (
            assignment.panel_id == candidate.panel_id
            and assignment.day == candidate.day
        )
    )

    same_room_day = sum(
        1
        for assignment in existing_assignments
        if (
            assignment.room_id == candidate.room_id
            and assignment.day == candidate.day
        )
    )

    same_student_day = sum(
        1
        for assignment in existing_assignments
        if (
            assignment.student_id == candidate.student_id
            and assignment.day == candidate.day
        )
    )

    # Prefer:
    # 1. Fewer interviews already assigned to this company/day.
    # 2. Less-used panels.
    # 3. Less-used rooms.
    # 4. Less-used student/day combinations.
    # 5. Earlier deterministic slots/resources.

    resource_load = (
        same_panel_day * 100
        + same_room_day * 10
        + same_student_day
    )

    return (
        same_company_day,
        resource_load,
        same_panel_day,
        same_room_day,
        same_student_day,
        candidate.day,
        candidate.start_time,
        candidate.panel_id,
        candidate.room_id,
        interview.id,
    )


def _add_minutes(
    start_time: str,
    duration_minutes: int,
) -> str | None:
    """Add minutes to an HH:MM time."""

    hour, minute = map(int, start_time.split(":"))

    total_minutes = (
        hour * 60
        + minute
        + duration_minutes
    )

    if total_minutes > 24 * 60 - 1:
        return None

    end_hour = total_minutes // 60
    end_minute = total_minutes % 60

    return f"{end_hour:02d}:{end_minute:02d}"