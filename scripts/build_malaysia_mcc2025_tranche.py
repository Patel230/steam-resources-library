from __future__ import annotations

import csv
import subprocess
from pathlib import Path


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "client/src/data"
OUTPUT = DATA / "malaysia_mcc2025_verified_resources.csv"
AUDIT = ROOT / "research/malaysia_mcc2025_url_audit.csv"
VERIFY_DATE = "2026-08-15"
SOURCE_URL = "https://ioimalaysia.org/competition/mcc/2025/archive/"

RESOURCES = [
    ("MCC 2025 — Problem 1: Building Fences", "https://ioimalaysia.org/competition/mcc/2025/archive/p1/", "Official contest problem page"),
    ("MCC 2025 — Problem 2: Fans", "https://ioimalaysia.org/competition/mcc/2025/archive/p2/", "Official contest problem page"),
    ("MCC 2025 — Problem 3: Trick or Treat", "https://ioimalaysia.org/competition/mcc/2025/archive/p3/", "Official contest problem page"),
    ("MCC 2025 — Problem 4: Word Distance", "https://ioimalaysia.org/competition/mcc/2025/archive/p4/", "Official contest problem page"),
    ("MCC 2025 — Problem 5: Reachability Queries", "https://ioimalaysia.org/competition/mcc/2025/archive/p5/", "Official contest problem page"),
    ("MCC 2025 — Problem 6: Increasing Subsequence Median Sum", "https://ioimalaysia.org/competition/mcc/2025/archive/p6/", "Official contest problem page"),
    ("MCC 2025 — Official Editorial", "https://ioimalaysia.org/competition/mcc/2025/archive/editorial/", "Official contest editorial / solution"),
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
        ["curl", "-L", "--silent", "--show-error", "--max-time", "20", "-A", "Mozilla/5.0", "-o", "/dev/null", "-w", "%{http_code}|%{content_type}", url],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    output = result.stdout.strip()
    if result.returncode != 0 or "|" not in output:
        return 0, "unavailable"
    code, content_type = output.split("|", 1)
    return (int(code) if code.isdigit() else 0), (content_type.lower() or "unknown")


def main() -> None:
    existing = catalog_urls()
    results = {url: verify(url) for _, url, _ in RESOURCES if url not in existing}
    verified = [(title, url, resource_class) for title, url, resource_class in RESOURCES if results.get(url, (0, ""))[0] == 200]

    fields = ["country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url", "resource_title", "resource_url", "resource_class", "language", "notes", "access_model", "verification_status", "free_resource"]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for title, url, resource_class in verified:
            writer.writerow({
                "country": "Malaysia",
                "track": "DM",
                "topic_tags": "algorithms;competitive programming;discrete mathematics;contest",
                "priority": "A",
                "source_type": "Official competition archive",
                "source_title": "Malaysian Computing Challenge 2025 archive",
                "source_url": SOURCE_URL,
                "resource_title": title,
                "resource_url": url,
                "resource_class": resource_class,
                "language": "English",
                "notes": "Public problem or editorial page explicitly linked from the official Malaysian Computing Challenge 2025 archive.",
                "access_model": "Free public web resource",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source_url", "resource_url", "resource_title", "http_status", "content_type", "included"])
        for title, url, _ in RESOURCES:
            status, content_type = results.get(url, (0, "duplicate or unavailable"))
            writer.writerow([SOURCE_URL, url, title, status, content_type, "Yes" if status == 200 else "No"])
    print(f"Wrote {len(verified)} Malaysia MCC 2025 records to {OUTPUT}")


if __name__ == "__main__":
    main()
