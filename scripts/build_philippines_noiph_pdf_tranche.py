"""Build a verified Philippines tranche from the official direct-PDF NOI.PH archive.

The organiser's archive includes many HackerRank and Codeforces routes, but this
generator intentionally uses only the 2021–2026 same-domain PDFs explicitly
labelled "PDF Only" on the official archive page. Each source document must
return HTTP 200 as a PDF, contain extractable English contest language, and be
unique within the full catalog before it is emitted.
"""

from __future__ import annotations

import csv
import subprocess
import tempfile
from pathlib import Path


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "client/src/data"
OUTPUT = DATA / "philippines_noiph_pdf_verified_resources.csv"
AUDIT = ROOT / "research/philippines_noiph_pdf_url_audit.csv"
SOURCE_URL = "https://noi.ph/elims-finals-archive/"
VERIFY_DATE = "2026-08-15"

PAPERS = [
    ("2021", "Finals — Day 1", "https://noi.ph/wp-content/uploads/2023/07/NOI_PH_2021_Finals-2-1.pdf?x44806"),
    ("2021", "Finals — Day 2", "https://noi.ph/wp-content/uploads/2023/07/NOI_PH_2021_Finals-2.pdf?x44806"),
    ("2022", "Eliminations", "https://noi.ph/wp-content/uploads/2023/07/NOI_PH_2022_Elims.pdf?x44806"),
    ("2022", "Finals — Day 1", "https://noi.ph/wp-content/uploads/2023/07/NOI_PH_2022_Finals-10.pdf?x44806"),
    ("2022", "Finals — Day 2", "https://noi.ph/wp-content/uploads/2023/07/NOI_PH_2022_Finals-11.pdf?x44806"),
    ("2023", "Eliminations", "https://noi.ph/wp-content/uploads/2023/07/NOI_PH_2023_Elims-1.pdf?x44806"),
    ("2023", "Finals — Day 1", "https://noi.ph/wp-content/uploads/2023/07/NOI_PH_2023_Finals.pdf?x44806"),
    ("2023", "Finals — Day 2", "https://noi.ph/wp-content/uploads/2023/07/NOI_PH_2023_Finals-1.pdf?x44806"),
    ("2024", "Eliminations", "https://noi.ph/wp-content/uploads/2026/05/NOI_PH_2024_Elims.pdf?x44806"),
    ("2024", "Finals — Day 1", "https://noi.ph/wp-content/uploads/2026/05/NOI_PH_2024_Finals-1.pdf?x44806"),
    ("2024", "Finals — Day 2", "https://noi.ph/wp-content/uploads/2026/05/NOI_PH_2024_Finals-2.pdf?x44806"),
    ("2025", "Eliminations", "https://noi.ph/wp-content/uploads/2026/05/NOI_PH_2025_Elims.pdf?x44806"),
    ("2025", "Finals — Day 1", "https://noi.ph/wp-content/uploads/2026/05/NOI_PH_2025_Finals-1.pdf?x44806"),
    ("2025", "Finals — Day 2", "https://noi.ph/wp-content/uploads/2026/05/NOI_PH_2025_Finals-2.pdf?x44806"),
    ("2026", "Eliminations", "https://noi.ph/wp-content/uploads/2026/05/NOI_PH_2026_Elims.pdf?x44806"),
]


def catalog_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob("*.csv"):
        if path == OUTPUT:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            urls.update(row.get("resource_url", "").strip() for row in csv.DictReader(handle))
    return urls


def fetch_and_check(url: str, destination: Path) -> tuple[int, str, str, str]:
    result = subprocess.run(
        [
            "curl", "-L", "--silent", "--show-error", "--max-time", "50",
            "-A", "Mozilla/5.0", "-o", str(destination),
            "-w", "%{http_code}|%{content_type}", url,
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    output = result.stdout.strip()
    if result.returncode != 0 or "|" not in output:
        return 0, "unavailable", "", "curl failed"

    code_text, content_type = output.split("|", 1)
    status = int(code_text) if code_text.isdigit() else 0
    if status != 200 or "application/pdf" not in content_type.lower():
        return status, content_type.lower() or "unknown", "", "not a public PDF"

    extract = subprocess.run(
        ["pdftotext", "-f", "1", "-l", "2", "-layout", str(destination), "-"],
        capture_output=True,
        text=True,
        timeout=25,
        check=False,
    )
    preview = extract.stdout.replace("\x00", " ").strip().replace("\n", " ")[:300]
    lowered = extract.stdout.lower()
    markers = ("problem", "input", "output", "constraints", "contest", "algorithm")
    english_ok = sum(marker in lowered for marker in markers) >= 2
    return status, content_type.lower(), preview, "English contest language confirmed" if english_ok else "English contest markers not confirmed"


def main() -> None:
    existing = catalog_urls()
    outcomes: list[tuple[str, str, str, int, str, str, str]] = []
    verified: list[tuple[str, str, str]] = []

    with tempfile.TemporaryDirectory(prefix="noiph-pdf-") as directory:
        temp_dir = Path(directory)
        for index, (year, round_name, url) in enumerate(PAPERS, start=1):
            if url in existing:
                outcomes.append((year, round_name, url, 0, "duplicate", "", "No"))
                continue
            status, content_type, preview, finding = fetch_and_check(url, temp_dir / f"paper-{index}.pdf")
            included = status == 200 and "application/pdf" in content_type and finding == "English contest language confirmed"
            outcomes.append((year, round_name, url, status, content_type, preview, "Yes" if included else "No"))
            if included:
                verified.append((year, round_name, url))

    if not verified:
        raise RuntimeError("No verified non-duplicate official NOI.PH PDFs; refusing to write an empty tranche")

    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for year, round_name, url in verified:
            writer.writerow({
                "country": "Philippines",
                "track": "DM",
                "topic_tags": "discrete mathematics;algorithms;programming;logic;problem-solving;contest;olympiad",
                "priority": "A",
                "source_type": "National programming Olympiad organiser archive",
                "source_title": "NOI.PH official elimination and finals problem archive",
                "source_url": SOURCE_URL,
                "resource_title": f"NOI.PH {year} {round_name} (Official English Problem PDF)",
                "resource_url": url,
                "resource_class": "Informatics Olympiad problem paper",
                "language": "English",
                "notes": "Direct public English contest-problem PDF hosted on the official Philippine Programming Contest website. The official archive labels this round PDF Only; login-gated HackerRank and group-gated Codeforces routes are deliberately excluded.",
                "access_model": "Free public PDF",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source_url", "resource_url", "resource_title", "http_status", "content_type", "text_preview", "included"])
        for year, round_name, url, status, content_type, preview, included in outcomes:
            writer.writerow([SOURCE_URL, url, f"NOI.PH {year} {round_name}", status, content_type, preview, included])

    print(f"Wrote {len(verified)} verified official NOI.PH problem-PDF records to {OUTPUT}")


if __name__ == "__main__":
    main()
