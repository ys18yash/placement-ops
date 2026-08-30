"""Application services for PlacementOps."""

from __future__ import annotations

from typing import Any

from placementops.dataset import generate_dataset
from placementops.dataset.validation import validate_dataset
from placementops.scheduling.metrics import (
    calculate_replanning_metrics,
    calculate_schedule_metrics,
)
from placementops.scheduling.models import Disruption
from placementops.scheduling.replanner import replan_schedule
from placementops.scheduling.scheduler import generate_schedule


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

    replanned_schedule, changes = replan_schedule(
        dataset,
        original_schedule,
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
