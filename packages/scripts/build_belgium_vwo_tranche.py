from __future__ import annotations

import csv
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "apps/web/src/data"
SOURCE_URL = "https://www.vwo.be/vwo/wedstrijdvragen-per-jaargang-en-ronde/"
SNAPSHOT = Path("/home/ubuntu/belgium_vwo_html/archive.html")
OUTPUT = DATA / "belgium_vwo_verified_resources.csv"
AUDIT = ROOT / "research/belgium_vwo_url_audit.csv"
VERIFY_DATE = "2026-08-14"

COLUMNS = [
    ("Junior Mathematics Olympiad", "First round"),
    ("Junior Mathematics Olympiad", "Second round"),
    ("Junior Mathematics Olympiad", "Final"),
    ("Flemish Mathematics Olympiad", "First round"),
    ("Flemish Mathematics Olympiad", "Second round"),
    ("Flemish Mathematics Olympiad", "Final"),
]


def existing_catalog() -> tuple[set[str], int]:
    urls: set[str] = set()
    belgium_count = 0
    for path in DATA.glob("*.csv"):
        if path in {OUTPUT, DATA / "final_resources.csv"}:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                resource_url = row.get("resource_url", "").strip()
                if resource_url:
                    urls.add(resource_url)
                if row.get("country") == "Belgium" and row.get("free_resource", "").lower() == "yes":
                    belgium_count += 1
    return urls, belgium_count


def discover(existing_urls: set[str]) -> list[dict[str, str]]:
    if not SNAPSHOT.exists():
        raise RuntimeError(f"Missing official Flemish Olympiad source snapshot: {SNAPSHOT}")
    soup = BeautifulSoup(SNAPSHOT.read_text(encoding="utf-8"), "html.parser")
    table = soup.find("table")
    if not table:
        raise RuntimeError("Official Flemish Olympiad archive table not found")
    candidates: dict[str, dict[str, str]] = {}
    for row in table.select("tr"):
        cells = row.find_all("td", recursive=False)
        if not cells:
            continue
        if len(cells) != 6:
            raise RuntimeError(f"Unexpected official Flemish archive row shape: expected 6 cells, found {len(cells)}")
        if all(not cell.select_one("a[href]") for cell in cells):
            continue
        for index, cell in enumerate(cells):
            anchors = cell.select("a[href]")
            if len(anchors) > 1:
                raise RuntimeError(f"Unexpected multiple resource links in official archive column {index + 1}")
            if not anchors:
                continue
            anchor = anchors[0]
            url = urljoin(SOURCE_URL, anchor["href"].strip())
            if not re.fullmatch(r"https://www\.vwo\.be/vwo/wp-content/uploads/\d{4}/\d{2}/[^\s]+\.pdf", url, flags=re.I):
                raise RuntimeError(f"Unexpected source-published Belgian Olympiad resource URL: {url}")
            if url in existing_urls:
                continue
            school_year = anchor.get_text(" ", strip=True)
            if not re.fullmatch(r"\d{4}[–-]\d{4}", school_year):
                raise RuntimeError(f"Missing source-published school-year label for {url}: {school_year}")
            contest, round_name = COLUMNS[index]
            if url in candidates:
                raise RuntimeError(f"Duplicate direct resource target in official archive: {url}")
            candidates[url] = {
                "url": url,
                "contest": contest,
                "round": round_name,
                "school_year": school_year,
            }
    return list(candidates.values())


def verify(record: dict[str, str]) -> tuple[str, int, str]:
    result = subprocess.run(
        [
            "curl", "-L", "--silent", "--show-error", "--max-time", "50",
            "--user-agent", "Signal Atlas catalog verifier/1.0", "-o", "/dev/null",
            "-w", "%{http_code}|%{content_type}", record["url"],
        ],
        capture_output=True,
        text=True,
        timeout=65,
        check=False,
    )
    status_text, _, content_type = result.stdout.strip().partition("|")
    return record["url"], int(status_text) if status_text.isdigit() else 0, content_type.lower() or "unknown"


def main() -> None:
    existing_urls, baseline = existing_catalog()
    required = max(0, 100 - baseline)
    candidates = discover(existing_urls)
    print(f"Belgium baseline: {baseline}; target additions: {required}; official VWO candidates: {len(candidates)}")
    if len(candidates) < required:
        raise RuntimeError("Official VWO archive capacity is below target; refusing to pad Belgium")

    statuses: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(verify, record) for record in candidates]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            statuses[url] = (status, content_type)
    verified = [
        record for record in candidates
        if statuses.get(record["url"], (0, ""))[0] == 200 and "pdf" in statuses.get(record["url"], (0, ""))[1]
    ]
    verified.sort(key=lambda record: (record["school_year"], record["contest"], record["round"], record["url"]), reverse=True)
    print(f"Individually verified public Flemish Olympiad PDFs: {len(verified)}")
    selected = verified[:required]
    if len(selected) < required:
        raise RuntimeError(f"Only {len(selected)} official PDFs verified; refusing to pad Belgium")

    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in selected:
            writer.writerow({
                "country": "Belgium",
                "track": "EM",
                "topic_tags": "engineering mathematics;mathematical olympiad;algebra;geometry;number theory;combinatorics;contest;past paper",
                "priority": "A",
                "source_type": "Official mathematics Olympiad archive",
                "source_title": "Flemish Mathematics Olympiad official archive",
                "source_url": SOURCE_URL,
                "resource_title": f"{record['contest']} — {record['school_year']} — {record['round']} questions",
                "resource_url": record["url"],
                "resource_class": "Past Olympiad questions",
                "language": "Dutch source; English catalog title",
                "notes": "Direct public question paper listed in the official Flemish Mathematics Olympiad archive.",
                "access_model": "Free public download",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    selected_urls = {record["url"] for record in selected}
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "school_year", "contest", "round", "http_status", "content_type", "included"])
        for record in sorted(candidates, key=lambda item: (item["school_year"], item["contest"], item["round"], item["url"]), reverse=True):
            status, content_type = statuses.get(record["url"], (0, "not verified"))
            writer.writerow([record["url"], record["school_year"], record["contest"], record["round"], status, content_type, "Yes" if record["url"] in selected_urls else "No"])
    print(f"Wrote {len(selected)} verified Flemish Olympiad records to {OUTPUT}")


if __name__ == "__main__":
    main()
