from __future__ import annotations

import csv
import subprocess
from pathlib import Path


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "apps/web/src/data"
OUTPUT = DATA / "malaysia_emos_som2025_verified_resources.csv"
AUDIT = ROOT / "research/malaysia_emos_som2025_url_audit.csv"
VERIFY_DATE = "2026-08-15"
SOURCE_URL = "https://emosmalaysia.com/sample-questions/"
BASE_URL = "https://emosmalaysia.com/wp-content/uploads/2025/12/"

RESOURCES = [
    ("GA", "International Spirit of Math Contest 2025 — Grade 1 Question Paper", "Gr1_SoMC_2025.pdf", "Sample mathematics contest paper / MCQs", "Public English Grade 1 multiple-choice mathematics contest paper linked from EMOS Malaysia's official Sample Questions page."),
    ("GA", "International Spirit of Math Contest 2025 — Grade 2 Question Paper", "Gr2_SoMC_2025.pdf", "Sample mathematics contest paper / MCQs", "Public English Grade 2 multiple-choice mathematics contest paper linked from EMOS Malaysia's official Sample Questions page."),
    ("GA", "International Spirit of Math Contest 2025 — Grade 3 Question Paper", "Gr3_SoMC_2025.pdf", "Sample mathematics contest paper / MCQs", "Public English Grade 3 multiple-choice mathematics contest paper linked from EMOS Malaysia's official Sample Questions page."),
    ("GA", "International Spirit of Math Contest 2025 — Grade 4 Question Paper", "Gr4_SoMC_2025.pdf", "Sample mathematics contest paper / MCQs", "Public English Grade 4 multiple-choice mathematics contest paper linked from EMOS Malaysia's official Sample Questions page."),
    ("GA", "International Spirit of Math Contest 2025 — Grade 5 Question Paper", "Gr5_SoMC_2025-1.pdf", "Sample mathematics contest paper / MCQs", "Public English Grade 5 multiple-choice mathematics contest paper linked from EMOS Malaysia's official Sample Questions page."),
    ("GA", "International Spirit of Math Contest 2025 — Grade 6 Question Paper", "Gr6_SoMC_2025-1.pdf", "Sample mathematics contest paper / MCQs", "Public English Grade 6 multiple-choice mathematics contest paper linked from EMOS Malaysia's official Sample Questions page."),
    ("GA", "International Spirit of Math Contest 2025 — Grade 3 Official Solutions", "Gr3_SoMC_2025_Solutions.pdf", "Official mathematics contest solutions", "Public English Grade 3 answer key and worked mathematics explanations linked from EMOS Malaysia's official Sample Questions page."),
    ("GA", "International Spirit of Math Contest 2025 — Grade 4 Official Solutions", "Gr4_SoMC_2025_Solutions.pdf", "Official mathematics contest solutions", "Public English Grade 4 answer key and worked mathematics explanations linked from EMOS Malaysia's official Sample Questions page."),
    ("GA", "International Spirit of Math Contest 2025 — Grade 5 Official Solutions", "Gr5_SoMC_2025_Solutions-1.pdf", "Official mathematics contest solutions", "Public English Grade 5 answer key and worked mathematics explanations linked from EMOS Malaysia's official Sample Questions page."),
    ("GA", "International Spirit of Math Contest 2025 — Grade 6 Official Solutions", "Gr6_SoMC_2025_Solutions-1.pdf", "Official mathematics contest solutions", "Public English Grade 6 answer key and worked mathematics explanations linked from EMOS Malaysia's official Sample Questions page."),
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
    verified: list[tuple[str, str, str, str, str]] = []

    for track, title, filename, resource_class, notes in RESOURCES:
        url = BASE_URL + filename
        if url in existing:
            outcomes[url] = (0, "duplicate", "No")
            continue
        status, content_type = verify(url)
        included = status == 200 and "application/pdf" in content_type
        outcomes[url] = (status, content_type, "Yes" if included else "No")
        if included:
            verified.append((track, title, url, resource_class, notes))

    fields = ["country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url", "resource_title", "resource_url", "resource_class", "language", "notes", "access_model", "verification_status", "free_resource"]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for track, title, url, resource_class, notes in verified:
            writer.writerow({
                "country": "Malaysia",
                "track": track,
                "topic_tags": "mathematical reasoning;numeracy;multiple choice;competition",
                "priority": "B",
                "source_type": "Official competition sample-paper archive",
                "source_title": "EMOS Malaysia — Spirit of Math sample questions and solutions",
                "source_url": SOURCE_URL,
                "resource_title": title,
                "resource_url": url,
                "resource_class": resource_class,
                "language": "English",
                "notes": notes,
                "access_model": "Free public PDF",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source_url", "resource_url", "resource_title", "http_status", "content_type", "included"])
        for _, title, filename, _, _ in RESOURCES:
            url = BASE_URL + filename
            status, content_type, included = outcomes[url]
            writer.writerow([SOURCE_URL, url, title, status, content_type, included])

    print(f"Wrote {len(verified)} verified EMOS Malaysia Spirit of Math records to {OUTPUT}")


if __name__ == "__main__":
    main()
