"""Build a verified Khon Kaen University 2011 assessment tranche."""

from __future__ import annotations

import csv
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA_DIR = ROOT / "client/src/data"
OUTPUT = DATA_DIR / "thailand_kku_2011_assessments_verified_resources.csv"
AUDIT = ROOT / "research/thailand_kku_2011_assessments_url_audit.csv"
SOURCE_URL = "https://gear.kku.ac.th/~polpinit/classes/188200_2011_1/"
VERIFY_DATE = "2026-08-15"
FIELDS = [
    "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
    "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
    "verification_status", "free_resource",
]
CANDIDATES = [
    ("Homework 2 — 2011", "HW/HW2.pdf", "University assignment questions"),
    ("Homework 2 Solutions — 2011", "HW/Sol%20HW2.pdf", "University assignment solutions"),
    ("Homework 3 — 2011", "HW/HW3.pdf", "University assignment questions"),
    ("Homework 3 Solutions — 2011", "HW/Sol%20HW3.pdf", "University assignment solutions"),
    ("Homework 4 — 2011", "HW/HW4.pdf", "University assignment questions"),
    ("Homework 4 Solutions — 2011", "HW/Sol%20HW4.pdf", "University assignment solutions"),
    ("Homework 5 — 2011", "HW/HW5.pdf", "University assignment questions"),
    ("Homework 5 Solutions — 2011", "HW/Sol%20HW5.pdf", "University assignment solutions"),
    ("Homework 6 — 2011", "HW/HW6.pdf", "University assignment questions"),
    ("Homework 6 Solutions — 2011", "HW/Sol%20HW6.pdf", "University assignment solutions"),
    ("Homework 7 — 2011", "HW/HW7.pdf", "University assignment questions"),
    ("Quiz 1 — 2011", "exams/PQ1_sec2.pdf", "University quiz questions"),
    ("Quiz 2 — 2011", "exams/PQ2_Sec2.pdf", "University quiz questions"),
]
ENGLISH_CUES = re.compile(r"\b(the|and|of|to|in|for|with|let|given|find|show|prove|question|problem|solution|exercise|answer)\b", re.IGNORECASE)
SUBSTANTIVE_CUES = re.compile(r"\b(question|problem|exercise|prove|show|find|compute|determine|solve|let|solution|answer)\b", re.IGNORECASE)
EXCLUDED_AFTER_FULL_AUDIT = {
    "HW/HW2.pdf": "full clean-content audit found no question or solution evidence",
}


def catalogue_urls() -> set[str]:
    urls: set[str] = set()
    for csv_path in DATA_DIR.glob("*_verified_resources.csv"):
        with csv_path.open(newline="", encoding="utf-8") as handle:
            urls.update(row["resource_url"] for row in csv.DictReader(handle) if row.get("resource_url"))
    return urls


def fetch_pdf_text(url: str, directory: Path) -> tuple[int, str, str]:
    pdf_path = directory / "candidate.pdf"
    result = subprocess.run(
        ["curl", "-L", "--silent", "--show-error", "--max-time", "30", "--connect-timeout", "10", "-A", "Mozilla/5.0", "-o", str(pdf_path), "-w", "%{http_code}|%{content_type}", url],
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
    return 200, content_type.lower(), text_path.read_text(encoding="utf-8", errors="replace") if extract.returncode == 0 and text_path.exists() else ""


def main() -> None:
    existing_urls = catalogue_urls()
    records: list[dict[str, str]] = []
    audits: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="kku-2011-") as temp:
        temp_dir = Path(temp)
        for title, path, resource_class in CANDIDATES:
            url = SOURCE_URL + path
            if path in EXCLUDED_AFTER_FULL_AUDIT:
                audits.append({
                    "resource_title": title,
                    "resource_url": url,
                    "http_status": "not re-fetched",
                    "content_type": "",
                    "english_cues": "0",
                    "substantive_cues": "0",
                    "included": "No",
                    "reason": EXCLUDED_AFTER_FULL_AUDIT[path],
                })
                continue
            candidate_dir = temp_dir / path.replace("/", "_").replace("%20", "_").replace(".pdf", "")
            candidate_dir.mkdir()
            status, content_type, text = fetch_pdf_text(url, candidate_dir)
            english_hits = len(ENGLISH_CUES.findall(text))
            substantive_hits = len(SUBSTANTIVE_CUES.findall(text))
            text_length = len(re.sub(r"\s+", "", text))
            included = status == 200 and "pdf" in content_type and text_length >= 120 and english_hits >= 12 and substantive_hits >= 2 and url not in existing_urls
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
            audits.append({"resource_title": title, "resource_url": url, "http_status": str(status), "content_type": content_type, "english_cues": str(english_hits), "substantive_cues": str(substantive_hits), "included": "Yes" if included else "No", "reason": reason})
            if included:
                records.append({
                    "country": "Thailand",
                    "track": "DM",
                    "topic_tags": "discrete mathematics;linear algebra;logic;proof;sets;relations;assignment questions",
                    "priority": "A",
                    "source_type": "First-party university course archive",
                    "source_title": "Khon Kaen University — Discrete Mathematics and Linear Algebra (188200), 2011",
                    "source_url": SOURCE_URL,
                    "resource_title": f"Khon Kaen University — {title}",
                    "resource_url": url,
                    "resource_class": resource_class,
                    "language": "English",
                    "notes": "Direct public English PDF linked from Khon Kaen University’s 2011 188200 course index; item-level access, substantive-content, and duplicate evidence recorded in the audit ledger.",
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
    print(f"Wrote {len(records)} verified KKU 2011 records to {OUTPUT}")
    print(f"Wrote {len(audits)} item-level URL audits to {AUDIT}")


if __name__ == "__main__":
    main()
