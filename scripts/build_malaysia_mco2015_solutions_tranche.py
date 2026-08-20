"""Build a small, auditable Malaysia MCO 2015 organiser-linked solutions tranche.

The Malaysian Informatics and Programming Society's public practice archive
links to this MCO 2015 solution repository. This generator promotes only the
five distinct challenge solution files that remain public, return HTTP 200,
and are not already in the catalog. It never executes repository content.
"""

from __future__ import annotations

import csv
import subprocess
from pathlib import Path


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "client/src/data"
OUTPUT = DATA / "malaysia_mco2015_solutions_verified_resources.csv"
AUDIT = ROOT / "research/malaysia_mco2015_solutions_url_audit.csv"
SOURCE_URL = "https://ioimalaysia.org/resource/for-student/practice/"
VERIFY_DATE = "2026-08-15"

SOLUTIONS = [
    ("Badminton", "badminton.cpp", "Badminton/badminton.cpp"),
    ("Bitcoin", "bitcoin.cpp", "Bitcoin/bitcoin.cpp"),
    ("Honey", "honey.cpp", "Honey/honey.cpp"),
    ("Secret", "secret_knuth-morris-pratt.cpp", "Secret/secret_knuth-morris-pratt.cpp"),
    ("Trains", "trains.cpp", "Trains/trains.cpp"),
]
RAW_BASE = "https://raw.githubusercontent.com/yihangho/MCO-2015-Solutions/master/"


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
            "curl", "-L", "--silent", "--show-error", "--max-time", "20",
            "-A", "Mozilla/5.0", "-o", "/dev/null", "-w", "%{http_code}|%{content_type}", url,
        ],
        capture_output=True,
        text=True,
        timeout=25,
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

    for challenge, _, relative_path in SOLUTIONS:
        url = RAW_BASE + relative_path
        if url in existing:
            outcomes[url] = (0, "duplicate", "No")
            continue
        status, content_type = verify(url)
        included = status == 200 and content_type.startswith("text/plain")
        outcomes[url] = (status, content_type, "Yes" if included else "No")
        if included:
            verified.append((challenge, url))

    if not verified:
        raise RuntimeError("No verified non-duplicate MCO 2015 solution sources; refusing to write an empty tranche")

    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for challenge, url in verified:
            writer.writerow({
                "country": "Malaysia",
                "track": "DM",
                "topic_tags": "algorithms;competitive programming;discrete mathematics;contest;solutions",
                "priority": "A",
                "source_type": "Official competition organiser-linked solution archive",
                "source_title": "Malaysia Informatics and Programming Society public practice archive",
                "source_url": SOURCE_URL,
                "resource_title": f"Malaysian Computing Olympiad 2015 — {challenge} solution source",
                "resource_url": url,
                "resource_class": "Contest solution source code",
                "language": "English source code",
                "notes": "Direct public C++ solution source from the MCO 2015 repository explicitly linked by the official Malaysia Informatics and Programming Society practice archive.",
                "access_model": "Free public web resource",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source_url", "resource_url", "challenge", "http_status", "content_type", "included"])
        for challenge, _, relative_path in SOLUTIONS:
            url = RAW_BASE + relative_path
            status, content_type, included = outcomes[url]
            writer.writerow([SOURCE_URL, url, challenge, status, content_type, included])

    print(f"Wrote {len(verified)} verified MCO 2015 solution-source records to {OUTPUT}")


if __name__ == "__main__":
    main()
