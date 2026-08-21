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
SOURCE_URL = "https://om.sem.edu.pl/problems/"
SOURCE_SNAPSHOT = Path("/home/ubuntu/poland_om_html/problems.html")
OUTPUT = DATA / "poland_om_verified_resources.csv"
AUDIT = ROOT / "research/poland_om_url_audit.csv"
VERIFY_DATE = "2026-08-14"


def existing_catalog() -> tuple[set[str], int]:
    urls: set[str] = set()
    poland_count = 0
    for path in DATA.glob("*.csv"):
        if path in {OUTPUT, DATA / "final_resources.csv"}:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                url = row.get("resource_url", "").strip()
                if url:
                    urls.add(url)
                if row.get("country") == "Poland" and row.get("free_resource", "").lower() == "yes":
                    poland_count += 1
    return urls, poland_count


def discover(existing_urls: set[str]) -> list[dict[str, str | int]]:
    if not SOURCE_SNAPSHOT.exists():
        raise RuntimeError(f"Missing official Polish Olympiad source snapshot: {SOURCE_SNAPSHOT}")
    soup = BeautifulSoup(SOURCE_SNAPSHOT.read_text(encoding="utf-8"), "html.parser")
    table = soup.find("table", class_="list")
    if not table:
        raise RuntimeError("Official Polish Olympiad problems table not found")
    candidates: dict[str, dict[str, str | int]] = {}
    for row in table.select("tbody tr"):
        cells = row.find_all("td", recursive=False)
        if len(cells) != 7:
            raise RuntimeError(f"Unexpected official archive row shape: expected 7 cells, found {len(cells)}")
        edition_text = cells[0].get_text(" ", strip=True)
        if not edition_text and all(not cell.select_one("a[href]") for cell in cells[1:]):
            continue
        edition_match = re.fullmatch(r"(\d+)\s+OM", edition_text)
        if not edition_match:
            raise RuntimeError(f"Missing source-published Olympiad edition label: {edition_text}")
        edition = int(edition_match.group(1))
        for position, cell in enumerate(cells[1:]):
            anchors = cell.select("a[href]")
            if len(anchors) > 1:
                raise RuntimeError(f"Unexpected multiple direct documents in OM {edition}, table cell {position + 1}")
            if not anchors:
                continue
            href = anchors[0]["href"].strip()
            url = urljoin(SOURCE_URL, href)
            if not re.fullmatch(r"https://om\.sem\.edu\.pl/static/app_main/problems/om\d+_[123]r?\.pdf(?:\?[^\s]+)?", url):
                raise RuntimeError(f"Unexpected source-published Polish Olympiad document URL: {url}")
            if url in existing_urls:
                continue
            stage = position // 2 + 1
            is_solution = position % 2 == 1
            record: dict[str, str | int] = {
                "url": url,
                "edition": edition,
                "stage": stage,
                "material": "Official solutions" if is_solution else "Official problems",
            }
            if url in candidates:
                raise RuntimeError(f"Duplicate direct resource target in official table: {url}")
            candidates[url] = record
    return list(candidates.values())


def verify(record: dict[str, str | int]) -> tuple[str, int, str]:
    result = subprocess.run(
        [
            "curl", "-L", "--silent", "--show-error", "--max-time", "50",
            "--user-agent", "Signal Atlas catalog verifier/1.0", "-o", "/dev/null",
            "-w", "%{http_code}|%{content_type}", str(record["url"]),
        ],
        capture_output=True,
        text=True,
        timeout=65,
        check=False,
    )
    status_text, _, content_type = result.stdout.strip().partition("|")
    return str(record["url"]), int(status_text) if status_text.isdigit() else 0, content_type.lower() or "unknown"


def main() -> None:
    existing_urls, baseline = existing_catalog()
    required = max(0, 100 - baseline)
    candidates = discover(existing_urls)
    print(f"Poland baseline: {baseline}; target additions: {required}; official OM candidates: {len(candidates)}")
    if len(candidates) < required:
        raise RuntimeError("Official Polish Olympiad archive capacity is below target; refusing to pad Poland")

    statuses: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(verify, record) for record in candidates]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            statuses[url] = (status, content_type)
    verified = [
        record for record in candidates
        if statuses.get(str(record["url"]), (0, ""))[0] == 200
        and "pdf" in statuses.get(str(record["url"]), (0, ""))[1]
    ]
    verified.sort(key=lambda record: (-int(record["edition"]), int(record["stage"]), str(record["material"]), str(record["url"])))
    print(f"Individually verified public Polish Olympiad PDFs: {len(verified)}")
    selected = verified[:required]
    if len(selected) < required:
        raise RuntimeError(f"Only {len(selected)} official PDFs verified; refusing to pad Poland")

    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in selected:
            is_solution = str(record["material"]) == "Official solutions"
            writer.writerow({
                "country": "Poland",
                "track": "EM",
                "topic_tags": "engineering mathematics;mathematical olympiad;algebra;geometry;number theory;combinatorics;contest;past paper;solutions",
                "priority": "A",
                "source_type": "National mathematics Olympiad archive",
                "source_title": "Polish Mathematical Olympiad official problems and solutions",
                "source_url": SOURCE_URL,
                "resource_title": f"Polish Mathematical Olympiad {record['edition']} — Stage {record['stage']} — {record['material']}",
                "resource_url": record["url"],
                "resource_class": "Official Olympiad solutions" if is_solution else "Past Olympiad questions",
                "language": "Polish source; English catalog title",
                "notes": "Direct public document listed in the official Polish Mathematical Olympiad problems archive.",
                "access_model": "Free public download",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    selected_urls = {str(record["url"]) for record in selected}
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "edition", "stage", "material", "http_status", "content_type", "included"])
        for record in sorted(candidates, key=lambda item: (-int(item["edition"]), int(item["stage"]), str(item["material"]))):
            status, content_type = statuses.get(str(record["url"]), (0, "not verified"))
            writer.writerow([record["url"], record["edition"], record["stage"], record["material"], status, content_type, "Yes" if str(record["url"]) in selected_urls else "No"])
    print(f"Wrote {len(selected)} verified Polish Olympiad records to {OUTPUT}")


if __name__ == "__main__":
    main()
