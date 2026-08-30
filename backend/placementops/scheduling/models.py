"""Domain models for scheduling and replanning."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class ScheduleAssignment:
    """Concrete assignment of an interview to time and resources."""

    interview_id: str
    student_id: str
    company_id: str
    panel_id: str
    room_id: str
    day: str
    start_time: str
    end_time: str


@dataclass(slots=True)
class Schedule:
    """Result of a scheduling run."""

    assignments: list[ScheduleAssignment] = field(default_factory=list)
    unscheduled_interview_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True, frozen=True)
class Disruption:
    """A real-world event that may invalidate part of a schedule."""

    id: str
    type: str
    day: str
    effective_time: str | None = None
    resource_id: str | None = None
    details: str | None = None


@dataclass(slots=True, frozen=True)
class ScheduleChange:
    """A change made to an existing schedule during replanning."""

    interview_id: str
    change_type: str
    old_assignment: ScheduleAssignment | None = None
    new_assignment: ScheduleAssignment | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(slots=True, frozen=True)
class Conflict:
    """A detected conflict between scheduled interviews or resources."""

    conflict_type: str
    interview_id: str
    conflicting_interview_id: str | None = None
    resource_id: str | None = None
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
