"""Serialization helpers for generated datasets."""

from __future__ import annotations

import json
from pathlib import Path

from .models import Dataset
from .summary import build_dataset_summary
from .validation import validate_dataset


def write_dataset_files(dataset: Dataset, output_dir: Path | str) -> dict[str, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    summary = build_dataset_summary(dataset)
    validation_report = validate_dataset(dataset)
    payloads: dict[str, object] = {
        "dataset.json": dataset.to_dict(),
        "companies.json": [company for company in dataset.to_dict()["companies"]],
        "students.json": [student for student in dataset.to_dict()["students"]],
        "rooms.json": [room for room in dataset.to_dict()["rooms"]],
        "panels.json": [panel for panel in dataset.to_dict()["panels"]],
        "shortlists.json": [shortlist for shortlist in dataset.to_dict()["shortlists"]],
        "interviews.json": [interview for interview in dataset.to_dict()["interviews"]],
        "summary.json": summary,
        "validation.json": validation_report.to_dict(),
    }

    written_files: dict[str, Path] = {}
    for filename, payload in payloads.items():
        target = output_path / filename
        target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        written_files[filename] = target
    return written_files
