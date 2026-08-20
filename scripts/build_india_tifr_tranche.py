from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import urljoin

import requests

ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
OUTPUT = ROOT / "client/src/data/india_tifr_verified_resources.csv"
AUDIT = ROOT / "research/india_tifr_url_audit.csv"
SOURCE_URL = "https://www.tifr.res.in/academics/past_question_papers.php"
BASE = "https://www.tifr.res.in/academics/"

CANDIDATES = [
    ("GS 2026 Mathematics", "docs/past_QP/GS2026_QP_Mathematics.pdf"),
    ("GS 2025 Mathematics", "docs/past_QP/GS2025_QP_Mathematics.pdf"),
    ("GS 2024 Mathematics", "docs/past_QP/GS2024_QP_Maths.pdf"),
    ("GS 2023 Mathematics", "docs/past_QP/GS2023_QP_MTH.pdf"),
    ("GS 2022 Mathematics", "docs/past_QP/GS2022_QP_MTH.pdf"),
    ("GS 2021 Mathematics", "docs/past_QP/GS2021_QP_MTH.pdf"),
]


def verify(url: str) -> tuple[int, str]:
    response = requests.get(
        url,
        timeout=30,
        stream=True,
        headers={"User-Agent": "Mozilla/5.0 SignalAtlasResearch/1.0"},
    )
    status = response.status_code
    content_type = response.headers.get("content-type", "")
    response.close()
    return status, content_type


def main() -> None:
    headers = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    rows: list[dict[str, str]] = []
    audit_rows: list[tuple[str, int, str, str]] = []
    for title, relative in CANDIDATES:
        url = urljoin(BASE, relative)
        try:
            status, content_type = verify(url)
        except requests.RequestException as error:
            status, content_type = 0, type(error).__name__
        included = status == 200 and "pdf" in content_type.lower()
        audit_rows.append((url, status, content_type, "Yes" if included else "No"))
        if included:
            rows.append({
                "country": "India",
                "track": "EM/DM",
                "topic_tags": "engineering mathematics;discrete mathematics;mathematics;entrance exam;past-year",
                "priority": "A",
                "source_type": "University examination archive",
                "source_title": "TIFR Graduate Studies past question papers — Tata Institute of Fundamental Research",
                "source_url": SOURCE_URL,
                "resource_title": f"TIFR {title} question paper",
                "resource_url": url,
                "resource_class": "Exam paper",
                "language": "English",
                "notes": "Official TIFR Graduate Studies Mathematics entrance question paper. The PDF contains substantive mathematical questions and is directly public from the TIFR academic archive.",
                "access_model": "Free public PDF",
                "verification_status": "HTTP 200 · PDF · verified 2026-08-16",
                "free_resource": "Yes",
            })
    if len(rows) != len(CANDIDATES):
        raise RuntimeError(f"Only {len(rows)} of {len(CANDIDATES)} TIFR candidates passed direct PDF verification; refusing partial promotion")
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "http_status", "content_type", "included_in_tranche"])
        writer.writerows(audit_rows)
    print(f"Verified and wrote {len(rows)} TIFR Mathematics records to {OUTPUT}")
    print(f"Audit written to {AUDIT}")


if __name__ == "__main__":
    main()
