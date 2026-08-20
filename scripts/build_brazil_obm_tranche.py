"""Build Brazil's verified free-resource tranche from the official OBM archive."""

from __future__ import annotations

import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "client/src/data"
OUTPUT = DATA / "brazil_obm_verified_resources.csv"
AUDIT = ROOT / "research/brazil_obm_url_audit.csv"
ARCHIVE = "https://www.obm.org.br/como-se-preparar/provas-e-gabaritos/"
HEADERS = {"User-Agent": "Mozilla/5.0 SignalAtlasResearch/1.0"}


def current_catalog() -> tuple[set[str], int]:
    urls: set[str] = set()
    brazil_count = 0
    for path in DATA.glob("*.csv"):
        if path in {OUTPUT, DATA / "final_resources.csv"}:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("resource_url"):
                    urls.add(row["resource_url"].strip())
                if row.get("country") == "Brazil" and row.get("free_resource") == "Yes":
                    brazil_count += 1
    return urls, brazil_count


def english_label(raw: str, year: str, level: str) -> tuple[str, str]:
    compact = re.sub(r"\s+", " ", raw).strip()
    lower = compact.lower()
    stage_match = re.search(r"(\d)[ªº]\s*Fase", compact, re.I)
    if "fase única" in lower:
        stage = "single-stage"
    elif stage_match:
        stage = f"Stage {stage_match.group(1)}"
    else:
        stage = "archival round"
    is_key = "gabarito" in lower
    level_text = level.replace("Nível", "Level").strip() or "Competition level"
    if is_key:
        return f"OBM {year} — {stage} — {level_text} official answer key", "Solution archive"
    return f"OBM {year} — {stage} — {level_text} official examination paper", "Olympiad problem"


def candidates(existing_urls: set[str]) -> list[dict[str, str]]:
    response = requests.get(ARCHIVE, headers=HEADERS, timeout=45)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    records: list[dict[str, str]] = []
    for card in soup.select("div.prova.post"):
        heading = card.select_one(".title-md")
        anchor = card.select_one('a[href*="/content/uploads/"][href$=".pdf"]')
        if not heading or not anchor:
            continue
        url = anchor["href"].strip()
        if url in existing_urls:
            continue
        raw = re.sub(r"\s+", " ", heading.get_text(" ", strip=True)).strip()
        year_match = re.search(r"\b(19|20)\d{2}\b", raw)
        year = year_match.group(0) if year_match else card.get("data-ano", "archive")
        level = card.get("data-nivel", "")
        title, resource_class = english_label(raw, year, level)
        records.append({
            "year": year,
            "raw": raw,
            "title": title,
            "class": resource_class,
            "url": url,
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
    existing_urls, current_count = current_catalog()
    needed = max(0, 100 - current_count)
    source_records = candidates(existing_urls)
    source_records.sort(key=lambda record: (int(record["year"]) if record["year"].isdigit() else 0, record["class"] == "Olympiad problem"), reverse=True)
    print(f"Brazil baseline: {current_count}; target additions: {needed}; source-discovered non-duplicates: {len(source_records)}")
    statuses: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(verify, record) for record in source_records]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            statuses[url] = (status, content_type)
    verified = [record for record in source_records if statuses[record["url"]][0] == 200]
    selected = verified[:needed]
    if len(selected) < needed:
        raise RuntimeError(f"Only {len(selected)} verified OBM resources; refusing to pad Brazil's tranche")
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
                "country": "Brazil",
                "track": "GA",
                "topic_tags": "general aptitude;mathematical reasoning;algebra;geometry;combinatorics;number theory;Olympiad;contest;problem solving",
                "priority": "A",
                "source_type": "National mathematics Olympiad archive",
                "source_title": "Brazilian Mathematics Olympiad (OBM) past papers and answer keys (official)",
                "source_url": ARCHIVE,
                "resource_title": record["title"],
                "resource_url": record["url"],
                "resource_class": record["class"],
                "language": "Portuguese source (English catalog label)",
                "notes": f"Official OBM archive label: {record['raw']}",
                "access_model": "Free public PDF",
                "verification_status": "HTTP 200 · verified 2026-08-14",
                "free_resource": "Yes",
            })
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "http_status", "content_type", "included"])
        selected_urls = {record["url"] for record in selected}
        for record in source_records:
            writer.writerow([record["url"], *statuses[record["url"]], "Yes" if record["url"] in selected_urls else "No"])
    print(f"Verified {len(verified)} OBM documents; wrote {len(selected)} records to {OUTPUT}")


if __name__ == "__main__":
    main()
