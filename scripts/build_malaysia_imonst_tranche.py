from __future__ import annotations

import csv
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


"""Signal Atlas data style: source-led, English-facing, and access-audited.

Every candidate is a PDF URL directly published on the official IMONST page.
The builder records the closest source heading and visible link label rather than
guessing archive locations or contest editions.
"""

ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "client/src/data"
OUTPUT = DATA / "malaysia_imonst_verified_resources.csv"
AUDIT = ROOT / "research/malaysia_imonst_url_audit.csv"
SOURCE_URL = "https://imo-malaysia.org/imonst1/"
VERIFY_DATE = "2026-08-15"


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


def clean(text: str) -> str:
    return " ".join(text.split())


def source_context(anchor) -> str:
    heading = anchor.find_previous(["h2", "h3", "h4", "h5"])
    return clean(heading.get_text(" ", strip=True)) if heading else "Syllabus and sample problems"


def candidates(existing: set[str]) -> list[dict[str, str]]:
    soup = BeautifulSoup(fetch_html(), "html.parser")
    records: dict[str, dict[str, str]] = {}
    for anchor in soup.select("a[href]"):
        resource_url = anchor["href"].strip().replace("&amp;", "&")
        parsed = urlparse(resource_url)
        if parsed.scheme != "https" or parsed.netloc != "imo-malaysia.org" or not parsed.path.lower().endswith(".pdf"):
            continue
        if resource_url in existing:
            continue
        visible_label = clean(anchor.get_text(" ", strip=True))
        if not visible_label:
            visible_label = parsed.path.rsplit("/", 1)[-1].replace("_", " ").rsplit(".", 1)[0]
        records[resource_url] = {
            "resource_url": resource_url,
            "label": visible_label,
            "context": source_context(anchor),
        }
    return sorted(records.values(), key=lambda item: (item["context"], item["label"], item["resource_url"]))


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
    print(f"Official IMONST non-duplicate PDF candidates: {len(records)}")
    results: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(verify, record) for record in records]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            results[url] = (status, content_type)
    verified = [
        record for record in records
        if results.get(record["resource_url"], (0, ""))[0] == 200
        and "pdf" in results[record["resource_url"]][1]
    ]
    print(f"Individually verified public IMONST PDFs: {len(verified)}")

    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in verified:
            label = record["label"]
            is_solution = any(word in label.lower() for word in ("answer", "solution"))
            writer.writerow({
                "country": "Malaysia",
                "track": "GA",
                "topic_tags": "mathematical olympiad;problem solving;general aptitude;contest",
                "priority": "A",
                "source_type": "Official national olympiad archive",
                "source_title": "International Mathematical Olympiad National Selection Test (IMONST)",
                "source_url": SOURCE_URL,
                "resource_title": f"IMONST — {record['context']} — {label}",
                "resource_url": record["resource_url"],
                "resource_class": "Official olympiad problem and solution paper" if is_solution else "Official olympiad problem paper",
                "language": "English",
                "notes": f"Public PDF explicitly linked from the official IMONST page under “{record['context']}”.",
                "access_model": "Free public PDF",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "source_context", "visible_label", "http_status", "content_type", "included"])
        for record in records:
            status, content_type = results.get(record["resource_url"], (0, "unavailable"))
            writer.writerow([
                record["resource_url"], record["context"], record["label"], status, content_type,
                "Yes" if record in verified else "No",
            ])
    print(f"Wrote {len(verified)} verified IMONST records to {OUTPUT}")


if __name__ == "__main__":
    main()
