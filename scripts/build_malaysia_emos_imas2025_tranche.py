from __future__ import annotations

import csv
import subprocess
from pathlib import Path


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "client/src/data"
OUTPUT = DATA / "malaysia_emos_imas2025_verified_resources.csv"
AUDIT = ROOT / "research/malaysia_emos_imas2025_url_audit.csv"
VERIFY_DATE = "2026-08-15"
SOURCE_URL = "https://emosmalaysia.com/sample-questions/"

RESOURCES = [
    ("IMAS Malaysia 2025 — Junior Primary Pre-Round Paper", "https://emosmalaysia.com/wp-content/uploads/2025/12/2025-IMAS_Junior_Pre-Round_ENG_MALAYSIA.pdf"),
    ("IMAS Malaysia 2025 — Middle Primary Pre-Round Paper", "https://emosmalaysia.com/wp-content/uploads/2025/12/2025-IMAS_MP_Pre-Round_ENG_MALAYSIA.pdf"),
    ("IMAS Malaysia 2025 — Upper Primary Pre-Round Paper", "https://emosmalaysia.com/wp-content/uploads/2025/12/2025-IMAS_UP_Pre-Round_ENG-MALAYSIA-1.pdf"),
]


def catalog_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob("*.csv"):
        if path == OUTPUT:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            urls.update(row.get("resource_url", "").strip() for row in csv.DictReader(handle))
    return urls


def verify(url: str) -> tuple[int, str]:
    result = subprocess.run(
        ["curl", "-I", "-L", "--silent", "--show-error", "--max-time", "15", "-A", "Mozilla/5.0", "-o", "/dev/null", "-w", "%{http_code}|%{content_type}", url],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    output = result.stdout.strip()
    if result.returncode != 0 or "|" not in output:
        return 0, "unavailable"
    code, content_type = output.split("|", 1)
    return (int(code) if code.isdigit() else 0), (content_type.lower() or "unknown")


def main() -> None:
    existing = catalog_urls()
    outcomes: dict[str, tuple[int, str, str]] = {}
    verified: list[tuple[str, str]] = []

    for title, url in RESOURCES:
        if url in existing:
            outcomes[url] = (0, "duplicate", "No")
            continue
        status, content_type = verify(url)
        included = status == 200 and "application/pdf" in content_type
        outcomes[url] = (status, content_type, "Yes" if included else "No")
        if included:
            verified.append((title, url))

    fields = ["country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url", "resource_title", "resource_url", "resource_class", "language", "notes", "access_model", "verification_status", "free_resource"]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for title, url in verified:
            writer.writerow({
                "country": "Malaysia",
                "track": "GA",
                "topic_tags": "mathematical reasoning;numeracy;multiple choice;competition",
                "priority": "B",
                "source_type": "Official competition sample-paper archive",
                "source_title": "EMOS Malaysia — IMAS sample questions",
                "source_url": SOURCE_URL,
                "resource_title": title,
                "resource_url": url,
                "resource_class": "Sample mathematics assessment paper / MCQs",
                "language": "English",
                "notes": "Public English IMAS pre-round paper linked from the organiser's official Sample Questions page; 75-minute mathematics MCQ assessment.",
                "access_model": "Free public PDF",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source_url", "resource_url", "resource_title", "http_status", "content_type", "included"])
        for title, url in RESOURCES:
            status, content_type, included = outcomes[url]
            writer.writerow([SOURCE_URL, url, title, status, content_type, included])

    print(f"Wrote {len(verified)} verified EMOS Malaysia IMAS records to {OUTPUT}")


if __name__ == "__main__":
    main()
