"""HTTP routes for PlacementOps."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, field_validator

from placementops.api.service import (
    InvalidDisruptionError,
    generate_schedule_service,
    replan_schedule_service,
)
from placementops.scheduling.models import Disruption

router = APIRouter()


class DisruptionRequest(BaseModel):
    """HTTP representation of a scheduling disruption."""

    id: str
    type: Literal[
        "COMPANY_DELAY",
        "PANEL_DROPOUT",
        "STUDENT_WITHDRAWAL",
        "ROOM_UNAVAILABLE",
    ]
    day: Literal["DAY_1", "DAY_2", "DAY_3", "DAY_4"]
    effective_time: str | None = None
    resource_id: str | None = None
    details: str | None = None

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Disruption id must not be empty.")
        return value

    @field_validator("effective_time")
    @classmethod
    def validate_effective_time(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return value

        if len(value) != 5 or value[2] != ":":
            raise ValueError("effective_time must use HH:MM format.")

        hour, minute = value.split(":")

        if not (
            hour.isdigit()
            and minute.isdigit()
            and 0 <= int(hour) <= 23
            and minute in {"00", "15", "30", "45"}
        ):
            raise ValueError(
                "effective_time must use a 15-minute HH:MM boundary."
            )

        return value


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

    except InvalidDisruptionError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc
