"""Application services for PlacementOps."""

from __future__ import annotations

from typing import Any

from placementops.dataset import generate_dataset
from placementops.dataset.constants import PLACEMENT_DAYS
from placementops.dataset.validation import validate_dataset
from placementops.scheduling.conflict import detect_conflicts
from placementops.scheduling.constraints import can_assign
from placementops.scheduling.metrics import (
    calculate_replanning_metrics,
    calculate_schedule_metrics,
)
from placementops.scheduling.models import Disruption, Schedule
from placementops.scheduling.replanner import replan_schedule
from placementops.scheduling.scheduler import generate_schedule


class InvalidDisruptionError(ValueError):
    """Raised when a replanning request contains invalid disruption input."""


def generate_schedule_service(seed: int | None = None) -> dict[str, Any]:
    """Generate, validate, schedule, and report a PlacementOps run."""
    dataset = generate_dataset(seed=seed)

    validation = validate_dataset(dataset)

    if not validation.valid:
        raise ValueError(
            "Generated dataset failed validation: "
            + "; ".join(validation.errors)
        )

    schedule = generate_schedule(dataset)
    metrics = calculate_schedule_metrics(dataset, schedule)

    return {
        "seed": dataset.seed,
        "validation": validation.to_dict(),
        "schedule": schedule.to_dict(),
        "metrics": metrics,
    }


def replan_schedule_service(
    seed: int | None,
    disruption: Disruption,
) -> dict[str, Any]:
    """Generate an initial schedule and replan it after a disruption."""
    dataset = generate_dataset(seed=seed)

    validation = validate_dataset(dataset)

    if not validation.valid:
        raise ValueError(
            "Generated dataset failed validation: "
            + "; ".join(validation.errors)
        )

    original_schedule = generate_schedule(dataset)
    _validate_disruption(dataset, disruption)

    replanned_schedule, changes = replan_schedule(
        dataset,
        original_schedule,
        disruption,
    )

    _validate_replanned_schedule(
        dataset,
        replanned_schedule,
        disruption,
    )

    original_metrics = calculate_schedule_metrics(
        dataset,
        original_schedule,
    )

    replanned_metrics = calculate_schedule_metrics(
        dataset,
        replanned_schedule,
    )

    replanning_metrics = calculate_replanning_metrics(
        original_schedule,
        replanned_schedule,
        changes,
    )

    return {
        "seed": dataset.seed,
        "validation": validation.to_dict(),
        "disruption": disruption.to_dict()
        if hasattr(disruption, "to_dict")
        else {
            "id": disruption.id,
            "type": disruption.type,
            "day": disruption.day,
            "effective_time": disruption.effective_time,
            "resource_id": disruption.resource_id,
            "details": disruption.details,
        },
        "original_schedule": original_schedule.to_dict(),
        "replanned_schedule": replanned_schedule.to_dict(),
        "original_metrics": original_metrics,
        "replanned_metrics": replanned_metrics,
        "replanning_metrics": replanning_metrics,
        "changes": [
            change.to_dict()
            for change in changes
        ],
    }


def _validate_disruption(dataset: Any, disruption: Disruption) -> None:
    """Validate disruption semantics against the generated dataset."""

    supported_types = {
        "COMPANY_DELAY",
        "PANEL_DROPOUT",
        "STUDENT_WITHDRAWAL",
        "ROOM_UNAVAILABLE",
    }

    if disruption.type not in supported_types:
        raise InvalidDisruptionError(
            f"Unsupported disruption type: {disruption.type}."
        )

    if disruption.day not in PLACEMENT_DAYS:
        raise InvalidDisruptionError(
            f"Invalid disruption day: {disruption.day}."
        )

    resource_id = (
        disruption.resource_id.strip()
        if isinstance(disruption.resource_id, str)
        else None
    )

    if not resource_id:
        raise InvalidDisruptionError(
            f"Disruption type {disruption.type} requires a resource_id."
        )

    if (
        disruption.type != "COMPANY_DELAY"
        and disruption.effective_time is not None
    ):
        raise InvalidDisruptionError(
            f"Disruption type {disruption.type} does not support effective_time."
        )

    companies = {company.id: company for company in dataset.companies}
    panels = {panel.id: panel for panel in dataset.panels}
    rooms = {room.id: room for room in dataset.rooms}
    students = {student.id: student for student in dataset.students}

    if disruption.type == "COMPANY_DELAY":
        company = companies.get(resource_id)
        if company is None:
            raise InvalidDisruptionError(
                f"Unknown company resource_id: {resource_id}."
            )
        if (
            disruption.effective_time is not None
            and not _is_valid_time(disruption.effective_time)
        ):
            raise InvalidDisruptionError(
                "effective_time must use a 15-minute HH:MM boundary."
            )
        if disruption.day not in company.placement_days:
            raise InvalidDisruptionError(
                f"Company {resource_id} is not scheduled on {disruption.day}."
            )
        if not any(
            window.day == disruption.day
            for window in company.availability
        ):
            raise InvalidDisruptionError(
                f"Company {resource_id} has no availability on {disruption.day}."
            )
        return

    if disruption.type == "PANEL_DROPOUT":
        panel = panels.get(resource_id)
        if panel is None:
            raise InvalidDisruptionError(
                f"Unknown panel resource_id: {resource_id}."
            )
        if not any(
            window.day == disruption.day
            for window in panel.availability
        ):
            raise InvalidDisruptionError(
                f"Panel {resource_id} has no availability on {disruption.day}."
            )
        return

    if disruption.type == "ROOM_UNAVAILABLE":
        room = rooms.get(resource_id)
        if room is None:
            raise InvalidDisruptionError(
                f"Unknown room resource_id: {resource_id}."
            )
        if not any(
            window.day == disruption.day
            for window in room.availability
        ):
            raise InvalidDisruptionError(
                f"Room {resource_id} has no availability on {disruption.day}."
            )
        return

    if students.get(resource_id) is None:
        raise InvalidDisruptionError(
            f"Unknown student resource_id: {resource_id}."
        )


def _validate_replanned_schedule(
    dataset: Any,
    schedule: Schedule,
    disruption: Disruption,
) -> None:
    """Ensure the replanned schedule remains internally valid."""

    interviews = {
        interview.id: interview
        for interview in dataset.interviews
    }
    students = {student.id: student for student in dataset.students}
    companies = {company.id: company for company in dataset.companies}
    panels = {panel.id: panel for panel in dataset.panels}
    rooms = {room.id: room for room in dataset.rooms}

    errors: list[str] = []
    scheduled_ids: set[str] = set()
    previous_assignments = []

    for assignment in schedule.assignments:
        interview = interviews.get(assignment.interview_id)
        student = students.get(assignment.student_id)
        company = companies.get(assignment.company_id)
        panel = panels.get(assignment.panel_id)
        room = rooms.get(assignment.room_id)

        if interview is None:
            errors.append(
                f"Unknown interview in schedule: {assignment.interview_id}."
            )
            continue

        if (
            assignment.student_id != interview.student_id
            or assignment.company_id != interview.company_id
        ):
            errors.append(
                f"Assignment {assignment.interview_id} does not match its interview record."
            )
            continue

        if student is None or company is None or panel is None or room is None:
            errors.append(
                f"Assignment {assignment.interview_id} references missing resources."
            )
            continue

        result = can_assign(
            assignment,
            student=student,
            company=company,
            panel=panel,
            room=room,
            existing_assignments=previous_assignments,
        )

        if not result.valid:
            errors.append(
                f"Assignment {assignment.interview_id} is invalid: {result.reason}"
            )

        if assignment.interview_id in scheduled_ids:
            errors.append(
                f"Interview {assignment.interview_id} is scheduled more than once."
            )
        scheduled_ids.add(assignment.interview_id)
        previous_assignments.append(assignment)

    unscheduled_ids = set(schedule.unscheduled_interview_ids)
    interview_ids = set(interviews)

    if scheduled_ids & unscheduled_ids:
        errors.append(
            "Some interviews are both scheduled and unscheduled after replanning."
        )

    if scheduled_ids | unscheduled_ids != interview_ids:
        errors.append(
            "Replanned schedule does not account for every interview exactly once."
        )

    for conflict in detect_conflicts(schedule):
        errors.append(
            f"Conflict detected for interview {conflict.interview_id}: {conflict.reason}"
        )

    if disruption.type == "PANEL_DROPOUT":
        for assignment in schedule.assignments:
            if (
                assignment.panel_id == disruption.resource_id
                and assignment.day == disruption.day
            ):
                errors.append(
                    f"Panel dropout left interview {assignment.interview_id} on dropped panel."
                )

    if disruption.type == "ROOM_UNAVAILABLE":
        for assignment in schedule.assignments:
            if (
                assignment.room_id == disruption.resource_id
                and assignment.day == disruption.day
            ):
                errors.append(
                    f"Room unavailability left interview {assignment.interview_id} in unavailable room."
                )

    if disruption.type == "STUDENT_WITHDRAWAL":
        for assignment in schedule.assignments:
            if assignment.student_id == disruption.resource_id:
                errors.append(
                    f"Student withdrawal left interview {assignment.interview_id} scheduled."
                )

    if errors:
        raise ValueError("; ".join(errors))


def _is_valid_time(value: str) -> bool:
    if len(value) != 5 or value[2] != ":":
        return False

    hour, minute = value.split(":")

    return (
        hour.isdigit()
        and minute.isdigit()
        and 0 <= int(hour) <= 23
        and minute in {"00", "15", "30", "45"}
    )
