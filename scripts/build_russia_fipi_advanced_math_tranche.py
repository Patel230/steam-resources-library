from __future__ import annotations

import csv
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "client/src/data"
SNAPSHOT_DIR = Path("/home/ubuntu/fipi_russia_html")
PROJECT_ID = "AC437B34557F88EA4115D2F374B0A07B"
SOURCE_URL = f"https://ege.fipi.ru/bank/index.php?proj={PROJECT_ID}"
QUESTION_BASE = "https://ege.fipi.ru/bank/questions.php"
OUTPUT = DATA / "russia_fipi_advanced_math_verified_resources.csv"
AUDIT = ROOT / "research/russia_fipi_advanced_math_url_audit.csv"
VERIFY_DATE = "2026-08-14"
PAGE_COUNT = 12


def existing_catalog() -> tuple[set[str], int]:
    urls: set[str] = set()
    russia_count = 0
    for path in DATA.glob("*.csv"):
        if path in {OUTPUT, DATA / "final_resources.csv"}:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                url = row.get("resource_url", "").strip()
                if url:
                    urls.add(url)
                if row.get("country") == "Russia" and row.get("free_resource", "").lower() == "yes":
                    russia_count += 1
    return urls, russia_count


def page_url(page_index: int) -> str:
    return f"{QUESTION_BASE}?proj={PROJECT_ID}&page={page_index}&pagesize=10"


def discover(existing_urls: set[str]) -> list[dict[str, str | int]]:
    candidates: dict[str, dict[str, str | int]] = {}
    for page_number in range(1, PAGE_COUNT + 1):
        snapshot = SNAPSHOT_DIR / f"advanced_math_page_{page_number}.html"
        if not snapshot.exists():
            raise RuntimeError(f"Missing official FIPI snapshot: {snapshot}")
        soup = BeautifulSoup(snapshot.read_text(encoding="utf-8", errors="replace"), "html.parser")
        task_nodes = soup.find_all("div", id=re.compile(r"^i[A-F0-9]{6}$"))
        if not task_nodes:
            raise RuntimeError(f"No source-issued task identifiers found in {snapshot}")
        for node in task_nodes:
            task_id = node["id"][1:]
            backing_url = page_url(page_number - 1)
            resource_url = f"{backing_url}#i{task_id}"
            if resource_url in existing_urls:
                continue
            record: dict[str, str | int] = {
                "task_id": task_id,
                "page_number": page_number,
                "backing_url": backing_url,
                "resource_url": resource_url,
            }
            prior = candidates.get(task_id)
            if prior and prior != record:
                raise RuntimeError(f"Conflicting source-issued FIPI task ID across pages: {task_id}")
            candidates[task_id] = record
    return list(candidates.values())


def verify_page(url: str) -> tuple[str, int, str]:
    result = subprocess.run(
        [
            "curl", "-k", "-L", "--silent", "--show-error", "--max-time", "50",
            "--user-agent", "Signal Atlas catalog verifier/1.0", "-o", "/dev/null",
            "-w", "%{http_code}|%{content_type}", url,
        ],
        capture_output=True,
        text=True,
        timeout=65,
        check=False,
    )
    response = result.stdout.strip()
    status_text, _, content_type = response.partition("|")
    return url, int(status_text) if status_text.isdigit() else 0, content_type.lower() or "unknown"


def main() -> None:
    existing_urls, baseline = existing_catalog()
    required = max(0, 100 - baseline)
    candidates = discover(existing_urls)
    print(f"Russia baseline: {baseline}; target additions: {required}; source-issued task candidates: {len(candidates)}")
    if len(candidates) < required:
        raise RuntimeError("Official FIPI source capacity is below the target; refusing to pad Russia")

    backing_urls = sorted({str(record["backing_url"]) for record in candidates})
    statuses: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(verify_page, url) for url in backing_urls]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            statuses[url] = (status, content_type)

    verified = [
        record for record in candidates
        if statuses.get(str(record["backing_url"]), (0, ""))[0] == 200
        and "text/html" in statuses.get(str(record["backing_url"]), (0, ""))[1]
    ]
    verified.sort(key=lambda record: (int(record["page_number"]), str(record["task_id"])))
    print(f"Individually anchored FIPI tasks on verified public pages: {len(verified)}")
    selected = verified[:required]
    if len(selected) < required:
        raise RuntimeError(f"Only {len(selected)} FIPI tasks are on verified public pages; refusing to pad Russia")

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
                "country": "Russia",
                "track": "EM",
                "topic_tags": "engineering mathematics;advanced mathematics;algebra;calculus;geometry;vectors;exam;practice question",
                "priority": "A",
                "source_type": "National examination task bank",
                "source_title": "FIPI Unified State Examination open task bank — Advanced Mathematics",
                "source_url": SOURCE_URL,
                "resource_title": f"FIPI Unified State Examination Advanced Mathematics — official task {record['task_id']}",
                "resource_url": record["resource_url"],
                "resource_class": "Official examination practice question",
                "language": "Russian source; English catalog title",
                "notes": f"Individual source-issued task anchor on FIPI Advanced Mathematics task-bank page {record['page_number']}.",
                "access_model": "Free public web access",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    selected_urls = {str(record["resource_url"]) for record in selected}
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "task_id", "source_page", "http_status", "content_type", "included"])
        for record in sorted(candidates, key=lambda item: (int(item["page_number"]), str(item["task_id"]))):
            status, content_type = statuses.get(str(record["backing_url"]), (0, "not verified"))
            writer.writerow([
                record["resource_url"], record["task_id"], record["backing_url"], status, content_type,
                "Yes" if str(record["resource_url"]) in selected_urls else "No",
            ])
    print(f"Wrote {len(selected)} verified FIPI task records to {OUTPUT}")


if __name__ == "__main__":
    main()
