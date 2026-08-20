"""Build a clean-content verified Khon Kaen University 2010 assessment tranche."""

from __future__ import annotations

import csv
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA_DIR = ROOT / "client/src/data"
OUTPUT = DATA_DIR / "thailand_kku_2010_assessments_verified_resources.csv"
AUDIT = ROOT / "research/thailand_kku_2010_assessments_url_audit.csv"
SOURCE_URL = "https://gear.kku.ac.th/~polpinit/classes/188200_2010_1/"
BASE_URL = SOURCE_URL
VERIFY_DATE = "2026-08-15"

FIELDS = [
    "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
    "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
    "verification_status", "free_resource",
]

# Every path is directly published by the English 188200 course index. Score lists,
# lecture notes, textbook copies, and unlinked examinations are intentionally absent.
CANDIDATES = [
    ("Homework 1", "HW/HW1.pdf", "University homework problem set", "question"),
    ("Homework 2", "HW/HW2.pdf", "University homework problem set", "question"),
    ("Homework 3", "HW/HW3.pdf", "University homework problem set", "question"),
    ("Homework 4", "HW/HW4.pdf", "University homework problem set", "question"),
    ("Homework 5", "HW/HW5.pdf", "University homework problem set", "question"),
    ("Homework 5 solutions", "HW/HW5_Solution.pdf", "University homework solution", "solution"),
    ("Homework 6", "HW/HW6.pdf", "University homework problem set", "question"),
    ("Homework 6 solutions", "HW/HW6_Solution.pdf", "University homework solution", "solution"),
    ("Past Test 1 — Summer 2009", "Quiz1_2009_summer.pdf", "University past quiz", "question"),
    ("Past Test 1 — First Semester 2009", "Quiz1_2009_1.pdf", "University past quiz", "question"),
    ("Past Test 2 — Summer 2009", "Quiz2_2009_summer.pdf", "University past quiz", "question"),
    ("Past Test 2 — First Semester 2009", "Quiz2_2009_1.pdf", "University past quiz", "question"),
]

ENGLISH_CUES = re.compile(
    r"\b(the|and|of|to|in|for|with|let|given|find|show|prove|question|problem|solution|exercise|answer|\n)\b",
    re.IGNORECASE,
)
QUESTION_CUES = re.compile(r"\b(question|problem|exercise|prove|show|find|compute|determine|solve|let)\b", re.IGNORECASE)
SOLUTION_CUES = re.compile(r"\b(solution|answer|therefore|hence|proof|we have)\b", re.IGNORECASE)


def catalogue_urls() -> set[str]:
    urls: set[str] = set()
    for csv_path in DATA_DIR.glob("*_verified_resources.csv"):
        with csv_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("resource_url"):
                    urls.add(row["resource_url"])
    return urls


def download_and_extract(url: str, directory: Path) -> tuple[int, str, str]:
    pdf_path = directory / "candidate.pdf"
    result = subprocess.run(
        [
            "curl", "-L", "--silent", "--show-error", "--max-time", "30", "--connect-timeout", "10",
            "-A", "Mozilla/5.0", "-o", str(pdf_path), "-w", "%{http_code}|%{content_type}", url,
        ],
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    raw = result.stdout.strip()
    status, content_type = (raw.split("|", 1) + [""])[:2] if "|" in raw else ("0", "unavailable")
    if result.returncode != 0 or not status.isdigit() or int(status) != 200 or "pdf" not in content_type.lower():
        return int(status) if status.isdigit() else 0, content_type.lower() or "unknown", ""
    text_path = directory / "candidate.txt"
    extract = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), str(text_path)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if extract.returncode != 0 or not text_path.exists():
        return 200, content_type.lower(), ""
    return 200, content_type.lower(), text_path.read_text(encoding="utf-8", errors="replace")


def main() -> None:
    existing_urls = catalogue_urls()
    audits: list[dict[str, str]] = []
    records: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="kku-2010-") as temp:
        temp_dir = Path(temp)
        for title, relative_path, resource_class, category in CANDIDATES:
            url = BASE_URL + relative_path
            candidate_dir = temp_dir / relative_path.replace("/", "_").replace(".pdf", "")
            candidate_dir.mkdir()
            status, content_type, text = download_and_extract(url, candidate_dir)
            english_hits = len(ENGLISH_CUES.findall(text))
            substantive_hits = len((SOLUTION_CUES if category == "solution" else QUESTION_CUES).findall(text))
            nonempty_text = len(re.sub(r"\s+", "", text))
            included = (
                status == 200
                and "pdf" in content_type
                and nonempty_text >= 120
                and english_hits >= 12
                and substantive_hits >= 2
                and url not in existing_urls
            )
            if status != 200 or "pdf" not in content_type:
                reason = "not a directly accessible PDF"
            elif nonempty_text < 120:
                reason = "insufficient extractable document text"
            elif english_hits < 12:
                reason = "insufficient English-language evidence"
            elif substantive_hits < 2:
                reason = "insufficient substantive question or solution evidence"
            elif url in existing_urls:
                reason = "duplicate of an existing catalog URL"
            else:
                reason = "keep"
            audits.append({
                "resource_title": title, "resource_url": url, "http_status": str(status),
                "content_type": content_type, "english_cues": str(english_hits),
                "substantive_cues": str(substantive_hits), "included": "Yes" if included else "No", "reason": reason,
            })
            if included:
                records.append({
                    "country": "Thailand",
                    "track": "DM",
                    "topic_tags": "discrete mathematics;linear algebra;logic;proof;sets;relations;questions",
                    "priority": "A",
                    "source_type": "First-party university course archive",
                    "source_title": "Khon Kaen University — Discrete Mathematics and Linear Algebra (188200), 2010",
                    "source_url": SOURCE_URL,
                    "resource_title": f"Khon Kaen University — {title}",
                    "resource_url": url,
                    "resource_class": resource_class,
                    "language": "English",
                    "notes": "Direct public English PDF linked from Khon Kaen University’s 2010 188200 course index; item-level access and substantive-content evidence recorded in the audit ledger.",
                    "access_model": "Free public PDF",
                    "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                    "free_resource": "Yes",
                })

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["resource_title", "resource_url", "http_status", "content_type", "english_cues", "substantive_cues", "included", "reason"])
        writer.writeheader()
        writer.writerows(audits)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {len(records)} verified KKU 2010 records to {OUTPUT}")
    print(f"Wrote {len(audits)} item-level URL audits to {AUDIT}")


if __name__ == "__main__":
    main()
