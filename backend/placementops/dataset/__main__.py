"""CLI entry point for deterministic dataset generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .generator import DEFAULT_SEED, generate_dataset
from .storage import write_dataset_files
from .summary import build_dataset_summary
from .validation import validate_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic PlacementOps dataset files.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed for deterministic generation.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/generated"),
        help="Directory where JSON dataset files will be written.",
    )
    args = parser.parse_args()

    dataset = generate_dataset(seed=args.seed)
    report = validate_dataset(dataset)
    summary = build_dataset_summary(dataset)
    written_files = write_dataset_files(dataset, args.output_dir)

    print(json.dumps({"written_files": {k: str(v) for k, v in written_files.items()}, "summary": summary}, indent=2))
    if not report.valid:
        print(json.dumps(report.to_dict(), indent=2))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
