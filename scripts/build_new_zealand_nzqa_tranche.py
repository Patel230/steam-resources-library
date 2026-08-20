"""Build New Zealand's verified NZQA mathematics assessment tranche from official search pages."""

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
OUTPUT = DATA / "new_zealand_nzqa_verified_resources.csv"
AUDIT = ROOT / "research/new_zealand_nzqa_url_audit.csv"
SEARCH_URLS = [
    "https://www.nzqa.govt.nz/ncea/assessment/search.do?query=math&view=exams&level=01",
    "https://www.nzqa.govt.nz/ncea/assessment/search.do?query=math&view=exams&level=02",
    "https://www.nzqa.govt.nz/ncea/assessment/search.do?query=math&view=exams&level=03",
]
TARGET_ADDITIONS = 64
HEADERS = {"User-Agent": "Mozilla/5.0 SignalAtlasResearch/1.0"}
ENGLISH_CODES = {
    "exm": ("Past examination paper", 0, "official examination paper"),
    "qbk": ("Past examination paper", 0, "official question booklet"),
    "res": ("Assessment schedule", 1, "official assessment schedule"),
    "exp": ("Exemplar answer", 2, "official exemplar answer script"),
    "frm": ("Formulae resource", 3, "official formulae resource"),
    "sam": ("Sample assessment", 4, "official sample assessment"),
}


def existing_free_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob("*.csv"):
        if path in {OUTPUT, DATA / "final_resources.csv"}:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            urls.update(row.get("resource_url", "").strip() for row in csv.DictReader(handle) if row.get("resource_url"))
    return urls


def collect_candidates() -> list[dict[str, str | int]]:
    candidates: dict[str, dict[str, str | int]] = {}
    pattern = re.compile(r"/((?:19|20)\d{2})/(\d{5})-([a-z]+)-(?:19|20)\d{2}\.pdf$", re.I)
    for source_url in SEARCH_URLS:
        response = requests.get(source_url, headers=HEADERS, timeout=40)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for anchor in soup.select("a[href]"):
            url = urljoin(source_url, anchor["href"].strip())
            match = pattern.search(url)
            if not match:
                continue
            year, standard, code = match.groups()
            code = code.lower()
            if code not in ENGLISH_CODES:
                continue
            resource_class, rank, label = ENGLISH_CODES[code]
            candidates[url] = {
                "url": url,
                "year": year,
                "standard": standard,
                "resource_class": resource_class,
                "rank": rank,
                "label": label,
                "source_url": source_url,
            }
    return sorted(candidates.values(), key=lambda row: (-int(str(row["year"])), int(row["rank"]), str(row["url"])))


def verify(candidate: dict[str, str | int]) -> tuple[str, int, str]:
    try:
        response = requests.head(str(candidate["url"]), headers=HEADERS, timeout=30, allow_redirects=True)
        status = response.status_code
        content_type = response.headers.get("content-type", "")
        response.close()
        return str(candidate["url"]), status, content_type
    except requests.RequestException as error:
        return str(candidate["url"]), 0, f"{type(error).__name__}: {str(error)[:160]}"


def main() -> None:
    existing = existing_free_urls()
    candidates = [row for row in collect_candidates() if str(row["url"]) not in existing]
    print(f"Non-duplicate official NZQA candidates: {len(candidates)}")
    statuses: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(verify, candidate) for candidate in candidates]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            statuses[url] = (status, content_type)
    status_counts: dict[int, int] = {}
    for status, _content_type in statuses.values():
        status_counts[status] = status_counts.get(status, 0) + 1
    print(f"NZQA verification statuses: {dict(sorted(status_counts.items()))}")
    failures = [detail for status, detail in statuses.values() if status == 0]
    if failures:
        print(f"NZQA verifier failure sample: {failures[0]}")
    verified = [candidate for candidate in candidates if statuses[str(candidate["url"])][0] == 200][:TARGET_ADDITIONS]
    if len(verified) < TARGET_ADDITIONS:
        raise RuntimeError(f"Only {len(verified)} verified NZQA candidates; refusing to pad the tranche")

    columns = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for candidate in verified:
            standard = str(candidate["standard"])
            year = str(candidate["year"])
            label = str(candidate["label"])
            writer.writerow({
                "country": "New Zealand",
                "track": "EM",
                "topic_tags": "mathematics;statistics;calculus;algebra;geometry;trigonometry;probability;past examination;assessment",
                "priority": "A",
                "source_type": "National qualifications assessment archive",
                "source_title": "NZQA NCEA Mathematics and Statistics assessment archive (official)",
                "source_url": str(candidate["source_url"]),
                "resource_title": f"NCEA Mathematics and Statistics standard {standard} — {year} {label}",
                "resource_url": str(candidate["url"]),
                "resource_class": str(candidate["resource_class"]),
                "language": "English source",
                "notes": f"Official NZQA Level 1–3 public mathematics and statistics material; standard {standard}, year {year}.",
                "access_model": "Free public PDF",
                "verification_status": "HTTP 200 · verified 2026-08-14",
                "free_resource": "Yes",
            })
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "http_status", "content_type", "included_in_target"])
        included = {str(candidate["url"]) for candidate in verified}
        for candidate in candidates:
            url = str(candidate["url"])
            writer.writerow([url, *statuses[url], "Yes" if url in included else "No"])
    print(f"Verified and wrote {len(verified)} New Zealand records to {OUTPUT}")
    print(f"Audit written to {AUDIT}")


if __name__ == "__main__":
    main()
