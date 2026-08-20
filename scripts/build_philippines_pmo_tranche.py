"""Build a clean-content Philippines tranche from the official PMO archive.

The source archive intermittently returns HTTP 503, so its discovery page alone is
never counted as evidence. This builder checks every direct document URL observed
in the official archive extraction, retains only non-duplicate HTTP 200 PDFs with
extractable English question material, and keeps an item-level audit ledger.
"""

from __future__ import annotations

import csv
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "client/src/data"
OUTPUT = DATA / "philippines_pmo_verified_resources.csv"
AUDIT = ROOT / "research/philippines_pmo_url_audit.csv"
SOURCE_URL = "https://pmo.ph/pmo-archive-demo/"
VERIFY_DATE = "2026-08-15"

PAPERS = [
    ("26th", "Qualifying Stage", "https://pmo.ph/wp-content/uploads/2024/06/PMO26-Qualifying-Stage.pdf"),
    ("26th", "Area Stage", "https://pmo.ph/wp-content/uploads/2024/06/PMO26-Area-Stage.pdf"),
    ("26th", "National Stage", "https://pmo.ph/wp-content/uploads/2024/09/PMO-National-Finals-Written-Round.pdf"),
    ("25th", "Qualifying Stage", "https://pmo.ph/wp-content/uploads/2023/08/PMO-25-Qualifying-Stage.pdf"),
    ("25th", "Area Stage", "https://pmo.ph/wp-content/uploads/2023/08/PMO-25-Area-Stage.pdf"),
    ("25th", "National Stage", "https://pmo.ph/wp-content/uploads/2023/08/PMO-25-National-Stage.pdf"),
    ("24th", "Qualifying Stage", "https://pmo.ph/wp-content/uploads/2022/06/PMO24-Qualifying-Stage.pdf"),
    ("24th", "National Stage", "https://pmo.ph/wp-content/uploads/2022/06/PMO24-National-Stage.pdf"),
    ("23rd", "Qualifying Round", "https://pmo.ph/wp-content/uploads/2021/02/PMO23-Qualifying-Round.pdf"),
    ("23rd", "National Stage", "https://pmo.ph/wp-content/uploads/2021/07/PMO23-National-Stage.pdf"),
    ("22nd", "Qualifying Round with Answers", "http://pmo.ph/wp-content/uploads/2019/11/PMO-22-Qualifying-Round-with-answers.pdf"),
    ("22nd", "Area Stage with Solutions", "https://pmo.ph/wp-content/uploads/2021/01/22nd-PMO-Area-Stage-with-solutions.pdf"),
    ("21st", "Qualifying Stage", "http://pmo.ph/wp-content/uploads/2019/01/21st-PMO-Qualifying-Stage.pdf"),
    ("21st", "Area Stage", "http://pmo.ph/wp-content/uploads/2019/01/21st-PMO-Area-Stage.pdf"),
    ("20th", "Qualifying Round with Answers", "http://pmo.ph/wp-content/uploads/2018/08/PMO-20-Qualifying-Round-with-answers-only.pdf"),
    ("20th", "Area Stage with Answers", "http://pmo.ph/wp-content/uploads/2018/08/PMO-Area-Stage-answers-only.pdf"),
    ("19th", "Qualifying Stage Questions and Answers", "http://pmo.ph/wp-content/uploads/2014/08/19th-PMO-Qualifying-Stage-Questions-and-Answers.pdf"),
    ("19th", "Area Stage Questions and Answers", "http://pmo.ph/wp-content/uploads/2020/11/19th-PMO-Area-Stage-Questions-and-Answers.pdf"),
    ("18th", "Qualifying Stage Questions and Answers", "http://pmo.ph/wp-content/uploads/2020/12/18th-PMO-Qualifying-Stage-Questions-and-Answers.pdf"),
    ("18th", "Area Stage Questions and Answers", "http://pmo.ph/wp-content/uploads/2020/12/18th-PMO-Area-Stage-Questions-and-Answers.pdf"),
    ("17th", "Qualifying Stage Questions and Answers", "http://pmo.ph/wp-content/uploads/2020/12/17th-PMO-Qualifying-Stage-Questions-and-Answers.pdf"),
    ("17th", "Area Stage Questions and Answers", "http://pmo.ph/wp-content/uploads/2020/12/17th-PMO-Area-Stage-Questions-and-Answers.pdf"),
    ("16th", "Qualifying Stage", "http://pmo.ph/wp-content/uploads/2014/08/16th-PMO-Qualifying.pdf"),
    ("16th", "Area Stage", "http://pmo.ph/wp-content/uploads/2020/12/PMO-16-Area-Stage-w_-A.pdf"),
    ("15th", "Qualifying and Area Stage", "http://pmo.ph/wp-content/uploads/2020/12/15th-PMO-Qualifying-Area-Stage.pdf"),
    ("15th", "National Stage Written Round", "http://pmo.ph/wp-content/uploads/2020/12/15th-PMO-National-Stage-Written-Questions-and-Answers.pdf"),
    ("15th", "National Stage Oral Round", "http://pmo.ph/wp-content/uploads/2020/12/15th-PMO-National-Stage-Oral-Questions-and-Answers.pdf"),
    ("14th", "Qualifying and Area Stage", "http://pmo.ph/wp-content/uploads/2020/12/14th-PMO-Qualifying-Area-Stage.pdf"),
    ("14th", "National Stage Written Round", "http://pmo.ph/wp-content/uploads/2014/08/14th-PMO-National-stage-Written-FINAL.pdf"),
    ("13th", "Qualifying Stage Questions and Answers", "http://pmo.ph/wp-content/uploads/2020/12/13th-PMO-Qualifying-Stage-Questions-and-Answers.pdf"),
    ("13th", "Area Stage", "http://pmo.ph/wp-content/uploads/2014/08/13thPMO-Area_ver5.pdf"),
    ("13th", "National Stage Written Phase", "http://pmo.ph/wp-content/uploads/2020/12/13th-PMO-National-Stage-Written-Questions-and-Answers.pdf"),
    ("13th", "National Stage Oral Phase", "http://pmo.ph/wp-content/uploads/2020/12/13th-PMO-National-Stage-Oral-Questions-and-Answers.pdf"),
    ("12th", "Qualifying Stage Set A", "http://pmo.ph/wp-content/uploads/2020/12/PMO-12-Qualifying-Stage-w_-A.pdf"),
    ("12th", "Qualifying Stage Set B", "http://pmo.ph/wp-content/uploads/2020/12/PMO-12-Qualifying-Stage-for-Region-1-2-CAR-w_-A.pdf"),
    ("12th", "Area Stage", "http://pmo.ph/wp-content/uploads/2020/12/PMO-12-Area-Stage-w_-A.pdf"),
    ("12th", "National Stage Written and Oral Round", "http://pmo.ph/wp-content/uploads/2020/12/PMO-12-National-Stage-Written-Oral-Round-w_-A.pdf"),
]

ENGLISH_RE = re.compile(r"\b(the|and|of|to|in|for|with|this|that|is|are|from|by|on|as|an|a)\b", re.IGNORECASE)
QUESTION_RE = re.compile(r"\b(question|problem|find|compute|prove|determine|given|choose|how many)\b", re.IGNORECASE)


def catalog_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob("*.csv"):
        if path == OUTPUT:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            urls.update(row.get("resource_url", "").strip().lower() for row in csv.DictReader(handle))
    return urls


def fetch_and_check(url: str, destination: Path) -> tuple[int, str, int, int, str, str]:
    response = subprocess.run(
        [
            "curl", "-L", "--silent", "--show-error", "--max-time", "50", "-A", "Mozilla/5.0",
            "-o", str(destination), "-w", "%{http_code}|%{content_type}", url,
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    raw = response.stdout.strip()
    if response.returncode != 0 or "|" not in raw:
        return 0, "unavailable", 0, 0, "", "curl failed"
    code_text, content_type = raw.split("|", 1)
    status = int(code_text) if code_text.isdigit() else 0
    if status != 200 or "pdf" not in content_type.lower():
        return status, content_type.lower() or "unknown", 0, 0, "", "not a public HTTP 200 PDF"
    extracted = subprocess.run(
        ["pdftotext", "-f", "1", "-l", "8", "-layout", str(destination), "-"],
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    ).stdout.replace("\x00", " ")
    english_hits = len(ENGLISH_RE.findall(extracted))
    question_hits = len(QUESTION_RE.findall(extracted))
    preview = " ".join(extracted.split())[:360]
    if english_hits < 10:
        return status, content_type.lower(), english_hits, question_hits, preview, "English text threshold not met"
    if question_hits < 2:
        return status, content_type.lower(), english_hits, question_hits, preview, "Substantive question threshold not met"
    return status, content_type.lower(), english_hits, question_hits, preview, "English substantive question material confirmed"


def main() -> None:
    existing = catalog_urls()
    outcomes: list[dict[str, str | int]] = []
    verified: list[tuple[str, str, str]] = []
    with tempfile.TemporaryDirectory(prefix="pmo-pdf-") as directory:
        temp_dir = Path(directory)
        for index, (edition, stage, url) in enumerate(PAPERS, start=1):
            if url.lower() in existing:
                outcomes.append({"edition": edition, "stage": stage, "resource_url": url, "http_status": 0, "content_type": "duplicate", "english_hits": 0, "question_hits": 0, "text_preview": "", "finding": "URL already present in another live CSV", "included": "No"})
                continue
            status, content_type, english_hits, question_hits, preview, finding = fetch_and_check(url, temp_dir / f"pmo-{index}.pdf")
            included = status == 200 and "pdf" in content_type and english_hits >= 10 and question_hits >= 2
            outcomes.append({"edition": edition, "stage": stage, "resource_url": url, "http_status": status, "content_type": content_type, "english_hits": english_hits, "question_hits": question_hits, "text_preview": preview, "finding": finding, "included": "Yes" if included else "No"})
            if included:
                verified.append((edition, stage, url))

    fields = ["country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url", "resource_title", "resource_url", "resource_class", "language", "notes", "access_model", "verification_status", "free_resource"]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for edition, stage, url in verified:
            writer.writerow({
                "country": "Philippines",
                "track": "GA",
                "topic_tags": "mathematical olympiad;problem solving;algebra;geometry;number theory;combinatorics;general aptitude;contest;questions",
                "priority": "A",
                "source_type": "National mathematics Olympiad organiser archive",
                "source_title": "Philippine Mathematical Olympiad (PMO) official archive",
                "source_url": SOURCE_URL,
                "resource_title": f"{edition} Philippine Mathematical Olympiad — {stage} (Official English Question Paper)",
                "resource_url": url,
                "resource_class": "National mathematics Olympiad question paper",
                "language": "English",
                "notes": "Direct public English question-paper PDF published by the PMO official archive. It passed item-level HTTP, PDF, extractable-English, and substantive-question checks; souvenir programmes and failed documents are excluded.",
                "access_model": "Free public PDF",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    audit_fields = ["edition", "stage", "resource_url", "http_status", "content_type", "english_hits", "question_hits", "text_preview", "finding", "included"]
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=audit_fields)
        writer.writeheader()
        writer.writerows(outcomes)
    print(f"Wrote {len(verified)} verified PMO records to {OUTPUT}; full audit: {AUDIT}")
    if not verified:
        raise RuntimeError("No PMO direct PDFs passed the strict public English-question checks")


if __name__ == "__main__":
    main()
