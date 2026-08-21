"""Build a verified South Africa Computer Olympiad tranche from official public ZIP inventories."""

from __future__ import annotations

import csv
import io
import re
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote

import requests


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "apps/web/src/data"
OUTPUT = DATA / "south_africa_computer_olympiad_verified_resources.csv"
AUDIT = ROOT / "research/south_africa_computer_olympiad_url_audit.csv"
BASE = "https://s3.af-south-1.amazonaws.com/olympiad.org.za"
ARCHIVES = {
    "programming": f"{BASE}/programming-olympiad.zip",
    "applications": f"{BASE}/applications-olympiad.zip",
}
SOURCE_PAGES = {
    "programming": "https://olympiad.org.za/past-papers/programming",
    "applications": "https://olympiad.org.za/past-papers/applications",
}
TARGET_ADDITIONS = 97
HEADERS = {"User-Agent": "Mozilla/5.0 SignalAtlasResearch/1.0"}


def existing_free_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob("*.csv"):
        if path in {OUTPUT, DATA / "final_resources.csv"}:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            urls.update(row.get("resource_url", "").strip() for row in csv.DictReader(handle) if row.get("resource_url"))
    return urls


def candidates() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    allowed = re.compile(r"(?:question[- ]?paper|paper|solutions?|marking[- ]?schedule)\.pdf$", re.I)
    for kind, archive_url in ARCHIVES.items():
        response = requests.get(archive_url, headers=HEADERS, timeout=90)
        response.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            for name in archive.namelist():
                if name.endswith("/") or not allowed.search(name):
                    continue
                if not re.search(r"(?:19|20)\d{2}/", name):
                    continue
                year = re.search(r"((?:19|20)\d{2})/", name).group(1)
                url = f"{BASE}/{kind}/{quote(name)}"
                lower = name.lower()
                if "solution" in lower:
                    resource_class = "Solution archive"
                elif "marking" in lower:
                    resource_class = "Marking scheme"
                else:
                    resource_class = "Contest paper"
                clean_name = Path(name).stem.replace("-", " ")
                rows.append({
                    "kind": kind,
                    "year": year,
                    "url": url,
                    "resource_class": resource_class,
                    "resource_title": f"{clean_name} — official {resource_class.lower()}",
                })
    # Recent first, then direct problem papers before supporting records.
    priority = {"Contest paper": 0, "Solution archive": 1, "Marking scheme": 2}
    unique = {row["url"]: row for row in rows}
    return sorted(unique.values(), key=lambda row: (-int(row["year"]), priority[row["resource_class"]], row["url"]))


def verify(candidate: dict[str, str]) -> tuple[str, int, str]:
    try:
        response = requests.get(candidate["url"], headers=HEADERS, timeout=25, stream=True)
        content_type = response.headers.get("content-type", "")
        response.close()
        return candidate["url"], response.status_code, content_type
    except requests.RequestException as error:
        return candidate["url"], 0, type(error).__name__


def main() -> None:
    existing = existing_free_urls()
    possible = [candidate for candidate in candidates() if candidate["url"] not in existing]
    print(f"Non-duplicate official South Africa candidates: {len(possible)}")
    results: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(verify, candidate): candidate["url"] for candidate in possible}
        for future in as_completed(futures):
            url, status, content_type = future.result()
            results[url] = (status, content_type)
    verified = [candidate for candidate in possible if results[candidate["url"]][0] == 200][:TARGET_ADDITIONS]
    if len(verified) < TARGET_ADDITIONS:
        raise RuntimeError(f"Only {len(verified)} verified South Africa candidates; refusing to pad the tranche")

    columns = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for candidate in verified:
            title = "Programming Olympiad" if candidate["kind"] == "programming" else "Applications Olympiad"
            writer.writerow({
                "country": "South Africa",
                "track": "DM" if candidate["kind"] == "programming" else "GA",
                "topic_tags": "algorithms;computational thinking;logic;problem solving;Olympiad;contest" if candidate["kind"] == "programming" else "general aptitude;logic;data interpretation;computer applications;contest",
                "priority": "A",
                "source_type": "National computer Olympiad archive",
                "source_title": f"Computer Olympiad South Africa — {title} archive (official)",
                "source_url": SOURCE_PAGES[candidate["kind"]],
                "resource_title": candidate["resource_title"],
                "resource_url": candidate["url"],
                "resource_class": candidate["resource_class"],
                "language": "English source",
                "notes": f"Official {title} resource from the public annual archive; year {candidate['year']}.",
                "access_model": "Free public PDF",
                "verification_status": "HTTP 200 · verified 2026-08-14",
                "free_resource": "Yes",
            })
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "http_status", "content_type", "included_in_target"])
        included = {candidate["url"] for candidate in verified}
        for candidate in possible:
            writer.writerow([candidate["url"], *results[candidate["url"]], "Yes" if candidate["url"] in included else "No"])
    print(f"Verified and wrote {len(verified)} South Africa records to {OUTPUT}")
    print(f"Audit written to {AUDIT}")


if __name__ == "__main__":
    main()
