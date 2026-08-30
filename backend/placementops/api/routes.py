"""HTTP routes for PlacementOps."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from placementops.api.service import (
    generate_schedule_service,
    replan_schedule_service,
)
from placementops.scheduling.models import Disruption

router = APIRouter()


class DisruptionRequest(BaseModel):
    """HTTP representation of a scheduling disruption."""

    id: str
    type: str
    day: str
    effective_time: str | None = None
    resource_id: str | None = None
    details: str | None = None


class ReplanRequest(BaseModel):
    """Request to generate and replan a schedule."""

    seed: int | None = None
    disruption: DisruptionRequest


@router.post("/schedule/generate")
def generate_schedule(
    seed: int | None = Query(
        default=None,
        description="Optional deterministic dataset seed.",
    ),
) -> dict[str, object]:
    """Generate and return a validated placement schedule."""
    try:
        return generate_schedule_service(seed=seed)
    except ValueError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@router.post("/schedule/replan")
def replan_schedule(
    request: ReplanRequest,
) -> dict[str, object]:
    """Generate a schedule and replan it after a disruption."""
    try:
        disruption = Disruption(
            id=request.disruption.id,
            type=request.disruption.type,
            day=request.disruption.day,
            effective_time=request.disruption.effective_time,
            resource_id=request.disruption.resource_id,
            details=request.disruption.details,
        )

        return replan_schedule_service(
            seed=request.seed,
            disruption=disruption,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc
