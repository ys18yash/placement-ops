"""Dataset summary statistics."""

from __future__ import annotations

from .metrics import calculate_dataset_metrics
from .models import Dataset


def build_dataset_summary(dataset: Dataset) -> dict[str, object]:
    metrics = calculate_dataset_metrics(dataset)
    return {
        "seed": dataset.seed,
        "counts": metrics["counts"],
        "cgpa_statistics": metrics["cgpa_statistics"],
        "average_shortlists": metrics["averages"],
        "shortlist_distribution": metrics["shortlist_distribution"],
        "cgpa_band_statistics": metrics["cgpa_band_statistics"],
        "cgpa_shortlist_correlation": metrics["cgpa_shortlist_correlation"],
        "company_shortlist_statistics": metrics["company_shortlist_statistics"],
        "company_popularity": metrics["company_popularity"],
        "popularity_shortlist_correlation": metrics["popularity_shortlist_correlation"],
        "capacity": metrics["capacity"],
        "day_demand_estimate": metrics["day_demand_estimate"],
        "interview_count": metrics["counts"]["interviews"],
    }
