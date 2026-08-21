"""Build the Netherlands tranche from source-discovered Dutch Mathematics Olympiad materials."""

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
OUTPUT = DATA / "netherlands_math_olympiad_verified_resources.csv"
AUDIT = ROOT / "research/netherlands_math_olympiad_url_audit.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 SignalAtlasResearch/1.0"}
SOURCES = [
    ("https://www.wiskundeolympiade.nl/wedstrijdarchief/1e-ronde", "first round"),
    ("https://www.wiskundeolympiade.nl/wedstrijdarchief/finale", "national final"),
]


def current_catalog() -> tuple[set[str], int]:
    urls: set[str] = set()
    count = 0
    for path in DATA.glob("*.csv"):
        if path in {OUTPUT, DATA / "final_resources.csv"}:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("resource_url"):
                    urls.add(row["resource_url"].strip())
                if row.get("country") == "Netherlands" and row.get("free_resource") == "Yes":
                    count += 1
    return urls, count


def document_kind(url: str, label: str) -> str | None:
    combined = f"{url} {label}".lower()
    if any(term in combined for term in ("verslag", "uitslag", "result", "report")):
        return None
    if any(term in combined for term in ("solutions", "uitwerkingen")):
        return "Solution archive"
    if any(term in combined for term in ("problems", "opgaven")):
        return "Olympiad problem"
    return None


def extract(source_url: str, round_name: str, existing_urls: set[str]) -> list[dict[str, str]]:
    response = requests.get(source_url, headers=HEADERS, timeout=45)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    records: list[dict[str, str]] = []
    for anchor in soup.select("a[href]"):
        url = urljoin(source_url, anchor["href"])
        if not re.search(r"/(phocadownload|files)/opgaven/.+\.pdf$", url, re.I) or url in existing_urls:
            continue
        label = re.sub(r"\s+", " ", (anchor.get("title") or anchor.get_text(" ", strip=True))).strip()
        kind = document_kind(url, label)
        if not kind:
            continue
        year_match = re.search(r"/(20\d{2})/", url) or re.search(r"\b(20\d{2})\b", label)
        if not year_match:
            continue
        records.append({
            "url": url,
            "year": year_match.group(1),
            "label": label,
            "kind": kind,
            "round": round_name,
            "source_url": source_url,
            "english": bool(re.search(r"(problems|solutions)", f"{url} {label}", re.I)),
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
    records = [record for source in SOURCES for record in extract(*source, existing_urls)]
    records = list({record["url"]: record for record in records}.values())
    records.sort(key=lambda record: (record["english"], int(record["year"]), record["round"], record["kind"]), reverse=True)
    print(f"Netherlands baseline: {baseline}; target additions: {needed}; source-discovered eligible non-duplicates: {len(records)}")
    statuses: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(verify, record) for record in records]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            statuses[url] = (status, content_type)
    verified = [record for record in records if statuses[record["url"]][0] == 200]
    selected = verified[:needed]
    if len(selected) < needed:
        raise RuntimeError(f"Only {len(selected)} verified Olympiad documents; refusing to pad Netherlands' tranche")
    columns = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for record in selected:
            language = "English" if record["english"] else "Dutch source (English catalog label)"
            document_title = "official problem paper" if record["kind"] == "Olympiad problem" else "official solution"
            writer.writerow({
                "country": "Netherlands",
                "track": "GA",
                "topic_tags": "general aptitude;mathematical reasoning;algebra;geometry;combinatorics;number theory;Olympiad;contest;problem solving",
                "priority": "A",
                "source_type": "National mathematics Olympiad archive",
                "source_title": "Dutch Mathematics Olympiad competition papers and solutions (official)",
                "source_url": record["source_url"],
                "resource_title": f"Dutch Mathematics Olympiad {record['year']} — {record['round']} — {document_title}",
                "resource_url": record["url"],
                "resource_class": record["kind"],
                "language": language,
                "notes": f"Official archive label: {record['label']}",
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
    print(f"Verified {len(verified)} Dutch Olympiad documents; wrote {len(selected)} records to {OUTPUT}")


if __name__ == "__main__":
    main()
