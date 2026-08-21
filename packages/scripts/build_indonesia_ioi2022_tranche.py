"""Build an audited Indonesia tranche from the official Indonesia-hosted IOI 2022 archive.

The task page links to twelve English PDFs, but two are general contest notices.
This generator deliberately promotes only the ten documents that contain practice or
competition tasks. Every record is checked for a public HTTP 200 PDF response and
against every existing catalog URL before it can enter the deferred catalog chunk.
"""

from __future__ import annotations

import csv
import subprocess
from pathlib import Path


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "apps/web/src/data"
OUTPUT = DATA / "indonesia_ioi2022_verified_resources.csv"
AUDIT = ROOT / "research/indonesia_ioi2022_url_audit.csv"
SOURCE_URL = "https://ioi2022.id/tasks/"
VERIFY_DATE = "2026-08-15"

TASKS = [
    ("Practice", "Cards", "https://ioi2022.id/data/practice/cards-en_ISC.pdf"),
    ("Practice", "Hoax", "https://ioi2022.id/data/practice/hoax-en_ISC.pdf"),
    ("Practice", "Team", "https://ioi2022.id/data/practice/team-en_ISC.pdf"),
    ("Practice", "Towns", "https://ioi2022.id/data/practice/towns-en_ISC.pdf"),
    ("Day 1", "Fish", "https://ioi2022.id/data/day1/fish-en_ISC.pdf"),
    ("Day 1", "Prison", "https://ioi2022.id/data/day1/prison-en_ISC.pdf"),
    ("Day 1", "Towers", "https://ioi2022.id/data/day1/towers-en_ISC.pdf"),
    ("Day 2", "Circuit", "https://ioi2022.id/data/day2/circuit-en_ISC.pdf"),
    ("Day 2", "Insects", "https://ioi2022.id/data/day2/insects-en_ISC.pdf"),
    ("Day 2", "Islands", "https://ioi2022.id/data/day2/islands-en_ISC.pdf"),
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
    outcomes: dict[str, tuple[int, str, str]] = {}
    verified: list[tuple[str, str, str]] = []

    for session, task, url in TASKS:
        if url in existing:
            outcomes[url] = (0, "duplicate", "No")
            continue
        status, content_type = verify(url)
        included = status == 200 and "application/pdf" in content_type
        outcomes[url] = (status, content_type, "Yes" if included else "No")
        if included:
            verified.append((session, task, url))

    if not verified:
        raise RuntimeError("No verified non-duplicate IOI 2022 task PDFs; refusing to write an empty tranche")

    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for session, task, url in verified:
            writer.writerow({
                "country": "Indonesia",
                "track": "DM",
                "topic_tags": "discrete mathematics;algorithms;programming;logic;problem-solving;contest;olympiad",
                "priority": "A",
                "source_type": "Indonesia-hosted international informatics Olympiad organiser archive",
                "source_title": "IOI 2022 official task archive — Indonesia",
                "source_url": SOURCE_URL,
                "resource_title": f"IOI 2022 {session} — {task} (Official English Task PDF)",
                "resource_url": url,
                "resource_class": "Informatics Olympiad problem paper",
                "language": "English",
                "notes": "Direct public English contest-task PDF from the official IOI 2022 organiser archive hosted in Indonesia. The archive also exposes two general notices, which are deliberately excluded because they are not problem materials.",
                "access_model": "Free public PDF",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source_url", "resource_url", "resource_title", "http_status", "content_type", "included"])
        for session, task, url in TASKS:
            status, content_type, included = outcomes[url]
            writer.writerow([SOURCE_URL, url, f"IOI 2022 {session} — {task}", status, content_type, included])

    print(f"Wrote {len(verified)} verified Indonesia-hosted IOI 2022 task records to {OUTPUT}")


if __name__ == "__main__":
    main()
