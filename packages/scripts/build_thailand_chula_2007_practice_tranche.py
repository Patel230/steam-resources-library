"""Build a strictly verified Chulalongkorn University 2007 practice-set tranche.

The candidates are limited to two direct PDF links labelled "Practice Problems" on
the official 2143110 Discrete Mathematics course page. Lecture slides and the
syllabus are intentionally outside this question/solution-only tranche.
"""

from __future__ import annotations

import csv
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA_DIR = ROOT / "apps/web/src/data"
OUTPUT = DATA_DIR / "thailand_chula_2007_practice_verified_resources.csv"
AUDIT = ROOT / "research/thailand_chula_2007_practice_url_audit.csv"
SOURCE_URL = "https://www.cp.eng.chula.ac.th/~atiwong/2143110/"
VERIFY_DATE = "2026-08-15"
FIELDS = [
    "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
    "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
    "verification_status", "free_resource",
]
CANDIDATES = [
    (
        "Practice Problem Set 1 — 2007",
        "2007-2-PracticeQuestions_Set1.pdf",
        "University practice problem set",
    ),
    (
        "Practice Problem Set 2 — 2007",
        "2007-2-Practice%20Question%20Set2.pdf",
        "University practice problem set",
    ),
]
ENGLISH_CUES = re.compile(
    r"\b(the|and|of|to|in|for|with|let|given|find|show|prove|question|problem|solution|exercise|answer)\b",
    re.IGNORECASE,
)
SUBSTANTIVE_CUES = re.compile(
    r"\b(question|problem|exercise|prove|show|find|compute|determine|solve|let|answer)\b",
    re.IGNORECASE,
)


def catalogued_urls() -> set[str]:
    urls: set[str] = set()
    for csv_path in DATA_DIR.glob("*_verified_resources.csv"):
        with csv_path.open(newline="", encoding="utf-8") as handle:
            urls.update(row["resource_url"] for row in csv.DictReader(handle) if row.get("resource_url"))
    return urls


def fetch_pdf_text(url: str, directory: Path) -> tuple[int, str, str]:
    pdf_path = directory / "candidate.pdf"
    result = subprocess.run(
        [
            "curl", "-L", "--silent", "--show-error", "--max-time", "45", "--connect-timeout", "15",
            "-A", "Mozilla/5.0", "-o", str(pdf_path), "-w", "%{http_code}|%{content_type}", url,
        ],
        capture_output=True,
        text=True,
        timeout=55,
        check=False,
    )
    raw = result.stdout.strip()
    status, content_type = (raw.split("|", 1) + [""])[:2] if "|" in raw else ("0", "unavailable")
    if result.returncode != 0 or not status.isdigit() or int(status) != 200 or "pdf" not in content_type.lower():
        return int(status) if status.isdigit() else 0, content_type.lower() or "unknown", ""
    text_path = directory / "candidate.txt"
    extracted = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), str(text_path)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    text = text_path.read_text(encoding="utf-8", errors="replace") if extracted.returncode == 0 and text_path.exists() else ""
    return 200, content_type.lower(), text


def main() -> None:
    existing_urls = catalogued_urls()
    records: list[dict[str, str]] = []
    audits: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="chula-2007-") as temporary_directory:
        temporary_root = Path(temporary_directory)
        for title, relative_url, resource_class in CANDIDATES:
            url = SOURCE_URL + relative_url
            candidate_directory = temporary_root / relative_url.replace("%20", "_").replace(".pdf", "")
            candidate_directory.mkdir()
            status, content_type, text = fetch_pdf_text(url, candidate_directory)
            english_hits = len(ENGLISH_CUES.findall(text))
            substantive_hits = len(SUBSTANTIVE_CUES.findall(text))
            text_length = len(re.sub(r"\s+", "", text))
            included = (
                status == 200
                and "pdf" in content_type
                and text_length >= 120
                and english_hits >= 12
                and substantive_hits >= 2
                and url not in existing_urls
            )
            if status != 200 or "pdf" not in content_type:
                reason = "not a directly accessible PDF"
            elif text_length < 120:
                reason = "insufficient extractable document text"
            elif english_hits < 12:
                reason = "insufficient English-language evidence"
            elif substantive_hits < 2:
                reason = "insufficient substantive question or solution evidence"
            elif url in existing_urls:
                reason = "duplicate of an existing catalog URL"
            else:
                reason = "keep"
            audits.append(
                {
                    "resource_title": title,
                    "resource_url": url,
                    "http_status": str(status),
                    "content_type": content_type,
                    "english_cues": str(english_hits),
                    "substantive_cues": str(substantive_hits),
                    "included": "Yes" if included else "No",
                    "reason": reason,
                }
            )
            if included:
                records.append(
                    {
                        "country": "Thailand",
                        "track": "DM",
                        "topic_tags": "discrete mathematics;logic;sets;functions;relations;proof;counting;practice problems",
                        "priority": "A",
                        "source_type": "First-party university course archive",
                        "source_title": "Chulalongkorn University — Discrete Mathematics (2143110), 2007",
                        "source_url": SOURCE_URL,
                        "resource_title": f"Chulalongkorn University — {title}",
                        "resource_url": url,
                        "resource_class": resource_class,
                        "language": "English",
                        "notes": "Direct public English practice-problem PDF explicitly linked from Chulalongkorn University’s 2007 Discrete Mathematics course archive; item-level access, substantive-content, and duplicate evidence is recorded in the audit ledger.",
                        "access_model": "Free public PDF",
                        "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                        "free_resource": "Yes",
                    }
                )
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["resource_title", "resource_url", "http_status", "content_type", "english_cues", "substantive_cues", "included", "reason"],
        )
        writer.writeheader()
        writer.writerows(audits)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {len(records)} verified Chulalongkorn 2007 records to {OUTPUT}")
    print(f"Wrote {len(audits)} item-level URL audits to {AUDIT}")


if __name__ == "__main__":
    main()
