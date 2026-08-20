"""Verify historic Japanese Olympiad in Informatics task and solution PDFs."""

from __future__ import annotations

import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "client/src/data"
OUTPUT = DATA / "japan_joi_verified_resources.csv"
AUDIT = ROOT / "research/japan_joi_url_audit.csv"
TARGET_ADDITIONS = 92
YEARS = range(2019, 2026)
OFFICIAL_PAGES = [
    *(f"https://contests.ioi-jp.org/joi-ho-{year}/index-en.html" for year in YEARS),
    *(f"https://contests.ioi-jp.org/joi-sp-{year}/index-en.html" for year in YEARS),
]
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 SignalAtlasResearch/1.0"})


def existing_free_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob("*.csv"):
        if path == OUTPUT or path.name == "final_resources.csv":
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            urls.update(row.get("resource_url", "").strip() for row in csv.DictReader(handle) if row.get("resource_url"))
    return urls


def contest_kind(page_url: str) -> str:
    return "Spring Camp" if "/joi-sp-" in page_url else "Final Stage"


def task_collections(page_url: str) -> list[str]:
    response = SESSION.get(page_url, timeout=35)
    if response.status_code != 200:
        print(f"WARN skipped unavailable JOI source page: {page_url} ({response.status_code})")
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    collections = []
    for link in soup.select("a[href]"):
        href = requests.compat.urljoin(page_url, link["href"])
        if re.match(r"https://(?:(?:www2|www)\.)?ioi-jp\.org/joi/", href) and href.endswith("index.html"):
            collections.append(href)
    return list(dict.fromkeys(collections))


def candidates() -> list[dict[str, str]]:
    collected: dict[str, dict[str, str]] = {}
    for page_url in OFFICIAL_PAGES:
        stage = contest_kind(page_url)
        for collection_url in task_collections(page_url):
            response = SESSION.get(collection_url, timeout=35)
            if response.status_code != 200:
                print(f"WARN skipped unavailable JOI task collection: {collection_url} ({response.status_code})")
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            session = re.search(r"/(20\d{2})/(20\d{2})-(?:ho|sp)/", collection_url)
            period = f"{session.group(1)}/{session.group(2)}" if session else "archive"

            # Prefer one English final statement per task; retain a Japanese statement only where no English pair exists.
            english_tasks: set[str] = set()
            for link in soup.select('a[href$=".pdf"], a[href*=".pdf?"]'):
                href = link.get("href", "")
                if re.search(r"-(?:t|task)(\d+)-en\.pdf(?:\?|$)", href, re.I):
                    english_tasks.add(re.search(r"-(?:t|task)(\d+)-en\.pdf", href, re.I).group(1))

            for link in soup.select('a[href$=".pdf"], a[href*=".pdf?"]'):
                href = link.get("href", "")
                url = requests.compat.urljoin(collection_url, href)
                basename = url.split("?")[0].rsplit("/", 1)[-1].lower()
                final_english = re.search(r"-(?:t|task)(\d+)-en\.pdf$", basename)
                final_japanese = re.search(r"-(?:t|task)(\d+)\.pdf$", basename)
                preliminary = re.search(r"-pr-(?:t|task)(\d+)\.pdf$", basename)
                solution = re.search(r"-(?:t|task)(\d+)-review\.pdf$", basename)
                task_number = ""
                kind = ""
                language = ""
                if final_english:
                    task_number = final_english.group(1)
                    kind = "Contest paper"
                    language = "English source"
                elif solution:
                    task_number = solution.group(1)
                    kind = "Solution archive"
                    language = "Japanese source; English catalog metadata"
                elif preliminary:
                    task_number = preliminary.group(1)
                    kind = "Contest paper"
                    language = "Japanese source; English catalog metadata"
                elif final_japanese and final_japanese.group(1) not in english_tasks:
                    task_number = final_japanese.group(1)
                    kind = "Contest paper"
                    language = "Japanese source; English catalog metadata"
                else:
                    continue
                noun = "official solution notes" if kind == "Solution archive" else "problem paper"
                collected[url] = {
                    "url": url,
                    "stage": stage,
                    "period": period,
                    "task": task_number,
                    "kind": kind,
                    "language": language,
                    "source_url": collection_url,
                    "noun": noun,
                }
    return list(collected.values())


def verify(candidate: dict[str, str]) -> tuple[str, int, str]:
    try:
        response = requests.get(candidate["url"], timeout=18, stream=True, headers={"User-Agent": "Mozilla/5.0 SignalAtlasResearch/1.0"})
        content_type = response.headers.get("content-type", "")
        response.close()
        return candidate["url"], response.status_code, content_type
    except requests.RequestException as error:
        return candidate["url"], 0, type(error).__name__


def main() -> None:
    existing = existing_free_urls()
    pool_candidates = [candidate for candidate in candidates() if candidate["url"] not in existing]
    pool_candidates.sort(key=lambda row: (row["period"], row["stage"], row["kind"], row["task"]), reverse=True)
    print(f"Non-duplicate JOI task and solution candidates: {len(pool_candidates)}")
    audit: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(verify, candidate): candidate["url"] for candidate in pool_candidates}
        for future in as_completed(futures):
            url, status, content_type = future.result()
            audit[url] = (status, content_type)
    verified = [candidate for candidate in pool_candidates if audit[candidate["url"]][0] == 200][:TARGET_ADDITIONS]
    if len(verified) < TARGET_ADDITIONS:
        raise RuntimeError(f"Only {len(verified)} verified non-duplicate JOI records; refusing to pad the tranche")

    headers = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for candidate in verified:
            writer.writerow({
                "country": "Japan",
                "track": "DM",
                "topic_tags": "discrete mathematics;algorithms;informatics;programming contest;Olympiad;contest;solution",
                "priority": "A",
                "source_type": "National informatics Olympiad archive",
                "source_title": "Japanese Olympiad in Informatics task archive (official)",
                "source_url": candidate["source_url"],
                "resource_title": f"Japanese Olympiad in Informatics {candidate['period']} {candidate['stage']} — Task {candidate['task']} {candidate['noun']}",
                "resource_url": candidate["url"],
                "resource_class": candidate["kind"],
                "language": candidate["language"],
                "notes": "Official JOI contest material. The catalog title and description are supplied in English; the original task or solution URL is preserved.",
                "access_model": "Free public PDF",
                "verification_status": "HTTP 200 · verified 2026-08-14",
                "free_resource": "Yes",
            })
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "http_status", "content_type", "included_in_target"])
        included = {candidate["url"] for candidate in verified}
        for candidate in pool_candidates:
            writer.writerow([candidate["url"], *audit[candidate["url"]], "Yes" if candidate["url"] in included else "No"])
    print(f"Verified and wrote {len(verified)} Japan JOI records to {OUTPUT}")
    print(f"Audit written to {AUDIT}")


if __name__ == "__main__":
    main()
