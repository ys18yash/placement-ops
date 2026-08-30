from __future__ import annotations

import unittest

from placementops.dataset import generate_dataset
from placementops.scheduling.constraints import can_assign
from placementops.scheduling.models import ScheduleAssignment


class SchedulingConstraintTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = generate_dataset()

        cls.students = {student.id: student for student in cls.dataset.students}
        cls.companies = {company.id: company for company in cls.dataset.companies}
        cls.panels = {
            panel.id: panel
            for panel in cls.dataset.panels
            if panel.status == "AVAILABLE"
        }
        cls.rooms = {
            room.id: room
            for room in cls.dataset.rooms
            if room.status == "AVAILABLE"
        }

    def _find_valid_candidate(self):
        for interview in self.dataset.interviews:
            student = self.students[interview.student_id]
            company = self.companies[interview.company_id]

            for panel in self.panels.values():
                if panel.company_id != company.id:
                    continue

                for room in self.rooms.values():
                    for window in student.availability:
                        if window.day not in company.placement_days:
                            continue

                        if not any(
                            company_window.day == window.day
                            and company_window.start_time <= window.start_time
                            and window.end_time <= company_window.end_time
                            for company_window in company.availability
                        ):
                            continue

                        if not any(
                            panel_window.day == window.day
                            and panel_window.start_time <= window.start_time
                            and window.end_time <= panel_window.end_time
                            for panel_window in panel.availability
                        ):
                            continue

                        if not any(
                            room_window.day == window.day
                            and room_window.start_time <= window.start_time
                            and window.end_time <= room_window.end_time
                            for room_window in room.availability
                        ):
                            continue

                        duration = interview.duration_minutes
                        start_minutes = (
                            int(window.start_time[:2]) * 60
                            + int(window.start_time[3:])
                        )
                        end_minutes = start_minutes + duration

                        if end_minutes > (
                            int(window.end_time[:2]) * 60
                            + int(window.end_time[3:])
                        ):
                            continue

                        end_time = f"{end_minutes // 60:02d}:{end_minutes % 60:02d}"

                        assignment = ScheduleAssignment(
                            interview_id=interview.id,
                            student_id=student.id,
                            company_id=company.id,
                            panel_id=panel.id,
                            room_id=room.id,
                            day=window.day,
                            start_time=window.start_time,
                            end_time=end_time,
                        )

                        result = can_assign(
                            assignment,
                            student=student,
                            company=company,
                            panel=panel,
                            room=room,
                        )

                        if result.valid:
                            return assignment, student, company, panel, room

        self.fail("Could not find a valid candidate assignment.")

    def test_valid_assignment_is_accepted(self) -> None:
        assignment, student, company, panel, room = self._find_valid_candidate()

        result = can_assign(
            assignment,
            student=student,
            company=company,
            panel=panel,
            room=room,
        )

        self.assertTrue(result.valid)
        self.assertIsNone(result.reason)

    def test_student_overlap_is_rejected(self) -> None:
        assignment, student, company, panel, room = self._find_valid_candidate()

        result = can_assign(
            assignment,
            student=student,
            company=company,
            panel=panel,
            room=room,
            existing_assignments=[assignment],
        )

        self.assertFalse(result.valid)
        self.assertIn("Student", result.reason)

    def test_panel_overlap_is_rejected(self) -> None:
        assignment, student, company, panel, room = self._find_valid_candidate()

        conflicting = ScheduleAssignment(
            interview_id="INTERVIEW_CONFLICT",
            student_id="STU_CONFLICT",
            company_id=company.id,
            panel_id=panel.id,
            room_id=room.id,
            day=assignment.day,
            start_time=assignment.start_time,
            end_time=assignment.end_time,
        )

        result = can_assign(
            assignment,
            student=student,
            company=company,
            panel=panel,
            room=room,
            existing_assignments=[conflicting],
        )

        self.assertFalse(result.valid)
        self.assertIn("Panel", result.reason)

    def test_room_overlap_is_rejected(self) -> None:
        assignment, student, company, panel, room = self._find_valid_candidate()

        conflicting = ScheduleAssignment(
            interview_id="INTERVIEW_CONFLICT",
            student_id="STU_CONFLICT",
            company_id=company.id,
            panel_id="PANEL_CONFLICT",
            room_id=room.id,
            day=assignment.day,
            start_time=assignment.start_time,
            end_time=assignment.end_time,
        )

        result = can_assign(
            assignment,
            student=student,
            company=company,
            panel=panel,
            room=room,
            existing_assignments=[conflicting],
        )

        self.assertFalse(result.valid)
        self.assertIn("Room", result.reason)

    def test_invalid_day_is_rejected(self) -> None:
        assignment, student, company, panel, room = self._find_valid_candidate()

        invalid_assignment = ScheduleAssignment(
            interview_id=assignment.interview_id,
            student_id=assignment.student_id,
            company_id=assignment.company_id,
            panel_id=assignment.panel_id,
            room_id=assignment.room_id,
            day="DAY_5",
            start_time=assignment.start_time,
            end_time=assignment.end_time,
        )

        result = can_assign(
            invalid_assignment,
            student=student,
            company=company,
            panel=panel,
            room=room,
        )

        self.assertFalse(result.valid)
        self.assertIn("Invalid placement day", result.reason)

    def test_outside_operating_hours_is_rejected(self) -> None:
        assignment, student, company, panel, room = self._find_valid_candidate()

        invalid_assignment = ScheduleAssignment(
            interview_id=assignment.interview_id,
            student_id=assignment.student_id,
            company_id=assignment.company_id,
            panel_id=assignment.panel_id,
            room_id=assignment.room_id,
            day=assignment.day,
            start_time="08:00",
            end_time="09:00",
        )

        result = can_assign(
            invalid_assignment,
            student=student,
            company=company,
            panel=panel,
            room=room,
        )

        self.assertFalse(result.valid)
        self.assertIn("operating hours", result.reason)

    def test_dropped_panel_is_rejected(self) -> None:
        assignment, student, company, _, room = self._find_valid_candidate()

        dropped_panel = next(
            (
                panel
                for panel in self.dataset.panels
                if panel.company_id == company.id
                and panel.status == "DROPPED"
            ),
            None,
        )

        if dropped_panel is None:
            self.skipTest("Dataset contains no dropped panel for this company.")

        result = can_assign(
            assignment,
            student=student,
            company=company,
            panel=dropped_panel,
            room=room,
        )

        self.assertFalse(result.valid)
        self.assertIn("not available", result.reason)

    def test_unavailable_room_is_rejected(self) -> None:
        assignment, student, company, panel, _ = self._find_valid_candidate()

        unavailable_room = next(
            (
                room
                for room in self.dataset.rooms
                if room.status == "UNAVAILABLE"
            ),
            None,
        )

        if unavailable_room is None:
            self.skipTest("Dataset contains no unavailable room.")

        result = can_assign(
            assignment,
            student=student,
            company=company,
            panel=panel,
            room=unavailable_room,
        )

        self.assertFalse(result.valid)
        self.assertIn("not available", result.reason)


if __name__ == "__main__":
    unittest.main()
