"""Deterministic scarcity-aware greedy scheduler for PlacementOps."""

from __future__ import annotations

from collections import Counter, defaultdict

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

    # Precompute valid slots per duration
    durations = {interview.duration_minutes for interview in interviews}
    slots_by_duration: dict[int, list[tuple[str, str, str]]] = {}
    for duration in durations:
        valid_slots = []
        for day in PLACEMENT_DAYS:
            for start_time in TIME_SLOTS:
                end_time = _add_minutes(start_time, duration)
                if end_time is not None and end_time <= "18:00":
                    valid_slots.append((day, start_time, end_time))
        slots_by_duration[duration] = valid_slots

    all_slots = {
        slot
        for slot_list in slots_by_duration.values()
        for slot in slot_list
    }

    # Precompute static availability sets
    student_avail: dict[str, set[tuple[str, str, str]]] = {
        student.id: {
            (d, s, e)
            for d, s, e in all_slots
            if _fits_any_window(d, s, e, student.availability)
        }
        for student in dataset.students
    }

    company_avail: dict[str, set[tuple[str, str, str]]] = {
        company.id: {
            (d, s, e)
            for d, s, e in all_slots
            if d in company.placement_days and _fits_any_window(d, s, e, company.availability)
        }
        for company in dataset.companies
    }

    panel_avail: dict[str, set[tuple[str, str, str]]] = {
        panel.id: {
            (d, s, e)
            for d, s, e in all_slots
            if _fits_any_window(d, s, e, panel.availability)
        }
        for panel in available_panels
    }

    room_avail: dict[str, set[tuple[str, str, str]]] = {
        room.id: {
            (d, s, e)
            for d, s, e in all_slots
            if _fits_any_window(d, s, e, room.availability)
        }
        for room in available_rooms
    }

    panels_by_company: dict[str, list[object]] = defaultdict(list)
    for panel in available_panels:
        panels_by_company[panel.company_id].append(panel)

    # Dynamic occupancy tracking: (resource_id, day) -> list of (start_time, end_time)
    student_busy: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    panel_busy: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    room_busy: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)

    # Incremental score counters: (id, day) -> count
    company_day_counts: dict[tuple[str, str], int] = defaultdict(int)
    panel_day_counts: dict[tuple[str, str], int] = defaultdict(int)
    room_day_counts: dict[tuple[str, str], int] = defaultdict(int)
    student_day_counts: dict[tuple[str, str], int] = defaultdict(int)

    assignments: list[ScheduleAssignment] = []
    unscheduled: list[str] = []

    for interview in interviews:
        student = students.get(interview.student_id)
        company = companies.get(interview.company_id)

        if student is None or company is None:
            unscheduled.append(interview.id)
            continue

        company_panels = panels_by_company.get(company.id, [])
        if not company_panels:
            unscheduled.append(interview.id)
            continue

        candidate_slots = slots_by_duration.get(interview.duration_minutes, [])
        c_avail = company_avail[company.id]
        s_avail = student_avail[student.id]

        best_score = None
        best_candidate: tuple[object, object, str, str, str] | None = None

        for day, start_time, end_time in candidate_slots:
            slot_tuple = (day, start_time, end_time)

            if slot_tuple not in c_avail:
                continue

            if slot_tuple not in s_avail:
                continue

            # Student conflict check
            s_busy_list = student_busy.get((student.id, day))
            if s_busy_list:
                has_s_conflict = False
                for s, e in s_busy_list:
                    if start_time < e and s < end_time:
                        has_s_conflict = True
                        break
                if has_s_conflict:
                    continue

            # Filter valid panels for this slot
            valid_panels = []
            for panel in company_panels:
                if slot_tuple not in panel_avail[panel.id]:
                    continue
                p_busy_list = panel_busy.get((panel.id, day))
                if p_busy_list:
                    has_p_conflict = False
                    for s, e in p_busy_list:
                        if start_time < e and s < end_time:
                            has_p_conflict = True
                            break
                    if has_p_conflict:
                        continue
                valid_panels.append(panel)

            if not valid_panels:
                continue

            # Filter valid rooms for this slot
            valid_rooms = []
            for room in available_rooms:
                if slot_tuple not in room_avail[room.id]:
                    continue
                r_busy_list = room_busy.get((room.id, day))
                if r_busy_list:
                    has_r_conflict = False
                    for s, e in r_busy_list:
                        if start_time < e and s < end_time:
                            has_r_conflict = True
                            break
                    if has_r_conflict:
                        continue
                valid_rooms.append(room)

            if not valid_rooms:
                continue

            same_company_day = company_day_counts[(company.id, day)]
            same_student_day = student_day_counts[(student.id, day)]

            # Generate and score candidates in exact nested order: panels -> rooms
            for panel in valid_panels:
                same_panel_day = panel_day_counts[(panel.id, day)]
                panel_load = same_panel_day * 100 + same_student_day

                for room in valid_rooms:
                    same_room_day = room_day_counts[(room.id, day)]
                    resource_load = panel_load + same_room_day * 10

                    score = (
                        same_company_day,
                        resource_load,
                        same_panel_day,
                        same_room_day,
                        same_student_day,
                        day,
                        start_time,
                        panel.id,
                        room.id,
                        interview.id,
                    )

                    if best_score is None or score < best_score:
                        best_score = score
                        best_candidate = (panel, room, day, start_time, end_time)

        if best_candidate is None:
            unscheduled.append(interview.id)
            continue

        panel, room, day, start_time, end_time = best_candidate
        assignment = ScheduleAssignment(
            interview_id=interview.id,
            student_id=student.id,
            company_id=company.id,
            panel_id=panel.id,
            room_id=room.id,
            day=day,
            start_time=start_time,
            end_time=end_time,
        )

        assignments.append(assignment)

        # Update dynamic state
        student_busy[(student.id, day)].append((start_time, end_time))
        panel_busy[(panel.id, day)].append((start_time, end_time))
        room_busy[(room.id, day)].append((start_time, end_time))

        company_day_counts[(company.id, day)] += 1
        student_day_counts[(student.id, day)] += 1
        panel_day_counts[(panel.id, day)] += 1
        room_day_counts[(room.id, day)] += 1

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