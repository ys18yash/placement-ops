from __future__ import annotations

import unittest

from placementops.dataset import generate_dataset
from placementops.scheduling.metrics import calculate_schedule_metrics
from placementops.scheduling.scheduler import generate_schedule


class SchedulingMetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = generate_dataset()
        cls.schedule = generate_schedule(cls.dataset)

    def test_metrics_include_core_counts(self) -> None:
        metrics = calculate_schedule_metrics(
            self.dataset,
            self.schedule,
        )

        self.assertIn("scheduled_interviews", metrics)
        self.assertIn("unscheduled_interviews", metrics)
        self.assertIn("completion_rate", metrics)

    def test_scheduled_plus_unscheduled_equals_total(self) -> None:
        metrics = calculate_schedule_metrics(
            self.dataset,
            self.schedule,
        )

        self.assertEqual(
            metrics["scheduled_interviews"]
            + metrics["unscheduled_interviews"],
            len(self.dataset.interviews),
        )

    def test_completion_rate_is_between_zero_and_one(self) -> None:
        metrics = calculate_schedule_metrics(
            self.dataset,
            self.schedule,
        )

        self.assertGreaterEqual(metrics["completion_rate"], 0.0)
        self.assertLessEqual(metrics["completion_rate"], 1.0)

    def test_metrics_include_resource_utilization(self) -> None:
        metrics = calculate_schedule_metrics(
            self.dataset,
            self.schedule,
        )

        self.assertIn("room_utilization", metrics)
        self.assertIn("panel_utilization", metrics)

    def test_utilization_values_are_non_negative(self) -> None:
        metrics = calculate_schedule_metrics(
            self.dataset,
            self.schedule,
        )

        self.assertGreaterEqual(metrics["room_utilization"], 0.0)
        self.assertGreaterEqual(metrics["panel_utilization"], 0.0)

    def test_metrics_include_schedule_span(self) -> None:
        metrics = calculate_schedule_metrics(
            self.dataset,
            self.schedule,
        )

        self.assertIn("schedule_span", metrics)

    def test_metrics_are_deterministic(self) -> None:
        first = calculate_schedule_metrics(
            self.dataset,
            self.schedule,
        )
        second = calculate_schedule_metrics(
            self.dataset,
            self.schedule,
        )

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
