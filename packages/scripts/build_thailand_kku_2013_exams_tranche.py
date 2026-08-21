"""Build a clean-content-verified Khon Kaen University 2013 past-exam tranche."""

from __future__ import annotations

import csv
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA_DIR = ROOT / "apps/web/src/data"
OUTPUT = DATA_DIR / "thailand_kku_2013_exams_verified_resources.csv"
AUDIT = ROOT / "research/thailand_kku_2013_exams_url_audit.csv"
SOURCE_URL = "https://gear.kku.ac.th/~polpinit/classes/188200_2013_1/index.html"
BASE_URL = "https://gear.kku.ac.th/~polpinit/classes/188200_2013_1/"
VERIFY_DATE = "2026-08-15"

FIELDS = [
    "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
    "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
    "verification_status", "free_resource",
]

# Every candidate is directly linked from the English first-party course index. The
# two 2009 quizzes have already been promoted from the 2010 archive with identical
# material and are retained here only to make their exclusion reproducible.
CANDIDATES = [
    ("Midterm Exam — 2009", "Exams/Midterm_2009_1.pdf", None),
    ("Midterm Exam — 2010", "Exams/Midterm_2010_1.pdf", None),
    ("Midterm Exam — 2011", "Exams/Midterm_2011_1.pdf", None),
    ("Midterm Exam — 2012", "Exams/Midterm_2012_1.pdf", None),
    ("Final Exam — 2009", "Exams/Final_2009_1.pdf", None),
    ("Final Exam — 2010", "Exams/Final_2010_1.pdf", None),
    ("Final Exam — 2011", "Exams/Final_2011_1.pdf", None),
    ("Final Exam — 2012", "Exams/Final_2012_1.pdf", None),
    ("Quiz 1 — 2009", "Exams/Quiz1_2009_1.pdf", "Already catalogued from the 2010 course archive"),
    ("Quiz 1 — 2010", "Exams/Quiz1_2010_1.pdf", None),
    ("Quiz 1 — 2012", "Exams/Quiz1_2012_1.pdf", None),
    ("Quiz 2 — 2009", "Exams/Quiz2_2009_1.pdf", "Already catalogued from the 2010 course archive"),
    ("Quiz 2 — 2011", "Exams/Quiz2_2011_1.pdf", None),
    ("Quiz 2 — 2012", "Exams/Quiz2_2012_1.pdf", None),
]

ENGLISH_CUES = re.compile(
    r"\b(the|and|of|to|in|for|with|let|given|find|show|prove|question|problem|solution|exercise|answer)\b",
    re.IGNORECASE,
)
QUESTION_CUES = re.compile(r"\b(question|problem|exercise|prove|show|find|compute|determine|solve|let)\b", re.IGNORECASE)


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
    extract = subprocess.run(["pdftotext", "-layout", str(pdf_path), str(text_path)], capture_output=True, text=True, timeout=30, check=False)
    if extract.returncode != 0 or not text_path.exists():
        return 200, content_type.lower(), ""
    return 200, content_type.lower(), text_path.read_text(encoding="utf-8", errors="replace")


def main() -> None:
    existing_urls = catalogue_urls()
    audits: list[dict[str, str]] = []
    records: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="kku-2013-") as temp:
        temp_dir = Path(temp)
        for title, relative_path, known_duplicate in CANDIDATES:
            url = BASE_URL + relative_path
            candidate_dir = temp_dir / relative_path.replace("/", "_").replace(".pdf", "")
            candidate_dir.mkdir()
            status, content_type, text = download_and_extract(url, candidate_dir)
            english_hits = len(ENGLISH_CUES.findall(text))
            question_hits = len(QUESTION_CUES.findall(text))
            nonempty_text = len(re.sub(r"\s+", "", text))
            included = (
                status == 200 and "pdf" in content_type and nonempty_text >= 120
                and english_hits >= 12 and question_hits >= 2 and url not in existing_urls
                and known_duplicate is None
            )
            if known_duplicate:
                reason = known_duplicate
            elif status != 200 or "pdf" not in content_type:
                reason = "not a directly accessible PDF"
            elif nonempty_text < 120:
                reason = "insufficient extractable document text"
            elif english_hits < 12:
                reason = "insufficient English-language evidence"
            elif question_hits < 2:
                reason = "insufficient substantive question evidence"
            elif url in existing_urls:
                reason = "duplicate of an existing catalog URL"
            else:
                reason = "keep"
            audits.append({
                "resource_title": title, "resource_url": url, "http_status": str(status), "content_type": content_type,
                "english_cues": str(english_hits), "substantive_cues": str(question_hits),
                "included": "Yes" if included else "No", "reason": reason,
            })
            if included:
                records.append({
                    "country": "Thailand", "track": "DM",
                    "topic_tags": "discrete mathematics;linear algebra;logic;proof;sets;relations;exam questions",
                    "priority": "A", "source_type": "First-party university course archive",
                    "source_title": "Khon Kaen University — Discrete Mathematics and Linear Algebra (188200), 2013",
                    "source_url": SOURCE_URL, "resource_title": f"Khon Kaen University — {title}",
                    "resource_url": url, "resource_class": "University past examination questions", "language": "English",
                    "notes": "Direct public English PDF linked from Khon Kaen University’s 2013 188200 course index; item-level access, content, and duplicate evidence recorded in the audit ledger.",
                    "access_model": "Free public PDF", "verification_status": f"HTTP 200 · verified {VERIFY_DATE}", "free_resource": "Yes",
                })
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["resource_title", "resource_url", "http_status", "content_type", "english_cues", "substantive_cues", "included", "reason"])
        writer.writeheader()
        writer.writerows(audits)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {len(records)} verified KKU 2013 records to {OUTPUT}")
    print(f"Wrote {len(audits)} item-level URL audits to {AUDIT}")


if __name__ == "__main__":
    main()
