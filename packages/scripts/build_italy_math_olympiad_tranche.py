"""Build Italy's verified free-resource tranche from official Mathematics Olympiad archives."""

from __future__ import annotations

import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "apps/web/src/data"
OUTPUT = DATA / "italy_math_olympiad_verified_resources.csv"
AUDIT = ROOT / "research/italy_math_olympiad_url_audit.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 SignalAtlasResearch/1.0"}
SOURCES = [
    ("https://olimpiadi.dm.unibo.it/le-gare/giochi-di-archimede/", "Archimedes Games opening round", "Olympiad paper and solution pack"),
    ("https://olimpiadi.dm.unibo.it/le-gare/gare-distrettuali/", "February district round", "Olympiad paper and solution pack"),
    ("https://olimpiadi.dm.unibo.it/le-gare/gara-nazionale/", "Cesenatico national individual final", "Olympiad paper and solution pack"),
    ("https://olimpiadi.dm.unibo.it/le-gare/gara-a-squadre/", "Cesenatico national team final", "Team contest paper and solution pack"),
]


def current_catalog() -> tuple[set[str], int]:
    urls: set[str] = set()
    italy_count = 0
    for path in DATA.glob("*.csv"):
        if path in {OUTPUT, DATA / "final_resources.csv"}:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("resource_url"):
                    urls.add(row["resource_url"].strip())
                if row.get("country") == "Italy" and row.get("free_resource") == "Yes":
                    italy_count += 1
    return urls, italy_count


def extract_source(source_url: str, archive_name: str, resource_class: str, known_urls: set[str]) -> list[dict[str, str]]:
    response = requests.get(source_url, headers=HEADERS, timeout=45)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    records: list[dict[str, str]] = []
    for anchor in soup.select("a[href]"):
        href = urljoin(source_url, anchor["href"])
        if not re.search(r"/wp-content/uploads/.+\.(pdf|zip)$", href, re.I) or href in known_urls:
            continue
        label = re.sub(r"\s+", " ", anchor.get_text(" ", strip=True)).strip()
        year_match = re.search(r"\b(19|20)\d{2}\b", label) or re.search(r"\b(19|20)\d{2}\b", href)
        year = year_match.group(0) if year_match else "archive"
        records.append({
            "url": href,
            "year": year,
            "label": label,
            "source_url": source_url,
            "archive_name": archive_name,
            "resource_class": resource_class,
        })
    return records


def verify(record: dict[str, str]) -> tuple[str, int, str]:
    try:
        response = requests.head(record["url"], headers=HEADERS, timeout=30, allow_redirects=True)
        status = response.status_code
        content_type = response.headers.get("content-type", "")
        response.close()
        return record["url"], status, content_type
    except requests.RequestException as error:
        return record["url"], 0, type(error).__name__


def main() -> None:
    existing_urls, baseline = current_catalog()
    needed = max(0, 100 - baseline)
    records = [record for source in SOURCES for record in extract_source(*source, existing_urls)]
    unique_records = {record["url"]: record for record in records}
    records = list(unique_records.values())
    records.sort(key=lambda record: int(record["year"]) if record["year"].isdigit() else 0, reverse=True)
    print(f"Italy baseline: {baseline}; target additions: {needed}; source-discovered non-duplicates: {len(records)}")
    statuses: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(verify, record) for record in records]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            statuses[url] = (status, content_type)
    verified = [record for record in records if statuses[record["url"]][0] == 200]
    selected = verified[:needed]
    if len(selected) < needed:
        raise RuntimeError(f"Only {len(selected)} verified Italy resources; refusing to pad the country tranche")
    columns = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for record in selected:
            writer.writerow({
                "country": "Italy",
                "track": "GA",
                "topic_tags": "general aptitude;mathematical reasoning;algebra;geometry;combinatorics;number theory;Olympiad;contest;problem solving",
                "priority": "A",
                "source_type": "National mathematics Olympiad archive",
                "source_title": "Italian Mathematics Olympiad past papers and solutions (official University of Bologna project)",
                "source_url": record["source_url"],
                "resource_title": f"Italian Mathematics Olympiad {record['year']} — {record['archive_name']} — official archive pack",
                "resource_url": record["url"],
                "resource_class": record["resource_class"],
                "language": "Italian source (English catalog label)",
                "notes": f"Official archive entry: {record['label']}",
                "access_model": "Free public document bundle",
                "verification_status": "HTTP 200 · verified 2026-08-14",
                "free_resource": "Yes",
            })
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "http_status", "content_type", "included"])
        selected_urls = {record["url"] for record in selected}
        for record in records:
            writer.writerow([record["url"], *statuses[record["url"]], "Yes" if record["url"] in selected_urls else "No"])
    print(f"Verified {len(verified)} Italy documents; wrote {len(selected)} records to {OUTPUT}")


if __name__ == "__main__":
    main()
