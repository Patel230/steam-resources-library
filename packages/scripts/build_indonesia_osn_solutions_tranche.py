"""Build a verified Indonesia tranche from the official OSN Informatics solutions archive.

The candidate inventory is transcribed only from explicit solution links observed in
https://osn.toki.id/arsip on 2026-08-15. It deliberately excludes question PDFs
already represented by the earlier TOKI contest-package tranche, and does not
infer any URL from filenames or years.
"""

import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "apps/web/src/data"
OUTPUT = DATA / "indonesia_osn_solutions_verified_resources.csv"
AUDIT = ROOT / "research/indonesia_osn_solutions_url_audit.csv"
VERIFY_DATE = "2026-08-15"
SOURCE_URL = "https://osn.toki.id/arsip"
HEADERS = {"User-Agent": "Signal Atlas catalog verifier/1.0 (+public-resource-audit)"}

# Exact source-published solution links observed in the official rendered table.
CANDIDATES = [
    ("2013", "https://osn.toki.id/data/OSN2013Pembahasan.pdf", "PDF"),
    ("2015", "https://osn.toki.id/data/OSN2015Pembahasan.pdf", "PDF"),
    ("2017", "https://osn.toki.id/data/OSN2017Pembahasan.pdf", "PDF"),
    ("2018", "https://osn.toki.id/data/OSN2018Pembahasan.pdf", "PDF"),
    ("2019", "https://osn.toki.id/data/OSN2019Pembahasan.pdf", "PDF"),
    ("2020", "https://docs.google.com/presentation/d/1NrPtZ5zKC443hjPsu0EByZqKIhWy5aPMPN6fEHvGqjc/", "Google Slides"),
    ("2021", "https://docs.google.com/presentation/d/1ZvDBHjdHDLE2z2smygAP-po1peWPzxFGoYqDzoRDTzg/", "Google Slides"),
    ("2022", "https://docs.google.com/presentation/d/10yjaJYmQqGaAin8Eq70OHQQ5ZUtXNFq4cKihXB9oyb4/", "Google Slides"),
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


def verify(candidate: tuple[str, str, str]) -> tuple[tuple[str, str, str], int, str]:
    year, url, kind = candidate
    try:
        response = requests.get(url, headers=HEADERS, timeout=35, allow_redirects=True)
        status = response.status_code
        content_type = response.headers.get("content-type", "").lower()
        response.close()
        return candidate, status, content_type
    except requests.RequestException as exc:
        return candidate, 0, f"request error: {type(exc).__name__}"


def main() -> None:
    existing = existing_urls()
    candidates = [candidate for candidate in CANDIDATES if candidate[1] not in existing]
    if not candidates:
        raise RuntimeError("No non-duplicate source-published OSN solution candidates found")

    outcomes: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(verify, candidate) for candidate in candidates]
        for future in as_completed(futures):
            candidate, status, content_type = future.result()
            outcomes[candidate[1]] = (status, content_type)

    verified = []
    for year, url, kind in candidates:
        status, content_type = outcomes[url]
        is_pdf = kind == "PDF" and "pdf" in content_type
        is_public_slide = kind == "Google Slides" and "text/html" in content_type
        if status == 200 and (is_pdf or is_public_slide):
            verified.append((year, url, kind))

    if not verified:
        raise RuntimeError("No direct OSN solution resource passed public-access verification")

    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for year, url, kind in sorted(verified):
            writer.writerow({
                "country": "Indonesia",
                "track": "DM",
                "topic_tags": "discrete mathematics;algorithms;programming;logic;problem-solving;contest;olympiad;solution",
                "priority": "A",
                "source_type": "National informatics olympiad organiser archive",
                "source_title": "Indonesian National Olympiad in Informatics (OSN) solutions archive",
                "source_url": SOURCE_URL,
                "resource_title": f"Indonesia OSN Informatics official solution set — {year}",
                "resource_url": url,
                "resource_class": "Official solution set" if kind == "PDF" else "Official solution presentation",
                "language": "Indonesian source; English-facing metadata",
                "notes": f"{kind} solution material explicitly linked in the organiser-owned OSN Informatics archive; original material may be Indonesian and catalog metadata is English-facing.",
                "access_model": "Free public access",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    included = {url for _, url, _ in verified}
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["year", "resource_url", "resource_kind", "http_status", "content_type", "included"])
        for year, url, kind in candidates:
            status, content_type = outcomes[url]
            writer.writerow([year, url, kind, status, content_type, "Yes" if url in included else "No"])

    print(f"Individually verified public Indonesia OSN solution resources: {len(verified)}")
    print(f"Wrote {len(verified)} records to {OUTPUT}")


if __name__ == "__main__":
    main()
