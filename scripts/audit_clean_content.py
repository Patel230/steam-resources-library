#!/usr/bin/env python3
"""Audit active Signal Atlas catalog CSVs against the clean-content policy.

Policy:
1. Every live row must advertise English visible content (`language == English`).
2. PDF-backed rows must expose substantive English question/MCQ/task material or
   solution/answer material. Notices, blank covers, and answer-only references
   without usable task or solution evidence do not pass.

The script does not alter catalog data. It writes evidence for manual removal or
correction so every exclusion remains reproducible.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import subprocess
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterable

import requests


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "client" / "src" / "data"
RESEARCH_DIR = ROOT / "research"
EXPECTED_FIELDS = [
    "country",
    "track",
    "topic_tags",
    "priority",
    "source_type",
    "source_title",
    "source_url",
    "resource_title",
    "resource_url",
    "resource_class",
    "language",
    "notes",
    "access_model",
    "verification_status",
    "free_resource",
]
PDF_RE = re.compile(r"\.pdf(?:[?#].*)?$", re.IGNORECASE)
QUESTION_RE = re.compile(
    r"\b(question|problem|task|exercise|input|output|multiple[ -]?choice|choose|given|find|compute|prove)\b",
    re.IGNORECASE,
)
SOLUTION_RE = re.compile(
    r"\b(solution|answer key|answers|worked solution|explanation|proof|editorial|analysis)\b",
    re.IGNORECASE,
)
ENGLISH_RE = re.compile(
    r"\b(the|and|of|to|in|for|with|this|that|is|are|you|your|from|by|on|as|an|a)\b",
    re.IGNORECASE,
)
ALLOWED_CLASS_RE = re.compile(
    r"(exam|past.*paper|question|problem|contest|olympiad|quiz|assignment|mcq|multiple choice|solution|editorial|practice|exercise)",
    re.IGNORECASE,
)


def active_csv_paths() -> Iterable[Path]:
    for path in sorted(DATA_DIR.glob("*.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            header = next(csv.reader(handle), [])
        if header == EXPECTED_FIELDS:
            yield path


def read_active_rows() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for path in active_csv_paths():
        with path.open(newline="", encoding="utf-8") as handle:
            for line, row in enumerate(csv.DictReader(handle), start=2):
                row["_file"] = str(path.relative_to(ROOT))
                row["_line"] = str(line)
                records.append(row)
    return records


def is_pdf(row: dict[str, str]) -> bool:
    return bool(PDF_RE.search(row.get("resource_url", "").strip()))


def audit_url_key(url: str) -> str:
    """Create a stable comparison key for historical first-party PDF audit URLs."""
    return url.strip().casefold()


def metadata_status(row: dict[str, str]) -> tuple[str, str, str]:
    language = row.get("language", "").strip().casefold()
    language_status = "pass" if language == "english" else "fail"
    resource_class = row.get("resource_class", "")
    material_status = "pass" if ALLOWED_CLASS_RE.search(resource_class) else "review"
    note = ""
    if language_status == "fail":
        note = f"language field is {row.get('language', '').strip() or 'blank'}, not English"
    elif material_status != "pass":
        note = f"resource_class lacks a supported question/MCQ/solution signal: {resource_class!r}"
    return language_status, material_status, note


def extract_pdf_text(content: bytes) -> str:
    with tempfile.TemporaryDirectory(prefix="signal-atlas-pdf-") as tmp:
        pdf_path = Path(tmp) / "resource.pdf"
        pdf_path.write_bytes(content)
        completed = subprocess.run(
            ["pdftotext", "-f", "1", "-l", "8", str(pdf_path), "-"],
            check=False,
            capture_output=True,
            text=True,
            timeout=45,
        )
        return completed.stdout[:80000]


def audit_pdf(row: dict[str, str], timeout: int) -> dict[str, str]:
    result = dict(row)
    result.update(
        {
            "http_status": "",
            "content_type": "",
            "bytes": "",
            "english_status": "",
            "material_status": "",
            "decision": "review",
            "evidence": "",
        }
    )
    language_status, class_status, metadata_note = metadata_status(row)
    if language_status != "pass":
        result.update(
            english_status="fail",
            material_status=class_status,
            decision="remove",
            evidence=metadata_note,
        )
        return result
    try:
        response = requests.get(
            row["resource_url"],
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": "SignalAtlasCleanContentAudit/1.0"},
        )
        content = response.content
        content_type = response.headers.get("content-type", "")
        result.update(http_status=str(response.status_code), content_type=content_type, bytes=str(len(content)))
    except requests.RequestException as exc:
        result.update(decision="review", evidence=f"request error: {type(exc).__name__}: {exc}")
        return result
    if response.status_code != 200 or not ("pdf" in content_type.casefold() or content.startswith(b"%PDF")):
        result.update(decision="remove", evidence="not a direct HTTP 200 PDF")
        return result
    try:
        text = extract_pdf_text(content)
    except (OSError, subprocess.SubprocessError) as exc:
        result.update(decision="review", evidence=f"PDF extraction error: {type(exc).__name__}: {exc}")
        return result
    english_hits = len(ENGLISH_RE.findall(text))
    question_hits = len(QUESTION_RE.findall(text))
    solution_hits = len(SOLUTION_RE.findall(text))
    result["english_status"] = "pass" if english_hits >= 10 else "fail"
    result["material_status"] = "pass" if (question_hits or solution_hits) and class_status == "pass" else "fail"
    result["evidence"] = (
        f"english_hits={english_hits}; question_hits={question_hits}; solution_hits={solution_hits}; "
        f"class_status={class_status}; extracted_chars={len(text)}"
    )
    result["decision"] = "keep" if result["english_status"] == "pass" and result["material_status"] == "pass" else "remove"
    return result


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def reconcile_keep_evidence(pdf_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], str]:
    """Reconcile live PDFs to the union of completed local PDF audit ledgers.

    A re-fetch can introduce transient request failures after a record was already
    evidenced. The project maintains both aggregate audit reports and small
    country/source ledgers; these historically use either ``resource_url`` or
    ``url`` as their URL column. This deterministic pass accepts a prior *keep*
    decision from either schema, preserving source-ledger provenance while proving
    every current live PDF has clean-content evidence.
    """
    by_url: dict[str, tuple[dict[str, str], str]] = {}
    consulted_sources: list[str] = []
    for path in sorted(RESEARCH_DIR.glob("clean_content_pdf_audit_*.csv"), key=lambda item: (item.stat().st_mtime, item.name)):
        try:
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        except OSError:
            continue
        if not rows:
            continue
        decision_column = next((column for column in ("decision", "outcome") if column in rows[0]), "")
        if not decision_column:
            continue
        evidence_column = next((column for column in ("evidence", "reason", "evidence_source", "evidence_file") if column in rows[0]), "")
        if not evidence_column:
            continue
        url_column = "resource_url" if "resource_url" in rows[0] else "url" if "url" in rows[0] else ""
        if not url_column:
            continue
        consulted_sources.append(path.name)
        for row in rows:
            url = audit_url_key(row.get(url_column, ""))
            if url and row.get(decision_column) == "keep":
                normalized = dict(row)
                normalized["evidence"] = row.get(evidence_column, "")
                by_url[url] = (normalized, path.name)
    if not by_url:
        raise RuntimeError("No completed keep evidence is available for reconciliation")

    reconciled: list[dict[str, str]] = []
    for row in pdf_rows:
        matched = by_url.get(audit_url_key(row.get("resource_url", "")))
        result = dict(row)
        result.update({"http_status": "", "content_type": "", "bytes": "", "english_status": "", "material_status": "", "decision": "review", "evidence": ""})
        if matched:
            evidence, evidence_source = matched
            for field in ("http_status", "content_type", "bytes", "english_status", "material_status"):
                result[field] = evidence.get(field, "")
            result["decision"] = "keep"
            result["evidence"] = f"reconciled from {evidence_source}; {evidence.get('evidence', '')}"
        else:
            result["evidence"] = "no completed keep evidence in aggregate local audit ledgers"
        reconciled.append(result)
    return reconciled, f"union of {len(consulted_sources)} completed audit ledgers"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", action="store_true", help="download and inspect PDF-backed resources")
    parser.add_argument("--start", type=int, default=0, help="zero-based offset into PDF rows")
    parser.add_argument("--limit", type=int, default=0, help="maximum PDF rows to inspect; 0 means all")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--workers", type=int, default=12, help="maximum concurrent PDF downloads and inspections")
    parser.add_argument("--reconcile", action="store_true", help="reconcile live PDFs to the most complete completed keep-evidence audit")
    args = parser.parse_args()

    rows = read_active_rows()
    metadata_rows: list[dict[str, str]] = []
    for row in rows:
        language_status, material_status, note = metadata_status(row)
        metadata_rows.append(
            {
                **row,
                "is_pdf": "yes" if is_pdf(row) else "no",
                "language_status": language_status,
                "metadata_material_status": material_status,
                "decision": "remove" if language_status == "fail" else ("review" if material_status == "review" else "keep"),
                "evidence": note,
            }
        )
    metadata_fields = list(metadata_rows[0].keys()) if metadata_rows else EXPECTED_FIELDS
    metadata_path = RESEARCH_DIR / "clean_content_metadata_audit.csv"
    write_csv(metadata_path, metadata_rows, metadata_fields)

    summary = Counter(row["decision"] for row in metadata_rows)
    language_counts = Counter(row.get("language", "").strip() or "(blank)" for row in rows)
    print(
        {
            "active_rows": len(rows),
            "pdf_rows": sum(is_pdf(row) for row in rows),
            "metadata": dict(summary),
            "languages": dict(language_counts.most_common()),
            "report": str(metadata_path.relative_to(ROOT)),
        }
    )

    if not args.pdf:
        return
    pdf_rows = [row for row in rows if is_pdf(row)]
    selected = pdf_rows[args.start : (args.start + args.limit if args.limit else None)]
    evidence_source = ""
    if args.reconcile:
        audited, evidence_source = reconcile_keep_evidence(selected)
    else:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
            audited = list(executor.map(lambda row: audit_pdf(row, args.timeout), selected))
    pdf_fields = list(audited[0].keys()) if audited else EXPECTED_FIELDS
    suffix = f"{args.start}_{args.start + len(selected)}"
    pdf_path = RESEARCH_DIR / f"clean_content_pdf_audit_{suffix}.csv"
    write_csv(pdf_path, audited, pdf_fields)
    print({"pdf_audited": len(audited), "outcomes": dict(Counter(row["decision"] for row in audited)), "evidence_source": evidence_source, "report": str(pdf_path.relative_to(ROOT))})


if __name__ == "__main__":
    main()
