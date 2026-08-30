from __future__ import annotations

import copy
import unittest

from placementops.dataset import generate_dataset
from placementops.scheduling.constraints import can_assign
from placementops.scheduling.scheduler import generate_schedule


class SchedulingTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = generate_dataset()

    def test_scheduler_produces_schedule(self) -> None:
        schedule = generate_schedule(self.dataset)

        self.assertGreater(len(schedule.assignments), 0)
        self.assertEqual(
            len(schedule.assignments) + len(schedule.unscheduled_interview_ids),
            len(self.dataset.interviews),
        )

    def test_every_interview_is_scheduled_or_unscheduled(self) -> None:
        schedule = generate_schedule(self.dataset)

        scheduled_ids = {
            assignment.interview_id
            for assignment in schedule.assignments
        }
        unscheduled_ids = set(schedule.unscheduled_interview_ids)
        interview_ids = {
            interview.id
            for interview in self.dataset.interviews
        }

        self.assertEqual(
            scheduled_ids | unscheduled_ids,
            interview_ids,
        )

        self.assertEqual(
            len(scheduled_ids & unscheduled_ids),
            0,
        )

    def test_no_student_overlaps(self) -> None:
        schedule = generate_schedule(self.dataset)

        assignments = sorted(
            schedule.assignments,
            key=lambda item: (
                item.student_id,
                item.day,
                item.start_time,
            ),
        )

        for previous, current in zip(assignments, assignments[1:]):
            if (
                previous.student_id == current.student_id
                and previous.day == current.day
            ):
                self.assertGreaterEqual(
                    current.start_time,
                    previous.end_time,
                )

    def test_no_panel_overlaps(self) -> None:
        schedule = generate_schedule(self.dataset)

        assignments = sorted(
            schedule.assignments,
            key=lambda item: (
                item.panel_id,
                item.day,
                item.start_time,
            ),
        )

        for previous, current in zip(assignments, assignments[1:]):
            if (
                previous.panel_id == current.panel_id
                and previous.day == current.day
            ):
                self.assertGreaterEqual(
                    current.start_time,
                    previous.end_time,
                )

    def test_no_room_overlaps(self) -> None:
        schedule = generate_schedule(self.dataset)

        assignments = sorted(
            schedule.assignments,
            key=lambda item: (
                item.room_id,
                item.day,
                item.start_time,
            ),
        )

        for previous, current in zip(assignments, assignments[1:]):
            if (
                previous.room_id == current.room_id
                and previous.day == current.day
            ):
                self.assertGreaterEqual(
                    current.start_time,
                    previous.end_time,
                )

    def test_all_assignments_satisfy_constraints(self) -> None:
        students = {
            student.id: student
            for student in self.dataset.students
        }
        companies = {
            company.id: company
            for company in self.dataset.companies
        }
        panels = {
            panel.id: panel
            for panel in self.dataset.panels
        }
        rooms = {
            room.id: room
            for room in self.dataset.rooms
        }

        schedule = generate_schedule(self.dataset)

        previous_assignments = []

        for assignment in schedule.assignments:
            result = can_assign(
                assignment,
                student=students[assignment.student_id],
                company=companies[assignment.company_id],
                panel=panels[assignment.panel_id],
                room=rooms[assignment.room_id],
                existing_assignments=previous_assignments,
            )

            self.assertTrue(
                result.valid,
                msg=result.reason,
            )

            previous_assignments.append(assignment)

    def test_scheduler_is_deterministic(self) -> None:
        schedule_one = generate_schedule(self.dataset).to_dict()
        schedule_two = generate_schedule(self.dataset).to_dict()

        self.assertEqual(schedule_one, schedule_two)

    def test_scheduler_does_not_mutate_dataset(self) -> None:
        dataset_copy = copy.deepcopy(self.dataset)

        generate_schedule(self.dataset)

        self.assertEqual(
            self.dataset.to_dict(),
            dataset_copy.to_dict(),
        )


if __name__ == "__main__":
    unittest.main()
