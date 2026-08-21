"""Create a verified USACO historical-contest tranche for the United States catalog."""

from __future__ import annotations

import csv
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "apps/web/src/data"
OUTPUT = DATA / "united_states_usaco_verified_resources.csv"
AUDIT = ROOT / "research/united_states_usaco_url_audit.csv"
BASE = "https://usaco.org/"
EVENTS = ["feb25results", "jan25results", "dec24results"]
HEADERS = {"User-Agent": "Mozilla/5.0 SignalAtlasResearch/1.0"}


def existing_free_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob("*.csv"):
        if path in {OUTPUT, DATA / "final_resources.csv"}:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            urls.update(row.get("resource_url", "").strip() for row in csv.DictReader(handle) if row.get("resource_url"))
    return urls


def event_candidates(event: str) -> list[dict[str, str]]:
    source_url = f"{BASE}index.php?page={event}"
    response = requests.get(source_url, headers=HEADERS, timeout=40)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    event_title = soup.find("h2").get_text(" ", strip=True) if soup.find("h2") else event.replace("results", "")
    candidates: list[dict[str, str]] = []
    anchors = list(soup.select("a[href]"))
    for index, anchor in enumerate(anchors):
        if anchor.get_text(" ", strip=True).lower() != "view problem":
            continue
        problem_url = urljoin(source_url, anchor["href"])
        problem_name_element = anchor.find_previous(["strong", "b"])
        problem_name = problem_name_element.get_text(" ", strip=True) if problem_name_element else "Official contest problem"
        division_element = anchor.find_previous("h2")
        division = division_element.get_text(" ", strip=True).split(",")[-1].strip() if division_element else "Contest division"
        solution_url = ""
        for next_anchor in anchors[index + 1 :]:
            label = next_anchor.get_text(" ", strip=True).lower()
            if label == "view problem":
                break
            if label == "solution":
                solution_url = urljoin(source_url, next_anchor["href"])
                break
        candidates.append({
            "event_title": event_title,
            "division": division,
            "problem_name": problem_name,
            "kind": "problem",
            "resource_url": problem_url,
            "source_url": source_url,
        })
        if solution_url:
            candidates.append({
                "event_title": event_title,
                "division": division,
                "problem_name": problem_name,
                "kind": "solution",
                "resource_url": solution_url,
                "source_url": source_url,
            })
    return candidates


def verify(candidate: dict[str, str]) -> tuple[str, int, str]:
    try:
        result = subprocess.run(
            ["curl", "-L", "-I", "--max-time", "35", "-A", HEADERS["User-Agent"], candidate["resource_url"]],
            text=True,
            capture_output=True,
            check=False,
        )
        blocks = [block for block in result.stdout.split("\r\n\r\n") if "HTTP/" in block]
        header_block = blocks[-1] if blocks else result.stdout
        status_match = __import__("re").search(r"HTTP/\S+\s+(\d{3})", header_block)
        content_match = __import__("re").search(r"(?im)^content-type:\s*(.+)$", header_block)
        return candidate["resource_url"], int(status_match.group(1)) if status_match else 0, content_match.group(1).strip() if content_match else ""
    except OSError as error:
        return candidate["resource_url"], 0, type(error).__name__


def main() -> None:
    existing = existing_free_urls()
    candidates = [candidate for event in EVENTS for candidate in event_candidates(event)]
    candidates = [candidate for candidate in candidates if candidate["resource_url"] not in existing]
    print(f"Non-duplicate source-discovered USACO candidates: {len(candidates)}")
    statuses: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(verify, candidate) for candidate in candidates]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            statuses[url] = (status, content_type)
    verified = [candidate for candidate in candidates if statuses[candidate["resource_url"]][0] == 200]
    if len(verified) < 69:
        raise RuntimeError(f"Only {len(verified)} verified USACO resources; refusing to pad the United States tranche")

    columns = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for candidate in verified:
            is_solution = candidate["kind"] == "solution"
            writer.writerow({
                "country": "United States",
                "track": "DM",
                "topic_tags": "discrete mathematics;algorithms;combinatorics;graph theory;programming;Olympiad;contest;problem solving",
                "priority": "A",
                "source_type": "National computing Olympiad contest archive",
                "source_title": "USA Computing Olympiad historical contest archive (official)",
                "source_url": candidate["source_url"],
                "resource_title": f"{candidate['event_title']} — {candidate['division']} — {candidate['problem_name']} ({'official solution' if is_solution else 'official problem'})",
                "resource_url": candidate["resource_url"],
                "resource_class": "Solution archive" if is_solution else "Olympiad problem",
                "language": "English source",
                "notes": "Official USACO historic contest material; source page publishes public problems with associated solutions.",
                "access_model": "Free public web resource",
                "verification_status": "HTTP 200 · verified 2026-08-14",
                "free_resource": "Yes",
            })
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "http_status", "content_type", "included"])
        for candidate in candidates:
            url = candidate["resource_url"]
            writer.writerow([url, *statuses[url], "Yes" if statuses[url][0] == 200 else "No"])
    print(f"Verified and wrote {len(verified)} United States records to {OUTPUT}")
    print(f"Audit written to {AUDIT}")


if __name__ == "__main__":
    main()
