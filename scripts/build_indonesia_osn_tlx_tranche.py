"""Build a verified Indonesia tranche from exact OSN Informatics TLX routes.

The URLs below are transcribed from the organiser-owned OSN archive table. The
builder accepts a contest route only when the public TLX page returns 200 and
contains visible problem-content signals. It does not infer slugs or promote
landing pages that do not expose a problem collection.
"""

import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "client/src/data"
OUTPUT = DATA / "indonesia_osn_tlx_verified_resources.csv"
AUDIT = ROOT / "research/indonesia_osn_tlx_url_audit.csv"
VERIFY_DATE = "2026-08-15"
SOURCE_URL = "https://osn.toki.id/arsip"
HEADERS = {"User-Agent": "Signal Atlas catalog verifier/1.0 (+public-resource-audit)"}

# Exact OSN archive-table routes observed on 2026-08-15; no slug is inferred.
CANDIDATES = [
    ("2020", "KSN", "https://tlx.toki.id/problems/ksn-2020"),
    ("2021", "KSN", "https://tlx.toki.id/problems/ksn-2021"),
    ("2022", "OSN", "https://tlx.toki.id/problems/osn-2022"),
    ("2023", "OSN", "https://tlx.toki.id/problems/osn-2023"),
    ("2024", "OSN", "https://tlx.toki.id/problems/osn-2024"),
    ("2025", "OSN", "https://tlx.toki.id/problems/osn-2025"),
]


def existing_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob("*.csv"):
        if path in {OUTPUT, DATA / "final_resources.csv"}:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                url = row.get("resource_url", "").strip()
                if url:
                    urls.add(url)
    return urls


def verify(candidate: tuple[str, str, str]) -> tuple[tuple[str, str, str], int, str, int]:
    year, event, url = candidate
    try:
        response = requests.get(url, headers=HEADERS, timeout=35, allow_redirects=True)
        status = response.status_code
        content_type = response.headers.get("content-type", "").lower()
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(" ", strip=True).lower()
        problem_links = [
            anchor.get("href", "")
            for anchor in soup.select("a[href]")
            if "/problems/" in anchor.get("href", "") or "/problems/" in anchor.get("href", "")
        ]
        valid = int("problem" in text and (len(problem_links) > 0 or "submission" in text or "contest" in text))
        response.close()
        return candidate, status, content_type, valid
    except requests.RequestException as exc:
        return candidate, 0, f"request error: {type(exc).__name__}", 0


def main() -> None:
    existing = existing_urls()
    candidates = [candidate for candidate in CANDIDATES if candidate[2] not in existing]
    if not candidates:
        raise RuntimeError("No non-duplicate OSN TLX candidate routes found")

    outcomes: dict[str, tuple[int, str, int]] = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(verify, candidate) for candidate in candidates]
        for future in as_completed(futures):
            candidate, status, content_type, valid = future.result()
            outcomes[candidate[2]] = (status, content_type, valid)

    verified = [
        candidate for candidate in candidates
        if outcomes[candidate[2]][0] == 200
        and "text/html" in outcomes[candidate[2]][1]
        and outcomes[candidate[2]][2] == 1
    ]
    if not verified:
        raise RuntimeError("No public OSN TLX problem collection met the verification gate")

    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for year, event, url in verified:
            writer.writerow({
                "country": "Indonesia",
                "track": "DM",
                "topic_tags": "discrete mathematics;algorithms;programming;logic;problem-solving;contest;olympiad;solution",
                "priority": "A",
                "source_type": "National informatics olympiad organiser archive",
                "source_title": "Indonesian National Olympiad in Informatics (OSN) problems archive",
                "source_url": SOURCE_URL,
                "resource_title": f"Indonesia {event} Informatics official problem and solution collection — {year}",
                "resource_url": url,
                "resource_class": "Olympiad problems and solutions",
                "language": "Indonesian source; English-facing metadata",
                "notes": "Public interactive problem collection and organiser-published solution route explicitly linked in the official OSN Informatics archive; original material may be Indonesian and catalog metadata is English-facing.",
                "access_model": "Free public access",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    selected = {url for _, _, url in verified}
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["year", "event", "resource_url", "http_status", "content_type", "problem_content_confirmed", "included"])
        for year, event, url in candidates:
            status, content_type, valid = outcomes[url]
            writer.writerow([year, event, url, status, content_type, valid, "Yes" if url in selected else "No"])

    print(f"Individually verified public Indonesia OSN TLX collections: {len(verified)}")
    print(f"Wrote {len(verified)} records to {OUTPUT}")


if __name__ == "__main__":
    main()
