"""Deterministic correlated dataset generation."""

from __future__ import annotations

import math
import random
from collections import Counter, defaultdict

from .constants import (
    BUILDINGS,
    COMPANY_COUNT,
    COMPANY_TEMPLATES,
    DEFAULT_SEED,
    FIRST_NAMES,
    LAST_NAMES,
    PLACEMENT_DAYS,
    ROOM_COUNT,
    STUDENT_COUNT,
)
from .models import AvailabilityWindow, Company, Dataset, Interview, Panel, Room, Shortlist, Student

BRANCH_WEIGHTS = {
    "CSE": 0.23,
    "IT": 0.16,
    "ECE": 0.16,
    "EEE": 0.10,
    "ME": 0.12,
    "CE": 0.08,
    "AI": 0.08,
    "DS": 0.07,
}

BRANCH_CGPA_OFFSETS = {
    "CSE": 0.18,
    "IT": 0.11,
    "ECE": 0.08,
    "EEE": -0.04,
    "ME": -0.08,
    "CE": -0.12,
    "AI": 0.22,
    "DS": 0.16,
}

BRANCH_MARKET_FACTORS = {
    "CSE": 1.08,
    "IT": 1.05,
    "ECE": 1.02,
    "EEE": 0.97,
    "ME": 0.95,
    "CE": 0.92,
    "AI": 1.09,
    "DS": 1.08,
}


def generate_dataset(seed: int = DEFAULT_SEED) -> Dataset:
    rng = random.Random(seed)
    companies = _generate_companies(rng)
    students, student_scores = _generate_students(rng)
    rooms = _generate_rooms(rng)
    panels = _generate_panels(rng, companies)
    shortlists = _generate_shortlists(rng, companies, students, student_scores, rooms, panels)
    interviews = _generate_interviews(companies, shortlists)
    return Dataset(
        seed=seed,
        companies=companies,
        students=students,
        rooms=rooms,
        panels=panels,
        shortlists=shortlists,
        interviews=interviews,
        supported_disruptions=[
            "COMPANY_DELAY",
            "PANEL_DROPOUT",
            "STUDENT_WITHDRAWAL",
            "ROOM_UNAVAILABILITY",
        ],
    )


def _generate_companies(rng: random.Random) -> list[Company]:
    templates = list(COMPANY_TEMPLATES)
    assert len(templates) == COMPANY_COUNT

    popularity_sorted = sorted(templates, key=lambda item: item.popularity, reverse=True)
    day_one_names = {item.name for item in popularity_sorted[:10]}
    companies: list[Company] = []

    for index, template in enumerate(templates, start=1):
        popularity = min(max(template.popularity + rng.uniform(-0.03, 0.03), 0.35), 0.99)
        cutoff = round(min(max(template.cutoff_base + rng.uniform(-0.25, 0.15), 6.2), 8.8), 2)
        duration = _choose_duration(rng, template.duration_options, popularity)
        priority_tier = _priority_tier_for_popularity(popularity)
        day_count = _company_day_count(rng, popularity)
        placement_days = _pick_company_days(rng, day_count, force_day_one=template.name in day_one_names)
        panel_count = _panel_count_for_company(rng, popularity, duration, len(placement_days))
        availability = _company_availability(rng, placement_days, popularity)
        companies.append(
            Company(
                id=f"COMP{index:03d}",
                name=template.name,
                industry=template.industry,
                priority_tier=priority_tier,
                cgpa_cutoff=cutoff,
                interview_duration_minutes=duration,
                panel_count=panel_count,
                placement_days=placement_days,
                availability=availability,
                popularity_score=int(round(popularity * 100)),
            )
        )
    return companies


def _generate_students(rng: random.Random) -> tuple[list[Student], dict[str, float]]:
    students: list[Student] = []
    market_scores: dict[str, float] = {}
    branch_names = list(BRANCH_WEIGHTS)
    branch_weights = [BRANCH_WEIGHTS[name] for name in branch_names]

    for index in range(1, STUDENT_COUNT + 1):
        branch = rng.choices(branch_names, weights=branch_weights, k=1)[0]
        cgpa = _sample_cgpa(rng, branch)
        status = "WITHDRAWN" if rng.random() < 0.03 else "ACTIVE"
        name = f"{FIRST_NAMES[(index - 1) % len(FIRST_NAMES)]} {LAST_NAMES[(index * 3) % len(LAST_NAMES)]}"
        availability = _student_availability(rng, index)
        student_id = f"STU{index:04d}"
        students.append(
            Student(
                id=student_id,
                name=name,
                branch=branch,
                cgpa=cgpa,
                status=status,
                availability=availability,
            )
        )
        cgpa_signal = (cgpa - 5.0) / 5.0
        communication = 0.65 + rng.random() * 0.35
        market_scores[student_id] = round(
            cgpa_signal * 0.7 + communication * 0.18 + BRANCH_MARKET_FACTORS[branch] * 0.12,
            6,
        )

    return students, market_scores


def _generate_rooms(rng: random.Random) -> list[Room]:
    rooms: list[Room] = []
    for index in range(1, ROOM_COUNT + 1):
        building = BUILDINGS[(index - 1) % len(BUILDINGS)]
        floor = ((index - 1) % 5) + 1
        capacity = 4 + ((index * 3) % 11)
        rooms.append(
            Room(
                id=f"ROOM{index:03d}",
                name=f"Interview Room {index:02d}",
                building=building,
                floor=floor,
                capacity=capacity,
                availability=_room_availability(index),
                status="AVAILABLE",
            )
        )
    return rooms


def _generate_panels(rng: random.Random, companies: list[Company]) -> list[Panel]:
    panels: list[Panel] = []
    for company in companies:
        for panel_index in range(1, company.panel_count + 1):
            panels.append(
                Panel(
                    id=f"PANEL-{company.id}-{panel_index:02d}",
                    company_id=company.id,
                    name=f"{company.name} Panel {panel_index}",
                    availability=_panel_availability(company, panel_index),
                    status="AVAILABLE",
                )
            )
    return panels


def _generate_shortlists(
    rng: random.Random,
    companies: list[Company],
    students: list[Student],
    student_scores: dict[str, float],
    rooms: list[Room],
    panels: list[Panel],
) -> list[Shortlist]:
    active_students = [student for student in students if student.status == "ACTIVE"]
    company_targets = _company_shortlist_targets(rng, companies, active_students, rooms, panels)
    eligible_companies_by_student: dict[str, list[Company]] = {}
    eligible_students_by_company: dict[str, list[Student]] = {}
    for student in active_students:
        eligible_companies_by_student[student.id] = [
            company for company in companies if _is_student_eligible_for_company(student, company)
        ]
    for company in companies:
        eligible_students_by_company[company.id] = [
            student for student in active_students if _is_student_eligible_for_company(student, company)
        ]

    remaining_slots = dict(company_targets)
    shortlists: list[Shortlist] = []
    shortlist_counter = 1
    student_shortlist_counts: Counter[str] = Counter()
    student_company_pairs: set[tuple[str, str]] = set()
    company_templates = {template.name: template for template in COMPANY_TEMPLATES}

    coverage_order = sorted(
        active_students,
        key=lambda student: (len(eligible_companies_by_student[student.id]), -student.cgpa, student.id),
    )
    for student in coverage_order:
        companies_for_student = [
            company for company in eligible_companies_by_student[student.id] if remaining_slots[company.id] > 0
        ]
        if not companies_for_student:
            continue
        coverage_chance = min(0.92, 0.48 + max(0.0, student.cgpa - 6.4) * 0.18 + len(companies_for_student) * 0.01)
        if rng.random() > coverage_chance:
            continue
        weights = []
        for company in companies_for_student:
            template = company_templates[company.name]
            weights.append(
                _shortlist_weight(
                    rng=rng,
                    student=student,
                    company=company,
                    student_score=student_scores[student.id],
                    preferred_branches=template.preferred_branches,
                    existing_shortlists=student_shortlist_counts[student.id],
                    coverage_mode=True,
                )
            )
        selected_company = companies_for_student[_weighted_choice(rng, weights)]
        pair = (student.id, selected_company.id)
        if pair in student_company_pairs:
            continue
        shortlists.append(
            Shortlist(
                id=f"SHORT{shortlist_counter:05d}",
                student_id=student.id,
                company_id=selected_company.id,
            )
        )
        shortlist_counter += 1
        student_company_pairs.add(pair)
        student_shortlist_counts[student.id] += 1
        remaining_slots[selected_company.id] -= 1

    selection_order = sorted(
        companies,
        key=lambda company: (
            company.popularity_score,
            company.panel_count,
            len(company.placement_days),
            -company.cgpa_cutoff,
        ),
        reverse=True,
    )
    for company in selection_order:
        template = company_templates[company.name]
        while remaining_slots[company.id] > 0:
            remaining_students = [
                student
                for student in eligible_students_by_company[company.id]
                if (student.id, company.id) not in student_company_pairs
            ]
            if not remaining_students:
                break
            weights = [
                _shortlist_weight(
                    rng=rng,
                    student=student,
                    company=company,
                    student_score=student_scores[student.id],
                    preferred_branches=template.preferred_branches,
                    existing_shortlists=student_shortlist_counts[student.id],
                    coverage_mode=False,
                )
                for student in remaining_students
            ]
            selected_student = remaining_students[_weighted_choice(rng, weights)]
            shortlists.append(
                Shortlist(
                    id=f"SHORT{shortlist_counter:05d}",
                    student_id=selected_student.id,
                    company_id=company.id,
                )
            )
            shortlist_counter += 1
            student_company_pairs.add((selected_student.id, company.id))
            student_shortlist_counts[selected_student.id] += 1
            remaining_slots[company.id] -= 1

    return shortlists


def _generate_interviews(companies: list[Company], shortlists: list[Shortlist]) -> list[Interview]:
    company_durations = {company.id: company.interview_duration_minutes for company in companies}
    interviews: list[Interview] = []
    for index, shortlist in enumerate(shortlists, start=1):
        interviews.append(
            Interview(
                id=f"INT{index:05d}",
                student_id=shortlist.student_id,
                company_id=shortlist.company_id,
                duration_minutes=company_durations[shortlist.company_id],
                status="UNSCHEDULED",
            )
        )
    return interviews


def _priority_tier_for_popularity(popularity: float) -> str:
    if popularity >= 0.86:
        return "P1"
    if popularity >= 0.71:
        return "P2"
    if popularity >= 0.56:
        return "P3"
    return "P4"


def _pick_company_days(rng: random.Random, day_count: int, force_day_one: bool) -> list[str]:
    available_days = list(PLACEMENT_DAYS)
    selected: list[str] = []
    if force_day_one:
        selected.append("DAY_1")
        available_days.remove("DAY_1")
    while len(selected) < day_count:
        choice = rng.choice(available_days)
        available_days.remove(choice)
        selected.append(choice)
    selected.sort(key=PLACEMENT_DAYS.index)
    return selected


def _panel_count_for_company(rng: random.Random, popularity: float, duration: int, day_count: int) -> int:
    raw = 0.95 + popularity * 2.1 + (day_count - 1) * 0.45 - (duration - 30) / 90.0 + rng.uniform(-0.3, 0.3)
    return max(1, min(4, int(round(raw))))


def _sample_cgpa(rng: random.Random, branch: str) -> float:
    band = rng.random()
    if band < 0.18:
        base = rng.gauss(6.35, 0.45)
    elif band < 0.73:
        base = rng.gauss(7.35, 0.52)
    else:
        base = rng.gauss(8.42, 0.43)
    adjusted = min(max(base + BRANCH_CGPA_OFFSETS[branch], 5.0), 9.95)
    return round(adjusted, 2)


def _choose_duration(rng: random.Random, options: tuple[int, ...], popularity: float) -> int:
    if len(options) == 1:
        return options[0]
    ordered = sorted(options)
    if popularity >= 0.8 and rng.random() < 0.72:
        return ordered[0]
    if popularity < 0.55 and rng.random() < 0.58:
        return ordered[-1]
    return rng.choice(ordered)


def _company_day_count(rng: random.Random, popularity: float) -> int:
    if popularity >= 0.86:
        return 2
    if popularity >= 0.74:
        return 2 if rng.random() < 0.7 else 1
    if popularity >= 0.6:
        return 2 if rng.random() < 0.28 else 1
    return 1


def _company_availability(rng: random.Random, placement_days: list[str], popularity: float) -> list[AvailabilityWindow]:
    windows: list[AvailabilityWindow] = []
    for day in placement_days:
        start_time = "09:00"
        end_time = "18:00"
        if popularity < 0.55 and rng.random() < 0.55:
            start_time = "10:00"
        elif popularity < 0.72 and rng.random() < 0.35:
            start_time = "09:30"
        if popularity < 0.6 and rng.random() < 0.42:
            end_time = "17:00"
        elif popularity < 0.78 and rng.random() < 0.28:
            end_time = "17:30"
        windows.append(AvailabilityWindow(day=day, start_time=start_time, end_time=end_time))
    return windows


def _student_availability(rng: random.Random, index: int) -> list[AvailabilityWindow]:
    windows: list[AvailabilityWindow] = []
    missing_day = PLACEMENT_DAYS[index % len(PLACEMENT_DAYS)] if index % 17 == 0 else None
    for day_index, day in enumerate(PLACEMENT_DAYS):
        if day == missing_day:
            continue
        start_time = "09:00"
        end_time = "18:00"
        if (index + day_index) % 9 == 0:
            start_time = "09:30"
        if (index + day_index * 2) % 11 == 0:
            start_time = "10:00"
        if (index + day_index * 3) % 10 == 0:
            end_time = "17:30"
        if (index + day_index * 5) % 16 == 0:
            end_time = "17:00"
        windows.append(AvailabilityWindow(day=day, start_time=start_time, end_time=end_time))
    return windows


def _room_availability(room_index: int) -> list[AvailabilityWindow]:
    windows: list[AvailabilityWindow] = []
    for day_index, day in enumerate(PLACEMENT_DAYS):
        start_time = "09:00"
        end_time = "18:00"
        if (room_index + day_index) % 6 == 0:
            start_time = "09:30"
        if (room_index * (day_index + 1)) % 7 == 0:
            end_time = "17:30"
        if (room_index + day_index) % 13 == 0:
            start_time = "10:00"
        if (room_index + 2 * day_index) % 11 == 0:
            end_time = "17:00"
        windows.append(AvailabilityWindow(day=day, start_time=start_time, end_time=end_time))
    return windows


def _panel_availability(company: Company, panel_index: int) -> list[AvailabilityWindow]:
    windows: list[AvailabilityWindow] = []
    for day_position, slot in enumerate(company.availability):
        start_time = slot.start_time
        end_time = slot.end_time
        if panel_index > 1 and (panel_index + day_position) % 3 == 0 and start_time == "09:00":
            start_time = "09:30"
        if panel_index % 2 == 0 and day_position == len(company.availability) - 1 and end_time == "18:00":
            end_time = "17:30"
        windows.append(AvailabilityWindow(day=slot.day, start_time=start_time, end_time=end_time))
    return windows


def _company_shortlist_targets(
    rng: random.Random,
    companies: list[Company],
    active_students: list[Student],
    rooms: list[Room],
    panels: list[Panel],
) -> dict[str, int]:
    panel_groups: dict[str, list[Panel]] = defaultdict(list)
    for panel in panels:
        if panel.status == "AVAILABLE":
            panel_groups[panel.company_id].append(panel)

    room_minutes = sum(_availability_minutes(room.availability) for room in rooms if room.status == "AVAILABLE")
    target_room_minutes = int(room_minutes * 0.94)
    company_rows: list[dict[str, float | int | str]] = []
    for company in companies:
        available_panels = panel_groups[company.id]
        panel_minutes = sum(_availability_minutes(panel.availability) for panel in available_panels)
        panel_capacity_interviews = panel_minutes // company.interview_duration_minutes
        eligible_count = sum(1 for student in active_students if _is_student_eligible_for_company(student, company))
        target_load = 0.6 + company.popularity_score / 330.0
        if "DAY_1" in company.placement_days:
            target_load += 0.05
        if len(company.placement_days) > 1:
            target_load += 0.03
        target_load += rng.uniform(-0.03, 0.03)
        target_load = min(max(target_load, 0.52), 0.9)
        max_target = int(min(eligible_count, max(2, round(panel_capacity_interviews * target_load))))
        raw_weight = (
            max_target
            * (0.85 + company.popularity_score / 90.0)
            * (1.14 if "DAY_1" in company.placement_days else 1.0)
            * (0.96 + rng.random() * 0.08)
        )
        company_rows.append(
            {
                "company_id": company.id,
                "duration": company.interview_duration_minutes,
                "max_target": max_target,
                "raw_weight": raw_weight,
            }
        )

    total_weighted_minutes = sum(int(row["duration"]) * float(row["raw_weight"]) for row in company_rows)
    allocations = {str(row["company_id"]): 0 for row in company_rows}
    for row in company_rows:
        duration = int(row["duration"])
        proportional_minutes = target_room_minutes * (float(row["raw_weight"]) / total_weighted_minutes)
        target = min(int(row["max_target"]), int(round(proportional_minutes / duration)))
        allocations[str(row["company_id"])] = max(0, target)

    remaining_minutes = target_room_minutes - sum(
        allocations[str(row["company_id"])] * int(row["duration"]) for row in company_rows
    )
    while remaining_minutes >= min(int(row["duration"]) for row in company_rows):
        candidates = [
            row
            for row in company_rows
            if allocations[str(row["company_id"])] < int(row["max_target"])
            and remaining_minutes >= int(row["duration"])
        ]
        if not candidates:
            break
        candidates.sort(
            key=lambda row: float(row["raw_weight"]) / (1 + allocations[str(row["company_id"])]),
            reverse=True,
        )
        chosen = candidates[0]
        company_id = str(chosen["company_id"])
        allocations[company_id] += 1
        remaining_minutes -= int(chosen["duration"])

    return allocations


def _availability_minutes(windows: list[AvailabilityWindow]) -> int:
    total = 0
    for window in windows:
        start_hour, start_minute = map(int, window.start_time.split(":"))
        end_hour, end_minute = map(int, window.end_time.split(":"))
        total += (end_hour * 60 + end_minute) - (start_hour * 60 + start_minute)
    return total


def _is_student_eligible_for_company(student: Student, company: Company) -> bool:
    if student.cgpa < company.cgpa_cutoff:
        return False
    for student_window in student.availability:
        for company_window in company.availability:
            if student_window.day != company_window.day:
                continue
            if _overlaps(student_window.start_time, student_window.end_time, company_window.start_time, company_window.end_time):
                return True
    return False


def _overlaps(start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
    return max(start_a, start_b) < min(end_a, end_b)


def _shortlist_weight(
    rng: random.Random,
    student: Student,
    company: Company,
    student_score: float,
    preferred_branches: tuple[str, ...],
    existing_shortlists: int,
    coverage_mode: bool,
) -> float:
    branch_bonus = 0.08 if student.branch in preferred_branches else 0.0
    cgpa_margin = max(0.0, student.cgpa - company.cgpa_cutoff)
    margin_factor = 1.0 / (1.0 + math.exp(-(cgpa_margin * 1.5 - 0.65)))
    fairness_factor = 1.45 if existing_shortlists == 0 else 1.0 / (1.0 + existing_shortlists * 0.18)
    if coverage_mode:
        fairness_factor *= 1.1
    popularity_factor = 0.9 + company.popularity_score / 180.0
    soft_cgpa_bias = 0.88 + max(0.0, student.cgpa - 6.2) * 0.08
    noise = 0.96 + rng.random() * 0.08
    weight = (
        student_score * 0.5
        + margin_factor * 0.24
        + branch_bonus
        + soft_cgpa_bias * 0.18
    ) * fairness_factor * popularity_factor * noise
    return max(weight, 0.001)


def _weighted_choice(rng: random.Random, weights: list[float]) -> int:
    total = sum(weights)
    threshold = rng.random() * total
    cumulative = 0.0
    for index, weight in enumerate(weights):
        cumulative += weight
        if cumulative >= threshold:
            return index
    return len(weights) - 1
