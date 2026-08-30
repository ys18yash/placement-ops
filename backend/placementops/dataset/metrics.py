"""Shared dataset metrics for reporting and validation."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import fmean, median, pstdev

from .constants import PLACEMENT_DAYS
from .models import Dataset

CGPA_BANDS = (
    ("<6.5", lambda value: value < 6.5),
    ("6.5-7", lambda value: 6.5 <= value < 7.0),
    ("7-7.5", lambda value: 7.0 <= value < 7.5),
    ("7.5-8", lambda value: 7.5 <= value < 8.0),
    ("8-8.5", lambda value: 8.0 <= value < 8.5),
    ("8.5-9", lambda value: 8.5 <= value < 9.0),
    ("9+", lambda value: value >= 9.0),
)


def calculate_dataset_metrics(dataset: Dataset) -> dict[str, object]:
    student_shortlists = Counter(shortlist.student_id for shortlist in dataset.shortlists)
    company_shortlists = Counter(shortlist.company_id for shortlist in dataset.shortlists)
    company_by_id = {company.id: company for company in dataset.companies}
    panel_groups = defaultdict(list)
    for panel in dataset.panels:
        panel_groups[panel.company_id].append(panel)

    room_capacity_minutes_total = sum(_window_minutes(room.availability) for room in dataset.rooms)
    room_capacity_minutes_available = sum(
        _window_minutes(room.availability) for room in dataset.rooms if room.status == "AVAILABLE"
    )
    total_interview_duration_minutes = sum(interview.duration_minutes for interview in dataset.interviews)

    company_capacity_rows: list[dict[str, object]] = []
    for company in dataset.companies:
        panels = panel_groups[company.id]
        available_panels = [panel for panel in panels if panel.status == "AVAILABLE"]
        panel_capacity_minutes_available = sum(_window_minutes(panel.availability) for panel in available_panels)
        panel_capacity_interviews = panel_capacity_minutes_available // company.interview_duration_minutes
        day_capacity_minutes: dict[str, int] = defaultdict(int)
        for panel in available_panels:
            for window in panel.availability:
                day_capacity_minutes[window.day] += _window_minutes([window])
        company_capacity_rows.append(
            {
                "company_id": company.id,
                "company_name": company.name,
                "priority_tier": company.priority_tier,
                "popularity_score": company.popularity_score,
                "panel_count": company.panel_count,
                "available_panel_count": len(available_panels),
                "placement_days": company.placement_days,
                "shortlist_count": company_shortlists[company.id],
                "interview_duration_minutes": company.interview_duration_minutes,
                "panel_capacity_interviews": int(panel_capacity_interviews),
                "panel_capacity_minutes": int(panel_capacity_minutes_available),
                "day_capacity_minutes": dict(day_capacity_minutes),
            }
        )

    day_demand = _estimate_day_demand(company_capacity_rows)
    student_cgpas = [student.cgpa for student in dataset.students]
    active_students = [student for student in dataset.students if student.status == "ACTIVE"]
    withdrawn_students = [student for student in dataset.students if student.status == "WITHDRAWN"]
    all_shortlist_counts = [student_shortlists[student.id] for student in dataset.students]
    active_shortlist_counts = [student_shortlists[student.id] for student in active_students]

    return {
        "counts": {
            "companies": len(dataset.companies),
            "students": len(dataset.students),
            "active_students": len(active_students),
            "withdrawn_students": len(withdrawn_students),
            "rooms": len(dataset.rooms),
            "panels": len(dataset.panels),
            "available_panels": sum(1 for panel in dataset.panels if panel.status == "AVAILABLE"),
            "shortlists": len(dataset.shortlists),
            "interviews": len(dataset.interviews),
        },
        "cgpa_statistics": {
            "min": round(min(student_cgpas), 2),
            "max": round(max(student_cgpas), 2),
            "mean": round(fmean(student_cgpas), 3),
            "median": round(median(student_cgpas), 3),
            "stdev": round(pstdev(student_cgpas), 3),
        },
        "shortlist_distribution": {
            "all_students": _distribution_block(all_shortlist_counts),
            "active_students": _distribution_block(active_shortlist_counts),
        },
        "averages": {
            "average_shortlists_per_student": round(len(dataset.shortlists) / len(dataset.students), 3),
            "average_shortlists_per_active_student": round(
                len(dataset.shortlists) / max(1, len(active_students)),
                3,
            ),
        },
        "cgpa_band_statistics": _cgpa_band_stats(dataset, student_shortlists),
        "cgpa_shortlist_correlation": {
            "all_students": round(
                _correlation(
                    [student.cgpa for student in dataset.students],
                    [student_shortlists[student.id] for student in dataset.students],
                ),
                4,
            ),
            "active_students": round(
                _correlation(
                    [student.cgpa for student in active_students],
                    [student_shortlists[student.id] for student in active_students],
                ),
                4,
            ),
        },
        "company_shortlist_statistics": {
            "top_10_by_shortlists": sorted(
                company_capacity_rows,
                key=lambda row: (row["shortlist_count"], row["popularity_score"]),
                reverse=True,
            )[:10],
            "bottom_10_by_shortlists": sorted(
                company_capacity_rows,
                key=lambda row: (row["shortlist_count"], row["popularity_score"]),
            )[:10],
            "shortlists_per_company": {
                company_by_id[row["company_id"]].name: row["shortlist_count"]
                for row in sorted(company_capacity_rows, key=lambda item: item["company_name"])
            },
        },
        "company_popularity": sorted(
            company_capacity_rows,
            key=lambda row: (row["popularity_score"], row["shortlist_count"]),
            reverse=True,
        ),
        "popularity_shortlist_correlation": round(
            _correlation(
                [row["popularity_score"] for row in company_capacity_rows],
                [row["shortlist_count"] for row in company_capacity_rows],
            ),
            4,
        ),
        "capacity": {
            "total_interview_duration_minutes": total_interview_duration_minutes,
            "room_capacity_minutes_total": room_capacity_minutes_total,
            "room_capacity_minutes_available": room_capacity_minutes_available,
            "panel_capacity_minutes_available": sum(
                int(row["panel_capacity_minutes"]) for row in company_capacity_rows
            ),
            "panel_capacity_interviews_available": sum(
                int(row["panel_capacity_interviews"]) for row in company_capacity_rows
            ),
            "room_demand_capacity_ratio": round(
                total_interview_duration_minutes / max(1, room_capacity_minutes_available),
                4,
            ),
            "panel_demand_capacity_ratio": round(
                total_interview_duration_minutes
                / max(1, sum(int(row["panel_capacity_minutes"]) for row in company_capacity_rows)),
                4,
            ),
        },
        "day_demand_estimate": day_demand,
        "company_capacity_rows": company_capacity_rows,
    }

def calculate_replanning_metrics(
    original_schedule: Schedule,
    replanned_schedule: Schedule,
    changes: list[object],
) -> dict[str, object]:
    """Measure how much an existing schedule changed after replanning."""

    original_assignments = {
        assignment.interview_id: assignment
        for assignment in original_schedule.assignments
    }

    replanned_assignments = {
        assignment.interview_id: assignment
        for assignment in replanned_schedule.assignments
    }

    original_scheduled = len(original_assignments)
    replanned_scheduled = len(replanned_assignments)

    original_unscheduled = len(
        original_schedule.unscheduled_interview_ids
    )

    replanned_unscheduled = len(
        replanned_schedule.unscheduled_interview_ids
    )

    all_interview_ids = (
        set(original_assignments)
        | set(replanned_assignments)
        | set(original_schedule.unscheduled_interview_ids)
        | set(replanned_schedule.unscheduled_interview_ids)
    )

    unchanged_interviews = 0
    moved_interviews = 0

    for interview_id in all_interview_ids:
        original = original_assignments.get(interview_id)
        replanned = replanned_assignments.get(interview_id)

        if original is not None and replanned is not None:
            if original == replanned:
                unchanged_interviews += 1
            else:
                moved_interviews += 1

    affected_interviews = unchanged_interviews + moved_interviews

    newly_unscheduled_interviews = len(
        set(replanned_schedule.unscheduled_interview_ids)
        - set(original_schedule.unscheduled_interview_ids)
    )

    schedule_change_count = len(changes)

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


def _completion_rate(
    scheduled: int,
    total: int,
) -> float:
    if total == 0:
        return 0.0

    return scheduled / total

def _distribution_block(shortlist_counts: list[int]) -> dict[str, float]:
    count = len(shortlist_counts)
    return {
        "median": median(shortlist_counts) if shortlist_counts else 0,
        "students_with_0": sum(1 for value in shortlist_counts if value == 0),
        "students_with_1_to_3": sum(1 for value in shortlist_counts if 1 <= value <= 3),
        "students_with_4_to_7": sum(1 for value in shortlist_counts if 4 <= value <= 7),
        "students_with_8_to_15": sum(1 for value in shortlist_counts if 8 <= value <= 15),
        "students_with_16_plus": sum(1 for value in shortlist_counts if value >= 16),
        "students_with_0_pct": round(sum(1 for value in shortlist_counts if value == 0) * 100 / max(1, count), 2),
        "students_with_1_to_3_pct": round(
            sum(1 for value in shortlist_counts if 1 <= value <= 3) * 100 / max(1, count),
            2,
        ),
        "students_with_4_to_7_pct": round(
            sum(1 for value in shortlist_counts if 4 <= value <= 7) * 100 / max(1, count),
            2,
        ),
        "students_with_8_to_15_pct": round(
            sum(1 for value in shortlist_counts if 8 <= value <= 15) * 100 / max(1, count),
            2,
        ),
        "students_with_16_plus_pct": round(
            sum(1 for value in shortlist_counts if value >= 16) * 100 / max(1, count),
            2,
        ),
    }


def _cgpa_band_stats(dataset: Dataset, student_shortlists: Counter[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for label, predicate in CGPA_BANDS:
        students = [student for student in dataset.students if predicate(student.cgpa)]
        counts = [student_shortlists[student.id] for student in students]
        rows.append(
            {
                "band": label,
                "student_count": len(students),
                "average_shortlists": round(sum(counts) / len(counts), 3) if counts else 0.0,
                "median_shortlists": median(counts) if counts else 0,
                "zero_shortlist_count": sum(1 for count in counts if count == 0),
            }
        )
    return rows


def _estimate_day_demand(company_rows: list[dict[str, object]]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {
        day: {"companies": 0, "estimated_interviews": 0.0, "estimated_minutes": 0.0}
        for day in PLACEMENT_DAYS
    }
    for row in company_rows:
        day_capacity_minutes: dict[str, int] = row["day_capacity_minutes"]  # type: ignore[assignment]
        total_day_capacity = sum(day_capacity_minutes.values())
        if total_day_capacity == 0:
            continue
        duration = int(row["interview_duration_minutes"])
        shortlist_count = int(row["shortlist_count"])
        for day, capacity_minutes in day_capacity_minutes.items():
            share = capacity_minutes / total_day_capacity
            estimated_interviews = shortlist_count * share
            result[day]["companies"] += 1
            result[day]["estimated_interviews"] += estimated_interviews
            result[day]["estimated_minutes"] += estimated_interviews * duration
    for day in PLACEMENT_DAYS:
        result[day]["estimated_interviews"] = round(result[day]["estimated_interviews"], 2)
        result[day]["estimated_minutes"] = round(result[day]["estimated_minutes"], 2)
    return result


def _window_minutes(windows: list[object]) -> int:
    total = 0
    for window in windows:
        start_hour, start_minute = map(int, window.start_time.split(":"))  # type: ignore[attr-defined]
        end_hour, end_minute = map(int, window.end_time.split(":"))  # type: ignore[attr-defined]
        total += (end_hour * 60 + end_minute) - (start_hour * 60 + start_minute)
    return total


def _correlation(first: list[float], second: list[float]) -> float:
    if len(first) != len(second) or len(first) < 2:
        return 0.0
    first_mean = sum(first) / len(first)
    second_mean = sum(second) / len(second)
    numerator = sum((left - first_mean) * (right - second_mean) for left, right in zip(first, second))
    denominator = (
        sum((left - first_mean) ** 2 for left in first) * sum((right - second_mean) ** 2 for right in second)
    ) ** 0.5
    return numerator / denominator if denominator else 0.0
