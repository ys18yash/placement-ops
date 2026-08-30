"""Serializable domain models for dataset generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class AvailabilityWindow:
    day: str
    start_time: str
    end_time: str


@dataclass(slots=True)
class Company:
    id: str
    name: str
    industry: str
    priority_tier: str
    cgpa_cutoff: float
    interview_duration_minutes: int
    panel_count: int
    placement_days: list[str]
    availability: list[AvailabilityWindow]
    popularity_score: int


@dataclass(slots=True)
class Student:
    id: str
    name: str
    branch: str
    cgpa: float
    status: str
    availability: list[AvailabilityWindow]


@dataclass(slots=True)
class Room:
    id: str
    name: str
    building: str
    floor: int
    capacity: int
    availability: list[AvailabilityWindow]
    status: str


@dataclass(slots=True)
class Panel:
    id: str
    company_id: str
    name: str
    availability: list[AvailabilityWindow]
    status: str


@dataclass(slots=True)
class Shortlist:
    id: str
    student_id: str
    company_id: str


@dataclass(slots=True)
class Interview:
    id: str
    student_id: str
    company_id: str
    duration_minutes: int
    status: str


@dataclass(slots=True)
class Dataset:
    seed: int
    companies: list[Company]
    students: list[Student]
    rooms: list[Room]
    panels: list[Panel]
    shortlists: list[Shortlist]
    interviews: list[Interview]
    supported_disruptions: list[str]

    def to_dict(self) -> dict[str, object]:
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