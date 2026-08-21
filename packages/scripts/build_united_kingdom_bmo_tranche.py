"""Build a verified UK BMO problem-paper tranche from the official public archive."""

from __future__ import annotations

import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "apps/web/src/data"
OUTPUT = DATA / "united_kingdom_bmo_verified_resources.csv"
AUDIT = ROOT / "research/united_kingdom_bmo_url_audit.csv"
SOURCE_URL = "https://bmos.ukmt.org.uk/home/bmo.shtml"
TARGET_ADDITIONS = 94
HEADERS = {"User-Agent": "Mozilla/5.0 SignalAtlasResearch/1.0"}


def existing_free_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob("*.csv"):
        if path == OUTPUT or path.name == "final_resources.csv":
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            urls.update(row.get("resource_url", "").strip() for row in csv.DictReader(handle) if row.get("resource_url"))
    return urls


def archive_candidates() -> list[dict[str, str]]:
    response = requests.get(SOURCE_URL, headers=HEADERS, timeout=35)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    candidates: dict[str, dict[str, str]] = {}
    for link in soup.select("a[href]"):
        url = requests.compat.urljoin(SOURCE_URL, link["href"])
        basename = url.split("?", 1)[0].rsplit("/", 1)[-1].lower()
        if not re.fullmatch(r"(?:bmo1|bmo2|bmo|fist)-\d{4}\.pdf", basename):
            continue
        match = re.search(r"(bmo1|bmo2|bmo|fist)-(\d{4})\.pdf", basename)
        if not match:
            continue
        family, year = match.groups()
        label = {
            "bmo1": "British Mathematical Olympiad Round 1",
            "bmo2": "British Mathematical Olympiad Round 2",
            "bmo": "British Mathematical Olympiad",
            "fist": "Further International Selection Test",
        }[family]
        candidates[url] = {"url": url, "year": year, "label": label}
    return sorted(candidates.values(), key=lambda row: (int(row["year"]), row["label"]), reverse=True)


def verify(candidate: dict[str, str]) -> tuple[str, int, str]:
    try:
        response = requests.get(candidate["url"], headers=HEADERS, timeout=20, stream=True)
        content_type = response.headers.get("content-type", "")
        response.close()
        return candidate["url"], response.status_code, content_type
    except requests.RequestException as error:
        return candidate["url"], 0, type(error).__name__


def main() -> None:
    existing = existing_free_urls()
    candidates = [candidate for candidate in archive_candidates() if candidate["url"] not in existing]
    print(f"Non-duplicate BMO archive candidates: {len(candidates)}")
    audit: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(verify, candidate): candidate["url"] for candidate in candidates}
        for future in as_completed(futures):
            url, status, content_type = future.result()
            audit[url] = (status, content_type)
    verified = [candidate for candidate in candidates if audit[candidate["url"]][0] == 200][:TARGET_ADDITIONS]
    if len(verified) < TARGET_ADDITIONS:
        raise RuntimeError(f"Only {len(verified)} verified BMO papers found; refusing to pad the United Kingdom tranche")

    columns = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for candidate in verified:
            writer.writerow({
                "country": "United Kingdom",
                "track": "DM",
                "topic_tags": "discrete mathematics;combinatorics;number theory;problem solving;Olympiad;contest",
                "priority": "A",
                "source_type": "National mathematics Olympiad archive",
                "source_title": "British Mathematical Olympiad archive (official)",
                "source_url": SOURCE_URL,
                "resource_title": f"{candidate['label']} {candidate['year']} — official problem paper",
                "resource_url": candidate["url"],
                "resource_class": "Contest paper",
                "language": "English source",
                "notes": "Official UKMT British Mathematical Olympiad problem paper from the public archive.",
                "access_model": "Free public PDF",
                "verification_status": "HTTP 200 · verified 2026-08-14",
                "free_resource": "Yes",
            })
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "http_status", "content_type", "included_in_target"])
        included = {candidate["url"] for candidate in verified}
        for candidate in candidates:
            writer.writerow([candidate["url"], *audit[candidate["url"]], "Yes" if candidate["url"] in included else "No"])
    print(f"Verified and wrote {len(verified)} United Kingdom BMO records to {OUTPUT}")
    print(f"Audit written to {AUDIT}")


if __name__ == "__main__":
    main()
