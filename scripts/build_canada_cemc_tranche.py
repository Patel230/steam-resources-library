"""Extract, verify, and promote CEMC contest and solution PDFs for Canada."""

from __future__ import annotations

import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from time import sleep

import requests
from bs4 import BeautifulSoup


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "client/src/data"
OUTPUT = DATA / "canada_cemc_verified_resources.csv"
AUDIT = ROOT / "research/canada_cemc_url_audit.csv"
ARCHIVE = "https://cemc.uwaterloo.ca/resources/past-contests"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 SignalAtlasResearch/1.0"})

# These public English contest families expose separate contest and solution PDFs in the
# same official table. BCC/CCC supply discrete-computing material; Euclid, Gauss, and PCF
# add university-published mathematical problem sets without relying on inferred URLs.
CATEGORIES = (("BCC", 26), ("CCC", 29), ("Euclid", 24), ("Gauss", 13), ("PCF", 14))


def existing_free_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob("*.csv"):
        if path == OUTPUT or path.name == "final_resources.csv":
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("resource_url"):
                    urls.add(row["resource_url"].strip())
    return urls


def table_candidates() -> list[dict[str, str]]:
    collected: dict[str, dict[str, str]] = {}
    for category_name, category_id in CATEGORIES:
        for page in range(0, 10):
            response = None
            for attempt in range(3):
                try:
                    response = SESSION.get(ARCHIVE, params={"contest_category": category_id, "page": page}, timeout=35)
                    response.raise_for_status()
                    break
                except requests.RequestException:
                    response = None
                    sleep(1 + attempt)
            if response is None:
                print(f"WARN skipped unavailable CEMC table page: category={category_name}, page={page}")
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            rows = soup.select("table tbody tr")
            if not rows:
                break
            discovered = 0
            for row in rows:
                cells = [cell.get_text(" ", strip=True) for cell in row.select("td")]
                if len(cells) < 4:
                    continue
                # Leading column is the English-availability cue, then title/year/grade.
                title, year, grade = cells[1], cells[2], cells[3]
                pdfs = [link.get("href") for link in row.select('a[href$=".pdf"]') if link.get("href")]
                # The official table orders contest PDF, solution PDF, then results PDF.
                for kind, url in (("Contest paper", pdfs[0] if len(pdfs) > 0 else None), ("Solution archive", pdfs[1] if len(pdfs) > 1 else None)):
                    if not url:
                        continue
                    absolute = requests.compat.urljoin(ARCHIVE, url)
                    collected[absolute] = {
                        "category": category_name,
                        "title": title,
                        "year": year,
                        "grade": grade,
                        "kind": kind,
                        "url": absolute,
                    }
                    discovered += 1
            if discovered == 0:
                break
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
    candidates = [candidate for candidate in table_candidates() if candidate["url"] not in existing]
    candidates.sort(key=lambda row: (row["year"], row["category"], row["grade"], row["kind"]), reverse=True)
    print(f"Non-duplicate CEMC contest/solution candidates: {len(candidates)}")

    audit: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(verify, candidate): candidate["url"] for candidate in candidates}
        for future in as_completed(futures):
            url, status, content_type = future.result()
            audit[url] = (status, content_type)

    verified = [candidate for candidate in candidates if audit[candidate["url"]][0] == 200][:100]
    if len(verified) < 100:
        raise RuntimeError(f"Only {len(verified)} verified non-duplicate CEMC records; refusing to pad the tranche")

    headers = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for candidate in verified:
            noun = "contest paper" if candidate["kind"] == "Contest paper" else "solutions"
            writer.writerow({
                "country": "Canada",
                "track": "EM/DM",
                "topic_tags": "engineering mathematics;discrete mathematics;computational thinking;algorithms;problem solving;contest;solution",
                "priority": "A",
                "source_type": "University contest archive",
                "source_title": "University of Waterloo CEMC past contests archive",
                "source_url": ARCHIVE,
                "resource_title": f"CEMC {candidate['title']} {candidate['year']} — Grade {candidate['grade']} {noun}",
                "resource_url": candidate["url"],
                "resource_class": candidate["kind"],
                "language": "English",
                "notes": "Official University of Waterloo CEMC archive entry, extracted from the public past-contests table.",
                "access_model": "Free public PDF",
                "verification_status": "HTTP 200 · verified 2026-08-14",
                "free_resource": "Yes",
            })
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "http_status", "content_type", "included_in_100"])
        included = {candidate["url"] for candidate in verified}
        for candidate in candidates:
            writer.writerow([candidate["url"], *audit[candidate["url"]], "Yes" if candidate["url"] in included else "No"])
    print(f"Verified and wrote {len(verified)} Canada CEMC records to {OUTPUT}")
    print(f"Audit written to {AUDIT}")


if __name__ == "__main__":
    main()
