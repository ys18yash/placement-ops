from __future__ import annotations

import copy
import statistics
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from placementops.dataset import calculate_dataset_metrics, generate_dataset, validate_dataset
from placementops.dataset.models import Interview, Shortlist


class DatasetGeneratorTests(unittest.TestCase):
    def test_default_seed_dataset_meets_core_counts(self) -> None:
        dataset = generate_dataset()

        self.assertEqual(35, len(dataset.companies))
        self.assertEqual(800, len(dataset.students))
        self.assertEqual(20, len(dataset.rooms))
        self.assertEqual(len(dataset.shortlists), len(dataset.interviews))
        self.assertGreaterEqual(len(dataset.panels), 35)

        report = validate_dataset(dataset)
        self.assertTrue(report.valid, msg="\n".join(report.errors))

    def test_generation_is_deterministic_for_same_seed(self) -> None:
        dataset_one = generate_dataset().to_dict()
        dataset_two = generate_dataset().to_dict()
        self.assertEqual(dataset_one, dataset_two)

    def test_different_seed_changes_dataset_shape(self) -> None:
        default_dataset = generate_dataset()
        alternate_dataset = generate_dataset(seed=20260830)

        default_pairs = {(item.student_id, item.company_id) for item in default_dataset.shortlists}
        alternate_pairs = {(item.student_id, item.company_id) for item in alternate_dataset.shortlists}
        self.assertNotEqual(default_pairs, alternate_pairs)

    def test_summary_metrics_include_zero_shortlist_students(self) -> None:
        dataset = generate_dataset()
        metrics = calculate_dataset_metrics(dataset)
        all_counts = []
        shortlist_counts = {student.id: 0 for student in dataset.students}
        for shortlist in dataset.shortlists:
            shortlist_counts[shortlist.student_id] += 1
        for student in dataset.students:
            all_counts.append(shortlist_counts[student.id])

        self.assertEqual(statistics.median(all_counts), metrics["shortlist_distribution"]["all_students"]["median"])
        self.assertIn("students_with_8_to_15", metrics["shortlist_distribution"]["all_students"])
        self.assertIn("room_demand_capacity_ratio", metrics["capacity"])
        self.assertIn("panel_demand_capacity_ratio", metrics["capacity"])

    def test_realism_metrics_stay_within_expected_thresholds(self) -> None:
        metrics = calculate_dataset_metrics(generate_dataset())

        self.assertLessEqual(metrics["capacity"]["room_demand_capacity_ratio"], 1.03)
        self.assertGreaterEqual(metrics["capacity"]["room_demand_capacity_ratio"], 0.78)
        self.assertLessEqual(metrics["capacity"]["panel_demand_capacity_ratio"], 0.92)
        self.assertLessEqual(metrics["shortlist_distribution"]["active_students"]["students_with_0_pct"], 25.0)
        self.assertGreaterEqual(metrics["cgpa_shortlist_correlation"]["active_students"], 0.45)
        self.assertGreaterEqual(metrics["popularity_shortlist_correlation"], 0.45)

    def test_validation_detects_invalid_interview_reference(self) -> None:
        dataset = generate_dataset()
        broken_dataset = copy.deepcopy(dataset)
        broken_dataset.interviews[0] = Interview(
            id=broken_dataset.interviews[0].id,
            student_id="STU9999",
            company_id=broken_dataset.interviews[0].company_id,
            duration_minutes=broken_dataset.interviews[0].duration_minutes,
            status=broken_dataset.interviews[0].status,
        )

        report = validate_dataset(broken_dataset)
        self.assertFalse(report.valid)
        self.assertTrue(any("unknown student" in error for error in report.errors))

    def test_validation_detects_duplicate_shortlist_relationship(self) -> None:
        dataset = generate_dataset()
        broken_dataset = copy.deepcopy(dataset)
        original = broken_dataset.shortlists[0]
        broken_dataset.shortlists.append(
            Shortlist(
                id="SHORT99999",
                student_id=original.student_id,
                company_id=original.company_id,
            )
        )

        report = validate_dataset(broken_dataset)
        self.assertFalse(report.valid)
        self.assertTrue(any("Duplicate shortlist relationship" in error for error in report.errors))


if __name__ == "__main__":
    unittest.main()
