from __future__ import annotations

import csv
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


"""Signal Atlas data style: source-led, English-facing, and access-audited.

UiTM publishes this public Mathematical Olympiad sample-question series on an
official Google Site. The page names the 2022, 2023, and 2024 sample-question
groups but its embedded Google Drive frames do not expose a reliable one-to-one
year/category caption in static markup. This builder deliberately retains the
source order as an individual document identifier instead of inventing metadata.
"""

ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "client/src/data"
OUTPUT = DATA / "malaysia_uitm_mo_verified_resources.csv"
AUDIT = ROOT / "research/malaysia_uitm_mo_url_audit.csv"
SOURCE_URL = "https://sites.google.com/tmsk.uitm.edu.my/idm-uitm/activities/mathematical-olympiad/sample-questions"
VERIFY_DATE = "2026-08-15"

# Google Sites injects these iframe URLs client-side. This bounded list was
# captured directly from the official rendered source page on 2026-08-15 and
# is retained here as source evidence rather than synthesized from file names.
PUBLISHED_DRIVE_PREVIEWS = [
    "https://drive.google.com/file/d/1dcYC-ecWWclfYkYF_EShNr4dYyeMLN9T/preview",
    "https://drive.google.com/file/d/1FTtDqjhcnyt2Qo_WIR5E0vL9HBu2IXon/preview",
    "https://drive.google.com/file/d/1akCoh4dsNCOWHYm3TqHUzmViBvTOVSci/preview",
    "https://drive.google.com/file/d/1pq_gcoV5JasScSYBpDSbATpn8XFn31KB/preview",
    "https://drive.google.com/file/d/1LYT1MIBBwvTClkG_uBbHKAN1Yv2SxFpE/preview",
    "https://drive.google.com/file/d/1LIa6zgFajUuy4kwhaH9R7STw_hrdGeU7/preview",
    "https://drive.google.com/file/d/1aUo1XlpN_q5Y28YcXB9iiBSkWbfxFQ6S/preview",
    "https://drive.google.com/file/d/1M4SdUeDYE8Ik5dPnwARoKtTDKEkaYEx4/preview",
    "https://drive.google.com/file/d/1ne-dANE2dj261ylcbXbto-07NYkdabFQ/preview",
    "https://drive.google.com/file/d/1wQuPII3WktiuFwYj7EMOwtLTdrGsKxA3/preview",
]


def catalog_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob("*.csv"):
        if path == OUTPUT:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            urls.update(row.get("resource_url", "").strip() for row in csv.DictReader(handle))
    return urls


def fetch_html() -> str:
    request = Request(SOURCE_URL, headers={"User-Agent": "SignalAtlas/1.0 (+public-resource-audit)"})
    with urlopen(request, timeout=40) as response:
        return response.read().decode("utf-8", errors="replace")


def candidates(existing: set[str]) -> list[dict[str, str]]:
    soup = BeautifulSoup(fetch_html(), "html.parser")
    source_urls = [frame["src"].strip().replace("&amp;", "&") for frame in soup.select("iframe[src]")]
    # The server-rendered response often omits Google Sites' client-injected
    # iframe attributes. Include only the bounded official DOM capture above
    # when that happens; no URL is inferred or generated.
    if not source_urls:
        source_urls = PUBLISHED_DRIVE_PREVIEWS
    documents: list[dict[str, str]] = []
    for source in source_urls:
        match = re.fullmatch(r"https://drive\.google\.com/file/d/([\w-]+)/preview", source)
        if not match or source in existing:
            continue
        documents.append({"resource_url": source, "file_id": match.group(1)})
    unique: dict[str, dict[str, str]] = {document["resource_url"]: document for document in documents}
    return list(unique.values())


def verify(record: dict[str, str]) -> tuple[str, int, str]:
    result = subprocess.run(
        [
            "curl", "-L", "--silent", "--show-error", "--max-time", "30",
            "-A", "Mozilla/5.0", "-o", "/dev/null", "-w", "%{http_code}|%{content_type}",
            record["resource_url"],
        ],
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    raw = result.stdout.strip()
    if result.returncode != 0 or "|" not in raw:
        return record["resource_url"], 0, "unavailable"
    code, content_type = raw.split("|", 1)
    return record["resource_url"], int(code) if code.isdigit() else 0, content_type.lower() or "unknown"


def main() -> None:
    records = candidates(catalog_urls())
    print(f"Official UiTM non-duplicate sample-question candidates: {len(records)}")
    results: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(verify, record) for record in records]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            results[url] = (status, content_type)
    verified = [record for record in records if results.get(record["resource_url"], (0, ""))[0] == 200]
    print(f"Individually verified public UiTM sample-question documents: {len(verified)}")

    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, record in enumerate(verified, start=1):
            writer.writerow({
                "country": "Malaysia",
                "track": "GA",
                "topic_tags": "mathematical olympiad;problem solving;general aptitude;contest",
                "priority": "A",
                "source_type": "Official university olympiad archive",
                "source_title": "Mathematical Olympiad, Institute of Mathematical Sciences, Universiti Teknologi MARA (UiTM)",
                "source_url": SOURCE_URL,
                "resource_title": f"UiTM Mathematical Olympiad — Sample-question document {index:02d}",
                "resource_url": record["resource_url"],
                "resource_class": "Official olympiad sample problem document",
                "language": "English",
                "notes": "Public Google Drive preview embedded by UiTM on its official sample-question page. The source page lists 2022–2024 sample-question groups; document order is retained because the static embed markup does not safely attach a year to each individual file.",
                "access_model": "Free public Google Drive preview",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "document_order", "http_status", "content_type", "included"])
        for index, record in enumerate(records, start=1):
            status, content_type = results.get(record["resource_url"], (0, "unavailable"))
            writer.writerow([record["resource_url"], index, status, content_type, "Yes" if record in verified else "No"])
    print(f"Wrote {len(verified)} verified UiTM records to {OUTPUT}")


if __name__ == "__main__":
    main()
