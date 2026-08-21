"""Build an audited Indonesia tranche from the public OSN Informatics archive.

Each resource URL is a direct PDF visibly published in the organiser-maintained
OSN archive table. The script refuses to promote duplicate URLs or responses
that do not return public PDF content.
"""

from __future__ import annotations

import csv
import subprocess
from pathlib import Path


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "apps/web/src/data"
OUTPUT = DATA / "indonesia_osn_pdf_verified_resources.csv"
AUDIT = ROOT / "research/indonesia_osn_pdf_url_audit.csv"
SOURCE_URL = "https://osn.toki.id/arsip"
BASE_URL = "https://osn.toki.id/data/"
VERIFY_DATE = "2026-08-15"

PROBLEMS = [
    (year, f"OSN{year}.pdf", f"Indonesian National Science Olympiad Informatics — {year} Problem Paper")
    for year in range(2005, 2020)
]
SOLUTIONS = [
    (year, f"OSN{year}Pembahasan.pdf", f"Indonesian National Science Olympiad Informatics — {year} Official Solutions")
    for year in (2013, 2017, 2018, 2019)
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
        [
            "curl", "-I", "-L", "--silent", "--show-error", "--max-time", "35",
            "-A", "Mozilla/5.0", "-o", "/dev/null", "-w", "%{http_code}|%{content_type}", url,
        ],
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    output = result.stdout.strip()
    if result.returncode != 0 or "|" not in output:
        return 0, "unavailable"
    code, content_type = output.split("|", 1)
    return (int(code) if code.isdigit() else 0), (content_type.lower() or "unknown")


def main() -> None:
    existing = catalog_urls()
    resources = [
        (year, filename, title, "Olympiad problem paper") for year, filename, title in PROBLEMS
    ] + [
        (year, filename, title, "Official olympiad solutions") for year, filename, title in SOLUTIONS
    ]
    outcomes: dict[str, tuple[int, str, str]] = {}
    verified: list[tuple[int, str, str, str, str]] = []

    for year, filename, title, resource_class in resources:
        url = BASE_URL + filename
        if url in existing:
            outcomes[url] = (0, "duplicate", "No")
            continue
        status, content_type = verify(url)
        included = status == 200 and "application/pdf" in content_type
        outcomes[url] = (status, content_type, "Yes" if included else "No")
        if included:
            verified.append((year, title, url, resource_class, filename))

    if not verified:
        raise RuntimeError("No verified non-duplicate OSN PDFs; refusing to write an empty tranche")

    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for _, title, url, resource_class, _ in verified:
            writer.writerow({
                "country": "Indonesia",
                "track": "DM",
                "topic_tags": "discrete mathematics;algorithms;programming;logic;problem-solving;contest;olympiad",
                "priority": "A",
                "source_type": "National informatics olympiad organiser archive",
                "source_title": "OSN Informatics archive — IA TOKI",
                "source_url": SOURCE_URL,
                "resource_title": title,
                "resource_url": url,
                "resource_class": resource_class,
                "language": "Indonesian source; English-facing metadata",
                "notes": "Direct public PDF visibly listed in the organiser-maintained OSN Informatics archive. The original contest material is Indonesian; the catalog title and description are English-facing.",
                "access_model": "Free public PDF",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source_url", "resource_url", "resource_title", "http_status", "content_type", "included"])
        for _, filename, title, _ in resources:
            url = BASE_URL + filename
            status, content_type, included = outcomes[url]
            writer.writerow([SOURCE_URL, url, title, status, content_type, included])

    print(f"Wrote {len(verified)} verified Indonesian OSN PDF records to {OUTPUT}")


if __name__ == "__main__":
    main()
