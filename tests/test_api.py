from __future__ import annotations

import unittest

from fastapi import HTTPException
from pydantic import ValidationError

from placementops.api.routes import (
    DisruptionRequest,
    ReplanRequest,
    replan_schedule,
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


if __name__ == "__main__":
    unittest.main()
