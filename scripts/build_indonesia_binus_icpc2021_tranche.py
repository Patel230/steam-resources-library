"""Generate a verified Indonesia tranche from BINUS University's ICPC Jakarta 2021 PDFs.

Each organiser-hosted candidate is checked separately for a direct unauthenticated
HTTP 200 PDF response, English contest-problem cues, and absence from the live CSV
catalog. This avoids assuming that an alphabetic filename sequence is public.
"""

from __future__ import annotations

import csv
import subprocess
import tempfile
from pathlib import Path


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "client/src/data"
OUTPUT = DATA / "indonesia_binus_icpc2021_verified_resources.csv"
AUDIT = ROOT / "research/indonesia_binus_icpc2021_url_audit.csv"
SOURCE_URL = "https://competition.binus.ac.id/icpc2021/"
VERIFY_DATE = "2026-08-15"
TASKS = [(letter, f"https://competition.binus.ac.id/icpc2021/{letter}.pdf") for letter in "ABCDEFGHIJKLM"]

FIELDS = [
    "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
    "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
    "verification_status", "free_resource",
]


def catalog_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob("*.csv"):
        if path == OUTPUT:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            urls.update(row.get("resource_url", "").strip() for row in csv.DictReader(handle))
    return urls


def verify(url: str) -> tuple[int, str, str, str]:
    """Return status, type, first-page English cues, and a promotion diagnostic."""
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = Path(tmp) / "candidate.pdf"
        result = subprocess.run(
            [
                "curl", "-L", "--silent", "--show-error", "--max-time", "45",
                "-A", "Mozilla/5.0", "-o", str(pdf_path), "-w", "%{http_code}|%{content_type}", url,
            ],
            capture_output=True,
            text=True,
            timeout=50,
            check=False,
        )
        output = result.stdout.strip()
        if result.returncode != 0 or "|" not in output:
            return 0, "unavailable", "", "curl failed"
        code_raw, content_type = output.split("|", 1)
        status = int(code_raw) if code_raw.isdigit() else 0
        content_type = content_type.lower() or "unknown"
        if status != 200 or "pdf" not in content_type or not pdf_path.exists():
            return status, content_type, "", "not an HTTP 200 PDF"

        text_result = subprocess.run(
            ["pdftotext", "-f", "1", "-l", "1", str(pdf_path), "-"],
            capture_output=True,
            text=True,
            timeout=25,
            check=False,
        )
        page_one = " ".join(text_result.stdout.split())
        lowered = page_one.lower()
        cues = [cue for cue in ("icpc", "problem", "input", "output") if cue in lowered]
        if {"icpc", "problem"}.issubset(cues) and ("input" in cues or "output" in cues):
            return status, content_type, "; ".join(cues), "eligible"
        return status, content_type, "; ".join(cues), "missing English problem-statement cues"


def main() -> None:
    existing = catalog_urls()
    outcomes: list[tuple[str, str, int, str, str, str, str]] = []
    verified: list[tuple[str, str]] = []

    for letter, url in TASKS:
        if url in existing:
            outcomes.append((letter, url, 0, "duplicate", "", "No", "already in catalog"))
            continue
        status, content_type, evidence, diagnostic = verify(url)
        included = status == 200 and "pdf" in content_type and diagnostic == "eligible"
        outcomes.append((letter, url, status, content_type, evidence, "Yes" if included else "No", diagnostic))
        if included:
            verified.append((letter, url))

    if not verified:
        raise RuntimeError("No eligible BINUS ICPC 2021 records; refusing to write an empty tranche")

    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for letter, url in verified:
            writer.writerow({
                "country": "Indonesia",
                "track": "DM",
                "topic_tags": "discrete mathematics;algorithms;programming;logic;problem-solving;contest;ICPC",
                "priority": "A",
                "source_type": "BINUS University organiser-hosted ICPC regional contest archive",
                "source_title": "BINUS University — ICPC Asia Jakarta Regional Contest 2021",
                "source_url": SOURCE_URL,
                "resource_title": f"ICPC Asia Jakarta 2021 — Problem {letter} (Official English PDF)",
                "resource_url": url,
                "resource_class": "Programming contest problem paper",
                "language": "English",
                "notes": "Direct, organiser-hosted English ICPC Asia Jakarta 2021 problem PDF from BINUS University. Individual access, PDF type, first-page statement cues, and URL uniqueness were checked before promotion.",
                "access_model": "Free public PDF",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source_url", "resource_url", "resource_title", "http_status", "content_type", "english_cues", "included", "diagnostic"])
        for letter, url, status, content_type, evidence, included, diagnostic in outcomes:
            writer.writerow([SOURCE_URL, url, f"ICPC Asia Jakarta 2021 — Problem {letter}", status, content_type, evidence, included, diagnostic])

    print(f"Wrote {len(verified)} verified BINUS ICPC Asia Jakarta 2021 records to {OUTPUT}")


if __name__ == "__main__":
    main()
