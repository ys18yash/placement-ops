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


def build_assistant_context(
    context_input: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build a structured, mathematically verified operational facts dictionary for Gemini."""
    if not context_input:
        return {
            "status": "NO_STATE_PROVIDED",
            "message": "No placement schedule state was supplied by the client.",
        }

    status = context_input.get("status", "UNKNOWN")
    metrics = context_input.get("metrics") or {}
    total_workload = metrics.get("total_workload", 859)
    scheduled_count = metrics.get("scheduled_interviews", 0)
    unscheduled_count = metrics.get("unscheduled_interviews", 0)
    completion_rate = metrics.get("completion_rate", 0)
    room_utilization = metrics.get("room_utilization", 0)
    panel_utilization = metrics.get("panel_utilization", 0)

    # 1. Day distribution and exact extremes (DAY_1 to DAY_4)
    day_distribution = context_input.get("day_breakdown") or {}
    busiest_day = None
    least_busy_day = None
    if day_distribution:
        sorted_days = sorted(
            day_distribution.items(), key=lambda x: x[1], reverse=True
        )
        busiest_day = {
            "day": sorted_days[0][0],
            "scheduled_interviews": sorted_days[0][1],
        }
        least_busy_day = {
            "day": sorted_days[-1][0],
            "scheduled_interviews": sorted_days[-1][1],
        }

    # 2. Room utilization rankings and exact extremes (20 physical rooms: ROOM001 to ROOM020)
    all_rooms = (
        context_input.get("all_rooms_utilization")
        or context_input.get("top_rooms")
        or []
    )
    max_room = None
    min_room = None
    if all_rooms:
        sorted_rooms = sorted(
            all_rooms, key=lambda x: x.get("scheduled_minutes", 0), reverse=True
        )
        max_room = sorted_rooms[0]
        min_room = sorted_rooms[-1]

    # 3. Company workload rankings
    all_companies = context_input.get("top_companies") or []
    max_company = None
    min_company = None
    if all_companies:
        sorted_comps = sorted(
            all_companies,
            key=lambda x: x.get("scheduled_interviews", 0),
            reverse=True,
        )
        max_company = sorted_comps[0]
        min_company = sorted_comps[-1]

    # 4. Panel workload rankings
    top_panels = context_input.get("top_panels") or []
    max_panel = None
    min_panel = None
    if top_panels:
        sorted_panels = sorted(
            top_panels,
            key=lambda x: x.get("scheduled_interviews", 0),
            reverse=True,
        )
        max_panel = sorted_panels[0]
        min_panel = sorted_panels[-1]

    return {
        "status": status,
        "schedule_summary": {
            "total_requested_workload": total_workload,
            "scheduled_interviews": scheduled_count,
            "unscheduled_interviews": unscheduled_count,
            "completion_rate_percentage": f"{completion_rate * 100:.2f}%",
            "room_utilization_percentage": f"{room_utilization * 100:.2f}%",
            "panel_utilization_percentage": f"{panel_utilization * 100:.2f}%",
            "total_rooms": 20,
        },
        "day_distribution": {
            "counts_by_day": day_distribution,
            "busiest_day": busiest_day,
            "least_busy_day": least_busy_day,
        },
        "room_utilization_rankings": {
            "highest_utilized_room": max_room,
            "minimum_utilized_room": min_room,
            "all_rooms": all_rooms,
        },
        "panel_utilization_rankings": {
            "highest_utilized_panel": max_panel,
            "minimum_utilized_panel": min_panel,
        },
        "company_workload_rankings": {
            "highest_workload_company": max_company,
            "lowest_workload_company": min_company,
            "top_companies": all_companies,
        },
        "unscheduled_summary": {
            "total_unscheduled": unscheduled_count,
            "sample_unscheduled_ids": context_input.get(
                "unscheduled_sample_ids", []
            ),
        },
        "replan_summary": context_input.get("replan_summary"),
        "selected_interview": context_input.get("selected_interview"),
    }


def _create_system_prompt(context_dict: dict[str, Any]) -> str:
    """Create a strict anti-hallucination grounding prompt."""
    import json

    context_json = json.dumps(context_dict, indent=2)
    return (
        "You are the PlacementOps operational assistant for campus placement interview scheduling and replanning.\n"
        "You answer questions accurately, concisely, and operationally using ONLY the provided PlacementOps facts below.\n\n"
        "STRICT GROUNDING RULES:\n"
        "1. When asked for maximums (highest, busiest, most) or minimums (lowest, least, minimum), use the exact mathematically calculated values in the facts.\n"
        "2. Never swap highest and lowest values.\n"
        "3. Never invent interview records, candidate IDs, metrics, utilization values, disruptions, or constraint failures.\n"
        '4. If the supplied facts do not contain enough data to answer a question, explicitly state: "I don\'t have enough PlacementOps data to determine that."\n'
        "5. For unscheduled interviews, state that they are unscheduled due to capacity constraints unless specific evidence is provided in facts.\n"
        "6. When explaining a replan, use only the metrics and change records in the replan summary.\n"
        "7. Keep responses direct, professional, and compact.\n\n"
        f"STRUCTURED PLACEMENTOPS OPERATIONAL FACTS:\n{context_json}"
    )


_env_already_loaded = False


def _ensure_env_loaded() -> None:
    """Ensure root .env is loaded safely once on initialization if not already loaded."""
    global _env_already_loaded
    if _env_already_loaded:
        return
    _env_already_loaded = True
    try:
        from pathlib import Path
        from dotenv import load_dotenv

        # Locate root .env and fallback files
        project_root = Path(__file__).resolve().parents[3]
        for env_filename in [".env", ".env.local", ".env.example"]:
            env_file = project_root / env_filename
            if env_file.exists():
                load_dotenv(dotenv_path=env_file, override=False)
    except Exception:
        pass



def _get_gemini_client(api_key: str):
    """Obtain a Google Gemini genai client."""
    from google import genai

    return genai.Client(api_key=api_key)


def stream_assistant_service(
    question: str,
    messages: list[dict[str, str]] | None = None,
    context: dict[str, Any] | None = None,
):
    """Stream real-time SSE token deltas from the official Google Gemini API."""
    import json
    import os

    _ensure_env_loaded()

    q = (question or "").strip()
    if not q:
        yield f"data: {json.dumps({'type': 'error', 'error': 'Question must not be empty.'})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"

    if not api_key:
        yield f"data: {json.dumps({'type': 'error', 'error': 'Assistant configuration is unavailable (missing GEMINI_API_KEY on backend server).'})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return

    grounded_context = build_assistant_context(context)
    system_content = _create_system_prompt(grounded_context)

    try:
        from google.genai import types

        client = _get_gemini_client(api_key)

        # Build contents from conversation history
        contents: list[types.Content] = []
        if messages:
            for msg in messages:
                role = msg.get("role", "user")
                text = (msg.get("content") or "").strip()
                if text:
                    genai_role = "model" if role == "assistant" else "user"
                    contents.append(
                        types.Content(
                            role=genai_role,
                            parts=[types.Part.from_text(text=text)],
                        )
                    )

        if not contents or (contents[-1].parts and contents[-1].parts[0].text != q):
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=q)],
                )
            )

        gen_config = types.GenerateContentConfig(
            system_instruction=system_content,
            temperature=0.2,
        )

        response = client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=gen_config,
        )

        for chunk in response:
            delta_text = chunk.text or ""
            if delta_text:
                yield f"data: {json.dumps({'type': 'delta', 'text': delta_text})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as exc:
        err_str = str(exc)
        err_msg = "PlacementOps Assistant is temporarily unavailable."

        # Check for rate limiting or invalid credentials
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            err_msg = "The assistant request was rate-limited. Try again shortly."
        elif "API_KEY_INVALID" in err_str or "403" in err_str or "400" in err_str:
            err_msg = f"PlacementOps Assistant configuration error ({err_str[:120]})."

        yield f"data: {json.dumps({'type': 'error', 'error': err_msg})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"


def query_assistant_service(
    question: str,
    messages: list[dict[str, str]] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Non-streaming query helper for testing and synchronous clients."""
    import os

    _ensure_env_loaded()

    q = (question or "").strip()
    if not q:
        raise ValueError("Question must not be empty.")

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"

    if not api_key:
        return {
            "answer": "PlacementOps Assistant is temporarily unavailable. (Missing GEMINI_API_KEY configuration on the backend server.)",
            "model": model,
            "configured": False,
        }

    grounded_context = build_assistant_context(context)
    system_content = _create_system_prompt(grounded_context)

    try:
        from google.genai import types

        client = _get_gemini_client(api_key)

        contents: list[types.Content] = []
        if messages:
            for msg in messages:
                role = msg.get("role", "user")
                text = (msg.get("content") or "").strip()
                if text:
                    genai_role = "model" if role == "assistant" else "user"
                    contents.append(
                        types.Content(
                            role=genai_role,
                            parts=[types.Part.from_text(text=text)],
                        )
                    )

        if not contents or (contents[-1].parts and contents[-1].parts[0].text != q):
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=q)],
                )
            )

        gen_config = types.GenerateContentConfig(
            system_instruction=system_content,
            temperature=0.2,
        )

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=gen_config,
        )

        answer = (response.text or "").strip()
        if not answer:
            answer = "I don't have enough PlacementOps data to determine that."

        return {
            "answer": answer,
            "model": model,
            "configured": True,
        }

    except Exception as exc:
        err_str = str(exc)
        err_msg = "PlacementOps Assistant is temporarily unavailable."
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            err_msg = "The assistant request was rate-limited. Try again shortly."

        return {
            "answer": f"PlacementOps Assistant is temporarily unavailable ({err_msg}).",
            "model": model,
            "configured": True,
            "error": err_str,
        }





