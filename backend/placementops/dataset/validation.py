"""Dataset validation rules."""

from __future__ import annotations

from dataclasses import dataclass, field

from .constants import (
    COMPANY_COUNT,
    OPERATING_END,
    OPERATING_START,
    PANEL_STATUSES,
    PLACEMENT_DAYS,
    PRIORITY_TIERS,
    ROOM_COUNT,
    ROOM_STATUSES,
    STUDENT_COUNT,
    STUDENT_STATUSES,
    VALIDATION_THRESHOLDS,
)
from .metrics import calculate_dataset_metrics
from .models import Dataset


@dataclass(slots=True)
class ValidationReport:
    valid: bool
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {"valid": self.valid, "errors": self.errors}


def validate_dataset(dataset: Dataset) -> ValidationReport:
    errors: list[str] = []

    if len(dataset.companies) != COMPANY_COUNT:
        errors.append(f"Expected {COMPANY_COUNT} companies, found {len(dataset.companies)}.")
    if len(dataset.students) != STUDENT_COUNT:
        errors.append(f"Expected {STUDENT_COUNT} students, found {len(dataset.students)}.")
    if len(dataset.rooms) != ROOM_COUNT:
        errors.append(f"Expected {ROOM_COUNT} rooms, found {len(dataset.rooms)}.")

    company_ids = {company.id for company in dataset.companies}
    student_ids = {student.id for student in dataset.students}
    shortlist_ids: set[str] = set()
    shortlist_pairs: set[tuple[str, str]] = set()
    interview_ids: set[str] = set()
    interview_pairs: set[tuple[str, str]] = set()

    for company in dataset.companies:
        if company.priority_tier not in PRIORITY_TIERS:
            errors.append(f"Company {company.id} has invalid priority tier {company.priority_tier}.")
        if not 5.0 <= company.cgpa_cutoff <= 10.0:
            errors.append(f"Company {company.id} has out-of-range cutoff {company.cgpa_cutoff}.")
        if company.panel_count < 1:
            errors.append(f"Company {company.id} must have at least one panel.")
        if any(day not in PLACEMENT_DAYS for day in company.placement_days):
            errors.append(f"Company {company.id} has invalid placement day.")
        if sorted(company.placement_days, key=PLACEMENT_DAYS.index) != company.placement_days:
            errors.append(f"Company {company.id} placement days must be sorted.")
        _validate_availability(errors, company.id, company.availability)

    for student in dataset.students:
        if student.status not in STUDENT_STATUSES:
            errors.append(f"Student {student.id} has invalid status {student.status}.")
        if not 5.0 <= student.cgpa <= 10.0:
            errors.append(f"Student {student.id} has out-of-range CGPA {student.cgpa}.")
        _validate_availability(errors, student.id, student.availability)

    for room in dataset.rooms:
        if room.status not in ROOM_STATUSES:
            errors.append(f"Room {room.id} has invalid status {room.status}.")
        if room.capacity <= 0:
            errors.append(f"Room {room.id} must have positive capacity.")
        _validate_availability(errors, room.id, room.availability)

    panel_companies: set[str] = set()
    for panel in dataset.panels:
        panel_companies.add(panel.company_id)
        if panel.company_id not in company_ids:
            errors.append(f"Panel {panel.id} references unknown company {panel.company_id}.")
        if panel.status not in PANEL_STATUSES:
            errors.append(f"Panel {panel.id} has invalid status {panel.status}.")
        _validate_availability(errors, panel.id, panel.availability)

    for shortlist in dataset.shortlists:
        if shortlist.id in shortlist_ids:
            errors.append(f"Duplicate shortlist id {shortlist.id}.")
        shortlist_ids.add(shortlist.id)
        pair = (shortlist.student_id, shortlist.company_id)
        if pair in shortlist_pairs:
            errors.append(f"Duplicate shortlist relationship {pair}.")
        shortlist_pairs.add(pair)
        if shortlist.student_id not in student_ids:
            errors.append(f"Shortlist {shortlist.id} references unknown student {shortlist.student_id}.")
        if shortlist.company_id not in company_ids:
            errors.append(f"Shortlist {shortlist.id} references unknown company {shortlist.company_id}.")

    for interview in dataset.interviews:
        if interview.id in interview_ids:
            errors.append(f"Duplicate interview id {interview.id}.")
        interview_ids.add(interview.id)
        pair = (interview.student_id, interview.company_id)
        if pair in interview_pairs:
            errors.append(f"Duplicate interview relationship {pair}.")
        interview_pairs.add(pair)
        if interview.student_id not in student_ids:
            errors.append(f"Interview {interview.id} references unknown student {interview.student_id}.")
        if interview.company_id not in company_ids:
            errors.append(f"Interview {interview.id} references unknown company {interview.company_id}.")
        if pair not in shortlist_pairs:
            errors.append(
                f"Interview {interview.id} does not correspond to a valid shortlist "
                f"({interview.student_id}, {interview.company_id})."
            )

    if len(dataset.interviews) != len(dataset.shortlists):
        errors.append(
            f"Interview count {len(dataset.interviews)} does not match shortlist count {len(dataset.shortlists)}."
        )

    missing_panel_companies = sorted(company_ids - panel_companies)
    if missing_panel_companies:
        errors.append(f"Companies without panels: {', '.join(missing_panel_companies)}.")

    errors.extend(_validate_realism_thresholds(dataset))
    return ValidationReport(valid=not errors, errors=errors)


def _validate_realism_thresholds(dataset: Dataset) -> list[str]:
    errors: list[str] = []
    metrics = calculate_dataset_metrics(dataset)
    capacity = metrics["capacity"]
    active_distribution = metrics["shortlist_distribution"]["active_students"]
    correlations = metrics["cgpa_shortlist_correlation"]
    popularity_correlation = metrics["popularity_shortlist_correlation"]
    band_stats = metrics["cgpa_band_statistics"]

    room_ratio = capacity["room_demand_capacity_ratio"]
    panel_ratio = capacity["panel_demand_capacity_ratio"]
    if room_ratio < VALIDATION_THRESHOLDS["room_demand_ratio_min"]:
        errors.append(
            f"Room demand ratio {room_ratio} is below minimum threshold "
            f"{VALIDATION_THRESHOLDS['room_demand_ratio_min']}."
        )
    if room_ratio > VALIDATION_THRESHOLDS["room_demand_ratio_max"]:
        errors.append(
            f"Room demand ratio {room_ratio} exceeds maximum threshold "
            f"{VALIDATION_THRESHOLDS['room_demand_ratio_max']}."
        )
    if panel_ratio > VALIDATION_THRESHOLDS["panel_demand_ratio_max"]:
        errors.append(
            f"Panel demand ratio {panel_ratio} exceeds maximum threshold "
            f"{VALIDATION_THRESHOLDS['panel_demand_ratio_max']}."
        )

    active_zero_pct = active_distribution["students_with_0_pct"]
    if active_zero_pct > VALIDATION_THRESHOLDS["active_zero_shortlist_pct_max"]:
        errors.append(
            f"Active zero-shortlist percentage {active_zero_pct} exceeds maximum threshold "
            f"{VALIDATION_THRESHOLDS['active_zero_shortlist_pct_max']}."
        )

    if correlations["active_students"] < VALIDATION_THRESHOLDS["cgpa_shortlist_correlation_min"]:
        errors.append(
            f"Active CGPA-shortlist correlation {correlations['active_students']} is below minimum threshold "
            f"{VALIDATION_THRESHOLDS['cgpa_shortlist_correlation_min']}."
        )
    if popularity_correlation < VALIDATION_THRESHOLDS["popularity_shortlist_correlation_min"]:
        errors.append(
            f"Popularity-shortlist correlation {popularity_correlation} is below minimum threshold "
            f"{VALIDATION_THRESHOLDS['popularity_shortlist_correlation_min']}."
        )

    previous_average: float | None = None
    for band in band_stats:
        average = band["average_shortlists"]
        if previous_average is not None and average + 0.25 < previous_average:
            errors.append(
                f"CGPA band shortlist averages are not gradually non-decreasing around band {band['band']}."
            )
            break
        previous_average = average

    return errors


def _validate_availability(errors: list[str], entity_id: str, windows: list[object]) -> None:
    for window in windows:
        day = getattr(window, "day", None)
        start_time = getattr(window, "start_time", None)
        end_time = getattr(window, "end_time", None)
        if day not in PLACEMENT_DAYS:
            errors.append(f"{entity_id} availability has invalid day {day}.")
            continue
        if not _is_valid_time(start_time) or not _is_valid_time(end_time):
            errors.append(f"{entity_id} availability has invalid time window {start_time}-{end_time}.")
            continue
        if not (OPERATING_START <= start_time < end_time <= OPERATING_END):
            errors.append(f"{entity_id} availability window {start_time}-{end_time} is outside operating hours.")


def _is_valid_time(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 5 or value[2] != ":":
        return False
    hour, minute = value.split(":")
    return hour.isdigit() and minute.isdigit() and 0 <= int(hour) <= 23 and minute in {"00", "15", "30", "45"}
