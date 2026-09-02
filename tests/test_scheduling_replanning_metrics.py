from __future__ import annotations

import unittest

from placementops.dataset import generate_dataset
from placementops.scheduling.metrics import calculate_replanning_metrics
from placementops.scheduling.models import (
    Disruption,
    Schedule,
    ScheduleAssignment,
    ScheduleChange,
)
from placementops.scheduling.replanner import replan_schedule
from placementops.scheduling.scheduler import generate_schedule


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

    def test_metrics_count_affected_and_newly_unscheduled_from_changes(self) -> None:
        original = Schedule(
            assignments=[
                ScheduleAssignment(
                    interview_id="INT1",
                    student_id="STU1",
                    company_id="COMP1",
                    panel_id="PANEL1",
                    room_id="ROOM1",
                    day="DAY_1",
                    start_time="09:00",
                    end_time="09:30",
                ),
                ScheduleAssignment(
                    interview_id="INT2",
                    student_id="STU2",
                    company_id="COMP1",
                    panel_id="PANEL1",
                    room_id="ROOM2",
                    day="DAY_1",
                    start_time="09:30",
                    end_time="10:00",
                ),
            ],
            unscheduled_interview_ids=["INT3"],
        )
        replanned = Schedule(
            assignments=[
                ScheduleAssignment(
                    interview_id="INT1",
                    student_id="STU1",
                    company_id="COMP1",
                    panel_id="PANEL2",
                    room_id="ROOM3",
                    day="DAY_1",
                    start_time="10:00",
                    end_time="10:30",
                ),
            ],
            unscheduled_interview_ids=["INT2", "INT3"],
        )
        changes = [
            ScheduleChange(
                interview_id="INT1",
                change_type="RESCHEDULED",
                old_assignment=original.assignments[0],
                new_assignment=replanned.assignments[0],
            ),
            ScheduleChange(
                interview_id="INT2",
                change_type="UNSCHEDULED",
                old_assignment=original.assignments[1],
                new_assignment=None,
            ),
        ]

        metrics = calculate_replanning_metrics(
            original,
            replanned,
            changes,
        )

        self.assertEqual(2, metrics["affected_interviews"])
        self.assertEqual(0, metrics["unchanged_interviews"])
        self.assertEqual(1, metrics["moved_interviews"])
        self.assertEqual(1, metrics["newly_unscheduled_interviews"])
        self.assertEqual(2, metrics["schedule_change_count"])


if __name__ == "__main__":
    unittest.main()
