from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from pydantic import ValidationError

from placementops.api.routes import (
    AssistantQueryRequest,
    DisruptionRequest,
    ReplanRequest,
    query_assistant,
    replan_schedule,
)
from placementops.api.service import (
    build_assistant_context,
    query_assistant_service,
    stream_assistant_service,
)


class ApiTests(unittest.TestCase):
    def test_replan_request_rejects_unsupported_disruption_type(self) -> None:
        with self.assertRaises(ValidationError):
            DisruptionRequest(
                id="BAD-TYPE",
                type="ROOM_UNAVAILABILITY",
                day="DAY_1",
                resource_id="ROOM001",
            )

    def test_replan_request_rejects_invalid_day(self) -> None:
        with self.assertRaises(ValidationError):
            DisruptionRequest(
                id="BAD-DAY",
                type="ROOM_UNAVAILABLE",
                day="DAY_5",
                resource_id="ROOM001",
            )

    def test_replan_request_rejects_invalid_effective_time(self) -> None:
        with self.assertRaises(ValidationError):
            DisruptionRequest(
                id="BAD-TIME",
                type="COMPANY_DELAY",
                day="DAY_1",
                effective_time="12:10",
                resource_id="COMP001",
            )

    def test_replan_route_returns_400_for_unknown_resource(self) -> None:
        request = ReplanRequest(
            seed=20260829,
            disruption=DisruptionRequest(
                id="UNKNOWN-ROOM",
                type="ROOM_UNAVAILABLE",
                day="DAY_1",
                resource_id="ROOM999",
            ),
        )

        with self.assertRaises(HTTPException) as context:
            replan_schedule(request)

        self.assertEqual(400, context.exception.status_code)
        self.assertIn("Unknown room resource_id", context.exception.detail)

    def test_assistant_request_rejects_empty_question(self) -> None:
        with self.assertRaises(ValidationError):
            AssistantQueryRequest(question="   ")

    def test_assistant_context_builder_calculates_extremes_correctly(self) -> None:
        context_input = {
            "status": "SCHEDULE_GENERATED",
            "metrics": {
                "total_workload": 859,
                "scheduled_interviews": 476,
                "unscheduled_interviews": 383,
                "completion_rate": 0.5541,
                "room_utilization": 0.5382,
            },
            "day_breakdown": {
                "DAY_1": 135,
                "DAY_2": 120,
                "DAY_3": 115,
                "DAY_4": 106,
            },
            "all_rooms_utilization": [
                {"room": "ROOM012", "scheduled_minutes": 1400},
                {"room": "ROOM005", "scheduled_minutes": 850},
                {"room": "ROOM019", "scheduled_minutes": 620},
            ],
            "top_companies": [
                {"company": "COMP001", "scheduled_interviews": 45},
                {"company": "COMP008", "scheduled_interviews": 10},
            ],
            "top_panels": [
                {"panel": "PANEL-01", "scheduled_interviews": 20},
                {"panel": "PANEL-09", "scheduled_interviews": 3},
            ],
        }

        ctx = build_assistant_context(context_input)
        self.assertEqual("DAY_1", ctx["day_distribution"]["busiest_day"]["day"])
        self.assertEqual("DAY_4", ctx["day_distribution"]["least_busy_day"]["day"])
        self.assertEqual("ROOM012", ctx["room_utilization_rankings"]["highest_utilized_room"]["room"])
        self.assertEqual("ROOM019", ctx["room_utilization_rankings"]["minimum_utilized_room"]["room"])
        self.assertEqual("COMP001", ctx["company_workload_rankings"]["highest_workload_company"]["company"])
        self.assertEqual("COMP008", ctx["company_workload_rankings"]["lowest_workload_company"]["company"])

    def test_assistant_stream_missing_api_key_yields_error_event(self) -> None:
        old_key = os.environ.get("GEMINI_API_KEY", None)
        os.environ["GEMINI_API_KEY"] = ""
        try:
            chunks = list(stream_assistant_service(
                question="Which room has the minimum utilization?",
                context={"status": "SCHEDULE_GENERATED"},
            ))
            output = "".join(chunks)
            self.assertIn("Assistant configuration is unavailable", output)
            self.assertIn('"type": "done"', output)
        finally:
            if old_key is not None:
                os.environ["GEMINI_API_KEY"] = old_key
            else:
                os.environ.pop("GEMINI_API_KEY", None)

    def test_assistant_query_missing_api_key_returns_graceful_response(self) -> None:
        old_key = os.environ.get("GEMINI_API_KEY", None)
        os.environ["GEMINI_API_KEY"] = ""
        try:
            req = AssistantQueryRequest(
                question="Can you explain the schedule?",
                context={"status": "SCHEDULE_GENERATED"},
            )
            result = query_assistant(req)
            self.assertIn("temporarily unavailable", result["answer"])
            self.assertFalse(result["configured"])
        finally:
            if old_key is not None:
                os.environ["GEMINI_API_KEY"] = old_key
            else:
                os.environ.pop("GEMINI_API_KEY", None)

    @patch("placementops.api.service._get_gemini_client")
    def test_assistant_stream_yields_mocked_gemini_deltas(self, mock_client_factory: MagicMock) -> None:
        old_key = os.environ.get("GEMINI_API_KEY", None)
        os.environ["GEMINI_API_KEY"] = "fake-test-key"
        try:
            mock_client = MagicMock()
            mock_chunk_1 = MagicMock()
            mock_chunk_1.text = "ROOM015 has the minimum utilization "
            mock_chunk_2 = MagicMock()
            mock_chunk_2.text = "at 1035 scheduled minutes."

            mock_client.models.generate_content_stream.return_value = [mock_chunk_1, mock_chunk_2]
            mock_client_factory.return_value = mock_client

            chunks = list(stream_assistant_service(
                question="Which room has the minimum utilization?",
                context={
                    "status": "SCHEDULE_GENERATED",
                    "metrics": {"total_workload": 859, "scheduled_interviews": 476},
                },
            ))

            full_output = "".join(chunks)
            self.assertIn('"type": "delta"', full_output)
            self.assertIn("ROOM015 has the minimum utilization", full_output)
            self.assertIn('"type": "done"', full_output)
        finally:
            if old_key is not None:
                os.environ["GEMINI_API_KEY"] = old_key
            else:
                os.environ.pop("GEMINI_API_KEY", None)

    @patch("placementops.api.service._get_gemini_client")
    def test_assistant_query_returns_mocked_gemini_answer(self, mock_client_factory: MagicMock) -> None:
        old_key = os.environ.get("GEMINI_API_KEY", None)
        os.environ["GEMINI_API_KEY"] = "fake-test-key"
        try:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "476 interviews are scheduled out of 859 requested."
            mock_client.models.generate_content.return_value = mock_response
            mock_client_factory.return_value = mock_client

            result = query_assistant_service(
                question="How many interviews are scheduled?",
                context={
                    "status": "SCHEDULE_GENERATED",
                    "metrics": {"total_workload": 859, "scheduled_interviews": 476},
                },
            )

            self.assertTrue(result["configured"])
            self.assertIn("476 interviews are scheduled", result["answer"])
        finally:
            if old_key is not None:
                os.environ["GEMINI_API_KEY"] = old_key
            else:
                os.environ.pop("GEMINI_API_KEY", None)

    @patch("placementops.api.service._get_gemini_client")
    def test_assistant_handles_gemini_rate_limiting_gracefully(self, mock_client_factory: MagicMock) -> None:
        old_key = os.environ.get("GEMINI_API_KEY", None)
        os.environ["GEMINI_API_KEY"] = "fake-test-key"
        try:
            mock_client = MagicMock()
            mock_client.models.generate_content_stream.side_effect = Exception("429 RESOURCE_EXHAUSTED: Quota exceeded")
            mock_client_factory.return_value = mock_client

            chunks = list(stream_assistant_service(
                question="Which day has the most interviews?",
                context={"status": "SCHEDULE_GENERATED"},
            ))

            full_output = "".join(chunks)
            self.assertIn('"type": "error"', full_output)
            self.assertIn("rate-limited", full_output)
            self.assertIn('"type": "done"', full_output)
        finally:
            if old_key is not None:
                os.environ["GEMINI_API_KEY"] = old_key
            else:
                os.environ.pop("GEMINI_API_KEY", None)


if __name__ == "__main__":
    unittest.main()
