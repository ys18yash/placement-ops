from __future__ import annotations

import copy
import unittest

from placementops.dataset import generate_dataset
from placementops.scheduling.constraints import can_assign
from placementops.scheduling.models import Disruption
from placementops.scheduling.replanner import replan_schedule
from placementops.scheduling.scheduler import generate_schedule


class ReplanningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = generate_dataset()
        cls.schedule = generate_schedule(cls.dataset)

    def test_unknown_disruption_keeps_schedule_unchanged(self) -> None:
        disruption = Disruption(
            id="DISRUPTION_UNKNOWN",
            type="UNKNOWN",
            day="DAY_1",
        )

        new_schedule, changes = replan_schedule(
            self.dataset,
            self.schedule,
            disruption,
        )

        self.assertEqual(
            self.schedule.to_dict(),
            new_schedule.to_dict(),
        )
        self.assertEqual([], changes)

    def test_replanner_does_not_mutate_original_schedule(self) -> None:
        original = copy.deepcopy(self.schedule)

        disruption = self._first_supported_disruption()

        replan_schedule(
            self.dataset,
            self.schedule,
            disruption,
        )

        self.assertEqual(
            original.to_dict(),
            self.schedule.to_dict(),
        )

    def test_replanner_is_deterministic(self) -> None:
        disruption = self._first_supported_disruption()

        result_one, changes_one = replan_schedule(
            self.dataset,
            self.schedule,
            disruption,
        )
        result_two, changes_two = replan_schedule(
            self.dataset,
            self.schedule,
            disruption,
        )

        self.assertEqual(
            result_one.to_dict(),
            result_two.to_dict(),
        )
        self.assertEqual(
            [change.to_dict() for change in changes_one],
            [change.to_dict() for change in changes_two],
        )

    def test_panel_dropout_replans_affected_interviews(self) -> None:
        assignment = self._find_assignment()

        disruption = Disruption(
            id="DISRUPTION_PANEL_1",
            type="PANEL_DROPOUT",
            day=assignment.day,
            resource_id=assignment.panel_id,
        )

        new_schedule, changes = replan_schedule(
            self.dataset,
            self.schedule,
            disruption,
        )

        affected_interview_ids = {
            item.interview_id
            for item in self.schedule.assignments
            if item.panel_id == assignment.panel_id
            and item.day == assignment.day
        }

        changed_ids = {
            change.interview_id
            for change in changes
        }

        self.assertTrue(affected_interview_ids)
        self.assertTrue(
            affected_interview_ids.issubset(changed_ids)
        )

        for new_assignment in new_schedule.assignments:
            if new_assignment.interview_id in affected_interview_ids:
                self.assertFalse(
                    new_assignment.panel_id == assignment.panel_id
                    and new_assignment.day == assignment.day
                )

    def test_room_unavailable_replans_affected_interviews(self) -> None:
        assignment = self._find_assignment()

        disruption = Disruption(
            id="DISRUPTION_ROOM_1",
            type="ROOM_UNAVAILABLE",
            day=assignment.day,
            resource_id=assignment.room_id,
        )

        new_schedule, changes = replan_schedule(
            self.dataset,
            self.schedule,
            disruption,
        )

        affected_interview_ids = {
            item.interview_id
            for item in self.schedule.assignments
            if item.room_id == assignment.room_id
            and item.day == assignment.day
        }

        changed_ids = {
            change.interview_id
            for change in changes
        }

        self.assertTrue(affected_interview_ids)
        self.assertTrue(
            affected_interview_ids.issubset(changed_ids)
        )

        for new_assignment in new_schedule.assignments:
            if new_assignment.interview_id in affected_interview_ids:
                self.assertFalse(
                    new_assignment.room_id == assignment.room_id
                    and new_assignment.day == assignment.day
                )

    def test_company_delay_moves_affected_interview_after_delay(self) -> None:
        assignment = self._find_assignment()

        disruption = Disruption(
            id="DISRUPTION_COMPANY_1",
            type="COMPANY_DELAY",
            day=assignment.day,
            resource_id=assignment.company_id,
            effective_time=assignment.start_time,
        )

        new_schedule, changes = replan_schedule(
            self.dataset,
            self.schedule,
            disruption,
        )

        affected_interview_ids = {
            item.interview_id
            for item in self.schedule.assignments
            if item.company_id == assignment.company_id
            and item.day == assignment.day
            and item.start_time >= assignment.start_time
        }

        changed_ids = {
            change.interview_id
            for change in changes
        }

        self.assertTrue(affected_interview_ids)
        self.assertTrue(
            affected_interview_ids.issubset(changed_ids)
        )

        for new_assignment in new_schedule.assignments:
            if new_assignment.interview_id in affected_interview_ids:
                if new_assignment.day == disruption.day:
                    self.assertGreaterEqual(
                        new_assignment.start_time,
                        disruption.effective_time,
                    )

    def test_unaffected_assignments_remain_unchanged(self) -> None:
        assignment = self._find_assignment()

        disruption = Disruption(
            id="DISRUPTION_PANEL_2",
            type="PANEL_DROPOUT",
            day=assignment.day,
            resource_id=assignment.panel_id,
        )

        new_schedule, _ = replan_schedule(
            self.dataset,
            self.schedule,
            disruption,
        )

        affected_interview_ids = {
            item.interview_id
            for item in self.schedule.assignments
            if item.panel_id == assignment.panel_id
            and item.day == assignment.day
        }

        original_unaffected = {
            item.interview_id: item
            for item in self.schedule.assignments
            if item.interview_id not in affected_interview_ids
        }

        replanned_unaffected = {
            item.interview_id: item
            for item in new_schedule.assignments
            if item.interview_id not in affected_interview_ids
        }

        self.assertEqual(
            original_unaffected,
            replanned_unaffected,
        )

    def test_result_assignments_still_satisfy_constraints(self) -> None:
        assignment = self._find_assignment()

        disruption = Disruption(
            id="DISRUPTION_PANEL_3",
            type="PANEL_DROPOUT",
            day=assignment.day,
            resource_id=assignment.panel_id,
        )

        new_schedule, _ = replan_schedule(
            self.dataset,
            self.schedule,
            disruption,
        )

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

        previous = []

        for current in new_schedule.assignments:
            result = can_assign(
                current,
                student=students[current.student_id],
                company=companies[current.company_id],
                panel=panels[current.panel_id],
                room=rooms[current.room_id],
                existing_assignments=previous,
            )

            self.assertTrue(
                result.valid,
                msg=result.reason,
            )

            previous.append(current)

    def test_every_interview_remains_scheduled_or_unscheduled(self) -> None:
        disruption = self._first_supported_disruption()

        new_schedule, _ = replan_schedule(
            self.dataset,
            self.schedule,
            disruption,
        )

        scheduled_ids = {
            assignment.interview_id
            for assignment in new_schedule.assignments
        }
        unscheduled_ids = set(
            new_schedule.unscheduled_interview_ids
        )
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

    def _find_assignment(self):
        self.assertTrue(
            self.schedule.assignments,
            "Baseline schedule contains no assignments.",
        )
        return self.schedule.assignments[0]

    def _first_supported_disruption(self) -> Disruption:
        assignment = self._find_assignment()

        return Disruption(
            id="DISRUPTION_TEST",
            type="PANEL_DROPOUT",
            day=assignment.day,
            resource_id=assignment.panel_id,
        )


if __name__ == "__main__":
    unittest.main()
