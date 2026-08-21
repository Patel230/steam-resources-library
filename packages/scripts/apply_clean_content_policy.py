#!/usr/bin/env python3
"""Apply Signal Atlas's strict English and substantive-material catalog policy.

Run `audit_clean_content.py --pdf` first. This applicator keeps only rows with
English visible material, an approved question/MCQ/solution resource class, and
for PDFs, a clean-content audit decision of `keep`. It preserves every removal
reason in research/clean_content_removed_records.csv.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "client" / "src" / "data"
RESEARCH_DIR = ROOT / "research"
EXPECTED_FIELDS = [
    "country", "track", "topic_tags", "priority", "source_type", "source_title",
    "source_url", "resource_title", "resource_url", "resource_class", "language",
    "notes", "access_model", "verification_status", "free_resource",
]
STRICT_ENGLISH = {"English", "English source", "English source code"}
PDF_RE = re.compile(r"\.pdf(?:[?#].*)?$", re.IGNORECASE)
ALLOWED_CLASS_RE = re.compile(
    r"(exam|past.*paper|question|problem|contest|olympiad|quiz|assignment|mcq|multiple choice|solution|editorial|practice|exercise)",
    re.IGNORECASE,
)


def active_paths() -> list[Path]:
    paths: list[Path] = []
    for path in sorted(DATA_DIR.glob("*.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            header = next(csv.reader(handle), [])
        if header == EXPECTED_FIELDS:
            paths.append(path)
    return paths


def is_pdf(row: dict[str, str]) -> bool:
    return bool(PDF_RE.search(row.get("resource_url", "").strip()))


def load_pdf_decisions() -> dict[tuple[str, str], dict[str, str]]:
    audit_paths = list(RESEARCH_DIR.glob("clean_content_pdf_audit_*.csv"))
    if not audit_paths:
        raise SystemExit("Missing clean-content PDF audit. Run audit_clean_content.py --pdf first.")
    audit_path = max(audit_paths, key=lambda path: path.stat().st_mtime)
    with audit_path.open(newline="", encoding="utf-8") as handle:
        return {(row["_file"], row["_line"]): row for row in csv.DictReader(handle)}


def decide(row: dict[str, str], audit: dict[tuple[str, str], dict[str, str]], path: Path, line: int) -> tuple[bool, str]:
    language = row.get("language", "").strip()
    if language not in STRICT_ENGLISH:
        return False, f"non-English visible-content metadata: {language or '(blank)'}"
    if not ALLOWED_CLASS_RE.search(row.get("resource_class", "")):
        return False, f"non-substantive resource class: {row.get('resource_class', '')}"
    if not is_pdf(row):
        return True, "English question/MCQ/solution-class web resource"
    key = (str(path.relative_to(ROOT)), str(line))
    result = audit.get(key)
    if not result:
        return False, "missing PDF clean-content audit decision"
    if result.get("decision") != "keep":
        return False, f"PDF clean-content audit {result.get('decision')}: {result.get('evidence', '')}"
    return True, "English PDF with substantive question/solution evidence"


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="rewrite active CSVs after producing the removal ledger")
    args = parser.parse_args()
    audits = load_pdf_decisions()
    removals: list[dict[str, str]] = []
    kept_by_path: dict[Path, list[dict[str, str]]] = {}
    reasons = Counter()
    total = 0

    for path in active_paths():
        kept: list[dict[str, str]] = []
        with path.open(newline="", encoding="utf-8") as handle:
            for line, row in enumerate(csv.DictReader(handle), start=2):
                total += 1
                keep, reason = decide(row, audits, path, line)
                if keep:
                    row["language"] = "English"
                    kept.append(row)
                else:
                    reasons[reason.split(":", 1)[0]] += 1
                    removals.append({
                        "file": str(path.relative_to(ROOT)), "line": str(line), "reason": reason,
                        **{field: row.get(field, "") for field in EXPECTED_FIELDS},
                    })
        kept_by_path[path] = kept

    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    removal_path = RESEARCH_DIR / "clean_content_removed_records.csv"
    with removal_path.open("w", newline="", encoding="utf-8") as handle:
        fields = ["file", "line", "reason", *EXPECTED_FIELDS]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(removals)

    print({"active_rows": total, "kept": total - len(removals), "removed": len(removals), "reasons": dict(reasons), "ledger": str(removal_path.relative_to(ROOT)), "apply": args.apply})
    if args.apply:
        for path, kept in kept_by_path.items():
            write_rows(path, kept)


if __name__ == "__main__":
    main()
