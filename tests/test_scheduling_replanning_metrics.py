from __future__ import annotations

import unittest

from placementops.dataset import generate_dataset
from placementops.scheduling.metrics import calculate_replanning_metrics
from placementops.scheduling.replanner import replan_schedule
from placementops.scheduling.scheduler import generate_schedule
from placementops.scheduling.models import Disruption


class ReplanningMetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = generate_dataset()
        cls.schedule = generate_schedule(cls.dataset)

    def test_metrics_include_core_replanning_counts(self) -> None:
        disruption = Disruption(
            id="DISRUPTION_TEST",
            type="COMPANY_DELAY",
            day="DAY_1",
            effective_time="12:00",
            resource_id=self.dataset.companies[0].id,
        )

        replanned, changes = replan_schedule(
            self.dataset,
            self.schedule,
            disruption,
        )

        metrics = calculate_replanning_metrics(
            self.schedule,
            replanned,
            changes,
        )

        self.assertIn("original_scheduled", metrics)
        self.assertIn("replanned_scheduled", metrics)
        self.assertIn("affected_interviews", metrics)
        self.assertIn("unchanged_interviews", metrics)
        self.assertIn("moved_interviews", metrics)
        self.assertIn("schedule_change_count", metrics)
        self.assertIn("change_rate", metrics)

    def test_change_counts_are_consistent(self) -> None:
        disruption = Disruption(
            id="DISRUPTION_TEST",
            type="COMPANY_DELAY",
            day="DAY_1",
            effective_time="12:00",
            resource_id=self.dataset.companies[0].id,
        )

        replanned, changes = replan_schedule(
            self.dataset,
            self.schedule,
            disruption,
        )

        metrics = calculate_replanning_metrics(
            self.schedule,
            replanned,
            changes,
        )

        self.assertEqual(
            metrics["schedule_change_count"],
            len(changes),
        )

        self.assertGreaterEqual(
            metrics["affected_interviews"],
            metrics["moved_interviews"],
        )

    def test_change_rate_is_between_zero_and_one(self) -> None:
        disruption = Disruption(
            id="DISRUPTION_TEST",
            type="COMPANY_DELAY",
            day="DAY_1",
            effective_time="12:00",
            resource_id=self.dataset.companies[0].id,
        )

        replanned, changes = replan_schedule(
            self.dataset,
            self.schedule,
            disruption,
        )

        metrics = calculate_replanning_metrics(
            self.schedule,
            replanned,
            changes,
        )

        self.assertGreaterEqual(metrics["change_rate"], 0.0)
        self.assertLessEqual(metrics["change_rate"], 1.0)

    def test_metrics_are_deterministic(self) -> None:
        disruption = Disruption(
            id="DISRUPTION_TEST",
            type="COMPANY_DELAY",
            day="DAY_1",
            effective_time="12:00",
            resource_id=self.dataset.companies[0].id,
        )

        replanned_one, changes_one = replan_schedule(
            self.dataset,
            self.schedule,
            disruption,
        )

        replanned_two, changes_two = replan_schedule(
            self.dataset,
            self.schedule,
            disruption,
        )

        first = calculate_replanning_metrics(
            self.schedule,
            replanned_one,
            changes_one,
        )

        second = calculate_replanning_metrics(
            self.schedule,
            replanned_two,
            changes_two,
        )

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
