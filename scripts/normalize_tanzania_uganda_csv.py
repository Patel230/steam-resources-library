#!/usr/bin/env python3
"""Normalize accidental physical line wraps in the Tanzania and Uganda CSV tranches.

Both files are first-party records written with a 15-column schema. A manual line
wrap was introduced inside the free-text `notes` cell of each data row, which made
the generator count catalog records but miss their `free_resource=Yes` field. This
utility joins continuation lines, validates the schema, and writes RFC 4180 CSV.
"""

from __future__ import annotations

import csv
from pathlib import Path


FILES = {
    "Tanzania": Path("client/src/data/tanzania_necta_verified_resources.csv"),
    "Uganda": Path("client/src/data/uganda_uneb_verified_resources.csv"),
}
EXPECTED_HEADER = [
    "country", "track", "topic_tags", "priority", "source_type", "source_title",
    "source_url", "resource_title", "resource_url", "resource_class", "language",
    "notes", "access_model", "verification_status", "free_resource",
]


def normalize(path: Path, country: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError(f"{path}: empty file")

    records = [lines[0]]
    current = ""
    for line in lines[1:]:
        if line.startswith(f"{country},"):
            if current:
                records.append(current)
            current = line
        else:
            current += line
    if current:
        records.append(current)

    if records[0].split(",") != EXPECTED_HEADER:
        raise ValueError(f"{path}: unexpected header")
    parsed = [EXPECTED_HEADER]
    for row_number, record in enumerate(records[1:], start=2):
        # The original manually-authored files left commas in the prose `notes`
        # field unquoted. Preserve that prose by treating columns 0–10 and the
        # final three columns as fixed, and joining the middle fragments back.
        fields = record.split(",")
        if len(fields) < len(EXPECTED_HEADER):
            raise ValueError(f"{path}: row {row_number} has too few fields")
        row = [*fields[:11], ",".join(fields[11:-3]), *fields[-3:]]
        if len(row) != len(EXPECTED_HEADER):
            raise ValueError(f"{path}: row {row_number} normalization failed")
        if row[0] != country or row[-1].strip().lower() != "yes":
            raise ValueError(f"{path}: row {row_number} failed country/free validation")
        parsed.append(row)

    with path.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(parsed)
    print(f"Normalized {path}: {len(parsed) - 1} rows")


def main() -> None:
    for country, path in FILES.items():
        normalize(path, country)


if __name__ == "__main__":
    main()
