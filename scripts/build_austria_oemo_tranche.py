"""Build a verified Austria tranche from the official Austrian Mathematics Olympiad archive."""

from __future__ import annotations

import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "client/src/data"
OUTPUT = DATA / "austria_oemo_verified_resources.csv"
AUDIT = ROOT / "research/austria_oemo_url_audit.csv"
ARCHIVE_URL = "https://www.math.aau.at/OeMO/aufgaben/"
HEADERS = {"User-Agent": "Mozilla/5.0 SignalAtlasResearch/1.0"}


def existing_catalog() -> tuple[set[str], int]:
    urls: set[str] = set()
    country_count = 0
    for path in DATA.glob("*.csv"):
        if path in {OUTPUT, DATA / "final_resources.csv"}:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                url = row.get("resource_url", "").strip()
                if url:
                    urls.add(url)
                if row.get("country") == "Austria" and row.get("free_resource") == "Yes":
                    country_count += 1
    return urls, country_count


def discover(existing_urls: set[str]) -> list[dict[str, str]]:
    response = requests.get(ARCHIVE_URL, headers=HEADERS, timeout=45)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    found: list[dict[str, str]] = []
    for anchor in soup.select("a[href]"):
        url = urljoin(ARCHIVE_URL, anchor["href"])
        match = re.search(r"/OeMO/(aufgaben|loesungen)/([A-Z]+)/((?:19|20)\d{2})/?$", url)
        if not match or url in existing_urls:
            continue
        document_path, code, year = match.groups()
        parent = anchor.find_parent("li")
        context = re.sub(r"\s+", " ", parent.get_text(" ", strip=True) if parent else "").strip()
        if not context:
            context = code
        found.append({
            "url": url,
            "year": year,
            "round": context.replace(" Aufgaben Lösungen", "").strip(),
            "kind": "Olympiad problem" if document_path == "aufgaben" else "Solution archive",
            "source_url": ARCHIVE_URL,
        })
    return list({record["url"]: record for record in found}.values())


def verify(record: dict[str, str]) -> tuple[str, int, str]:
    try:
        response = requests.get(record["url"], headers=HEADERS, timeout=35, stream=True, allow_redirects=True)
        status = response.status_code
        content_type = response.headers.get("content-type", "")
        response.close()
        return record["url"], status, content_type
    except requests.RequestException as error:
        return record["url"], 0, type(error).__name__


def main() -> None:
    existing_urls, baseline = existing_catalog()
    needed = max(0, 100 - baseline)
    records = discover(existing_urls)
    records.sort(key=lambda record: (int(record["year"]), record["kind"], record["round"]), reverse=True)
    print(f"Austria baseline: {baseline}; target additions: {needed}; source-discovered non-duplicates: {len(records)}")
    statuses: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(verify, record) for record in records]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            statuses[url] = (status, content_type)
    verified = [record for record in records if statuses[record["url"]][0] == 200 and "pdf" in statuses[record["url"]][1].lower()]
    selected = verified[:needed]
    if len(selected) < needed:
        raise RuntimeError(f"Only {len(selected)} verified public Olympiad documents; refusing to pad Austria's tranche")
    columns = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for record in selected:
            title_kind = "official problem paper" if record["kind"] == "Olympiad problem" else "official solution"
            writer.writerow({
                "country": "Austria",
                "track": "GA",
                "topic_tags": "general aptitude;mathematical reasoning;algebra;geometry;combinatorics;number theory;Olympiad;contest;problem solving",
                "priority": "A",
                "source_type": "National mathematics Olympiad archive",
                "source_title": "Austrian Mathematics Olympiad tasks and solutions (official University of Klagenfurt archive)",
                "source_url": record["source_url"],
                "resource_title": f"Austrian Mathematics Olympiad {record['year']} — {record['round']} — {title_kind}",
                "resource_url": record["url"],
                "resource_class": record["kind"],
                "language": "German source (English catalog label)",
                "notes": "Official archive entry; document route serves the public PDF directly.",
                "access_model": "Free public PDF",
                "verification_status": "HTTP 200 · verified 2026-08-14",
                "free_resource": "Yes",
            })
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "http_status", "content_type", "included"])
        selected_urls = {record["url"] for record in selected}
        for record in records:
            writer.writerow([record["url"], *statuses[record["url"]], "Yes" if record["url"] in selected_urls else "No"])
    print(f"Verified {len(verified)} Austrian Olympiad documents; wrote {len(selected)} records to {OUTPUT}")


if __name__ == "__main__":
    main()
